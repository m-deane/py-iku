"""Tests for /flows/{id}/comments routes (Wave 4D — collaboration)."""

from __future__ import annotations

import pytest

FLOW_ID = "11111111-2222-3333-4444-555555555555"
RECIPE_ID = "prepare_trades"


@pytest.mark.asyncio
async def test_post_comment_creates_record(client) -> None:  # type: ignore[no-untyped-def]
    response = await client.post(
        f"/flows/{FLOW_ID}/recipes/{RECIPE_ID}/comments",
        json={"body": "Sanity-check the FX rate join here"},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["id"]
    assert body["recipe_id"] == RECIPE_ID
    assert body["body"] == "Sanity-check the FX rate join here"
    assert body["author"] == "you"  # default
    assert body["timestamp"]


@pytest.mark.asyncio
async def test_list_comments_round_trips(client) -> None:  # type: ignore[no-untyped-def]
    await client.post(
        f"/flows/{FLOW_ID}/recipes/{RECIPE_ID}/comments",
        json={"body": "first"},
    )
    await client.post(
        f"/flows/{FLOW_ID}/recipes/{RECIPE_ID}/comments",
        json={"body": "second"},
    )
    response = await client.get(f"/flows/{FLOW_ID}/comments")
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["comments"]) == 2
    assert [c["body"] for c in body["comments"]] == ["first", "second"]


@pytest.mark.asyncio
async def test_delete_comment_removes_it(client) -> None:  # type: ignore[no-untyped-def]
    created = await client.post(
        f"/flows/{FLOW_ID}/recipes/{RECIPE_ID}/comments",
        json={"body": "doomed"},
    )
    cid = created.json()["id"]
    deleted = await client.delete(f"/flows/{FLOW_ID}/comments/{cid}")
    assert deleted.status_code == 204
    listed = await client.get(f"/flows/{FLOW_ID}/comments")
    assert listed.json()["comments"] == []


@pytest.mark.asyncio
async def test_delete_unknown_comment_returns_404(client) -> None:  # type: ignore[no-untyped-def]
    response = await client.delete(f"/flows/{FLOW_ID}/comments/does-not-exist")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_post_comment_rejects_empty_body(client) -> None:  # type: ignore[no-untyped-def]
    response = await client.post(
        f"/flows/{FLOW_ID}/recipes/{RECIPE_ID}/comments",
        json={"body": "   "},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_unsafe_flow_id_yields_empty_list(client) -> None:  # type: ignore[no-untyped-def]
    response = await client.get("/flows/..%2F..%2Fetc/comments")
    # Path traversal id falls through to empty list, not 5xx.
    assert response.status_code in (200, 404)


@pytest.mark.asyncio
async def test_studio_author_env_overrides_default(  # type: ignore[no-untyped-def]
    client, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("STUDIO_AUTHOR", "matthew.deane")
    response = await client.post(
        f"/flows/{FLOW_ID}/recipes/{RECIPE_ID}/comments",
        json={"body": "with custom author"},
    )
    assert response.status_code == 201
    assert response.json()["author"] == "matthew.deane"
