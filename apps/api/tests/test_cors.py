"""Tests for CORS middleware configuration.

Verifies that the dev-time origin allowlist (regression coverage for the
flow-review CORS gap) and the wildcard regex (HF Spaces hostnames) both
produce ``access-control-allow-origin`` headers on preflight + simple GET.
"""

from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    "origin",
    [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://huggingface.co",
        "https://m-deane.github.io",
        # Regex-matched (HF Spaces production hostnames)
        "https://m-deane-py-iku.hf.space",
        "https://anything.hf.space",
    ],
)
@pytest.mark.asyncio
async def test_cors_allows_expected_origins(client, origin: str) -> None:  # type: ignore[no-untyped-def]
    """A simple GET from each whitelisted origin must echo the origin header."""
    response = await client.get("/health", headers={"Origin": origin})
    assert response.status_code == 200, response.text
    allow_origin = response.headers.get("access-control-allow-origin")
    assert allow_origin == origin, (
        f"Expected access-control-allow-origin == {origin!r}, "
        f"got {allow_origin!r}"
    )


@pytest.mark.parametrize(
    "origin",
    [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://m-deane-py-iku.hf.space",
    ],
)
@pytest.mark.asyncio
async def test_cors_preflight_allows_expected_origins(client, origin: str) -> None:  # type: ignore[no-untyped-def]
    """A CORS preflight from each whitelisted origin must succeed."""
    response = await client.options(
        "/convert",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code in (200, 204), response.text
    assert response.headers.get("access-control-allow-origin") == origin


@pytest.mark.asyncio
async def test_cors_blocks_unknown_origin(client) -> None:  # type: ignore[no-untyped-def]
    """An origin not in the allowlist or regex should NOT be echoed back."""
    response = await client.get(
        "/health",
        headers={"Origin": "https://evil.example.com"},
    )
    # The endpoint itself still returns 200 — CORS just doesn't authorise it.
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") in (None, "")
