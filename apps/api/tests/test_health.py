"""Tests for GET /health."""

from __future__ import annotations

import py2dataiku
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_200(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_response_has_required_keys(client: AsyncClient) -> None:
    response = await client.get("/health")
    body = response.json()
    assert "status" in body
    assert "version" in body
    assert "py_iku_version" in body


@pytest.mark.asyncio
async def test_health_status_is_ok(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_health_py_iku_version_matches(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.json()["py_iku_version"] == py2dataiku.__version__
