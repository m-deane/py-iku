"""GET /llm-history — list LLM calls; CSV export under /llm-history.csv.

Cost meter endpoints live in this router as well (``/llm-budget``,
``/llm-cost-summary``) so the prompt-history surface and the cost widget
share a single import boundary.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse

from ..deps import get_cost_meter, get_llm_audit_repo
from ..services.cost_meter import BudgetSettings, CostMeter
from ..services.llm_audit import LlmAuditRepo

logger = logging.getLogger(__name__)

router = APIRouter(tags=["llm"])


def _parse_iso(name: str, value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid ISO 8601 timestamp for '{name}': {value}",
        ) from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


@router.get("/llm-history", summary="List recorded LLM calls (newest first).")
def list_llm_history(
    provider: str | None = Query(default=None),
    status: str | None = Query(default=None),
    since: str | None = Query(default=None),
    until: str | None = Query(default=None),
    limit: int = Query(default=50, gt=0, le=500),
    cursor: str | None = Query(default=None),
    audit: LlmAuditRepo = Depends(get_llm_audit_repo),
) -> dict[str, Any]:
    since_dt = _parse_iso("since", since)
    until_dt = _parse_iso("until", until)
    records, next_cursor = audit.list(
        provider=provider,
        status=status,
        since=since_dt,
        until=until_dt,
        limit=limit,
        cursor=cursor,
    )
    return {
        "records": [r.to_dict() for r in records],
        "next_cursor": next_cursor,
    }


@router.get("/llm-history.csv", summary="Export filtered LLM history as CSV.")
def export_llm_history_csv(
    provider: str | None = Query(default=None),
    status: str | None = Query(default=None),
    since: str | None = Query(default=None),
    until: str | None = Query(default=None),
    audit: LlmAuditRepo = Depends(get_llm_audit_repo),
) -> PlainTextResponse:
    since_dt = _parse_iso("since", since)
    until_dt = _parse_iso("until", until)
    body = audit.export_csv(
        provider=provider,
        status=status,
        since=since_dt,
        until=until_dt,
    )
    filename = f"llm-history-{datetime.now(tz=UTC).date().isoformat()}.csv"
    return PlainTextResponse(
        content=body,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/llm-cost-summary", summary="Today / month-to-date LLM cost summary.")
def get_cost_summary(meter: CostMeter = Depends(get_cost_meter)) -> dict[str, Any]:
    return meter.summary().to_dict()


@router.get("/llm-budget", summary="Current LLM budget settings.")
def get_budget(meter: CostMeter = Depends(get_cost_meter)) -> dict[str, float]:
    return meter.get_budget().to_dict()


@router.put("/llm-budget", summary="Update LLM budget settings.")
def put_budget(
    payload: dict[str, float] = Body(...),
    meter: CostMeter = Depends(get_cost_meter),
) -> dict[str, float]:
    budget = BudgetSettings.from_dict(payload)
    meter.set_budget(budget)
    return budget.to_dict()
