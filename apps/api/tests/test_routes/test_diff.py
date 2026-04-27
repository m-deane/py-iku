"""Tests for POST /diff."""

from __future__ import annotations

import pytest


def _flow(*recipes: dict, datasets: list[dict] | None = None) -> dict:
    """Build a minimal flow dict whose recipes reference declared datasets."""
    if datasets is None:
        datasets = []
    return {
        "flow_name": "f",
        "total_recipes": len(recipes),
        "total_datasets": len(datasets),
        "datasets": datasets,
        "recipes": list(recipes),
    }


def _ds(name: str, dtype: str = "intermediate") -> dict:
    return {
        "name": name,
        "type": dtype,
        "connection_type": "Filesystem",
        "schema": [],
    }


def _recipe(
    name: str,
    rtype: str = "grouping",
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
    **extra,
) -> dict:
    base = {
        "name": name,
        "type": rtype,
        "inputs": inputs or [],
        "outputs": outputs or [],
    }
    base.update(extra)
    return base


@pytest.mark.asyncio
async def test_diff_identical_flows(client) -> None:  # type: ignore[no-untyped-def]
    """Two identical flows should yield empty added/removed/changed lists."""
    flow = _flow(
        _recipe("r1", "grouping", ["a"], ["b"], keys=["x"]),
        datasets=[_ds("a", "input"), _ds("b", "output")],
    )
    response = await client.post("/diff", json={"a": flow, "b": flow})
    assert response.status_code == 200
    body = response.json()
    assert body == {"added": [], "removed": [], "changed": []}


@pytest.mark.asyncio
async def test_diff_added(client) -> None:  # type: ignore[no-untyped-def]
    """Recipe present in B but not A is reported as added."""
    a = _flow(
        _recipe("r1", "grouping", ["a"], ["b"]),
        datasets=[_ds("a", "input"), _ds("b", "output")],
    )
    b = _flow(
        _recipe("r1", "grouping", ["a"], ["b"]),
        _recipe("r2", "sort", ["b"], ["c"]),
        datasets=[_ds("a", "input"), _ds("b"), _ds("c", "output")],
    )
    response = await client.post("/diff", json={"a": a, "b": b})
    assert response.status_code == 200
    body = response.json()
    assert body["removed"] == []
    assert body["changed"] == []
    assert len(body["added"]) == 1
    assert body["added"][0]["id"] == "r2"
    assert body["added"][0]["recipe_type_b"] == "sort"
    assert body["added"][0]["recipe_type_a"] is None


@pytest.mark.asyncio
async def test_diff_removed(client) -> None:  # type: ignore[no-untyped-def]
    """Recipe present in A but not B is reported as removed."""
    a = _flow(
        _recipe("r1", "grouping", ["a"], ["b"]),
        _recipe("r2", "sort", ["b"], ["c"]),
        datasets=[_ds("a", "input"), _ds("b"), _ds("c", "output")],
    )
    b = _flow(
        _recipe("r1", "grouping", ["a"], ["b"]),
        datasets=[_ds("a", "input"), _ds("b", "output")],
    )
    response = await client.post("/diff", json={"a": a, "b": b})
    assert response.status_code == 200
    body = response.json()
    assert body["added"] == []
    assert body["changed"] == []
    assert len(body["removed"]) == 1
    assert body["removed"][0]["id"] == "r2"
    assert body["removed"][0]["recipe_type_a"] == "sort"
    assert body["removed"][0]["recipe_type_b"] is None


@pytest.mark.asyncio
async def test_diff_changed_recipe_type(client) -> None:  # type: ignore[no-untyped-def]
    """Recipe with the same id but a different recipe_type is reported as changed."""
    a = _flow(
        _recipe("r1", "grouping", ["a"], ["b"], keys=["x"]),
        datasets=[_ds("a", "input"), _ds("b", "output")],
    )
    b = _flow(
        _recipe("r1", "sort", ["a"], ["b"], sortColumns=[{"column": "x"}]),
        datasets=[_ds("a", "input"), _ds("b", "output")],
    )
    response = await client.post("/diff", json={"a": a, "b": b})
    assert response.status_code == 200
    body = response.json()
    assert body["added"] == []
    assert body["removed"] == []
    assert len(body["changed"]) == 1
    entry = body["changed"][0]
    assert entry["id"] == "r1"
    assert entry["recipe_type_a"] == "grouping"
    assert entry["recipe_type_b"] == "sort"
    assert entry["diff"] is not None
    assert "type" in entry["diff"]


@pytest.mark.asyncio
async def test_diff_changed_settings(client) -> None:  # type: ignore[no-untyped-def]
    """Recipe with same type but different settings/steps is reported as changed."""
    a = _flow(
        _recipe("r1", "grouping", ["a"], ["b"], keys=["x"]),
        datasets=[_ds("a", "input"), _ds("b", "output")],
    )
    b = _flow(
        _recipe("r1", "grouping", ["a"], ["b"], keys=["x", "y"]),
        datasets=[_ds("a", "input"), _ds("b", "output")],
    )
    response = await client.post("/diff", json={"a": a, "b": b})
    assert response.status_code == 200
    body = response.json()
    assert len(body["changed"]) == 1
    entry = body["changed"][0]
    assert entry["id"] == "r1"
    assert entry["recipe_type_a"] == "grouping"
    assert entry["recipe_type_b"] == "grouping"


@pytest.mark.asyncio
async def test_diff_malformed_returns_422(client) -> None:  # type: ignore[no-untyped-def]
    """Malformed body (missing 'a') returns 422."""
    response = await client.post("/diff", json={"b": {"flow_name": "x"}})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_diff_unknown_dataset_reference_returns_422(client) -> None:  # type: ignore[no-untyped-def]
    """Recipe referencing a dataset name not in datasets[] is rejected."""
    a = _flow(
        _recipe("r1", "grouping", ["nonexistent"], ["b"]),
        datasets=[_ds("b", "output")],
    )
    b = _flow(
        _recipe("r1", "grouping", ["a"], ["b"]),
        datasets=[_ds("a", "input"), _ds("b", "output")],
    )
    response = await client.post("/diff", json={"a": a, "b": b})
    assert response.status_code == 422
