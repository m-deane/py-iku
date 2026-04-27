"""LLM call audit log — JSON-Lines persistence of every LLM call made via Studio.

Records timestamp, mode, provider, model, prompt/completion tokens, cost
estimate, success/failure, and the related flow id (when available). The log
is append-only and stored alongside the existing audit log under
``Settings.flows_dir / llm-history.log``.

Cost estimation lives next to the recording logic so a single source of truth
controls both the persisted ``cost_usd`` field and any in-flight budget checks
performed by ``cost_meter.py``.
"""

from __future__ import annotations

import csv
import io
import json
import threading
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Pricing table (USD per 1M tokens). Numbers track public list pricing as of
# 2026-Q1; they are deliberately conservative, and the cost-meter rounds up.
# Pull-requests adjusting these values should also update the docstring above
# the constant so reviewers see the source.
# ---------------------------------------------------------------------------
PRICING_USD_PER_M_TOKENS: dict[str, dict[str, float]] = {
    # Anthropic Claude family
    "claude-3-5-sonnet-latest": {"input": 3.00, "output": 15.00},
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
    "claude-3-5-haiku-latest": {"input": 0.80, "output": 4.00},
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
    "claude-opus-4-20250514": {"input": 15.00, "output": 75.00},
    # OpenAI GPT family
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    # Mock provider — no cost.
    "mock": {"input": 0.0, "output": 0.0},
}


def estimate_cost_usd(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> float:
    """Return a USD cost estimate for *model* given token counts.

    Falls back to a conservative default of $5 / $15 per 1M tokens for unknown
    model strings so over-budget calls never silently slip through.
    """
    pricing = PRICING_USD_PER_M_TOKENS.get(model)
    if pricing is None:
        # Defensive default — better to over-estimate than miss a budget alert.
        pricing = {"input": 5.00, "output": 15.00}
    cost_in = (prompt_tokens / 1_000_000.0) * pricing["input"]
    cost_out = (completion_tokens / 1_000_000.0) * pricing["output"]
    return round(cost_in + cost_out, 6)


@dataclass
class LlmCallRecord:
    """One row in the LLM history log."""

    ts: str
    mode: str  # "rule" | "llm"
    provider: str  # "anthropic" | "openai" | "mock"
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    status: str  # "success" | "failure"
    flow_id: Optional[str] = None
    error: Optional[str] = None
    feature: str = "convert"  # "convert" | "chat" | other surfaces
    request_id: Optional[str] = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LlmCallRecord":
        return cls(
            ts=str(data.get("ts") or datetime.now(tz=UTC).isoformat()),
            mode=str(data.get("mode", "llm")),
            provider=str(data.get("provider", "")),
            model=str(data.get("model", "")),
            prompt_tokens=int(data.get("prompt_tokens", 0) or 0),
            completion_tokens=int(data.get("completion_tokens", 0) or 0),
            cost_usd=float(data.get("cost_usd", 0.0) or 0.0),
            status=str(data.get("status", "success")),
            flow_id=data.get("flow_id"),
            error=data.get("error"),
            feature=str(data.get("feature", "convert")),
            request_id=data.get("request_id"),
            extra=dict(data.get("extra") or {}),
        )


def _parse_iso(ts: str) -> Optional[datetime]:
    try:
        dt = datetime.fromisoformat(ts)
    except (TypeError, ValueError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


class LlmAuditRepo:
    """Thread-safe append-only JSONL repo for LLM call records."""

    LOG_FILENAME = "llm-history.log"

    def __init__(self, base_dir: Path | str) -> None:
        self._base_dir = Path(base_dir)
        self._log_path = self._base_dir / self.LOG_FILENAME
        self._lock = threading.Lock()
        self._base_dir.mkdir(parents=True, exist_ok=True)
        if not self._log_path.exists():
            self._log_path.touch()

    @property
    def path(self) -> Path:
        return self._log_path

    def append(self, record: LlmCallRecord) -> None:
        line = json.dumps(record.to_dict(), separators=(",", ":"))
        with self._lock:
            with self._log_path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
                fh.flush()

    def _read_all(self) -> list[LlmCallRecord]:
        if not self._log_path.exists():
            return []
        records: list[LlmCallRecord] = []
        with self._log_path.open("r", encoding="utf-8") as fh:
            for raw in fh:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    records.append(LlmCallRecord.from_dict(json.loads(raw)))
                except (json.JSONDecodeError, ValueError):
                    continue
        return records

    def list(
        self,
        *,
        provider: Optional[str] = None,
        status: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100,
        cursor: Optional[str] = None,
    ) -> tuple[list[LlmCallRecord], Optional[str]]:
        """Return at most *limit* matching records, newest first."""
        if limit <= 0:
            return [], None
        with self._lock:
            all_records = self._read_all()
        # Newest-first ordering — log is append-only oldest-first on disk.
        all_records.reverse()

        filtered: list[LlmCallRecord] = []
        for rec in all_records:
            if provider and rec.provider != provider:
                continue
            if status and rec.status != status:
                continue
            ts = _parse_iso(rec.ts)
            if since and (ts is None or ts < since):
                continue
            if until and (ts is None or ts > until):
                continue
            filtered.append(rec)

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

    def export_csv(
        self,
        *,
        provider: Optional[str] = None,
        status: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> str:
        """Return CSV of all matching records (no pagination — date-range bounded)."""
        records, _ = self.list(
            provider=provider,
            status=status,
            since=since,
            until=until,
            limit=10_000,
        )
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(
            [
                "timestamp",
                "mode",
                "provider",
                "model",
                "prompt_tokens",
                "completion_tokens",
                "cost_usd",
                "status",
                "flow_id",
                "feature",
                "error",
            ]
        )
        for r in records:
            writer.writerow(
                [
                    r.ts,
                    r.mode,
                    r.provider,
                    r.model,
                    r.prompt_tokens,
                    r.completion_tokens,
                    f"{r.cost_usd:.6f}",
                    r.status,
                    r.flow_id or "",
                    r.feature,
                    (r.error or "").replace("\n", " "),
                ]
            )
        return buf.getvalue()
