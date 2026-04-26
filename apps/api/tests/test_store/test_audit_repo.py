"""Tests for ``AuditRepo`` (M7)."""

from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.store.audit_repo import AuditEvent, AuditRepo


def test_append_and_list_round_trip(tmp_path: Path) -> None:
    repo = AuditRepo(tmp_path)
    repo.append(
        AuditEvent(
            actor="alice",
            action="flow.create",
            resource_type="flow",
            resource_id="f-1",
            details={"name": "x"},
        )
    )
    events, cursor = repo.list()
    assert len(events) == 1
    assert events[0].actor == "alice"
    assert events[0].action == "flow.create"
    assert cursor is None


def test_filter_by_actor(tmp_path: Path) -> None:
    repo = AuditRepo(tmp_path)
    for actor in ("alice", "bob", "alice"):
        repo.append(
            AuditEvent(
                actor=actor, action="x", resource_type="t", resource_id="r"
            )
        )
    events, _ = repo.list(actor="alice")
    assert len(events) == 2
    assert all(ev.actor == "alice" for ev in events)


def test_filter_by_since(tmp_path: Path) -> None:
    repo = AuditRepo(tmp_path)
    past = (datetime.now(tz=timezone.utc) - timedelta(days=1)).isoformat()
    future = (datetime.now(tz=timezone.utc) + timedelta(days=1)).isoformat()
    repo.append(
        AuditEvent(
            actor="x", action="a", resource_type="t", resource_id="r1", ts=past
        )
    )
    repo.append(
        AuditEvent(
            actor="x", action="a", resource_type="t", resource_id="r2"
        )
    )
    cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=1)
    events, _ = repo.list(since=cutoff)
    # The "past" event should be filtered out.
    assert len(events) == 1
    assert events[0].resource_id == "r2"
    # And a "since" filter strictly in the future yields nothing.
    cutoff2 = datetime.fromisoformat(future) + timedelta(seconds=1)
    events2, _ = repo.list(since=cutoff2)
    assert events2 == []


def test_pagination_with_cursor_is_stable(tmp_path: Path) -> None:
    repo = AuditRepo(tmp_path)
    for i in range(5):
        repo.append(
            AuditEvent(
                actor="x",
                action="a",
                resource_type="t",
                resource_id=f"r{i}",
            )
        )
    page1, cursor1 = repo.list(limit=2)
    assert [ev.resource_id for ev in page1] == ["r0", "r1"]
    assert cursor1 is not None
    page2, cursor2 = repo.list(limit=2, cursor=cursor1)
    assert [ev.resource_id for ev in page2] == ["r2", "r3"]
    page3, cursor3 = repo.list(limit=2, cursor=cursor2)
    assert [ev.resource_id for ev in page3] == ["r4"]
    assert cursor3 is None


def test_concurrent_appends_keep_log_intact(tmp_path: Path) -> None:
    repo = AuditRepo(tmp_path)

    def writer(prefix: str) -> None:
        for i in range(25):
            repo.append(
                AuditEvent(
                    actor=prefix,
                    action="a",
                    resource_type="t",
                    resource_id=f"{prefix}-{i}",
                )
            )

    threads = [threading.Thread(target=writer, args=(p,)) for p in ["x", "y", "z"]]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    events, _ = repo.list(limit=1000)
    assert len(events) == 75
    # Every line should have parsed cleanly.
    assert {ev.actor for ev in events} == {"x", "y", "z"}
