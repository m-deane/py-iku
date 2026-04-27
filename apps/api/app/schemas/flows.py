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
    """Full saved-flow record.

    ``fixtures`` is an optional inlined :class:`FixtureBundle`, populated when
    the share record was minted with ``include_fixtures=True``. Recipients use
    it to "Run with embedded fixtures" without a separate bundle download.
    """

    id: str
    name: str
    flow: DataikuFlowModel
    created_at: str
    updated_at: str
    tags: list[str] = Field(default_factory=list)
    fixtures: dict | None = Field(
        default=None,
        description=(
            "Inlined fixture bundle (n_rows + datasets). None when the share "
            "was minted without embedded fixtures."
        ),
    )


class CreatedFlowResponse(BaseModel):
    """Slim response from ``POST /flows``."""

    id: str
    created_at: str


class ShareFlowRequest(BaseModel):
    """Body for ``POST /flows/{id}/share``."""

    ttl_seconds: int | None = Field(
        default=None,
        gt=0,
        description="Token validity in seconds (default: server-configured TTL).",
    )
    scopes: list[str] | None = Field(
        default=None,
        description="Token scopes (default: ['read']).",
    )
    include_fixtures: bool = Field(
        default=False,
        description=(
            "When true, attach a synthesised fixture bundle to the saved-flow "
            "record so the recipient can run with embedded data. The payload "
            "is gzip+base64 compressed on disk."
        ),
    )
    fixtures_n_rows: int = Field(
        default=100,
        ge=0,
        le=100,
        description="Per-input-dataset row cap when include_fixtures is true.",
    )


class ShareFlowResponse(BaseModel):
    """Response from ``POST /flows/{id}/share``."""

    token: str
    url: str
    expires_at: str
