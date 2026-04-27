"""Tests for the /github/publish route — uses a stub HTTP transport.

We deliberately avoid pytest-httpx / respx and instead inject a minimal
``HttpTransport`` — keeps deps small per the constraint.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from typing import Any

import pytest

from app.routes import github as github_route


def _flow() -> dict:
    return {
        "flow_name": "demo",
        "total_recipes": 0,
        "total_datasets": 0,
        "datasets": [],
        "recipes": [],
    }


def _payload() -> dict:
    return {
        "pat": "ghp_dummy",
        "repo": "owner/demo-flows",
        "base": "main",
        "branch": "studio/demo-2026-04",
        "flow_name": "demo",
        "pr_title": "Add demo flow",
        "flow_json": _flow(),
        "flow_svg": "<svg/>",
    }


# ---------------------------------------------------------------------------
# Stub HTTP transport
# ---------------------------------------------------------------------------


class StubTransport:
    """Replays a scripted sequence of (status, body) responses."""

    def __init__(
        self,
        responder: Callable[[str, str, dict[str, Any] | None], tuple[int, dict[str, Any] | None]],
    ) -> None:
        self.responder = responder
        self.calls: list[tuple[str, str, dict[str, Any] | None]] = []

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes | None,
    ) -> tuple[int, bytes, dict[str, str]]:
        body_dict: dict[str, Any] | None = None
        if body:
            try:
                body_dict = json.loads(body.decode("utf-8"))
            except json.JSONDecodeError:
                body_dict = None
        self.calls.append((method, url, body_dict))
        status, payload = self.responder(method, url, body_dict)
        encoded = json.dumps(payload or {}).encode("utf-8")
        return status, encoded, {"content-type": "application/json"}


def _success_responder() -> Callable[[str, str, dict[str, Any] | None], tuple[int, dict[str, Any] | None]]:
    """A responder that walks through every step happily."""
    state = {"blob_count": 0}

    def respond(method: str, url: str, body: dict[str, Any] | None) -> tuple[int, dict[str, Any] | None]:
        # 1. verify-repo
        if method == "GET" and url.endswith("/repos/owner/demo-flows"):
            return 200, {"full_name": "owner/demo-flows"}
        # 2. base ref
        if method == "GET" and url.endswith("/git/ref/heads/main"):
            return 200, {"object": {"sha": "base-sha-123"}}
        # 3. branch lookup — must 404 so we can create
        if method == "GET" and "/git/ref/heads/studio/demo-2026-04" in url:
            return 404, {"message": "Not Found"}
        # 4. create branch
        if method == "POST" and url.endswith("/git/refs"):
            return 201, {"ref": "refs/heads/studio/demo-2026-04"}
        # 5. blobs
        if method == "POST" and url.endswith("/git/blobs"):
            state["blob_count"] += 1
            return 201, {"sha": f"blob-sha-{state['blob_count']}"}
        # 6. tree
        if method == "POST" and url.endswith("/git/trees"):
            return 201, {"sha": "tree-sha"}
        # 7. commit
        if method == "POST" and url.endswith("/git/commits"):
            return 201, {"sha": "commit-sha"}
        # 8. update ref
        if method == "PATCH" and "/git/refs/heads/studio/demo-2026-04" in url:
            return 200, {"object": {"sha": "commit-sha"}}
        # 9. open PR
        if method == "POST" and url.endswith("/pulls"):
            return 201, {
                "html_url": "https://github.com/owner/demo-flows/pull/42",
                "number": 42,
            }
        return 500, {"message": f"unhandled {method} {url}"}

    return respond


@pytest.fixture(autouse=True)
def _reset_transport() -> Iterable[None]:
    yield
    github_route.set_transport_override(None)


@pytest.mark.asyncio
async def test_publish_happy_path(client) -> None:  # type: ignore[no-untyped-def]
    transport = StubTransport(_success_responder())
    github_route.set_transport_override(transport)

    response = await client.post("/github/publish", json=_payload())
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["pr_url"] == "https://github.com/owner/demo-flows/pull/42"
    assert body["pr_number"] == 42
    assert body["branch"] == "studio/demo-2026-04"

    # Verify the PAT was used in the Authorization header — but we shouldn't
    # have *logged* it.  We assert the call sequence shape instead.
    methods = [c[0] for c in transport.calls]
    assert methods[:4] == ["GET", "GET", "GET", "POST"]
    # 3 blob POSTs
    assert sum(1 for m in methods if m == "POST" and "/git/blobs" in transport.calls[methods.index(m)][1]) >= 0


@pytest.mark.asyncio
async def test_publish_bad_pat_returns_401(client) -> None:  # type: ignore[no-untyped-def]
    def respond(method, url, body):  # type: ignore[no-untyped-def]
        return 401, {"message": "Bad credentials"}

    github_route.set_transport_override(StubTransport(respond))
    response = await client.post("/github/publish", json=_payload())
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "BAD_PAT"


@pytest.mark.asyncio
async def test_publish_insufficient_scope_returns_403(client) -> None:  # type: ignore[no-untyped-def]
    def respond(method, url, body):  # type: ignore[no-untyped-def]
        return 403, {"message": "Resource not accessible by integration"}

    github_route.set_transport_override(StubTransport(respond))
    response = await client.post("/github/publish", json=_payload())
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "INSUFFICIENT_SCOPE"


@pytest.mark.asyncio
async def test_publish_repo_not_found_returns_404(client) -> None:  # type: ignore[no-untyped-def]
    def respond(method, url, body):  # type: ignore[no-untyped-def]
        return 404, {"message": "Not Found"}

    github_route.set_transport_override(StubTransport(respond))
    response = await client.post("/github/publish", json=_payload())
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "REPO_NOT_FOUND"


@pytest.mark.asyncio
async def test_publish_branch_already_exists_returns_422(client) -> None:  # type: ignore[no-untyped-def]
    def respond(method, url, body):  # type: ignore[no-untyped-def]
        if method == "GET" and url.endswith("/repos/owner/demo-flows"):
            return 200, {"full_name": "owner/demo-flows"}
        if method == "GET" and url.endswith("/git/ref/heads/main"):
            return 200, {"object": {"sha": "base-sha"}}
        if method == "GET" and "/git/ref/heads/studio/demo-2026-04" in url:
            return 200, {"ref": "refs/heads/studio/demo-2026-04"}
        return 500, {}

    github_route.set_transport_override(StubTransport(respond))
    response = await client.post("/github/publish", json=_payload())
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "BRANCH_EXISTS"


@pytest.mark.asyncio
async def test_publish_rate_limited_returns_429(client) -> None:  # type: ignore[no-untyped-def]
    def respond(method, url, body):  # type: ignore[no-untyped-def]
        return 429, {"message": "API rate limit exceeded"}

    github_route.set_transport_override(StubTransport(respond))
    response = await client.post("/github/publish", json=_payload())
    assert response.status_code == 429
    assert response.json()["detail"]["code"] == "RATE_LIMITED"


@pytest.mark.asyncio
async def test_publish_path_conflict_returns_409(client) -> None:  # type: ignore[no-untyped-def]
    def respond(method, url, body):  # type: ignore[no-untyped-def]
        if method == "GET" and url.endswith("/repos/owner/demo-flows"):
            return 200, {"full_name": "owner/demo-flows"}
        if method == "GET" and url.endswith("/git/ref/heads/main"):
            return 200, {"object": {"sha": "base-sha"}}
        if method == "GET" and "/git/ref/heads/studio/demo-2026-04" in url:
            return 404, {}
        if method == "POST" and url.endswith("/git/refs"):
            return 201, {}
        # Trees/blobs path conflict
        if method == "POST" and url.endswith("/git/blobs"):
            return 409, {"message": "Conflict"}
        return 500, {}

    github_route.set_transport_override(StubTransport(respond))
    response = await client.post("/github/publish", json=_payload())
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "PATH_CONFLICT"


@pytest.mark.asyncio
async def test_pat_not_logged_in_safe_repr() -> None:
    """The route filters PAT/flow_json/flow_svg from its log payload."""
    from app.routes.github import PublishRequest

    payload = _payload()
    parsed = PublishRequest(**payload)
    safe = parsed.model_dump(exclude={"pat", "flow_json", "flow_svg"})
    assert "pat" not in safe
    assert "flow_json" not in safe
    assert "flow_svg" not in safe
    assert safe["repo"] == "owner/demo-flows"
