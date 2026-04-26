"""WebSocket event envelope schema (used in M1c)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class WSEvent(BaseModel):
    """Envelope for all WebSocket messages sent by the server.

    Attributes:
        event: Event name, e.g. ``"started"``, ``"completed"``, ``"error"``.
        seq:   Monotonically increasing sequence number per connection.
        ts:    UTC timestamp of the event.
        payload: Arbitrary event-specific data.
    """

    event: str = Field(..., description="Event name")
    seq: int = Field(..., ge=0, description="Monotonically increasing sequence number")
    ts: datetime = Field(
        default_factory=lambda: datetime.now(tz=UTC),
        description="UTC timestamp",
    )
    payload: dict[str, Any] = Field(default_factory=dict, description="Event payload")
