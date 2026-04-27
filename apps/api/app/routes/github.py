"""POST /github/publish — open a PR with flow.json + flow.svg + README.md.

The PAT is accepted in the request body, used immediately for the GitHub
REST calls, and never logged or persisted.  We deliberately do **not**
store the PAT in any session — the user enters it once per publish.

OAuth (a richer browser-side device-code or app-install flow) is tracked
as a Wave 5+ extension; the PAT path is sufficient for the studio's
single-user scope.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services.github_publisher import (
    ERROR_CODES,
    GitHubPublishError,
    GitHubPublisher,
    HttpTransport,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/github", tags=["github"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class PublishRequest(BaseModel):
    """Body for ``POST /github/publish``."""

    pat: str = Field(min_length=1, max_length=400, description="GitHub PAT — never logged")
    repo: str = Field(description="owner/name")
    base: str = Field(default="main")
    branch: str = Field(min_length=1, max_length=200)
    flow_name: str = Field(min_length=1, max_length=120)
    pr_title: str = Field(min_length=1, max_length=200)
    pr_body: str | None = None
    commit_message: str | None = None
    flow_json: dict[str, object]
    flow_svg: str = Field(min_length=1)


class PublishResponse(BaseModel):
    pr_url: str
    pr_number: int
    branch: str
    commit_sha: str


# ---------------------------------------------------------------------------
# Module-level transport seam (tests inject a stub).
# ---------------------------------------------------------------------------


_transport_override: HttpTransport | None = None


def set_transport_override(transport: HttpTransport | None) -> None:
    """Test seam: replace the GitHub HTTP transport."""
    global _transport_override
    _transport_override = transport


def _get_publisher() -> GitHubPublisher:
    return GitHubPublisher(transport=_transport_override)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post(
    "/publish",
    response_model=PublishResponse,
    summary="Open a GitHub PR with the flow JSON + SVG preview",
    responses={
        401: {"description": "PAT is invalid or revoked"},
        403: {"description": "PAT lacks 'repo' scope"},
        404: {"description": "Repository not found or PAT can't see it"},
        409: {"description": "Path conflict on the target branch"},
        422: {"description": "Branch already exists or base branch missing"},
        429: {"description": "GitHub rate-limit reached"},
    },
)
def publish(body: PublishRequest) -> PublishResponse:
    publisher = _get_publisher()
    # IMPORTANT: scrub the PAT from the body dict *before* logging (defence
    # in depth — the error handler also avoids re-emitting the body).
    safe_repr = body.model_dump(exclude={"pat", "flow_json", "flow_svg"})
    logger.info("github.publish requested", extra={"github": safe_repr})
    try:
        result = publisher.publish(
            token=body.pat,
            repo=body.repo,
            base=body.base,
            branch=body.branch,
            flow_name=body.flow_name,
            flow_json=body.flow_json,  # type: ignore[arg-type]
            flow_svg=body.flow_svg,
            pr_title=body.pr_title,
            pr_body=body.pr_body,
            commit_message=body.commit_message,
        )
    except GitHubPublishError as exc:
        logger.warning(
            "github.publish failed",
            extra={"code": exc.code, "github_status": exc.status},
        )
        status = _http_status_for(exc.code)
        raise HTTPException(
            status_code=status,
            detail={"code": exc.code, "message": exc.message},
        ) from exc
    return PublishResponse(
        pr_url=result.pr_url,
        pr_number=result.pr_number,
        branch=result.branch,
        commit_sha=result.commit_sha,
    )


_STATUS_MAP = {
    "BAD_PAT": 401,
    "INSUFFICIENT_SCOPE": 403,
    "REPO_NOT_FOUND": 404,
    "BASE_NOT_FOUND": 422,
    "BRANCH_EXISTS": 422,
    "PATH_CONFLICT": 409,
    "RATE_LIMITED": 429,
    "NETWORK_ERROR": 502,
    "UNKNOWN": 500,
}


def _http_status_for(code: str) -> int:
    return _STATUS_MAP.get(code, 500) if code in ERROR_CODES else 500
