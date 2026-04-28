"""Test that LLM mode without an API key returns a structured 500 (ConfigurationError)."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_llm_missing_key_returns_500(client, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """LLM mode without ANTHROPIC_API_KEY must return 500 problem+json."""
    # Remove both LLM keys from env
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = await client.post(
        "/convert",
        json={"code": "import pandas as pd\ndf = pd.read_csv('x.csv')\n", "mode": "llm"},
    )
    assert response.status_code == 500
    body = response.json()
    assert body.get("status") == 500
    assert "ConfigurationError" in body.get("type", "")
    detail = body.get("detail", "")
    # Error must point users at the Settings UX OR the env var. Both paths
    # are acceptable to satisfy this assertion.
    assert "Settings" in detail or "ANTHROPIC_API_KEY" in detail


@pytest.mark.asyncio
async def test_llm_missing_key_openai_returns_500(client, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """LLM mode with provider=openai and no OPENAI_API_KEY must return 500."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = await client.post(
        "/convert",
        json={
            "code": "import pandas as pd\ndf = pd.read_csv('x.csv')\n",
            "mode": "llm",
            "options": {"provider": "openai"},
        },
    )
    assert response.status_code == 500
    body = response.json()
    assert "ConfigurationError" in body.get("type", "")
