"""File-backed JSONL store for inline comments on recipes.

Single-user mode for v1 — each comment defaults its ``author`` to the
``STUDIO_AUTHOR`` environment variable (or ``"you"`` when unset).  Storage
is one JSONL file per ``flow_id`` under ``settings.flows_dir / "comments"``,
making the layout symmetrical with the existing ``FlowsRepo`` and easy to
inspect from the shell.

Multi-user collaboration (real-time, presence, mentions) is explicitly
out-of-scope and tracked as a Wave 5+ extension.
"""

from __future__ import annotations

import json
import os
import re
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class Comment:
    """A single inline comment on a recipe within a flow."""

    id: str
    flow_id: str
    recipe_id: str
    author: str
    body: str
    timestamp: str
    edited_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Comment:
        return cls(
            id=str(data["id"]),
            flow_id=str(data["flow_id"]),
            recipe_id=str(data["recipe_id"]),
            author=str(data.get("author") or "you"),
            body=str(data["body"]),
            timestamp=str(data["timestamp"]),
            edited_at=(
                str(data["edited_at"])
                if data.get("edited_at") is not None
                else None
            ),
        )


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


def _default_author() -> str:
    return os.environ.get("STUDIO_AUTHOR") or "you"


_FLOW_ID_RE = re.compile(r"[0-9a-fA-F\-]{1,64}")


def _safe_flow_id(flow_id: str) -> bool:
    """UUID-shaped ids only — prevents path traversal via crafted ids."""
    return bool(_FLOW_ID_RE.fullmatch(flow_id))


class CommentsStore:
    """Append-only JSONL comments store, one file per ``flow_id``."""

    DIRNAME = "comments"

    def __init__(self, base_dir: Path | str) -> None:
        self._dir = Path(base_dir) / self.DIRNAME
        self._dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # internal
    # ------------------------------------------------------------------

    def _flow_file(self, flow_id: str) -> Path:
        if not _safe_flow_id(flow_id):
            raise ValueError(f"Invalid flow_id {flow_id!r}")
        path = (self._dir / f"{flow_id}.jsonl").resolve()
        if not str(path).startswith(str(self._dir.resolve())):
            raise ValueError(f"flow_id {flow_id!r} escapes the comments directory")
        return self._dir / f"{flow_id}.jsonl"

    def _read_all(self, flow_id: str) -> list[Comment]:
        path = self._flow_file(flow_id)
        if not path.exists():
            return []
        out: list[Comment] = []
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(Comment.from_dict(json.loads(line)))
                except (json.JSONDecodeError, KeyError):
                    continue
        return out

    def _write_all(self, flow_id: str, comments: list[Comment]) -> None:
        """Rewrite the JSONL file atomically — used by ``delete``."""
        path = self._flow_file(flow_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            for c in comments:
                fh.write(json.dumps(c.to_dict(), separators=(",", ":")) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def list(self, flow_id: str) -> list[Comment]:
        """Return all comments for *flow_id* (chronological)."""
        try:
            with self._lock:
                return self._read_all(flow_id)
        except ValueError:
            return []

    def add(
        self,
        flow_id: str,
        recipe_id: str,
        body: str,
        author: str | None = None,
    ) -> Comment:
        """Append a new comment and return the persisted record."""
        if not body or not body.strip():
            raise ValueError("body must be non-empty")
        if len(body) > 4000:
            raise ValueError("body exceeds 4000 characters")
        if not recipe_id or not recipe_id.strip():
            raise ValueError("recipe_id must be non-empty")
        comment = Comment(
            id=str(uuid.uuid4()),
            flow_id=flow_id,
            recipe_id=recipe_id,
            author=(author or _default_author()).strip() or "you",
            body=body.strip(),
            timestamp=_now_iso(),
        )
        with self._lock:
            path = self._flow_file(flow_id)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(comment.to_dict(), separators=(",", ":")) + "\n")
                fh.flush()
        return comment

    def delete(self, flow_id: str, comment_id: str) -> bool:
        """Remove a comment by id.  Returns True if it was found."""
        with self._lock:
            try:
                comments = self._read_all(flow_id)
            except ValueError:
                return False
            remaining = [c for c in comments if c.id != comment_id]
            if len(remaining) == len(comments):
                return False
            self._write_all(flow_id, remaining)
            return True
