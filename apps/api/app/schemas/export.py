"""Pydantic v2 schemas for the POST /export/{format} endpoint."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ExportFormat(StrEnum):
    """Supported export formats for ``POST /export/{format}``."""

    ZIP = "zip"
    JSON = "json"
    YAML = "yaml"
    SVG = "svg"
    PNG = "png"
    PDF = "pdf"


class ExportRequest(BaseModel):
    """Request body for ``POST /export/{format}``.

    ``flow`` is the raw ``DataikuFlow.to_dict()`` payload (round-trippable via
    ``DataikuFlow.from_dict``).  ``opts`` is a free-form dict reserved for
    format-specific knobs (e.g. ``{"scale": 2.0}`` for PNG).
    """

    flow: dict[str, Any] = Field(..., description="DataikuFlow.to_dict() payload")
    opts: dict[str, Any] | None = Field(
        default=None,
        description="Optional format-specific options (passed through to the sink)",
    )
