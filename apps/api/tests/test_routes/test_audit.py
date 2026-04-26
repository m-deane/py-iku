"""Tests for GET /audit (M7)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.deps import get_audit_repo
from app.store import AuditEvent


def _flow(name: str = "f") -> dict:
    return {
        "flow_name": name,
        "total_recipes": 0,
        "total_datasets": 0,
        "datasets": [],
        "recipes": [],
    }


@pytest.mark.asyncio
async def test_audit_returns_appended_events(client) -> None:  # type: ignore[no-untyped-def]
    repo = get_audit_repo()
    repo.append(
        AuditEvent(
            actor="alice",
            action="flow.create",
            resource_type="flow",
            resource_id="r1",
        )
    )
    response = await client.get("/audit")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["events"]
    assert any(ev["action"] == "flow.create" for ev in body["events"])


@pytest.mark.asyncio
async def test_audit_filters_by_actor(client) -> None:  # type: ignore[no-untyped-def]
    repo = get_audit_repo()
    for actor in ("alice", "bob"):
        repo.append(
            AuditEvent(
                actor=actor, action="x", resource_type="t", resource_id="r"
            )
        )
    response = await client.get("/audit", params={"actor": "alice"})
    assert response.status_code == 200
    body = response.json()
    assert all(ev["actor"] == "alice" for ev in body["events"])


@pytest.mark.asyncio
async def test_audit_pagination_advances_cursor(client) -> None:  # type: ignore[no-untyped-def]
    repo = get_audit_repo()
    for i in range(5):
        repo.append(
            AuditEvent(
                actor="x",
                action="a",
                resource_type="t",
                resource_id=f"r{i}",
            )
        )
    page1 = await client.get("/audit", params={"limit": 2})
    body1 = page1.json()
    assert len(body1["events"]) == 2
    assert body1["next_cursor"] is not None

    page2 = await client.get(
        "/audit", params={"limit": 2, "cursor": body1["next_cursor"]}
    )
    body2 = page2.json()
    assert len(body2["events"]) == 2
    assert [ev["resource_id"] for ev in body2["events"]] == ["r2", "r3"]


@pytest.mark.asyncio
async def test_audit_invalid_since_returns_422(client) -> None:  # type: ignore[no-untyped-def]
    response = await client.get("/audit", params={"since": "not-a-timestamp"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_audit_filters_by_since(client) -> None:  # type: ignore[no-untyped-def]
    repo = get_audit_repo()
    past = (datetime.now(tz=timezone.utc) - timedelta(days=1)).isoformat()
    repo.append(
        AuditEvent(
            actor="x", action="old", resource_type="t", resource_id="r1", ts=past
        )
    )
    repo.append(
        AuditEvent(actor="x", action="new", resource_type="t", resource_id="r2")
    )
    cutoff = (datetime.now(tz=timezone.utc) - timedelta(hours=1)).isoformat()
    response = await client.get("/audit", params={"since": cutoff})
    assert response.status_code == 200
    body = response.json()
    actions = {ev["action"] for ev in body["events"]}
    assert "new" in actions
    assert "old" not in actions
