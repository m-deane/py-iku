"""Tests for GET /catalog/recipes and GET /catalog/processors endpoints."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_recipes_returns_37_entries(client) -> None:  # type: ignore[no-untyped-def]
    """GET /catalog/recipes must return exactly 37 entries (one per RecipeType)."""
    response = await client.get("/catalog/recipes")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 37, f"Expected 37, got {len(data)}"


@pytest.mark.asyncio
async def test_recipes_has_cache_header(client) -> None:  # type: ignore[no-untyped-def]
    """Recipes endpoint must set Cache-Control: public, max-age=60."""
    response = await client.get("/catalog/recipes")
    assert response.status_code == 200
    cc = response.headers.get("cache-control", "")
    assert "public" in cc
    assert "max-age=60" in cc


@pytest.mark.asyncio
async def test_recipes_entry_shape(client) -> None:  # type: ignore[no-untyped-def]
    """Each recipe entry must have type, name, category, icon, description."""
    response = await client.get("/catalog/recipes")
    assert response.status_code == 200
    for entry in response.json():
        assert "type" in entry
        assert "name" in entry
        assert "category" in entry
        assert "icon" in entry
        assert "description" in entry


@pytest.mark.asyncio
async def test_processors_returns_expected_count(client) -> None:  # type: ignore[no-untyped-def]
    """GET /catalog/processors returns a non-empty list (catalog has 101+ entries)."""
    response = await client.get("/catalog/processors")
    assert response.status_code == 200
    data = response.json()
    # ProcessorCatalog.list_processors() returns 101 keys (including ColumnsSelector_delete alias)
    assert len(data) >= 100, f"Expected >=100, got {len(data)}"


@pytest.mark.asyncio
async def test_processors_has_cache_header(client) -> None:  # type: ignore[no-untyped-def]
    """Processors endpoint must set Cache-Control header."""
    response = await client.get("/catalog/processors")
    cc = response.headers.get("cache-control", "")
    assert "public" in cc
    assert "max-age=60" in cc


@pytest.mark.asyncio
async def test_processors_filter_by_category(client) -> None:  # type: ignore[no-untyped-def]
    """Category filter must return a subset of all processors."""
    all_resp = await client.get("/catalog/processors")
    filtered_resp = await client.get("/catalog/processors?category=Column+Manipulation")
    assert filtered_resp.status_code == 200
    all_count = len(all_resp.json())
    filtered_count = len(filtered_resp.json())
    assert filtered_count > 0, "Expected some Column Manipulation processors"
    assert filtered_count < all_count, "Category filter should narrow the results"


@pytest.mark.asyncio
async def test_processors_filter_by_query(client) -> None:  # type: ignore[no-untyped-def]
    """q= filter should narrow results."""
    resp = await client.get("/catalog/processors?q=renamer")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    # Every returned entry name or description must contain 'renamer' (case-insensitive)
    for entry in data:
        combined = (entry["name"] + entry["description"]).lower()
        assert "renamer" in combined


@pytest.mark.asyncio
async def test_unknown_processor_type_returns_404(client) -> None:  # type: ignore[no-untyped-def]
    """Unknown processor type in path should return 404."""
    response = await client.get("/catalog/processors/NonExistentProcessor99")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_known_processor_type_returns_200(client) -> None:  # type: ignore[no-untyped-def]
    """Known processor type should return 200 with expected fields."""
    response = await client.get("/catalog/processors/ColumnRenamer")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "ColumnRenamer"
    assert "category" in data
    assert "description" in data
    assert "required_params" in data


@pytest.mark.asyncio
async def test_processor_single_has_cache_header(client) -> None:  # type: ignore[no-untyped-def]
    """Single processor endpoint must set Cache-Control header."""
    response = await client.get("/catalog/processors/ColumnRenamer")
    cc = response.headers.get("cache-control", "")
    assert "public" in cc
