"""Pre-call budget gate on /convert and the `?force=true` bypass.

Hits two contracts:
  1. With LLM mode + a budget that the projected cost would breach,
     /convert returns 402 with `projected_cost_usd` in the detail.
  2. Re-firing the same call with `?force=true` bypasses the gate and the
     conversion proceeds (status 200 / 422 — anything but 402, since `mock`
     provider is exempt and we want to assert the gate logic, not the
     downstream LLM call's success).
"""

from __future__ import annotations

import pytest

from app.deps import get_cost_meter
from app.services.cost_meter import BudgetSettings


@pytest.fixture
def squeeze_budget() -> None:
    """Set the budget cap so any non-zero LLM call gets blocked.

    We squeeze BOTH per-call and monthly caps to near-zero so the
    pre-call projection (~$0.04 at the heuristic input/output ceilings) is
    guaranteed to breach.
    """
    meter = get_cost_meter()
    meter.set_budget(
        BudgetSettings(
            monthly_cap_usd=0.001,
            per_call_cap_usd=0.001,
            alert_threshold_pct=80.0,
        )
    )


@pytest.mark.asyncio
async def test_convert_returns_402_when_budget_exceeded(  # type: ignore[no-untyped-def]
    client, squeeze_budget
) -> None:
    body = {
        "code": "import pandas as pd\ndf = pd.DataFrame()\n",
        "mode": "llm",
        "options": {"provider": "anthropic", "model": "claude-3-5-sonnet-latest"},
    }
    resp = await client.post("/convert", json=body)
    assert resp.status_code == 402, resp.text
    detail = resp.json()["detail"]
    assert "projected_cost_usd" in detail
    assert detail["projected_cost_usd"] > 0


@pytest.mark.asyncio
async def test_convert_force_true_bypasses_budget_gate(  # type: ignore[no-untyped-def]
    client, squeeze_budget
) -> None:
    body = {
        "code": "import pandas as pd\ndf = pd.DataFrame()\n",
        "mode": "llm",
        "options": {"provider": "anthropic", "model": "claude-3-5-sonnet-latest"},
    }
    resp = await client.post("/convert?force=true", json=body)
    # The downstream LLM call may fail (no real API key in tests) — what
    # matters is that we got PAST the 402 gate. Any non-402 status proves
    # the bypass worked.
    assert resp.status_code != 402, resp.text


@pytest.mark.asyncio
async def test_convert_rule_mode_skips_budget_gate(client, squeeze_budget) -> None:  # type: ignore[no-untyped-def]
    """Rule mode is offline — the gate must never trigger."""
    body = {
        "code": "import pandas as pd\ndf = pd.DataFrame()\n",
        "mode": "rule",
    }
    resp = await client.post("/convert", json=body)
    assert resp.status_code != 402, resp.text
