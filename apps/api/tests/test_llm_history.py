"""Tests for /llm-history listing, CSV export, and budget endpoints."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.deps import get_llm_audit_repo
from app.services.llm_audit import LlmCallRecord


def _seed(repo, *, n: int = 3) -> None:
    base = datetime.now(tz=UTC) - timedelta(minutes=n)
    for i in range(n):
        repo.append(
            LlmCallRecord(
                ts=(base + timedelta(seconds=i)).isoformat(),
                mode="llm",
                provider="anthropic" if i % 2 == 0 else "openai",
                model="claude-3-5-sonnet-latest",
                prompt_tokens=1000 * (i + 1),
                completion_tokens=500 * (i + 1),
                cost_usd=0.01 * (i + 1),
                status="success" if i != 1 else "failure",
                feature="chat",
                flow_id=f"flow-{i}",
            )
        )


@pytest.mark.asyncio
async def test_llm_history_lists_newest_first(client) -> None:  # type: ignore[no-untyped-def]
    repo = get_llm_audit_repo()
    _seed(repo, n=3)
    resp = await client.get("/llm-history")
    body = resp.json()
    assert resp.status_code == 200
    assert len(body["records"]) == 3
    # newest-first
    ts = [r["ts"] for r in body["records"]]
    assert ts == sorted(ts, reverse=True)


@pytest.mark.asyncio
async def test_llm_history_filters_provider_and_status(client) -> None:  # type: ignore[no-untyped-def]
    repo = get_llm_audit_repo()
    _seed(repo, n=4)
    only_anthropic = await client.get("/llm-history?provider=anthropic")
    assert all(r["provider"] == "anthropic" for r in only_anthropic.json()["records"])
    only_failed = await client.get("/llm-history?status=failure")
    assert all(r["status"] == "failure" for r in only_failed.json()["records"])


@pytest.mark.asyncio
async def test_llm_history_csv_export(client) -> None:  # type: ignore[no-untyped-def]
    repo = get_llm_audit_repo()
    _seed(repo, n=2)
    resp = await client.get("/llm-history.csv")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    body = resp.text
    assert "timestamp,mode,provider,model" in body
    assert "claude-3-5-sonnet-latest" in body


@pytest.mark.asyncio
async def test_cost_summary_aggregates_today_and_month(client) -> None:  # type: ignore[no-untyped-def]
    repo = get_llm_audit_repo()
    _seed(repo, n=3)  # 0.01 + 0.02 + 0.03 = 0.06 today
    resp = await client.get("/llm-cost-summary")
    body = resp.json()
    assert resp.status_code == 200
    assert pytest.approx(body["today_usd"], rel=1e-3) == 0.06
    assert pytest.approx(body["month_usd"], rel=1e-3) == 0.06
    assert body["budget"]["monthly_cap_usd"] == 50.0


@pytest.mark.asyncio
async def test_budget_round_trip(client) -> None:  # type: ignore[no-untyped-def]
    initial = await client.get("/llm-budget")
    assert initial.json()["monthly_cap_usd"] == 50.0
    upd = await client.put(
        "/llm-budget",
        json={"monthly_cap_usd": 100.0, "per_call_cap_usd": 0.50, "alert_threshold_pct": 75.0},
    )
    body = upd.json()
    assert body["monthly_cap_usd"] == 100.0
    assert body["per_call_cap_usd"] == 0.50
    assert body["alert_threshold_pct"] == 75.0
    after = await client.get("/llm-budget")
    assert after.json()["monthly_cap_usd"] == 100.0


@pytest.mark.asyncio
async def test_chat_blocks_when_over_per_call_cap(client, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Set a tiny per-call cap and confirm the chat call is blocked with HTTP 402."""
    # Set cap below the projected cost for any non-mock model.
    await client.put(
        "/llm-budget",
        json={
            "monthly_cap_usd": 100.0,
            "per_call_cap_usd": 0.0001,
            "alert_threshold_pct": 80.0,
        },
    )
    resp = await client.post(
        "/chat",
        json={
            "flow_json": {"flow_name": "x", "datasets": [], "recipes": []},
            "question": "hi",
            "provider": "anthropic",
        },
    )
    assert resp.status_code == 402
    detail = resp.json()["detail"]
    assert "exceeds per-call cap" in detail["reason"]
    assert "projected_cost_usd" in detail
