"""Tests for the plugin marketplace routes."""

from __future__ import annotations

import pytest

from py2dataiku.models.dataiku_recipe import RecipeType
from py2dataiku.plugins.registry import PluginRegistry


@pytest.fixture(autouse=True)
def _clean_registry() -> None:
    """Each test gets a clean global PluginRegistry."""
    PluginRegistry.clear()
    yield
    PluginRegistry.clear()


@pytest.mark.asyncio
async def test_plugin_catalog_returns_five_bundled_entries(client) -> None:  # type: ignore[no-untyped-def]
    resp = await client.get("/plugins/catalog")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 5
    names = {e["name"] for e in body["entries"]}
    assert names == {
        "py-iku-trading-domain",
        "py-iku-sklearn-bridge",
        "py-iku-numpy-extensions",
        "py-iku-time-series",
        "py-iku-aggregations-extra",
    }


@pytest.mark.asyncio
async def test_plugin_catalog_entry_shape(client) -> None:  # type: ignore[no-untyped-def]
    resp = await client.get("/plugins/catalog")
    body = resp.json()
    entry = next(e for e in body["entries"] if e["name"] == "py-iku-trading-domain")
    # Every catalog field the UI relies on must be present.
    assert entry["version"]
    assert entry["description"]
    assert entry["author"]
    assert entry["install_command"].startswith("pip install ")
    assert entry["source_code_url"].startswith("https://")
    assert isinstance(entry["supported_recipes"], list)
    assert isinstance(entry["supported_processors"], list)
    assert isinstance(entry["tags"], list)


@pytest.mark.asyncio
async def test_plugin_catalog_single_lookup(client) -> None:  # type: ignore[no-untyped-def]
    resp = await client.get("/plugins/catalog/py-iku-time-series")
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "py-iku-time-series"
    assert "WINDOW" in body["supported_recipes"]


@pytest.mark.asyncio
async def test_plugin_catalog_single_lookup_404(client) -> None:  # type: ignore[no-untyped-def]
    resp = await client.get("/plugins/catalog/does-not-exist")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_plugins_installed_reflects_registry(client) -> None:  # type: ignore[no-untyped-def]
    PluginRegistry.register_recipe_mapping("custom_join", RecipeType.JOIN)
    PluginRegistry.register_plugin(
        "demo-plugin", version="0.1.0", description="A test plugin."
    )

    resp = await client.get("/plugins/installed")
    assert resp.status_code == 200
    body = resp.json()
    assert body["recipe_mappings"]["custom_join"] == "join"
    assert "demo-plugin" in body["plugins"]
    assert body["plugins"]["demo-plugin"]["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_plugins_installed_empty_after_clear(client) -> None:  # type: ignore[no-untyped-def]
    resp = await client.get("/plugins/installed")
    body = resp.json()
    assert body["recipe_mappings"] == {}
    assert body["processor_mappings"] == {}
    assert body["plugins"] == {}
