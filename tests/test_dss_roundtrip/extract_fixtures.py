"""Extract canonical-shape DSS JSON fixtures from the public-docs snapshot.

This script walks ``docs/dataiku-reference/{recipes,processors}/*.md``, finds
fenced JSON / YAML code blocks, attempts to parse them, classifies each as a
*recipe* or *processor* shape, and writes them to
``tests/test_dss_roundtrip/fixtures/{category}/{slug}__{n}.json`` with a
metadata header that records the source file and source URL.

The extractor is idempotent — re-running overwrites cleanly. Files in the
``fixtures/_seeds/`` subtree are NOT touched (they are hand-authored canonical
shapes the harness uses to complement the small set of inline JSON examples
present in the official docs).

Usage:
    python tests/test_dss_roundtrip/extract_fixtures.py

Run from the repo root. Prints a per-category summary at the end.
"""

from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Optional

try:
    import yaml  # PyYAML is already a runtime dep
except ImportError:  # pragma: no cover - PyYAML always available in dev
    yaml = None  # type: ignore[assignment]


REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = REPO_ROOT / "docs" / "dataiku-reference"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n", re.DOTALL)
_FENCE_RE = re.compile(r"^```([a-zA-Z0-9_+-]*)\s*\n(.*?)^```\s*$", re.DOTALL | re.MULTILINE)


def _parse_frontmatter(text: str) -> dict[str, Any]:
    """Pull YAML frontmatter out of a markdown file and return as dict."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}
    if yaml is None:
        return {}
    try:
        loaded = yaml.safe_load(match.group(1))
        return loaded if isinstance(loaded, dict) else {}
    except Exception:
        return {}


def _candidate_blocks(text: str) -> list[tuple[str, str]]:
    """Return all (lang_hint, body) fenced blocks in the markdown."""
    return [(m.group(1).lower(), m.group(2)) for m in _FENCE_RE.finditer(text)]


def _try_parse_json_or_yaml(lang: str, body: str) -> Optional[Any]:
    """Try to load the fence body as JSON, then YAML.

    Returns the loaded Python object on success, ``None`` on failure or if
    the body doesn't look like a structured payload (e.g. a SQL snippet).
    """
    body = body.strip()
    if not body:
        return None

    # Skip language hints we know aren't structured config.
    if lang in {"sql", "python", "py", "bash", "sh", "shell", "text", "regex", "grok"}:
        return None

    # First pass: JSON. Always try JSON first — it's strict, no false positives.
    try:
        parsed = json.loads(body)
    except (json.JSONDecodeError, ValueError):
        parsed = None

    if parsed is not None:
        return parsed

    # Second pass: YAML, but only if the lang hint says so or the body
    # looks plausibly like a YAML mapping (top-level ``key: value``).
    if lang == "yaml" or (lang == "" and re.match(r"^[A-Za-z_][\w-]*\s*:", body)):
        if yaml is None:
            return None
        try:
            loaded = yaml.safe_load(body)
            if isinstance(loaded, (dict, list)):
                return loaded
        except Exception:
            return None

    return None


_RECIPE_KEYS = {"type", "recipe_type", "recipeType"}
_RECIPE_FLOW_KEYS = {"inputs", "outputs"}
_PROCESSOR_KEYS = {"type", "params"}


def _classify(payload: Any) -> Optional[str]:
    """Return ``'recipe'``, ``'processor'``, or ``None``.

    Heuristic:
    - Recipe shape: dict with a ``type`` or ``recipe_type`` key AND
      either ``inputs`` / ``outputs`` or a ``settings``/``steps`` key.
    - Processor shape: dict with ``type`` and ``params`` (both present),
      OR a single ``params`` block alongside a ``processor_type`` field.
    - Otherwise: skip (not a wire-shape doc — usually an output example).
    """
    if not isinstance(payload, dict):
        return None

    has_type = bool(_RECIPE_KEYS & payload.keys())

    if has_type and (
        _RECIPE_FLOW_KEYS & payload.keys()
        or "settings" in payload
        or "steps" in payload
        or "name" in payload
    ):
        return "recipe"

    if "type" in payload and "params" in payload:
        return "processor"

    if "processor_type" in payload and "params" in payload:
        return "processor"

    return None


def _slug_from_filename(path: Path) -> str:
    return path.stem


def _wrap_with_metadata(
    payload: Any,
    *,
    kind: str,
    source_md: str,
    source_url: Optional[str],
    category: Optional[str],
    block_index: int,
) -> dict[str, Any]:
    """Build the on-disk fixture envelope: metadata header + canonical body."""
    return {
        "_meta": {
            "kind": kind,
            "source_md": source_md,
            "source_url": source_url,
            "category": category,
            "block_index": block_index,
            "extracted_by": "tests/test_dss_roundtrip/extract_fixtures.py",
        },
        "payload": payload,
    }


def extract() -> dict[str, int]:
    """Walk the docs, write fixture JSON files, return per-category counts."""
    counts: dict[str, int] = defaultdict(int)

    if not DOCS_DIR.exists():
        print(f"warn: docs dir missing at {DOCS_DIR}; nothing to extract")
        return dict(counts)

    # Wipe the auto-generated fixture subdirs (NOT _seeds — those are hand-
    # authored). Keep .gitkeep markers if any.
    for cat in ("recipes", "processors"):
        cat_dir = FIXTURES_DIR / cat
        if cat_dir.exists():
            for old in cat_dir.glob("*.json"):
                if not old.name.startswith("_seed_"):
                    old.unlink()
        else:
            cat_dir.mkdir(parents=True, exist_ok=True)

    for category in ("recipes", "processors"):
        cat_docs = DOCS_DIR / category
        if not cat_docs.exists():
            continue

        out_dir = FIXTURES_DIR / category
        out_dir.mkdir(parents=True, exist_ok=True)

        for md_path in sorted(cat_docs.glob("*.md")):
            if md_path.name.startswith("_"):  # _index.md etc.
                continue

            text = md_path.read_text(encoding="utf-8")
            front = _parse_frontmatter(text)
            source_url = front.get("source_url")
            slug = _slug_from_filename(md_path)
            rel_md = str(md_path.relative_to(REPO_ROOT))

            for idx, (lang, body) in enumerate(_candidate_blocks(text)):
                payload = _try_parse_json_or_yaml(lang, body)
                if payload is None:
                    continue
                kind = _classify(payload)
                if kind is None:
                    continue

                fixture = _wrap_with_metadata(
                    payload,
                    kind=kind,
                    source_md=rel_md,
                    source_url=source_url,
                    category=category,
                    block_index=idx,
                )

                fixture_path = out_dir / f"{slug}__{idx}.json"
                fixture_path.write_text(
                    json.dumps(fixture, indent=2, sort_keys=False) + "\n",
                    encoding="utf-8",
                )
                counts[category] += 1

    return dict(counts)


def main() -> None:
    counts = extract()
    print("DSS round-trip fixture extraction")
    print("=================================")
    if not counts:
        print("(no JSON/YAML wire-shape blocks found in the doc snapshot)")
    for category, n in sorted(counts.items()):
        print(f"  {category}: {n} fixture(s)")
    seed_dir = FIXTURES_DIR / "_seeds"
    if seed_dir.exists():
        seeds = sum(1 for _ in seed_dir.rglob("*.json"))
        print(f"  _seeds  (hand-authored canonical shapes): {seeds} fixture(s)")
    print()
    print(f"Output dir: {FIXTURES_DIR}")


if __name__ == "__main__":
    main()
