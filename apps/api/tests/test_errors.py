"""Tests for RFC 7807 problem+json error handling of Py2DataikuError hierarchy."""

from __future__ import annotations

import pytest
from fastapi import APIRouter
from httpx import AsyncClient
from py2dataiku.exceptions import (
    ConfigurationError,
    ConversionError,
    ExportError,
    InvalidPythonCodeError,
    LLMResponseParseError,
    ProviderError,
    Py2DataikuError,
    ValidationError,
)

# ---------------------------------------------------------------------------
# Parameterised cases: (exception_class, expected_http_status)
# ---------------------------------------------------------------------------

ERROR_CASES: list[tuple[type[Py2DataikuError], int]] = [
    (InvalidPythonCodeError, 400),
    (ConversionError, 422),
    (ValidationError, 422),
    (LLMResponseParseError, 502),
    (ProviderError, 502),
    (ExportError, 500),
    (ConfigurationError, 500),
    (Py2DataikuError, 500),
]


def _register_throw_route(exc_class: type[Py2DataikuError]) -> APIRouter:
    """Return a one-shot router with a GET endpoint that raises *exc_class*."""
    sub = APIRouter()
    path = f"/test-error/{exc_class.__name__}"

    @sub.get(path)
    async def _raise() -> None:  # noqa: RUF029
        raise exc_class(f"test {exc_class.__name__}")

    return sub


@pytest.mark.asyncio
@pytest.mark.parametrize("exc_class,expected_status", ERROR_CASES)
async def test_error_status_code(
    exc_class: type[Py2DataikuError], expected_status: int
) -> None:
    """Each Py2DataikuError subclass maps to the correct HTTP status."""
    from httpx import ASGITransport, AsyncClient

    from app.main import create_app

    test_app = create_app()
    test_app.include_router(_register_throw_route(exc_class))

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://testserver"
    ) as ac:
        response = await ac.get(f"/test-error/{exc_class.__name__}")

    assert response.status_code == expected_status


@pytest.mark.asyncio
@pytest.mark.parametrize("exc_class,expected_status", ERROR_CASES)
async def test_error_content_type(
    exc_class: type[Py2DataikuError], expected_status: int
) -> None:
    """Response content-type is application/problem+json."""
    from httpx import ASGITransport, AsyncClient

    from app.main import create_app

    test_app = create_app()
    test_app.include_router(_register_throw_route(exc_class))

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://testserver"
    ) as ac:
        response = await ac.get(f"/test-error/{exc_class.__name__}")

    assert "application/problem+json" in response.headers["content-type"]


@pytest.mark.asyncio
@pytest.mark.parametrize("exc_class,expected_status", ERROR_CASES)
async def test_error_problem_json_shape(
    exc_class: type[Py2DataikuError], expected_status: int
) -> None:
    """RFC 7807 required fields: type, title, status, detail, instance."""
    from httpx import ASGITransport, AsyncClient

    from app.main import create_app

    test_app = create_app()
    test_app.include_router(_register_throw_route(exc_class))

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://testserver"
    ) as ac:
        response = await ac.get(f"/test-error/{exc_class.__name__}")

    body = response.json()
    for field in ("type", "title", "status", "detail", "instance"):
        assert field in body, f"Missing RFC 7807 field '{field}' for {exc_class.__name__}"

    assert body["status"] == expected_status
    assert exc_class.__name__ in body["type"]


@pytest.mark.asyncio
async def test_request_id_header_echoed(client: AsyncClient) -> None:
    """X-Request-ID from request is echoed in response headers."""
    custom_id = "my-test-request-id-123"
    response = await client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.headers.get("x-request-id") == custom_id


@pytest.mark.asyncio
async def test_request_id_generated_when_absent(client: AsyncClient) -> None:
    """X-Request-ID is generated if not provided by client."""
    response = await client.get("/health")
    assert "x-request-id" in response.headers
    assert len(response.headers["x-request-id"]) > 0
