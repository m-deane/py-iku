"""Tests for /flows persistence routes (M7)."""

from __future__ import annotations

import pytest


def _flow(name: str = "f", recipes: list[dict] | None = None, datasets: list[dict] | None = None) -> dict:
    return {
        "flow_name": name,
        "total_recipes": len(recipes or []),
        "total_datasets": len(datasets or []),
        "datasets": datasets or [],
        "recipes": recipes or [],
    }


@pytest.mark.asyncio
async def test_post_flow_creates_record(client) -> None:  # type: ignore[no-untyped-def]
    payload = {"flow": _flow("hello"), "name": "my-flow", "tags": ["t1"]}
    response = await client.post("/flows", json=payload)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["id"]
    assert body["created_at"]


@pytest.mark.asyncio
async def test_get_flow_round_trips(client) -> None:  # type: ignore[no-untyped-def]
    save = await client.post(
        "/flows",
        json={"flow": _flow("x"), "name": "x", "tags": ["a"]},
    )
    flow_id = save.json()["id"]
    response = await client.get(f"/flows/{flow_id}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == flow_id
    assert body["name"] == "x"
    assert body["tags"] == ["a"]
    assert body["flow"]["flow_name"] == "x"


@pytest.mark.asyncio
async def test_get_flow_unknown_returns_404(client) -> None:  # type: ignore[no-untyped-def]
    response = await client.get("/flows/does-not-exist")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_patch_flow_updates_name_and_tags(client) -> None:  # type: ignore[no-untyped-def]
    save = await client.post(
        "/flows",
        json={"flow": _flow(), "name": "orig", "tags": ["x"]},
    )
    flow_id = save.json()["id"]
    response = await client.patch(
        f"/flows/{flow_id}",
        json={"name": "renamed", "tags": ["a", "b"]},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["name"] == "renamed"
    assert body["tags"] == ["a", "b"]


@pytest.mark.asyncio
async def test_patch_flow_no_fields_returns_422(client) -> None:  # type: ignore[no-untyped-def]
    save = await client.post(
        "/flows",
        json={"flow": _flow(), "name": "orig"},
    )
    flow_id = save.json()["id"]
    response = await client.patch(f"/flows/{flow_id}", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_patch_flow_unknown_returns_404(client) -> None:  # type: ignore[no-untyped-def]
    response = await client.patch("/flows/nope", json={"name": "x"})
    assert response.status_code == 404


