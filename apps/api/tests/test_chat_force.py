"""Pre-call budget gate on /chat and the `?force=true` bypass."""

from __future__ import annotations

from typing import Any

import pytest
from py2dataiku.llm.providers import MockProvider

from app.deps import get_cost_meter
from app.services import chat as chat_service
from app.services.cost_meter import BudgetSettings


SAMPLE_FLOW: dict[str, Any] = {
    "flow_name": "trade_capture",
    "datasets": [{"name": "raw"}],
    "recipes": [
        {"name": "prep", "type": "PREPARE", "inputs": ["raw"], "outputs": ["clean"]}
    ],
}


def _squeeze_budget() -> None:
    meter = get_cost_meter()
    meter.set_budget(
        BudgetSettings(
            monthly_cap_usd=0.001,
            per_call_cap_usd=0.001,
            alert_threshold_pct=80.0,
        )
    )


@pytest.mark.asyncio
async def test_chat_returns_402_when_budget_exceeded(client) -> None:  # type: ignore[no-untyped-def]
    _squeeze_budget()
    resp = await client.post(
        "/chat",
        json={
            "flow_json": SAMPLE_FLOW,
            "question": "Q",
            # Anthropic provider triggers the gate; mock is exempt.
            "provider": "anthropic",
            "stream": False,
        },
    )
    assert resp.status_code == 402, resp.text
    detail = resp.json()["detail"]
    assert detail["title"] == "Budget exceeded"
    assert detail["projected_cost_usd"] > 0


@pytest.mark.asyncio
async def test_chat_force_true_bypasses_gate(  # type: ignore[no-untyped-def]
    client, monkeypatch
) -> None:
    _squeeze_budget()
    # Stub provider so the call returns immediately.
    mock = MockProvider(responses={"Q": "ok"})
    monkeypatch.setattr(chat_service, "resolve_provider", lambda *a, **kw: mock)
    resp = await client.post(
        "/chat?force=true",
        json={
            "flow_json": SAMPLE_FLOW,
            "question": "Q",
            "provider": "anthropic",
            "stream": False,
        },
    )
    # 402 must be bypassed. Downstream may 200 (mock OK) or 5xx (provider
    # error in stricter envs); we only care that the gate didn't fire.
    assert resp.status_code != 402, resp.text
