"""Append-only audit event log (JSONL on disk)."""

from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class AuditEvent:
    """A single audit log entry."""

    actor: str
    action: str
    resource_type: str
    resource_id: str
    details: dict[str, Any] = field(default_factory=dict)
    ts: str = field(default_factory=lambda: datetime.now(tz=UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuditEvent:
        return cls(
            actor=str(data.get("actor", "")),
            action=str(data.get("action", "")),
            resource_type=str(data.get("resource_type", "")),
            resource_id=str(data.get("resource_id", "")),
            details=dict(data.get("details") or {}),
            ts=str(data.get("ts") or datetime.now(tz=UTC).isoformat()),
        )


def _parse_iso(ts: str) -> datetime | None:
    try:
        return datetime.fromisoformat(ts)
    except (TypeError, ValueError):
        return None


class AuditRepo:
    """Thread-safe append-only JSONL audit log."""

    LOG_FILENAME = "audit.log"

    def __init__(self, base_dir: Path | str) -> None:
        self._base_dir = Path(base_dir)
        self._log_path = self._base_dir / self.LOG_FILENAME
        self._lock = threading.Lock()
        self._base_dir.mkdir(parents=True, exist_ok=True)
        if not self._log_path.exists():
            self._log_path.touch()

    def append(self, event: AuditEvent) -> None:
        """Append a single event as one JSON line."""
        line = json.dumps(event.to_dict(), separators=(",", ":"))
        with self._lock:
            with self._log_path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
                fh.flush()

    def _read_all(self) -> list[AuditEvent]:
        if not self._log_path.exists():
            return []
        events: list[AuditEvent] = []
        with self._log_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(AuditEvent.from_dict(json.loads(line)))
                except json.JSONDecodeError:
                    continue
        return events

    def list(
        self,
        *,
        since: datetime | None = None,
        actor: str | None = None,
        limit: int = 100,
        cursor: str | None = None,
    ) -> tuple[list[AuditEvent], str | None]:
        """Return at most *limit* matching events.

        ``cursor`` is the index (as a string) of the last item returned
        in the previous page; the next page starts at ``int(cursor) + 1``
        within the filtered list.
        """
        if limit <= 0:
            return [], None
        with self._lock:
            all_events = self._read_all()

        filtered: list[AuditEvent] = []
        for ev in all_events:
            if actor and ev.actor != actor:
                continue
            if since is not None:
                ev_dt = _parse_iso(ev.ts)
                if ev_dt is None:
                    continue
                if ev_dt.tzinfo is None:
                    ev_dt = ev_dt.replace(tzinfo=UTC)
                if ev_dt < since:
                    continue
            filtered.append(ev)

        start = 0
        if cursor is not None:
            try:
                start = int(cursor) + 1
            except (TypeError, ValueError):
                start = 0

        page = filtered[start : start + limit]
        next_index = start + limit
        next_cursor = str(next_index - 1) if next_index < len(filtered) else None
        return page, next_cursor
