"""
Recipe type icons for Dataiku flow visualization.

The icon paths follow Dataiku DSS visual conventions: each recipe type maps to
a colored circle node with an icon at its center. Paths use a 24x24 viewBox so
they composite cleanly into circles of any size.

Single source of truth (Sprint-7)
---------------------------------
SVG paths, glyphs, labels, ASCII tags, and Unicode icons are all loaded at
import time from ``docs/design/recipe-icons.json``. The same JSON file feeds
``packages/flow-viz/src/icons/recipeIcons.tsx`` so the React canvas and the
Python visualizers share a single icon catalog.

Phantom-name aliases (`fuzzy_join` <-> `fuzzyjoin`, `top_n` <-> `topn`, etc.)
are expanded by this module from a fixed alias table — the JSON stays
canonical-only.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


# Path resolved relative to the repository root.
_ICONS_PATH = (
    Path(__file__).resolve().parents[2] / "docs" / "design" / "recipe-icons.json"
)


# Phantom-name alias table — DSS canonical names map to the friendly aliases
# used elsewhere in the codebase. Each canonical key in recipe-icons.json is
# expanded to the listed aliases at load time.
_ICON_ALIASES: dict[str, tuple[str, ...]] = {
    "fuzzy_join": ("fuzzyjoin",),
    "geo_join": ("geojoin",),
    "top_n": ("topn",),
    "sampling": ("sample",),
    "sql": ("sql_script",),
    "sparksql": ("spark_sql_query",),
    "evaluation": ("standalone_evaluation",),
}


@lru_cache(maxsize=1)
def _load_icon_data() -> dict[str, dict[str, str]]:
    """Load and cache the canonical icon JSON.

    Returns a mapping ``{canonical_name: {path, glyph, label, unicode,
    ascii}}`` with the leading ``_note`` documentation key stripped.
    """
    with _ICONS_PATH.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)
    return {
        k: v
        for k, v in raw.items()
        if not k.startswith("_") and isinstance(v, dict)
    }


def _build_field(field_name: str) -> dict[str, str]:
    """Pull one field from every icon entry, expanding phantom aliases."""
    data = _load_icon_data()
    out: dict[str, str] = {}
    for canonical, entry in data.items():
        value = entry.get(field_name, entry.get("label", canonical))
        out[canonical] = value
        for alias in _ICON_ALIASES.get(canonical, ()):
            out[alias] = value
    return out


class RecipeIcons:
    """Icons for different Dataiku recipe types.

    Lookup keys are normalized: lowercased, with spaces converted to
    underscores. Both DSS-canonical names (``fuzzy_join``) and friendly aliases
    (``fuzzyjoin``) resolve to the same icon. Backed by
    ``docs/design/recipe-icons.json``.
    """

    # Build the lookup dicts at class-definition time. Keep these as plain
    # dicts for backward compatibility — downstream code reads them directly.
    SVG_PATHS: dict[str, str] = _build_field("path")
    GLYPHS: dict[str, str] = _build_field("glyph")
    LABELS: dict[str, str] = _build_field("label")
    UNICODE: dict[str, str] = _build_field("unicode")
    ASCII: dict[str, str] = _build_field("ascii")

    @staticmethod
    def _normalize(recipe_type: str) -> str:
        return (recipe_type or "default").lower().replace(" ", "_")

    @classmethod
    def get_unicode(cls, recipe_type: str) -> str:
        """Get Unicode icon for recipe type."""
        return cls.UNICODE.get(cls._normalize(recipe_type), cls.UNICODE["default"])

    @classmethod
    def get_glyph(cls, recipe_type: str) -> str:
        """Get a single-character glyph for a recipe type (terminal-safe)."""
        return cls.GLYPHS.get(cls._normalize(recipe_type), cls.GLYPHS["default"])

    @classmethod
    def get_label(cls, recipe_type: str) -> str:
        """Get text label for recipe type."""
        return cls.LABELS.get(cls._normalize(recipe_type), cls.LABELS["default"])

    @classmethod
    def get_ascii(cls, recipe_type: str) -> str:
        """Get bracketed ASCII representation for recipe type."""
        return cls.ASCII.get(cls._normalize(recipe_type), cls.ASCII["default"])

    @classmethod
    def get_svg_path(cls, recipe_type: str) -> str:
        """Get SVG path data (24x24 viewBox) for recipe type."""
        return cls.SVG_PATHS.get(cls._normalize(recipe_type), cls.SVG_PATHS["default"])

    @classmethod
    def coverage(cls) -> int:
        """Number of distinct recipe-type families with a dedicated SVG icon."""
        # De-dupe path strings — alias keys (fuzzy_join / fuzzyjoin) share the
        # same path, but represent the same family.
        return len({v for k, v in cls.SVG_PATHS.items() if k != "default"})
