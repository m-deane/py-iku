"""Validation tests for POST /convert: empty code, oversized code, invalid syntax."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_empty_code_returns_422(client) -> None:  # type: ignore[no-untyped-def]
    """Empty code string should return 422 (Pydantic validator rejects blank code)."""
    response = await client.post(
        "/convert",
        json={"code": "", "mode": "rule"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_whitespace_only_code_returns_422(client) -> None:  # type: ignore[no-untyped-def]
    """Whitespace-only code should return 422."""
    response = await client.post(
        "/convert",
        json={"code": "   \n\t  ", "mode": "rule"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_oversized_code_returns_422(client) -> None:  # type: ignore[no-untyped-def]
    """Code exceeding max_code_size_bytes should return 422 (validator raises ValueError → 422)."""
    big_code = "x = 1\n" * 50_000  # ~350 KB, well above 256 KB default
    response = await client.post(
        "/convert",
        json={
            "code": big_code,
            "mode": "rule",
            "options": {"max_code_size_bytes": 262144},
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_custom_max_size_accepted(client) -> None:  # type: ignore[no-untyped-def]
    """Code within a custom max_code_size_bytes should succeed."""
    code = "import pandas as pd\ndf = pd.read_csv('x.csv')\n"
    response = await client.post(
        "/convert",
        json={
            "code": code,
            "mode": "rule",
            "options": {"max_code_size_bytes": 262144},
        },
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_invalid_python_syntax_returns_400(client) -> None:  # type: ignore[no-untyped-def]
    """Syntactically invalid Python should map to 400 via InvalidPythonCodeError."""
    response = await client.post(
        "/convert",
        json={"code": "def broken(:\n    pass\n", "mode": "rule"},
    )
    assert response.status_code == 400
    body = response.json()
    # RFC 7807 problem+json
    assert "InvalidPythonCodeError" in body.get("type", "")
    assert body.get("status") == 400


@pytest.mark.asyncio
async def test_invalid_mode_returns_422(client) -> None:  # type: ignore[no-untyped-def]
    """Unknown conversion mode should return 422 from Pydantic."""
    response = await client.post(
        "/convert",
        json={"code": "import pandas as pd", "mode": "magic"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_missing_code_field_returns_422(client) -> None:  # type: ignore[no-untyped-def]
    """Request body without `code` field should return 422."""
    response = await client.post(
        "/convert",
        json={"mode": "rule"},
    )
    assert response.status_code == 422
