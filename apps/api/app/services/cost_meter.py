"""Cost meter — aggregates LLM spend over rolling windows and enforces budgets.

The meter reads from the JSONL log written by ``llm_audit.LlmAuditRepo`` and
exposes a small set of derived figures:

* ``today_usd`` — sum of ``cost_usd`` for records timestamped today (UTC).
* ``month_usd`` — sum for the current calendar month (UTC).
* ``budget`` — current ``BudgetSettings`` from disk.

Settings are persisted to ``Settings.flows_dir / llm-budget.json`` so they
survive process restarts.  We deliberately keep this **server-side** rather
than only in browser localStorage so multi-tab usage is consistent and so
budget enforcement happens before the request is dispatched.
"""

from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Optional

from .llm_audit import LlmAuditRepo


@dataclass
class BudgetSettings:
    """User-configurable budget caps."""

    monthly_cap_usd: float = 50.0
    per_call_cap_usd: float = 1.00
    alert_threshold_pct: float = 80.0  # 0..100

    def to_dict(self) -> dict[str, float]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, float]) -> "BudgetSettings":
        return cls(
            monthly_cap_usd=float(
                data.get("monthly_cap_usd", 50.0) if data else 50.0
            ),
            per_call_cap_usd=float(
                data.get("per_call_cap_usd", 1.00) if data else 1.00
            ),
            alert_threshold_pct=float(
                data.get("alert_threshold_pct", 80.0) if data else 80.0
            ),
        )


@dataclass
class CostSummary:
    today_usd: float
    month_usd: float
    budget: BudgetSettings
    over_threshold: bool
    over_budget: bool
    pct_of_monthly_cap: float

    def to_dict(self) -> dict[str, object]:
        return {
            "today_usd": round(self.today_usd, 6),
            "month_usd": round(self.month_usd, 6),
            "budget": self.budget.to_dict(),
            "over_threshold": self.over_threshold,
            "over_budget": self.over_budget,
            "pct_of_monthly_cap": round(self.pct_of_monthly_cap, 2),
        }


class CostMeter:
    """Aggregates LLM cost from an ``LlmAuditRepo`` and persists budget settings."""

    SETTINGS_FILENAME = "llm-budget.json"

    def __init__(self, base_dir: Path | str, audit: LlmAuditRepo) -> None:
        self._base_dir = Path(base_dir)
        self._settings_path = self._base_dir / self.SETTINGS_FILENAME
        self._audit = audit
        self._lock = threading.Lock()
        self._base_dir.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------------------
    # Budget settings
    # -----------------------------------------------------------------
    def get_budget(self) -> BudgetSettings:
        if not self._settings_path.exists():
            return BudgetSettings()
        try:
            with self._lock, self._settings_path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            return BudgetSettings.from_dict(data)
        except (json.JSONDecodeError, OSError):
            return BudgetSettings()

    def set_budget(self, budget: BudgetSettings) -> BudgetSettings:
        # Validate inputs — disallow negatives and threshold > 100.
        budget.monthly_cap_usd = max(0.0, budget.monthly_cap_usd)
        budget.per_call_cap_usd = max(0.0, budget.per_call_cap_usd)
        budget.alert_threshold_pct = max(0.0, min(100.0, budget.alert_threshold_pct))
        with self._lock:
            with self._settings_path.open("w", encoding="utf-8") as fh:
                json.dump(budget.to_dict(), fh, indent=2)
        return budget

    # -----------------------------------------------------------------
    # Totals
    # -----------------------------------------------------------------
    def summary(self, *, now: Optional[datetime] = None) -> CostSummary:
        now = now or datetime.now(tz=UTC)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_month = start_of_day.replace(day=1)

        records, _ = self._audit.list(limit=10_000)

        today = 0.0
        month = 0.0
        for r in records:
            try:
                ts = datetime.fromisoformat(r.ts)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=UTC)
            except ValueError:
                continue
            if ts >= start_of_month:
                month += r.cost_usd
            if ts >= start_of_day:
                today += r.cost_usd

        budget = self.get_budget()
        pct = (
            (month / budget.monthly_cap_usd * 100.0)
            if budget.monthly_cap_usd > 0
            else 0.0
        )
        over_threshold = pct >= budget.alert_threshold_pct
        over_budget = budget.monthly_cap_usd > 0 and month >= budget.monthly_cap_usd

        return CostSummary(
            today_usd=today,
            month_usd=month,
            budget=budget,
            over_threshold=over_threshold,
            over_budget=over_budget,
            pct_of_monthly_cap=pct,
        )

    def check_call_allowed(
        self, projected_cost_usd: float, *, now: Optional[datetime] = None
    ) -> tuple[bool, str]:
        """Return (allowed, reason). ``reason`` is empty when allowed.

        A call is blocked when:
        * It alone exceeds ``per_call_cap_usd``.
        * It would push the month-to-date over ``monthly_cap_usd``.
        Both rules are skipped silently if the corresponding cap is 0.
        """
        s = self.summary(now=now)
        if s.budget.per_call_cap_usd > 0 and projected_cost_usd > s.budget.per_call_cap_usd:
            return (
                False,
                f"projected_cost ${projected_cost_usd:.4f} exceeds per-call cap "
                f"${s.budget.per_call_cap_usd:.2f}",
            )
        if (
            s.budget.monthly_cap_usd > 0
            and (s.month_usd + projected_cost_usd) > s.budget.monthly_cap_usd
        ):
            return (
                False,
                f"projected month-to-date ${(s.month_usd + projected_cost_usd):.4f} "
                f"exceeds monthly cap ${s.budget.monthly_cap_usd:.2f}",
            )
        return True, ""
