"""Shared fixtures and helpers for the DSS round-trip harness.

The seam exposed by this module:

- ``FIXTURES_DIR``: the on-disk root of all fixtures (auto-extracted +
  hand-authored seeds).
- ``discover_fixtures(kind)``: walks ``FIXTURES_DIR`` and returns a list of
  ``FixtureCase`` records suitable for ``pytest.mark.parametrize`` ids.
- ``load_fixture(path)``: reads a fixture JSON and returns its envelope.
- ``slug_from_path(path)``: builds a stable, human-readable test id.
- ``EXPECTED_XFAILS``: a dict mapping fixture slug -> ``(reason, finding_ref)``
  for fixtures we KNOW will fail today against the current py-iku
  serializer / catalog. Adding a new entry here is how a fix-wave
  commit advertises that a previously-known failure has been addressed
  (the test will then xpass, prompting removal).

To extend the harness with a new fixture: drop a JSON file under
``fixtures/recipes/`` or ``fixtures/processors/`` (auto-extracted) or
``fixtures/_seeds/<category>/`` (hand-authored). It will be picked up
automatically by both ``test_recipe_roundtrip.py`` and
``test_processor_roundtrip.py`` based on its ``_meta.kind``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import pytest


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@dataclass(frozen=True)
class FixtureCase:
    """A single parametrized test case."""

    slug: str  # human-readable id, e.g. "_seeds/recipes/prepare__basic"
    path: Path
    kind: str  # "recipe" | "processor"
    payload: dict[str, Any]
    meta: dict[str, Any]

    @property
    def expected_xfail_marker(self) -> Optional[str]:
        """Return the xfail reason from the fixture meta, or ``None``."""
        reason = self.meta.get("expected_xfail")
        if isinstance(reason, str) and reason.strip():
            return reason
        return None


# ---------------------------------------------------------------------------
# Loader helpers (also imported by the test modules)
# ---------------------------------------------------------------------------


def slug_from_path(path: Path) -> str:
    """Build a stable, human-readable test id from a fixture path."""
    rel = path.relative_to(FIXTURES_DIR)
    return str(rel.with_suffix(""))


def load_fixture(path: Path) -> dict[str, Any]:
    """Read a fixture JSON and return its envelope dict.

    Each fixture envelope has shape ``{"_meta": {...}, "payload": {...}}``.
    """
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _iter_fixture_paths() -> list[Path]:
    """Walk FIXTURES_DIR and return all fixture JSON paths.

    Skips ``README.md`` and any ``.gitkeep`` markers. Walks both auto-
    extracted (``fixtures/recipes/*.json``, ``fixtures/processors/*.json``)
    and hand-authored seeds (``fixtures/_seeds/**/*.json``).
    """
    if not FIXTURES_DIR.exists():
        return []
    return sorted(p for p in FIXTURES_DIR.rglob("*.json"))


def discover_fixtures(kind: str) -> list[FixtureCase]:
    """Return all fixture cases whose ``_meta.kind`` matches ``kind``.

    Args:
        kind: ``"recipe"`` or ``"processor"``.

    Returns:
        List of :class:`FixtureCase`. The list is sorted by slug so test
        ordering is stable across runs.
    """
    cases: list[FixtureCase] = []
    for path in _iter_fixture_paths():
        try:
            envelope = load_fixture(path)
        except (json.JSONDecodeError, ValueError):
            # A malformed fixture file is itself a regression — but the
            # test layer can't surface it cleanly without producing a
            # parametrize-time exception. Skip and log to stderr.
            continue
        meta = envelope.get("_meta", {})
        if meta.get("kind") != kind:
            continue
        payload = envelope.get("payload")
        if not isinstance(payload, dict):
            continue
        cases.append(
            FixtureCase(
                slug=slug_from_path(path),
                path=path,
                kind=kind,
                payload=payload,
                meta=meta,
            )
        )
    return sorted(cases, key=lambda c: c.slug)


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """Absolute path to the fixtures root."""
    return FIXTURES_DIR


@pytest.fixture
def load_fixture_helper():
    """Function fixture that returns ``load_fixture`` for ad-hoc tests."""
    return load_fixture
