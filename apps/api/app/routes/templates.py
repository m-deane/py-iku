"""GET /templates and GET /templates/{id} — Trade-Blotter Recipe-Template Gallery.

Single source of truth: ``apps/web/src/features/templates/templates-<category>.json``.
This module reads those JSON files at import time, concatenates them in the
canonical category order, and exposes:

* ``GET /templates`` — list all 25 templates **without** ``pythonSource``
  (so a 200 KB-of-Python payload doesn't ship on every list call)
* ``GET /templates/{id}`` — return one template **with** ``pythonSource``

The frontend imports the same JSON files via Vite, so backend and frontend can
never disagree on what's available.

Sprint 5 grew the catalog from 10 → 25 templates. The combined JSON exceeded
the 30 KB single-file budget, so the catalog is split per-category. We
concatenate at serve time in the canonical category order.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

router = APIRouter(prefix="/templates", tags=["templates"])

_CACHE_CONTROL = "public, max-age=60"

# Canonical category order — matches TEMPLATE_CATEGORIES in templates-data.ts
# so the concatenated array order is byte-for-byte identical to the frontend's.
_TEMPLATE_CATEGORIES: tuple[str, ...] = (
    "trade-capture",
    "position-pnl",
    "curves",
    "counterparty",
    "power",
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class TemplateParameterSpec(BaseModel):
    """One ``${PLACEHOLDER}`` definition on a parametric template."""

    name: str
    label: str
    type: str  # "text" | "date" | "number" | "select"
    default_value: str = Field(..., alias="defaultValue")
    choices: list[str] | None = None
    description: str | None = None

    model_config = {
        "populate_by_name": True,
    }


class FlowTemplateSummary(BaseModel):
    """Template metadata returned by ``GET /templates`` (no source)."""

    id: str
    name: str
    category: str
    summary: str
    personas: list[str]
    tags: list[str]
    verified_recipes: list[str] = Field(..., alias="verifiedRecipes")
    verified_datasets: list[str] = Field(..., alias="verifiedDatasets")
    estimated_saving_minutes: int = Field(..., alias="estimatedSavingMinutes")
    parameters: list[TemplateParameterSpec] | None = None

    model_config = {
        "populate_by_name": True,
    }


class FlowTemplateDetail(FlowTemplateSummary):
    """Template metadata + ``pythonSource`` returned by ``GET /templates/{id}``."""

    python_source: str = Field(..., alias="pythonSource")


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def _templates_dir() -> Path:
    """Resolve the directory holding the per-category templates-*.json files."""
    here = Path(__file__).resolve()
    repo_root = here.parents[4]
    return repo_root / "apps" / "web" / "src" / "features" / "templates"


@lru_cache(maxsize=1)
def _load_templates() -> list[dict[str, Any]]:
    """Load + cache the canonical template definitions, concatenated in order."""
    base = _templates_dir()
    aggregated: list[dict[str, Any]] = []
    for cat in _TEMPLATE_CATEGORIES:
        path = base / f"templates-{cat}.json"
        if not path.exists():
            raise FileNotFoundError(
                f"templates-{cat}.json not found at {path}. Expected single source "
                "of truth alongside templates-data.ts."
            )
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, list):
            raise ValueError(
                f"templates-{cat}.json must contain a top-level JSON array"
            )
        aggregated.extend(data)
    return aggregated


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=list[FlowTemplateSummary],
    summary="List trade-blotter recipe templates",
)
def list_templates(response: Response) -> list[FlowTemplateSummary]:
    """Return all templates without their ``pythonSource``.

    Cached for 60s — templates are static, regenerated only at deploy time.
    """
    response.headers["Cache-Control"] = _CACHE_CONTROL
    raw = _load_templates()
    return [FlowTemplateSummary.model_validate(t) for t in raw]


@router.get(
    "/{template_id}",
    response_model=FlowTemplateDetail,
    summary="Get a single template by id (with pythonSource)",
)
def get_template(template_id: str, response: Response) -> FlowTemplateDetail:
    """Return one template including its full ``pythonSource``.

    Returns 404 if ``template_id`` is not in the catalog. Cached for 60s.
    """
    response.headers["Cache-Control"] = _CACHE_CONTROL
    raw = _load_templates()
    for t in raw:
        if t.get("id") == template_id:
            return FlowTemplateDetail.model_validate(t)
    raise HTTPException(
        status_code=404,
        detail=f"Template '{template_id}' not found",
    )
