"""Pydantic schemas for the audit log route (M7)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AuditEventModel(BaseModel):
    """A single audit log entry returned by ``GET /audit``."""

    actor: str
    action: str
    resource_type: str
    resource_id: str
    details: dict[str, Any] = Field(default_factory=dict)
    ts: str


class AuditListResponse(BaseModel):
    """Paginated audit response."""

    events: list[AuditEventModel]
    next_cursor: str | None = None
