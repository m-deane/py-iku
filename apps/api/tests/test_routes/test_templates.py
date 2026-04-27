"""Tests for GET /templates and GET /templates/{id} (Sprint 3)."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_list_templates_returns_ten_entries(client) -> None:  # type: ignore[no-untyped-def]
    """The Trade-Blotter Recipe-Template Gallery ships with exactly 10 templates."""
    response = await client.get("/templates")
    assert response.status_code == 200, response.text
    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 10


@pytest.mark.asyncio
async def test_list_templates_excludes_python_source(client) -> None:  # type: ignore[no-untyped-def]
    """The list endpoint must NOT ship pythonSource — that's a per-id fetch."""
    response = await client.get("/templates")
    assert response.status_code == 200
    for entry in response.json():
        assert "pythonSource" not in entry, (
            f"List entry {entry.get('id')!r} leaked pythonSource"
        )
        assert "python_source" not in entry


@pytest.mark.asyncio
async def test_list_templates_carries_required_fields(client) -> None:  # type: ignore[no-untyped-def]
    """Every list entry has the canonical metadata fields."""
    response = await client.get("/templates")
    body = response.json()
    required = {
        "id",
        "name",
        "category",
        "summary",
        "personas",
        "tags",
        "verifiedRecipes",
        "verifiedDatasets",
        "estimatedSavingMinutes",
    }
    for entry in body:
        missing = required - set(entry.keys())
        assert not missing, (
            f"Template {entry.get('id')!r} missing fields: {missing}"
        )


@pytest.mark.asyncio
async def test_list_templates_covers_all_five_categories(client) -> None:  # type: ignore[no-untyped-def]
    """Each of the five categories has at least one entry, and totals = 10."""
    response = await client.get("/templates")
    cats = [t["category"] for t in response.json()]
    expected = {
        "trade-capture",
        "position-pnl",
        "curves",
        "counterparty",
        "power",
    }
    assert set(cats) == expected, (
        f"Expected categories {expected}, got {set(cats)}"
    )
    # Two per category — sprint spec.
    for cat in expected:
        assert cats.count(cat) == 2, (
            f"Category {cat!r} should have 2 templates, found {cats.count(cat)}"
        )


@pytest.mark.asyncio
async def test_get_template_returns_python_source(client) -> None:  # type: ignore[no-untyped-def]
    """The detail endpoint includes the full Python script."""
    response = await client.get("/templates/forward-curve-scd")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == "forward-curve-scd"
    assert "pythonSource" in body
    assert body["pythonSource"].lstrip().startswith("import pandas")
    # The cond / ~cond shape is the structural assertion.
    assert "cond" in body["pythonSource"]


@pytest.mark.asyncio
async def test_get_template_404_for_unknown_id(client) -> None:  # type: ignore[no-untyped-def]
    """Unknown template ids return a 404."""
    response = await client.get("/templates/no-such-template")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_templates_carries_cache_header(client) -> None:  # type: ignore[no-untyped-def]
    """Templates are static; the API caches them for 60s."""
    response = await client.get("/templates")
    assert response.headers.get("Cache-Control") == "public, max-age=60"


@pytest.mark.asyncio
async def test_get_template_carries_cache_header(client) -> None:  # type: ignore[no-untyped-def]
    """Detail responses cache for 60s as well."""
    response = await client.get("/templates/trade-event-aggregation")
    assert response.status_code == 200
    assert response.headers.get("Cache-Control") == "public, max-age=60"
