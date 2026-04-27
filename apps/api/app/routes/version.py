"""Version endpoint — exposes the latest commit message for the in-app
"Show release notes" sub-modal in the Cmd+K command palette.

The endpoint resolves the commit message in three layers (highest priority
first) so it works in dev, in CI, and inside an immutable container build:

1. ``PY_IKU_RELEASE_NOTES`` environment variable (CI/CD bakes this in).
2. ``git log -1 --pretty=%B`` (developer machines / source checkouts).
3. A static fallback message so production never returns a 500.

The endpoint is deliberately shallow — it returns a plain JSON shape rather
than re-using the (already loaded) HealthResponse model, because release
notes is a UI-only concern and we'd rather not bake the latest commit text
into the health check.
"""

from __future__ import annotations

import importlib.metadata
import os
import shutil
import subprocess
from pathlib import Path

import py2dataiku
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["version"])


def _api_version() -> str:
    try:
        return importlib.metadata.version("py-iku-studio-api")
    except importlib.metadata.PackageNotFoundError:
        return "0.0.0"


def _git_repo_root() -> Path | None:
    """Walk up from this module looking for a ``.git`` directory.

    Returns ``None`` if no repo root is found (typical inside a container
    image with the working tree stripped out).
    """

    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / ".git").exists():
            return parent
    return None


def _latest_commit_message() -> str | None:
    """Return the latest commit message, or ``None`` when unavailable.

    Prefers ``PY_IKU_RELEASE_NOTES`` so a Docker image can ship a frozen
    note; falls back to ``git log -1 --pretty=%B`` for source checkouts.
    """

    env = os.environ.get("PY_IKU_RELEASE_NOTES")
    if env and env.strip():
        return env.strip()

    git = shutil.which("git")
    repo = _git_repo_root()
    if not git or not repo:
        return None
    try:
        result = subprocess.run(  # noqa: S603 — fixed argv, no shell.
            [git, "log", "-1", "--pretty=%B"],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=2.0,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    out = result.stdout.strip()
    return out or None


def _latest_commit_sha() -> str | None:
    """Short sha for the latest commit, or ``None``.

    Useful so the UI can render "abc1234" alongside the commit message.
    """

    git = shutil.which("git")
    repo = _git_repo_root()
    if not git or not repo:
        return None
    try:
        result = subprocess.run(  # noqa: S603 — fixed argv, no shell.
            [git, "rev-parse", "--short", "HEAD"],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=2.0,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    out = result.stdout.strip()
    return out or None


class VersionResponse(BaseModel):
    """Lightweight response for the in-app release-notes modal."""

    api_version: str
    py_iku_version: str
    commit: str | None
    commit_message: str
    source: str  # "env" | "git" | "fallback"


@router.get(
    "/api/version",
    response_model=VersionResponse,
    summary="Latest version + commit message for the release-notes modal",
)
async def version() -> VersionResponse:
    """Return service version + latest commit message."""

    msg = _latest_commit_message()
    sha = _latest_commit_sha()

    if os.environ.get("PY_IKU_RELEASE_NOTES"):
        source = "env"
    elif msg is not None:
        source = "git"
    else:
        source = "fallback"
        msg = "No release notes available — running outside a git checkout."

    return VersionResponse(
        api_version=_api_version(),
        py_iku_version=py2dataiku.__version__,
        commit=sha,
        commit_message=msg,
        source=source,
    )
