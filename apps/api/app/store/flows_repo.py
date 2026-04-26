"""Append-only repository for saved flows.

Storage model: one JSON file per flow under ``settings.flows_dir / "flows" /
{id}.json``.  Writes are atomic (``tempfile`` + ``os.replace``) and
serialised through a ``threading.Lock`` so concurrent requests cannot
corrupt the file.

A small ``index.json`` keeps an ordered list of saved-flow ids so
listing remains O(N) without scanning the directory on every call.
"""

from __future__ import annotations

import json
import os
import tempfile
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class SavedFlow:
    """A persisted flow record returned by ``FlowsRepo``."""

    id: str
    name: str
    flow: dict[str, Any]
    created_at: str
    updated_at: str
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SavedFlow:
        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            flow=dict(data["flow"]),
            created_at=str(data["created_at"]),
            updated_at=str(data["updated_at"]),
            tags=list(data.get("tags") or []),
        )


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


def _atomic_write_text(path: Path, content: str) -> None:
    """Write *content* to *path* atomically (tempfile + os.replace)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=".tmp-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, path)
    except BaseException:
        # Best-effort cleanup on failure
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
        raise


class FlowsRepo:
    """Thread-safe, JSON-on-disk repo of saved flows."""

    INDEX_FILENAME = "index.json"
    FLOWS_DIRNAME = "flows"

    def __init__(self, base_dir: Path | str) -> None:
        self._base_dir = Path(base_dir)
        self._flows_dir = self._base_dir / self.FLOWS_DIRNAME
        self._index_path = self._base_dir / self.INDEX_FILENAME
        self._lock = threading.Lock()
        self._flows_dir.mkdir(parents=True, exist_ok=True)
        if not self._index_path.exists():
            _atomic_write_text(self._index_path, json.dumps({"ids": []}))

    # ------------------------------------------------------------------
    # internal helpers (caller must hold ``self._lock``)
    # ------------------------------------------------------------------

    def _read_index(self) -> list[str]:
        try:
            raw = self._index_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return []
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return []
        ids = data.get("ids") if isinstance(data, dict) else None
        return list(ids) if isinstance(ids, list) else []

    def _write_index(self, ids: list[str]) -> None:
        _atomic_write_text(
            self._index_path, json.dumps({"ids": list(ids)}, indent=2)
        )

    def _flow_path(self, flow_id: str) -> Path:
        return self._flows_dir / f"{flow_id}.json"

    def _read_flow(self, flow_id: str) -> SavedFlow | None:
        path = self._flow_path(flow_id)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        return SavedFlow.from_dict(data)

    def _write_flow(self, record: SavedFlow) -> None:
        _atomic_write_text(
            self._flow_path(record.id),
            json.dumps(record.to_dict(), indent=2),
        )

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def save(
        self, flow: dict[str, Any], name: str, tags: list[str] | None = None
    ) -> SavedFlow:
        """Persist a new flow and return the ``SavedFlow`` record."""
        with self._lock:
            flow_id = str(uuid.uuid4())
            ts = _now_iso()
            record = SavedFlow(
                id=flow_id,
                name=name,
                flow=dict(flow),
                created_at=ts,
                updated_at=ts,
                tags=list(tags or []),
            )
            self._write_flow(record)
            ids = self._read_index()
            ids.append(flow_id)
            self._write_index(ids)
            return record

    def get(self, flow_id: str) -> SavedFlow | None:
        with self._lock:
            return self._read_flow(flow_id)

    def update(
        self,
        flow_id: str,
        *,
        flow: dict[str, Any] | None = None,
        name: str | None = None,
        tags: list[str] | None = None,
    ) -> SavedFlow:
        """Patch a saved flow.  Raises ``KeyError`` if the id is unknown."""
        with self._lock:
            existing = self._read_flow(flow_id)
            if existing is None:
                raise KeyError(flow_id)
            updated = SavedFlow(
                id=existing.id,
                name=name if name is not None else existing.name,
                flow=dict(flow) if flow is not None else existing.flow,
                created_at=existing.created_at,
                updated_at=_now_iso(),
                tags=list(tags) if tags is not None else existing.tags,
            )
            self._write_flow(updated)
            return updated

    def list(
        self, *, limit: int = 50, cursor: str | None = None
    ) -> tuple[list[SavedFlow], str | None]:
        """Return up to *limit* records starting after *cursor* (last seen id).

        The cursor is the id of the last item returned in the previous page;
        the next page begins with the item immediately after it.  When no
        more items are available the returned cursor is ``None``.
        """
        if limit <= 0:
            return [], None
        with self._lock:
            ids = self._read_index()
            start = 0
            if cursor is not None:
                try:
                    start = ids.index(cursor) + 1
                except ValueError:
                    return [], None
            page_ids = ids[start : start + limit]
            records: list[SavedFlow] = []
            for fid in page_ids:
                rec = self._read_flow(fid)
                if rec is not None:
                    records.append(rec)
            next_cursor = (
                page_ids[-1] if (start + limit) < len(ids) and page_ids else None
            )
            return records, next_cursor
