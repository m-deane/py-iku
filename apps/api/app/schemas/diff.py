"""Pydantic v2 schemas for the POST /diff endpoint."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .flow import DataikuFlowModel


class DiffRequest(BaseModel):
    """Request body for POST /diff."""

    a: DataikuFlowModel = Field(..., description="The 'before' flow (e.g., rule output)")
    b: DataikuFlowModel = Field(..., description="The 'after' flow (e.g., LLM output)")


class NodeDiff(BaseModel):
    """A single per-node difference entry.

    For ``added`` and ``removed`` entries ``diff`` is None. For ``changed`` entries
    ``diff`` enumerates which fields differ between A and B.
    """

    id: str = Field(..., description="Recipe name used as the node id")
    recipe_type_a: str | None = Field(
        default=None,
        description="Recipe type in flow A (None when added in B)",
    )
    recipe_type_b: str | None = Field(
        default=None,
        description="Recipe type in flow B (None when removed from B)",
    )
    diff: dict[str, Any] | None = Field(
        default=None,
        description="When kind=changed: which fields differ ({field: {a, b}}).",
    )


class DiffResponse(BaseModel):
    """Response body for POST /diff."""

    added: list[NodeDiff] = Field(default_factory=list)
    removed: list[NodeDiff] = Field(default_factory=list)
    changed: list[NodeDiff] = Field(default_factory=list)
