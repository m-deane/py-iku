"""Shared pytest fixtures for the API test suite."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.deps import get_settings, reset_repo_singletons
from app.main import app
from app.routes.share import reset_share_rate_limiter


@pytest.fixture(autouse=True)
def _isolate_persistence_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point Settings.flows_dir at a unique tmp dir so tests stay isolated."""
    # Patch the cached Settings instance to use the per-test tmp dir.
    settings = get_settings()
    monkeypatch.setattr(settings, "flows_dir", tmp_path / "flows-store")
    # Force a fresh FlowsRepo / AuditRepo bound to the new dir.
    reset_repo_singletons()
    reset_share_rate_limiter()
    yield
    reset_repo_singletons()
    reset_share_rate_limiter()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client wired directly to the FastAPI ASGI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac
