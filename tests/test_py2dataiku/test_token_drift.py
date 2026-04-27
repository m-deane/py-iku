"""
Sprint-7 — token-drift prevention.

Asserts that ``docs/design/tokens.json``, ``docs/design/recipe-icons.json``,
``apps/web/src/styles/tokens.css``, and ``py2dataiku/visualizers/themes.py``
all agree on the canonical recipe-palette + connection-stripe + layout values.
A failure here means somebody edited one consumer without re-running the sync
pipeline (or edited the JSON without regenerating the CSS).

Run on every PR. To repair drift:

  1. Edit only ``docs/design/tokens.json`` and/or ``recipe-icons.json``.
  2. Re-run the CSS pipeline:  ``cd apps/web && pnpm build:tokens``
     (or ``npx tsx scripts/sync-tokens.ts``).
  3. Re-run this test.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from py2dataiku.visualizers.icons import RecipeIcons
from py2dataiku.visualizers.themes import (
    DATAIKU_DARK,
    DATAIKU_LIGHT,
    _CONNECTION_STRIPES,
    _RECIPE_PALETTE_LIGHT,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
TOKENS_JSON = REPO_ROOT / "docs" / "design" / "tokens.json"
ICONS_JSON = REPO_ROOT / "docs" / "design" / "recipe-icons.json"
TOKENS_CSS = REPO_ROOT / "apps" / "web" / "src" / "styles" / "tokens.css"


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture(scope="module")
def tokens() -> dict:
    return _load_json(TOKENS_JSON)


@pytest.fixture(scope="module")
def icons() -> dict:
    return _load_json(ICONS_JSON)


@pytest.fixture(scope="module")
def tokens_css() -> str:
    return TOKENS_CSS.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# JSON <-> Python: every flow.recipe.* entry resolves through themes.py
# ---------------------------------------------------------------------------

class TestRecipePaletteJsonPythonParity:
    """The Python `recipe_palette` is loaded from `flow.recipe.*` in the JSON."""

    def test_every_canonical_recipe_in_json_is_in_python_palette(self, tokens):
        flow_recipe = tokens["flow"]["recipe"]
        for canonical, triplet in flow_recipe.items():
            assert canonical in _RECIPE_PALETTE_LIGHT, (
                f"flow.recipe.{canonical} present in JSON but missing from "
                f"_RECIPE_PALETTE_LIGHT (themes.py loader)"
            )
            py_fill, py_stroke, py_icon = _RECIPE_PALETTE_LIGHT[canonical]
            assert py_fill.lower() == triplet["bg"].lower(), (
                f"recipe `{canonical}` bg drift: JSON={triplet['bg']} "
                f"PY={py_fill}"
            )
            assert py_stroke.lower() == triplet["border"].lower(), (
                f"recipe `{canonical}` border drift: JSON={triplet['border']} "
                f"PY={py_stroke}"
            )
            assert py_icon.lower() == triplet["fg"].lower(), (
                f"recipe `{canonical}` fg drift: JSON={triplet['fg']} PY={py_icon}"
            )

    def test_get_recipe_palette_resolves_join_via_json(self, tokens):
        json_join = tokens["flow"]["recipe"]["join"]
        py_fill, py_stroke, py_icon = DATAIKU_LIGHT.get_recipe_palette("join")
        assert py_fill.lower() == json_join["bg"].lower()
        assert py_stroke.lower() == json_join["border"].lower()
        assert py_icon.lower() == json_join["fg"].lower()


# ---------------------------------------------------------------------------
# JSON <-> Python: connection stripes
# ---------------------------------------------------------------------------

class TestConnectionStripeJsonPythonParity:
    """The Python `_CONNECTION_STRIPES` is built from `flow.dataset.stripe.*`."""

    @pytest.mark.parametrize(
        "family,canonical_names",
        [
            ("filesystem", ["Filesystem", "filesystem"]),
            ("sql", ["PostgreSQL", "MySQL", "BigQuery", "Snowflake", "SQL"]),
            ("cloud", ["S3", "GCS", "Azure", "HDFS", "ManagedFolder"]),
            ("nosql", ["MongoDB", "Cassandra", "Elasticsearch"]),
            ("http", ["HTTP", "API"]),
            ("inline", ["Inline", "inline"]),
        ],
    )
    def test_family_color_matches_json(self, tokens, family, canonical_names):
        json_hex = tokens["flow"]["dataset"]["stripe"][family]
        for name in canonical_names:
            assert name in _CONNECTION_STRIPES, f"{name} missing from stripes"
            assert _CONNECTION_STRIPES[name].lower() == json_hex.lower(), (
                f"connection `{name}` (family={family}) drift: "
                f"JSON={json_hex} PY={_CONNECTION_STRIPES[name]}"
            )

    def test_default_stripe_matches_json(self, tokens):
        json_default = tokens["flow"]["dataset"]["stripe"]["default"]
        assert _CONNECTION_STRIPES["default"].lower() == json_default.lower()


# ---------------------------------------------------------------------------
# JSON <-> Python: layout, edge, node sizes
# ---------------------------------------------------------------------------

class TestLayoutEdgeNodeJsonPythonParity:
    """The Python theme's layout/edge/node values are sourced from JSON."""

    def test_layout_spacing_from_json(self, tokens):
        layout = tokens["flow"]["layout"]
        assert DATAIKU_LIGHT.layer_spacing == layout["layer_spacing"]
        assert DATAIKU_LIGHT.node_spacing == layout["node_spacing"]
        assert DATAIKU_LIGHT.padding == layout["padding"]

    def test_edge_stroke_from_json(self, tokens):
        edge = tokens["flow"]["edge"]
        assert DATAIKU_LIGHT.connection_color.lower() == edge["stroke"].lower()
        assert (
            DATAIKU_LIGHT.connection_hover.lower() == edge["stroke_hover"].lower()
        )
        assert DATAIKU_LIGHT.connection_width == float(edge["stroke_width"])

    def test_node_sizes_from_json(self, tokens):
        node = tokens["flow"]["node"]
        assert DATAIKU_LIGHT.dataset_width == node["dataset_width"]
        assert DATAIKU_LIGHT.dataset_height == node["dataset_height"]
        assert DATAIKU_LIGHT.recipe_size == node["recipe_diameter"]


# ---------------------------------------------------------------------------
# JSON <-> CSS: every flow.recipe.bg ends up as a CSS variable
# ---------------------------------------------------------------------------

_HEX_RE = re.compile(r"#[0-9a-fA-F]{6}")


def _extract_css_var(text: str, name: str) -> str | None:
    """Return the value of a CSS custom property (first match in the file)."""
    m = re.search(rf"{re.escape(name)}\s*:\s*([^;]+);", text)
    return m.group(1).strip() if m else None


class TestJsonCssParity:
    """Recipe + stripe values in tokens.css must match the JSON."""

    def test_recipe_bg_round_trip(self, tokens, tokens_css):
        for canonical, triplet in tokens["flow"]["recipe"].items():
            slug = canonical.replace("_", "-")
            css_value = _extract_css_var(tokens_css, f"--recipe-{slug}")
            # `--recipe-<type>` is set in `:root` (light) and overridden in
            # `[data-theme="dark"]`; only the first (light) match is checked.
            if css_value is None:
                continue  # not all 37 types have a --recipe-<slug> alias
            assert css_value.lower() == triplet["bg"].lower(), (
                f"recipe `{canonical}` CSS drift: JSON.bg={triplet['bg']} "
                f"CSS=--recipe-{slug}={css_value}"
            )

    def test_dataset_stripe_round_trip(self, tokens, tokens_css):
        for family, hex_value in tokens["flow"]["dataset"]["stripe"].items():
            slug = family.replace("_", "-")
            css_value = _extract_css_var(tokens_css, f"--dataset-stripe-{slug}")
            assert css_value is not None, (
                f"--dataset-stripe-{slug} not emitted to tokens.css"
            )
            assert css_value.lower() == hex_value.lower(), (
                f"dataset stripe `{family}` CSS drift: JSON={hex_value} "
                f"CSS={css_value}"
            )

    def test_edge_stroke_round_trip(self, tokens, tokens_css):
        json_stroke = tokens["flow"]["edge"]["stroke"]
        css_stroke = _extract_css_var(tokens_css, "--edge-stroke")
        assert css_stroke is not None
        assert css_stroke.lower() == json_stroke.lower()

    def test_layout_round_trip(self, tokens, tokens_css):
        json_layout = tokens["flow"]["layout"]
        for key in ("layer_spacing", "node_spacing", "padding"):
            slug = key.replace("_", "-")
            css_value = _extract_css_var(tokens_css, f"--flow-layout-{slug}")
            assert css_value is not None, f"--flow-layout-{slug} not emitted"
            assert int(css_value) == int(json_layout[key]), (
                f"layout `{key}` drift: JSON={json_layout[key]} CSS={css_value}"
            )


# ---------------------------------------------------------------------------
# JSON <-> Python: recipe-icons.json catalog
# ---------------------------------------------------------------------------

class TestIconCatalogJsonPythonParity:
    """RecipeIcons.SVG_PATHS / GLYPHS / LABELS are sourced from
    docs/design/recipe-icons.json."""

    def test_every_canonical_icon_resolves_in_python(self, icons):
        for canonical, entry in icons.items():
            if canonical.startswith("_") or not isinstance(entry, dict):
                continue
            # SVG path
            assert RecipeIcons.SVG_PATHS[canonical] == entry["path"], (
                f"icon `{canonical}` path drift"
            )
            # Glyph
            assert RecipeIcons.GLYPHS[canonical] == entry["glyph"], (
                f"icon `{canonical}` glyph drift"
            )
            # Label
            assert RecipeIcons.LABELS[canonical] == entry["label"], (
                f"icon `{canonical}` label drift"
            )

    def test_phantom_aliases_share_canonical_paths(self):
        # fuzzy_join <-> fuzzyjoin must resolve to the same SVG path.
        assert (
            RecipeIcons.SVG_PATHS["fuzzy_join"]
            == RecipeIcons.SVG_PATHS["fuzzyjoin"]
        )
        assert RecipeIcons.SVG_PATHS["top_n"] == RecipeIcons.SVG_PATHS["topn"]
        assert (
            RecipeIcons.SVG_PATHS["sampling"] == RecipeIcons.SVG_PATHS["sample"]
        )


# ---------------------------------------------------------------------------
# Smoke check: dark theme also resolves cleanly
# ---------------------------------------------------------------------------

class TestDarkPaletteSmoke:
    """Per Sprint-6, dark recipe palette = light palette (same hex)."""

    def test_dark_palette_resolves(self):
        for rt in ("prepare", "join", "grouping", "sort"):
            fill, stroke, icon = DATAIKU_DARK.get_recipe_palette(rt)
            assert fill.startswith("#")
            assert stroke.startswith("#")
            assert icon.startswith("#")
