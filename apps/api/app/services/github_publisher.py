"""GitHub-PR publisher — push flow JSON + SVG + README to a branch + open PR.

The PAT never leaves the backend; the frontend POSTs once to ``/github/publish``
with the PAT in the body, the server uses it to talk to api.github.com over
HTTPS, and the PAT is then dropped (we never persist or log it).

The flow is the standard GitHub REST "create-a-commit" sequence — we use it
in preference to the simpler Contents API because we want to commit multiple
files in one commit:

1. ``GET  /repos/{owner}/{repo}``                       — verify access + base ref
2. ``GET  /repos/{owner}/{repo}/git/ref/heads/{base}``  — base SHA
3. (optional) ``GET /repos/{owner}/{repo}/git/ref/heads/{branch}`` — branch exists?
4. ``POST /repos/{owner}/{repo}/git/refs``              — create branch
5. ``POST /repos/{owner}/{repo}/git/blobs`` (×3)        — flow.json, flow.svg, README.md
6. ``POST /repos/{owner}/{repo}/git/trees``             — tree under base commit
7. ``POST /repos/{owner}/{repo}/git/commits``           — commit pointing at tree
8. ``PATCH /repos/{owner}/{repo}/git/refs/heads/{br}``  — fast-forward branch
9. ``POST /repos/{owner}/{repo}/pulls``                 — open the PR

Errors are surfaced as :class:`GitHubPublishError` with a stable ``code``
attribute that the frontend can map to user-facing copy.
"""

from __future__ import annotations

import base64
import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Protocol
from urllib import error as urllib_error
from urllib import request as urllib_request

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class GitHubPublishError(Exception):
    """Raised when a GitHub publish step fails.

    ``code`` is one of the strings in :data:`ERROR_CODES` so the frontend
    can map it to user-friendly copy without parsing English.
    """

    def __init__(self, code: str, message: str, *, status: int | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.status = status
        self.message = message


ERROR_CODES = {
    "BAD_PAT",            # 401 — PAT invalid or revoked
    "INSUFFICIENT_SCOPE", # 403 — PAT lacks repo scope
    "REPO_NOT_FOUND",     # 404 — repo doesn't exist or PAT can't see it
    "BASE_NOT_FOUND",     # 422 — base branch missing
    "BRANCH_EXISTS",      # 422 — branch already exists
    "PATH_CONFLICT",      # 409 — file already at that path on branch
    "RATE_LIMITED",       # 429
    "NETWORK_ERROR",      # 0  — server-side network failure
    "UNKNOWN",
}


# ---------------------------------------------------------------------------
# HTTP transport (Protocol + default urllib impl) — keeps deps small and
# allows the test suite to inject a fake transport without pytest-httpx.
# ---------------------------------------------------------------------------


class HttpTransport(Protocol):
    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes | None,
    ) -> tuple[int, bytes, dict[str, str]]:
        ...


@dataclass
class _UrllibTransport:
    timeout: float = 15.0

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes | None,
    ) -> tuple[int, bytes, dict[str, str]]:
        req = urllib_request.Request(url, data=body, method=method)
        for k, v in headers.items():
            req.add_header(k, v)
        try:
            with urllib_request.urlopen(req, timeout=self.timeout) as resp:
                payload = resp.read()
                return (
                    resp.getcode(),
                    payload,
                    {k.lower(): v for k, v in resp.headers.items()},
                )
        except urllib_error.HTTPError as exc:
            payload = b""
            try:
                payload = exc.read()
            except Exception:  # noqa: BLE001
                pass
            return (
                exc.code,
                payload,
                {k.lower(): v for k, v in (exc.headers or {}).items()},
            )
        except urllib_error.URLError as exc:
            raise GitHubPublishError(
                "NETWORK_ERROR", f"GitHub network error: {exc.reason}"
            ) from exc


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


_REPO_RE = re.compile(r"^[A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+$")
_BRANCH_RE = re.compile(r"^[A-Za-z0-9._/\-]{1,200}$")


def _validate_repo(repo: str) -> tuple[str, str]:
    """Split ``owner/repo`` after sanity-checking the shape."""
    if not _REPO_RE.match(repo):
        raise GitHubPublishError(
            "REPO_NOT_FOUND",
            f"repo {repo!r} must be in 'owner/name' form",
            status=400,
        )
    owner, name = repo.split("/", 1)
    return owner, name


def _validate_branch(branch: str, *, label: str) -> str:
    if not _BRANCH_RE.match(branch):
        raise GitHubPublishError(
            "BASE_NOT_FOUND",
            f"{label} branch name {branch!r} is invalid",
            status=400,
        )
    return branch


# ---------------------------------------------------------------------------
# Publisher
# ---------------------------------------------------------------------------


@dataclass
class PublishResult:
    """What the server returns to the frontend on success."""

    pr_url: str
    pr_number: int
    branch: str
    commit_sha: str


@dataclass
class GitHubPublisher:
    """Stateless GitHub publisher — accepts the PAT per call, never stores it."""

    transport: HttpTransport

    def __init__(self, transport: HttpTransport | None = None) -> None:
        self.transport = transport or _UrllibTransport()

    # -- low level ------------------------------------------------------

    def _call(
        self,
        method: str,
        path: str,
        *,
        token: str,
        body: dict[str, Any] | None = None,
    ) -> tuple[int, dict[str, Any] | list[Any] | None, dict[str, str]]:
        url = f"{GITHUB_API}{path}"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "py-iku-studio/1.0",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        raw = None
        if body is not None:
            raw = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        status, payload, response_headers = self.transport.request(
            method, url, headers=headers, body=raw
        )
        decoded: dict[str, Any] | list[Any] | None
        if not payload:
            decoded = None
        else:
            try:
                decoded = json.loads(payload.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                decoded = None
        return status, decoded, response_headers

    def _raise_for_status(
        self,
        status: int,
        body: dict[str, Any] | list[Any] | None,
        *,
        step: str,
    ) -> None:
        if 200 <= status < 300:
            return
        msg = ""
        if isinstance(body, dict):
            msg = str(body.get("message") or "")
        if status == 401:
            raise GitHubPublishError(
                "BAD_PAT",
                f"{step}: PAT rejected by GitHub ({msg or 'unauthorized'})",
                status=status,
            )
        if status == 403:
            # GitHub uses 403 for both rate-limit and missing-scope.
            if "rate limit" in msg.lower():
                raise GitHubPublishError(
                    "RATE_LIMITED", f"{step}: GitHub rate-limit reached", status=status
                )
            raise GitHubPublishError(
                "INSUFFICIENT_SCOPE",
                f"{step}: PAT lacks the 'repo' scope ({msg})",
                status=status,
            )
        if status == 404:
            raise GitHubPublishError(
                "REPO_NOT_FOUND",
                f"{step}: not found ({msg or 'check repo + base branch'})",
                status=status,
            )
        if status == 409:
            raise GitHubPublishError(
                "PATH_CONFLICT",
                f"{step}: conflict ({msg})",
                status=status,
            )
        if status == 422:
            # 422 is overloaded — try to disambiguate.
            if "Reference already exists" in msg:
                raise GitHubPublishError(
                    "BRANCH_EXISTS", f"{step}: branch already exists", status=status
                )
            if "does not exist" in msg.lower():
                raise GitHubPublishError(
                    "BASE_NOT_FOUND",
                    f"{step}: base branch not found ({msg})",
                    status=status,
                )
            raise GitHubPublishError(
                "UNKNOWN", f"{step}: GitHub 422 ({msg})", status=status
            )
        if status == 429:
            raise GitHubPublishError(
                "RATE_LIMITED", f"{step}: GitHub rate-limit reached", status=status
            )
        raise GitHubPublishError(
            "UNKNOWN", f"{step}: HTTP {status} ({msg})", status=status
        )

    # -- public ---------------------------------------------------------

    def publish(
        self,
        *,
        token: str,
        repo: str,
        base: str,
        branch: str,
        flow_name: str,
        flow_json: dict[str, Any],
        flow_svg: str,
        pr_title: str,
        pr_body: str | None = None,
        commit_message: str | None = None,
        readme: str | None = None,
        on_progress: "ProgressFn | None" = None,
    ) -> PublishResult:
        """Run the full create-branch → commit-files → open-PR sequence."""
        if not token:
            raise GitHubPublishError("BAD_PAT", "PAT is required", status=401)
        owner, repo_name = _validate_repo(repo)
        base = _validate_branch(base, label="base")
        branch = _validate_branch(branch, label="head")

        progress = on_progress or (lambda _label: None)

        # 1. Verify repo
        progress("Verifying repo access…")
        status, body, _ = self._call("GET", f"/repos/{owner}/{repo_name}", token=token)
        self._raise_for_status(status, body, step="verify-repo")

        # 2. Get base ref SHA
        progress("Fetching base branch SHA…")
        status, body, _ = self._call(
            "GET",
            f"/repos/{owner}/{repo_name}/git/ref/heads/{base}",
            token=token,
        )
        self._raise_for_status(status, body, step="get-base-ref")
        base_sha = ""
        if isinstance(body, dict):
            obj = body.get("object")
            if isinstance(obj, dict):
                base_sha = str(obj.get("sha") or "")
        if not base_sha:
            raise GitHubPublishError(
                "BASE_NOT_FOUND", "base branch did not return a SHA"
            )

        # 3. Check if branch already exists (treat as fatal — the user must
        #    pick a unique branch).
        progress("Creating branch…")
        status, body, _ = self._call(
            "GET",
            f"/repos/{owner}/{repo_name}/git/ref/heads/{branch}",
            token=token,
        )
        if status < 400:
            raise GitHubPublishError(
                "BRANCH_EXISTS",
                f"branch {branch!r} already exists on {repo}",
                status=422,
            )

        # 4. Create the branch
        status, body, _ = self._call(
            "POST",
            f"/repos/{owner}/{repo_name}/git/refs",
            token=token,
            body={"ref": f"refs/heads/{branch}", "sha": base_sha},
        )
        self._raise_for_status(status, body, step="create-branch")

        # 5. Build the file tree
        progress("Committing files…")
        flow_dir = f"flows/{flow_name}"
        readme_text = readme or _default_readme(flow_name, pr_title)
        files = {
            f"{flow_dir}/flow.json": json.dumps(flow_json, indent=2, sort_keys=True),
            f"{flow_dir}/flow.svg": flow_svg,
            f"{flow_dir}/README.md": readme_text,
        }

        tree_entries: list[dict[str, Any]] = []
        for path, content in files.items():
            blob_status, blob_body, _ = self._call(
                "POST",
                f"/repos/{owner}/{repo_name}/git/blobs",
                token=token,
                body={
                    "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
                    "encoding": "base64",
                },
            )
            self._raise_for_status(blob_status, blob_body, step=f"create-blob {path}")
            blob_sha = ""
            if isinstance(blob_body, dict):
                blob_sha = str(blob_body.get("sha") or "")
            if not blob_sha:
                raise GitHubPublishError(
                    "UNKNOWN", f"blob for {path} returned no sha"
                )
            tree_entries.append(
                {"path": path, "mode": "100644", "type": "blob", "sha": blob_sha}
            )

        # 6. Create the tree
        status, body, _ = self._call(
            "POST",
            f"/repos/{owner}/{repo_name}/git/trees",
            token=token,
            body={"base_tree": base_sha, "tree": tree_entries},
        )
        self._raise_for_status(status, body, step="create-tree")
        tree_sha = ""
        if isinstance(body, dict):
            tree_sha = str(body.get("sha") or "")
        if not tree_sha:
            raise GitHubPublishError("UNKNOWN", "tree response had no sha")

        # 7. Commit
        commit_msg = commit_message or f"Add flow {flow_name} from py-iku Studio"
        status, body, _ = self._call(
            "POST",
            f"/repos/{owner}/{repo_name}/git/commits",
            token=token,
            body={
                "message": commit_msg,
                "tree": tree_sha,
                "parents": [base_sha],
            },
        )
        self._raise_for_status(status, body, step="create-commit")
        commit_sha = ""
        if isinstance(body, dict):
            commit_sha = str(body.get("sha") or "")
        if not commit_sha:
            raise GitHubPublishError("UNKNOWN", "commit response had no sha")

        # 8. Fast-forward the branch
        status, body, _ = self._call(
            "PATCH",
            f"/repos/{owner}/{repo_name}/git/refs/heads/{branch}",
            token=token,
            body={"sha": commit_sha, "force": False},
        )
        self._raise_for_status(status, body, step="update-ref")

        # 9. Open the PR
        progress("Opening PR…")
        status, body, _ = self._call(
            "POST",
            f"/repos/{owner}/{repo_name}/pulls",
            token=token,
            body={
                "title": pr_title,
                "head": branch,
                "base": base,
                "body": pr_body or _default_pr_body(flow_name),
            },
        )
        self._raise_for_status(status, body, step="open-pr")
        pr_url = ""
        pr_number = 0
        if isinstance(body, dict):
            pr_url = str(body.get("html_url") or "")
            pr_number = int(body.get("number") or 0)
        if not pr_url:
            raise GitHubPublishError("UNKNOWN", "PR response missing html_url")

        return PublishResult(
            pr_url=pr_url,
            pr_number=pr_number,
            branch=branch,
            commit_sha=commit_sha,
        )


class ProgressFn(Protocol):
    def __call__(self, label: str) -> None:
        ...


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------


def _default_readme(flow_name: str, pr_title: str) -> str:
    return (
        f"# {flow_name}\n\n"
        f"_{pr_title}_\n\n"
        "Generated by **py-iku Studio**.\n\n"
        "## Files\n\n"
        "- `flow.json` — the canonical Dataiku flow definition (round-trip\n"
        "  with `DataikuFlow.from_dict`).\n"
        "- `flow.svg` — a rendered preview of the DAG.\n"
        "- `README.md` — this file.\n"
    )


def _default_pr_body(flow_name: str) -> str:
    return (
        f"This PR adds the **{flow_name}** flow generated by py-iku Studio.\n\n"
        "## Contents\n\n"
        "- Flow JSON (`flow.json`)\n"
        "- Rendered SVG preview (`flow.svg`)\n"
        "- README\n\n"
        "_Created via the Studio Export pane → Open as PR._\n"
    )
