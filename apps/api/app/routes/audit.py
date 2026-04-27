"""GET /audit — paginated audit-log feed."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from ..deps import get_audit_repo
from ..schemas.audit import AuditEventModel, AuditListResponse
from ..store import AuditRepo

logger = logging.getLogger(__name__)

router = APIRouter(tags=["audit"])


def _parse_since(since: str | None) -> datetime | None:
    if since is None:
        return None
    try:
        dt = datetime.fromisoformat(since)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid ISO 8601 timestamp for 'since': {since}",
        ) from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


@router.get(
    "/audit",
    response_model=AuditListResponse,
    summary="List audit-log events",
)
def get_audit(
    since: str | None = Query(default=None, description="ISO timestamp lower bound"),
    actor: str | None = Query(default=None, description="Filter to a single actor"),
    limit: int = Query(default=100, gt=0, le=1000),
    cursor: str | None = Query(default=None, description="Pagination cursor"),
    audit: AuditRepo = Depends(get_audit_repo),
) -> AuditListResponse:
    since_dt = _parse_since(since)
    events, next_cursor = audit.list(
        since=since_dt, actor=actor, limit=limit, cursor=cursor
    )
    return AuditListResponse(
        events=[AuditEventModel.model_validate(ev.to_dict()) for ev in events],
        next_cursor=next_cursor,
    )
