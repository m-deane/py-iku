"""Tests for POST /score."""

from __future__ import annotations

import pytest


def _ds(name: str, dtype: str = "intermediate") -> dict:
    return {
        "name": name,
        "type": dtype,
        "connection_type": "Filesystem",
        "schema": [],
    }


@pytest.mark.asyncio
async def test_score_empty_flow(client) -> None:  # type: ignore[no-untyped-def]
    """A flow with no recipes scores zero on every metric."""
    flow = {
        "flow_name": "empty",
        "total_recipes": 0,
        "total_datasets": 0,
        "datasets": [],
        "recipes": [],
    }
    response = await client.post("/score", json=flow)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["recipe_count"] == 0
    assert body["processor_count"] == 0
    assert body["dataset_count"] == 0
    assert body["max_depth"] == 0
    assert body["fan_out_max"] == 0
    assert body["complexity"] == 0.0


@pytest.mark.asyncio
async def test_score_single_recipe(client) -> None:  # type: ignore[no-untyped-def]
    """A flow with one grouping recipe should report recipe_count=1."""
    flow = {
        "flow_name": "f",
        "total_recipes": 1,
        "total_datasets": 2,
        "datasets": [_ds("a", "input"), _ds("b", "output")],
        "recipes": [
            {
                "name": "r1",
                "type": "grouping",
                "inputs": ["a"],
                "outputs": ["b"],
                "keys": ["x"],
                "aggregations": [],
            },
        ],
    }
    response = await client.post("/score", json=flow)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["recipe_count"] == 1
    assert body["dataset_count"] == 2
    assert body["complexity"] >= 1.0


@pytest.mark.asyncio
async def test_score_chained_recipes_increases_depth(client) -> None:  # type: ignore[no-untyped-def]
    """Two chained recipes should yield max_depth >= 1."""
    flow = {
        "flow_name": "chain",
        "total_recipes": 2,
        "total_datasets": 3,
        "datasets": [
            _ds("a", "input"),
            _ds("b"),
            _ds("c", "output"),
        ],
        "recipes": [
            {
                "name": "r1",
                "type": "grouping",
                "inputs": ["a"],
                "outputs": ["b"],
                "keys": ["x"],
                "aggregations": [],
            },
            {
                "name": "r2",
                "type": "sort",
                "inputs": ["b"],
                "outputs": ["c"],
                "sortColumns": [],
            },
        ],
    }
    response = await client.post("/score", json=flow)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["recipe_count"] == 2
    assert body["max_depth"] >= 1


@pytest.mark.asyncio
async def test_score_malformed_returns_422(client) -> None:  # type: ignore[no-untyped-def]
    """Recipe referencing a missing dataset returns 422."""
    flow = {
        "flow_name": "bad",
        "total_recipes": 1,
        "total_datasets": 0,
        "datasets": [],
        "recipes": [
            {"name": "r1", "type": "grouping", "inputs": ["missing"], "outputs": []},
        ],
    }
    response = await client.post("/score", json=flow)
    assert response.status_code == 422
