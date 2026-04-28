"""Tests for the /api/settings/llm endpoints (CRUD on the credential file).

Three guarantees we lock in:

* GET /api/settings/llm reflects file-state in real time.
* POST /api/settings/llm/key writes a 0600 file containing the key, and the
  key NEVER appears in the GET response.
* DELETE /api/settings/llm/key removes the file entry, and the env-var
  fallback still satisfies has_key.
"""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

import pytest

from app.deps import get_settings
from app.services.llm_credentials import LlmCredentialStore


def _credentials_path() -> Path:
    return Path(get_settings().flows_dir) / LlmCredentialStore.FILENAME


@pytest.mark.asyncio
async def test_get_llm_status_no_key_no_env(client, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Without env vars or a file, has_key=False and source='none'."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    resp = await client.get("/api/settings/llm")
    assert resp.status_code == 200
    body = resp.json()
    assert body["provider"] == "anthropic"
    assert body["has_key"] is False
    assert body["source"] == "none"
    assert "key" not in body  # never echoed


@pytest.mark.asyncio
async def test_get_llm_status_env_only(client, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """With only an env var, has_key=True and source='env'."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-from-env")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    # Make sure no file shadows the env var.
    p = _credentials_path()
    if p.exists():
        p.unlink()

    resp = await client.get("/api/settings/llm")
    assert resp.status_code == 200
    body = resp.json()
    assert body["has_key"] is True
    assert body["source"] == "env"


@pytest.mark.asyncio
async def test_post_key_persists_and_get_reports_file(client, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """POSTing a key writes a 0600 file; subsequent GET reports source='file'."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    resp = await client.post(
        "/api/settings/llm/key",
        json={"provider": "anthropic", "key": "sk-ant-test-12345"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["has_key"] is True
    assert body["source"] == "file"

    # The on-disk file actually contains the key.
    p = _credentials_path()
    assert p.exists()
    with p.open() as fh:
        data = json.load(fh)
    assert data["anthropic"]["key"] == "sk-ant-test-12345"

    # GET reports the same.
    resp2 = await client.get("/api/settings/llm")
    assert resp2.status_code == 200
    body2 = resp2.json()
    assert body2["has_key"] is True
    assert body2["source"] == "file"
    # Defensive: the key must NEVER come back over the wire.
    assert "sk-ant-test-12345" not in resp2.text


@pytest.mark.asyncio
async def test_post_key_file_permissions_0600_on_posix(client) -> None:  # type: ignore[no-untyped-def]
    """The credentials file is locked down to user-rw-only on POSIX systems."""
    if os.name != "posix":  # pragma: no cover — guarded for Windows CI
        pytest.skip("POSIX-only check")
    resp = await client.post(
        "/api/settings/llm/key",
        json={"provider": "anthropic", "key": "sk-ant-test-perms"},
    )
    assert resp.status_code == 200
    p = _credentials_path()
    mode = stat.S_IMODE(p.stat().st_mode)
    assert mode == 0o600, f"expected 0o600, got {oct(mode)}"


@pytest.mark.asyncio
async def test_delete_key_falls_back_to_env(client, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """After deleting the file entry, env-var becomes the source again."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-from-env")

    # Save then delete.
    save_resp = await client.post(
        "/api/settings/llm/key",
        json={"provider": "anthropic", "key": "sk-ant-on-disk"},
    )
    assert save_resp.status_code == 200
    assert save_resp.json()["source"] == "file"

    del_resp = await client.delete("/api/settings/llm/key")
    assert del_resp.status_code == 200
    assert del_resp.json() == {"removed": True}

    after = await client.get("/api/settings/llm")
    body = after.json()
    assert body["has_key"] is True
    assert body["source"] == "env"


@pytest.mark.asyncio
async def test_post_rejects_empty_key(client) -> None:  # type: ignore[no-untyped-def]
    """422 from pydantic when the key is empty."""
    resp = await client.post(
        "/api/settings/llm/key",
        json={"provider": "anthropic", "key": ""},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_post_rejects_unknown_provider(client) -> None:  # type: ignore[no-untyped-def]
    """422 from the Literal['anthropic','openai'] schema."""
    resp = await client.post(
        "/api/settings/llm/key",
        json={"provider": "bedrock", "key": "abc"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_credentials_file_never_in_get_response(client) -> None:  # type: ignore[no-untyped-def]
    """Belt-and-braces — even after writing a key, GET stays redacted."""
    sentinel_key = "sk-ant-DO-NOT-LEAK-1234567890"
    save = await client.post(
        "/api/settings/llm/key",
        json={"provider": "anthropic", "key": sentinel_key},
    )
    assert save.status_code == 200
    assert sentinel_key not in save.text

    listing = await client.get("/api/settings/llm")
    assert sentinel_key not in listing.text
