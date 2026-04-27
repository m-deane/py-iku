"""GDPR export bundler — produces a per-user ZIP containing every
user-attributable record across the audit log, comments store, budget
config, and saved-flow snapshots.

The ZIP shape is a contract — the frontend ``Export my data`` button and the
backend tests both rely on the exact filename layout::

    py-iku-studio-export-<user>-<timestamp>.zip
    ├── llm-history.jsonl
    ├── comments.jsonl
    ├── budget-config.json
    └── flow-snapshots.jsonl

Empty files are still written so the round-trip checklist test can assert all
four exist regardless of how much data the user has.
"""

from __future__ import annotations

import io
import json
import os
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .comments_store import _default_author
from .llm_audit import LlmAuditRepo, _default_user

EXPORT_FILES = (
    "llm-history.jsonl",
    "comments.jsonl",
    "budget-config.json",
    "flow-snapshots.jsonl",
)


def _read_budget_config(base_dir: Path) -> str:
    """Return the persisted ``llm-budget.json`` body, or ``"{}"`` if absent."""
    path = base_dir / "llm-budget.json"
    if not path.exists():
        return "{}"
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return "{}"


def _gather_comments_for_user(base_dir: Path, user: str) -> str:
    """Return JSONL of every comment authored by *user* across all flows."""
    comments_dir = base_dir / "comments"
    if not comments_dir.is_dir():
        return ""
    out: list[str] = []
    for fp in sorted(comments_dir.glob("*.jsonl")):
        try:
            for line in fp.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                author = obj.get("author") or _default_author()
                if author == user:
                    out.append(json.dumps(obj, separators=(",", ":")))
        except OSError:
            continue
    return ("\n".join(out) + "\n") if out else ""


def _gather_flow_snapshots(base_dir: Path, user: str) -> str:
    """Return JSONL of every saved-flow snapshot the user owns.

    Sprint 5 introduces a soft notion of ownership — flows tagged with
    ``user:<name>`` belong to that user.  In single-user mode every saved
    flow is yours, so we include them all when the lookup matches the
    default user.
    """
    flows_dir = base_dir / "flows"
    if not flows_dir.is_dir():
        return ""
    default_user = _default_user()
    out: list[str] = []
    for fp in sorted(flows_dir.glob("*.json")):
        try:
            raw = fp.read_text(encoding="utf-8")
            obj = json.loads(raw)
        except (OSError, json.JSONDecodeError):
            continue
        tags = obj.get("tags") or []
        owner_tag: str | None = None
        for tag in tags:
            if isinstance(tag, str) and tag.startswith("user:"):
                owner_tag = tag.split(":", 1)[1]
                break
        owner = owner_tag or default_user
        if owner == user:
            out.append(json.dumps(obj, separators=(",", ":")))
    return ("\n".join(out) + "\n") if out else ""


def build_user_export(
    *,
    base_dir: Path | str,
    user: str,
    audit_repo: LlmAuditRepo,
) -> tuple[bytes, str]:
    """Build a ZIP of every user-attributable artefact.

    Returns ``(zip_bytes, filename)`` — the filename always follows the
    ``py-iku-studio-export-<user>-<timestamp>.zip`` contract.
    """
    base = Path(base_dir)
    if not user:
        raise ValueError("user is required")

    history = audit_repo.export_user_jsonl(user)
    comments = _gather_comments_for_user(base, user)
    budget = _read_budget_config(base)
    snapshots = _gather_flow_snapshots(base, user)

    buf = io.BytesIO()
    # ZIP_DEFLATED keeps the bundle small without external deps.
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("llm-history.jsonl", history)
        zf.writestr("comments.jsonl", comments)
        zf.writestr("budget-config.json", budget)
        zf.writestr("flow-snapshots.jsonl", snapshots)
        # Manifest so a downstream tool can verify the bundle without
        # re-implementing the file list.
        manifest = {
            "user": user,
            "generated_at": datetime.now(tz=UTC).isoformat(),
            "files": list(EXPORT_FILES),
            "studio_user_default": _default_user(),
            "host_studio_user_env": os.environ.get("STUDIO_USER"),
        }
        zf.writestr(
            "manifest.json",
            json.dumps(manifest, indent=2),
        )
    ts = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    safe_user = "".join(c if c.isalnum() or c in "-_." else "_" for c in user)
    filename = f"py-iku-studio-export-{safe_user}-{ts}.zip"
    return buf.getvalue(), filename


def list_export_files(zip_bytes: bytes) -> list[str]:
    """Test helper — return the file list inside a built export bundle."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes), mode="r") as zf:
        return sorted(zf.namelist())


def read_export_file(zip_bytes: bytes, name: str) -> str:
    """Test helper — read one file out of an export bundle."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes), mode="r") as zf:
        return zf.read(name).decode("utf-8")
