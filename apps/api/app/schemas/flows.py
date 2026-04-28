"""Pydantic schemas for the /flows persistence routes (M7)."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field

from .flow import DataikuFlowModel


class SaveFlowRequest(BaseModel):
    """Request body for ``POST /flows``."""

    flow: DataikuFlowModel
    name: Annotated[str, Field(min_length=1, max_length=200)]
    tags: list[str] = Field(default_factory=list)


class UpdateFlowRequest(BaseModel):
    """Request body for ``PATCH /flows/{id}`` — every field is optional."""

    flow: DataikuFlowModel | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    tags: list[str] | None = None


class SavedFlowResponse(BaseModel):
    """Full saved-flow record."""

    id: str
    name: str
    flow: DataikuFlowModel
    created_at: str
    updated_at: str
    tags: list[str] = Field(default_factory=list)


class CreatedFlowResponse(BaseModel):
    """Slim response from ``POST /flows``."""

    id: str
    created_at: str
