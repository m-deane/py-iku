"""Tests for GET /share/{token} (M7)."""

from __future__ import annotations

import pytest

from app.deps import get_settings
from app.routes.share import reset_share_rate_limiter
from app.security.share_links import sign


def _flow(name: str = "f") -> dict:
    return {
        "flow_name": name,
        "total_recipes": 0,
        "total_datasets": 0,
        "datasets": [],
        "recipes": [],
    }


@pytest.mark.asyncio
async def test_share_returns_flow_for_valid_token(client) -> None:  # type: ignore[no-untyped-def]
    save = await client.post(
        "/flows", json={"flow": _flow("public"), "name": "public-flow"}
    )
    flow_id = save.json()["id"]
    settings = get_settings()
    token = sign(
        flow_id, ttl_seconds=600, scopes=["read"], secret=settings.secret_key
    )
    response = await client.get(f"/share/{token}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == flow_id
    assert body["name"] == "public-flow"


@pytest.mark.asyncio
async def test_share_invalid_token_returns_401(client) -> None:  # type: ignore[no-untyped-def]
    response = await client.get("/share/!!!not-a-token!!!")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_share_unknown_flow_returns_404(client) -> None:  # type: ignore[no-untyped-def]
    settings = get_settings()
    token = sign(
        "unknown-id", ttl_seconds=600, scopes=["read"], secret=settings.secret_key
    )
    response = await client.get(f"/share/{token}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_share_rate_limited(client, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """After exceeding the per-IP cap, GET /share/{token} returns 429."""
    settings = get_settings()
    monkeypatch.setattr(settings, "share_rate_limit_per_minute", 2)
    reset_share_rate_limiter()

    save = await client.post("/flows", json={"flow": _flow(), "name": "rl"})
    flow_id = save.json()["id"]
    token = sign(
        flow_id, ttl_seconds=600, scopes=["read"], secret=settings.secret_key
    )

    # First two should succeed, third should 429.
    r1 = await client.get(f"/share/{token}")
    r2 = await client.get(f"/share/{token}")
    r3 = await client.get(f"/share/{token}")
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r3.status_code == 429


@pytest.mark.asyncio
async def test_share_rate_limiter_uses_forwarded_ip(client, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Rate limiter must key on X-Forwarded-For when present."""
    settings = get_settings()
    monkeypatch.setattr(settings, "share_rate_limit_per_minute", 1)
    reset_share_rate_limiter()

    save = await client.post("/flows", json={"flow": _flow(), "name": "xff"})
    flow_id = save.json()["id"]
    token = sign(
        flow_id, ttl_seconds=600, scopes=["read"], secret=settings.secret_key
    )

    # First request from 1.2.3.4 — should succeed.
    r1 = await client.get(f"/share/{token}", headers={"X-Forwarded-For": "1.2.3.4"})
    assert r1.status_code == 200

    # Second request from same IP — should be rate-limited.
    r2 = await client.get(f"/share/{token}", headers={"X-Forwarded-For": "1.2.3.4"})
    assert r2.status_code == 429

    # Request from a different IP — not limited.
    r3 = await client.get(f"/share/{token}", headers={"X-Forwarded-For": "9.9.9.9"})
    assert r3.status_code == 200


@pytest.mark.asyncio
async def test_share_deleted_flow_returns_404(client) -> None:  # type: ignore[no-untyped-def]
    """A share token for a flow that no longer exists should return 404."""
    settings = get_settings()
    # Sign a token for a flow that was never saved.
    token = sign(
        "00000000-0000-0000-0000-000000000000",
        ttl_seconds=600,
        scopes=["read"],
        secret=settings.secret_key,
    )
    response = await client.get(f"/share/{token}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_rate_limiter_stale_eviction() -> None:  # type: ignore[no-untyped-def]
    """Stale IP buckets are evicted after TTL so memory does not grow unboundedly."""
    import time
    from app.routes.share import _TokenBucket

    bucket = _TokenBucket(capacity=5, period=60.0)
    # Fill a bucket for a key and then fake-age it past the TTL.
    bucket.allow("victim-ip", now=0.0)
    # Advance time past TTL (600 s) to trigger eviction.
    bucket.allow("trigger-ip", now=bucket._TTL + 1)
    # 'victim-ip' should have been evicted.
    assert "victim-ip" not in bucket._tokens
