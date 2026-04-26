"""GET /catalog/recipes, /catalog/processors, /catalog/processors/{type}."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Response

from ..schemas.catalog import ProcessorCatalogEntry, RecipeCatalogEntry
from ..services import catalog_service

router = APIRouter(prefix="/catalog", tags=["catalog"])

_CACHE_CONTROL = "public, max-age=60"


@router.get(
    "/recipes",
    response_model=list[RecipeCatalogEntry],
    summary="List all 37 Dataiku recipe types",
)
def get_recipes(response: Response) -> list[RecipeCatalogEntry]:
    """Return catalog entries for all 37 RecipeType values.

    Response is cached for 60 seconds (public, max-age=60).
    """
    response.headers["Cache-Control"] = _CACHE_CONTROL
    return catalog_service.list_recipes()


@router.get(
    "/processors",
    response_model=list[ProcessorCatalogEntry],
    summary="List Dataiku Prepare processors",
)
def get_processors(
    response: Response,
    q: str | None = Query(default=None, description="Filter by name or description substring"),
    category: str | None = Query(default=None, description="Filter by exact category name"),
) -> list[ProcessorCatalogEntry]:
    """Return catalog entries for Prepare processors (up to 122).

    Optional filters: `q` (name/description substring) and `category` (exact match).
    Response is cached for 60 seconds.
    """
    response.headers["Cache-Control"] = _CACHE_CONTROL
    return catalog_service.list_processors(q=q, category=category)


@router.get(
    "/processors/{processor_type}",
    response_model=ProcessorCatalogEntry,
    summary="Get a single processor catalog entry by type",
)
def get_processor(
    processor_type: str,
    response: Response,
) -> ProcessorCatalogEntry:
    """Return the catalog entry for a single processor type.

    `processor_type` should be the DSS canonical name (e.g. `ColumnRenamer`).
    Returns 404 if the type is not in the catalog.
    """
    response.headers["Cache-Control"] = _CACHE_CONTROL
    try:
        return catalog_service.get_processor(processor_type)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
