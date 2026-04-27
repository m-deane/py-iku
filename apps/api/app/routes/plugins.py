"""Plugin marketplace routes — catalog + live registry introspection.

The marketplace is information-only in v1: ``GET /plugins/catalog`` returns a
hand-curated list of bundled plugin metadata, and ``GET /plugins/installed``
introspects the live ``PluginRegistry``.  No real install flow yet (that
needs a package registry).
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from ..services.plugin_marketplace import (
    get_catalog_entry,
    list_catalog,
    list_installed,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plugins", tags=["plugins"])


@router.get("/catalog", summary="List bundled plugin marketplace entries.")
def get_plugin_catalog() -> dict[str, Any]:
    """Return the static plugin catalog (5 bundled entries in v1)."""
    entries = list_catalog()
    return {"entries": entries, "count": len(entries)}


@router.get(
    "/catalog/{name}",
    summary="Fetch a single catalog entry by name.",
)
def get_plugin_catalog_entry(name: str) -> dict[str, Any]:
    entry = get_catalog_entry(name)
    if entry is None:
        raise HTTPException(
            status_code=404,
            detail=f"No catalog entry found for plugin '{name}'.",
        )
    return entry


@router.get(
    "/installed",
    summary="Introspect the live PluginRegistry and report active mappings.",
)
def get_plugins_installed() -> dict[str, Any]:
    """Return the runtime PluginRegistry state (handlers, mappings, plugins)."""
    return list_installed()
