"""Tests for the ``GET /api/version`` endpoint.

This endpoint is consumed by the in-app "Show release notes" sub-modal in
the Cmd+K command palette. The endpoint is intentionally permissive — it
falls back to a static message when neither the env override nor a git
checkout is available, so production never returns a 500.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_version_endpoint_returns_200() -> None:
    """The endpoint always returns 200 + a usable JSON payload."""
    client = _client()
    resp = client.get("/api/version")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    # Required shape — every field is non-optional except `commit`.
    assert isinstance(body["api_version"], str)
    assert isinstance(body["py_iku_version"], str)
    assert isinstance(body["commit_message"], str)
    assert body["source"] in {"env", "git", "fallback"}


def test_version_honours_env_override(monkeypatch) -> None:
    """``PY_IKU_RELEASE_NOTES`` takes precedence over the git command."""
    monkeypatch.setenv("PY_IKU_RELEASE_NOTES", "v1.2.3 — quarterly release")
    client = _client()
    resp = client.get("/api/version")
    assert resp.status_code == 200
    body = resp.json()
    assert body["commit_message"] == "v1.2.3 — quarterly release"
    assert body["source"] == "env"
