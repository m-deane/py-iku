"""GET /templates and GET /templates/{id} — Trade-Blotter Recipe-Template Gallery.

Single source of truth: ``apps/web/src/features/templates/templates.json``.
This module reads that JSON at import time and exposes:

* ``GET /templates`` — list all 10 templates **without** ``pythonSource``
  (so a 200 KB-of-Python payload doesn't ship on every list call)
* ``GET /templates/{id}`` — return one template **with** ``pythonSource``

The frontend imports the same JSON via Vite, so backend and frontend can
never disagree on what's available.
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


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


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

    model_config = {
        "populate_by_name": True,
    }


class FlowTemplateDetail(FlowTemplateSummary):
    """Template metadata + ``pythonSource`` returned by ``GET /templates/{id}``."""

    python_source: str = Field(..., alias="pythonSource")


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def _templates_json_path() -> Path:
    """Resolve the path to the canonical templates.json file.

    Lives next to ``templates-data.ts`` in the web app — we walk up from this
    file's location to the repo root, then down into apps/web/src.
    """
    # apps/api/app/routes/templates.py -> apps/api/app/routes -> apps/api/app
    # -> apps/api -> apps -> repo root
    here = Path(__file__).resolve()
    repo_root = here.parents[4]
    return repo_root / "apps" / "web" / "src" / "features" / "templates" / "templates.json"


@lru_cache(maxsize=1)
def _load_templates() -> list[dict[str, Any]]:
    """Load + cache the canonical template definitions."""
    path = _templates_json_path()
    if not path.exists():
        # Fail loud during import-time access if the path is wrong; the test
        # suite catches this immediately.
        raise FileNotFoundError(
            f"templates.json not found at {path}. Expected single source of "
            "truth alongside templates-data.ts."
        )
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError("templates.json must contain a top-level JSON array")
    return data


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
