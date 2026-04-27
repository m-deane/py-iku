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
from fastapi.responses import PlainTextResponse, Response

from ..deps import get_cost_meter, get_llm_audit_repo, get_settings
from ..services.cost_meter import BudgetSettings, CostMeter
from ..services.gdpr_export import build_user_export
from ..services.llm_audit import LlmAuditRepo, _default_user

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
    q: str | None = Query(default=None, description="Free-text search across prompt + response."),
    user: str | None = Query(default=None, description="Filter by Studio user."),
    severity: str | None = Query(
        default=None,
        description="Filter by derived severity (success / warning / error).",
    ),
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
        q=q,
        user=user,
        severity=severity,
    )
    payload = []
    for r in records:
        d = r.to_dict()
        d["severity"] = r.severity
        d["user"] = r.user or _default_user()
        payload.append(d)
    return {
        "records": payload,
        "next_cursor": next_cursor,
        "users": audit.list_users(),
    }


@router.get(
    "/llm-history/export",
    summary="GDPR — export every user-attributable record as a ZIP.",
)
def export_user_data(
    user: str | None = Query(default=None),
    audit: LlmAuditRepo = Depends(get_llm_audit_repo),
) -> Response:
    settings = get_settings()
    target_user = (user or _default_user()).strip()
    if not target_user:
        raise HTTPException(status_code=400, detail="user is required")
    zip_bytes, filename = build_user_export(
        base_dir=settings.flows_dir,
        user=target_user,
        audit_repo=audit,
    )
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Studio-User": target_user,
        },
    )


@router.delete(
    "/llm-history",
    summary="GDPR — delete every record for the named user.",
)
def delete_user_history(
    user: str | None = Query(default=None),
    confirm: str = Query(default=""),
    audit: LlmAuditRepo = Depends(get_llm_audit_repo),
) -> dict[str, Any]:
    """Hard-delete every audit record attributed to *user*.

    Confirmation token must equal ``"yes"`` so accidental DELETE calls bounce
    with a 400 instead of wiping data.
    """
    target_user = (user or _default_user()).strip()
    if not target_user:
        raise HTTPException(status_code=400, detail="user is required")
    if confirm != "yes":
        raise HTTPException(
            status_code=400,
            detail="Pass confirm=yes to acknowledge a destructive delete.",
        )
    removed = audit.delete_user_records(target_user)
    return {"user": target_user, "removed": removed}


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
