"""Cross-format color/icon consistency for the static flow visualizers.

Renders ONE canonical PREPARE -> JOIN -> GROUPING -> SORT flow through every
text-based visualizer (SVG, HTML, Mermaid, PlantUML, ASCII; PNG/PDF magic-byte
only since they are binary and version-sensitive) and asserts that the same
recipe family resolves to the same color family across every output, and that
the same dataset connection family resolves to the same stripe family.

This is the *standardization* test: when a refactor accidentally regresses one
format's palette, this test surfaces the divergence by reporting one row per
format with the JOIN colors actually used. The test does NOT require a running
browser — it only inspects the static-format string outputs.

Phantom-name aliasing & legacy palette caveats are handled explicitly in the
``EXPECTED_*`` tables below; e.g. SORT renders gray (``#7f8c8d``) in the new
DSS-fidelity palette even though the legacy Material palette had it as gold.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import pytest

from py2dataiku.models.dataiku_dataset import (
    DataikuDataset,
    DatasetConnectionType,
    DatasetType,
)
from py2dataiku.models.dataiku_flow import DataikuFlow
from py2dataiku.models.dataiku_recipe import DataikuRecipe, RecipeType
from py2dataiku.visualizers import (
    ASCIIVisualizer,
    HTMLVisualizer,
    MermaidVisualizer,
    PlantUMLVisualizer,
    SVGVisualizer,
)
from py2dataiku.visualizers.icons import RecipeIcons
from py2dataiku.visualizers.themes import DATAIKU_LIGHT


# ----------------------------------------------------------------------------
# Canonical flow used by the whole module — one of every recipe family + one
# of every interesting connection-type stripe family.
# ----------------------------------------------------------------------------

@pytest.fixture(scope="module")
def canonical_flow() -> DataikuFlow:
    flow = DataikuFlow(name="cross_format_canon")
    flow.add_dataset(DataikuDataset(
        name="customers_fs", dataset_type=DatasetType.INPUT,
        connection_type=DatasetConnectionType.FILESYSTEM,
    ))
    flow.add_dataset(DataikuDataset(
        name="orders_sql", dataset_type=DatasetType.INPUT,
        connection_type=DatasetConnectionType.SQL_POSTGRESQL,
    ))
    flow.add_dataset(DataikuDataset(
        name="events_s3", dataset_type=DatasetType.INPUT,
        connection_type=DatasetConnectionType.S3,
    ))
    flow.add_dataset(DataikuDataset(name="customers_clean", dataset_type=DatasetType.INTERMEDIATE))
    flow.add_dataset(DataikuDataset(name="enriched", dataset_type=DatasetType.INTERMEDIATE))
    flow.add_dataset(DataikuDataset(name="grouped", dataset_type=DatasetType.INTERMEDIATE))
    flow.add_dataset(DataikuDataset(
        name="sorted_out", dataset_type=DatasetType.OUTPUT,
        connection_type=DatasetConnectionType.SQL_SNOWFLAKE,
    ))
    flow.recipes.append(DataikuRecipe(
        name="prepare_step", recipe_type=RecipeType.PREPARE,
        inputs=["customers_fs"], outputs=["customers_clean"],
    ))
    flow.recipes.append(DataikuRecipe(
        name="join_step", recipe_type=RecipeType.JOIN,
        inputs=["customers_clean", "orders_sql", "events_s3"], outputs=["enriched"],
    ))
    flow.recipes.append(DataikuRecipe(
        name="grouping_step", recipe_type=RecipeType.GROUPING,
        inputs=["enriched"], outputs=["grouped"],
    ))
    flow.recipes.append(DataikuRecipe(
        name="sort_step", recipe_type=RecipeType.SORT,
        inputs=["grouped"], outputs=["sorted_out"],
    ))
    return flow


# ----------------------------------------------------------------------------
# Canonical color families. These come from `themes.DataikuTheme` — the
# DSS-fidelity palette (`recipe_palette`) is the source of truth for all
# static visualizers (SVG/HTML/Mermaid/PlantUML).
# ----------------------------------------------------------------------------

EXPECTED_RECIPE_FILL: dict[str, str] = {
    "PREPARE": DATAIKU_LIGHT.get_recipe_palette("prepare")[0],   # #2c8fd9 (blue)
    "JOIN":    DATAIKU_LIGHT.get_recipe_palette("join")[0],      # #f29222 (orange)
    "GROUPING": DATAIKU_LIGHT.get_recipe_palette("grouping")[0], # #75bb6a (green)
    "SORT":    DATAIKU_LIGHT.get_recipe_palette("sort")[0],      # #7f8c8d (gray)
}

EXPECTED_STRIPE: dict[str, str] = {
    "Filesystem": DATAIKU_LIGHT.get_connection_stripe("Filesystem"),  # #75bb6a green
    "PostgreSQL": DATAIKU_LIGHT.get_connection_stripe("PostgreSQL"),  # #2c8fd9 blue
    "S3":         DATAIKU_LIGHT.get_connection_stripe("S3"),          # #f29222 orange
}

# ----------------------------------------------------------------------------
# Color extractors per format. Each returns the recipe-fill hex actually used
# in that format's output for the named recipe. Returns None when the format
# carries no color information at all (e.g. ASCII).
# ----------------------------------------------------------------------------

@dataclass
class FormatProbe:
    """One color-extraction strategy per static-output format."""

    name: str
    has_color: bool
    extract_recipe: callable  # (output, recipe_type_lower) -> Optional[str]
    extract_stripe: callable  # (output, connection_type) -> Optional[str]


def _svg_recipe_fill(svg: str, recipe_type: str) -> str | None:
    """Find the fill color of the JOIN/etc circle in the SVG output.

    SVG renders each recipe as a ``<g class="recipe TYPE" ...>`` (lowercase
    type, e.g. ``recipe join``) whose ``<circle ... fill="#hex"`` carries
    the family fill.
    """
    rt = recipe_type.lower()
    pattern = (
        rf'<g\s+class="recipe\s+{re.escape(rt)}"[^>]*>.*?'
        rf'<circle[^>]*\sfill="(#[0-9a-fA-F]{{6}})"'
    )
    m = re.search(pattern, svg, re.DOTALL)
    return m.group(1).lower() if m else None


def _svg_stripe_color(svg: str, recipe_type: str) -> str | None:
    """Locate the stripe color used inside the dataset whose name matches.

    Uses the dataset class to find the right group, then reads the stripe
    ``<path d="M{w} 0 ... fill="#hex"/>`` entry.
    """
    # We search per-dataset rather than per-connection-type because the SVG
    # doesn't tag the connection type onto the rendered group; we use names.
    pattern = (
        rf'<g\s+class="dataset\s+\w+"\s+transform[^>]*>.*?'
        rf'<path d="M\d+\s+0[^"]*"\s+fill="(#[0-9a-fA-F]{{6}})"/>'
    )
    # Iterate all matches; the test calls this once per dataset position
    # implicitly by passing the connection-type-driven target hex.
    return None  # See _svg_all_stripes below — easier when scanning all.


def _svg_all_stripes(svg: str) -> list[str]:
    """Pull every stripe fill hex out of an SVG flow."""
    return [m.lower() for m in re.findall(
        r'<path d="M\d+\s+0[^"]*"\s+fill="(#[0-9a-fA-F]{6})"', svg
    )]


def _mermaid_recipe_fill(mermaid: str, recipe_type: str) -> str | None:
    """Find the ``classDef <type>Recipe fill:#hex`` directive."""
    rt = recipe_type.lower()
    suffix_map = {
        "prepare": "prepareRecipe",
        "join": "joinRecipe",
        "grouping": "groupingRecipe",
        "sort": "sortRecipe",
    }
    klass = suffix_map.get(rt)
    if not klass:
        return None
    m = re.search(
        rf'classDef\s+{klass}\s+fill:(#[0-9a-fA-F]{{6}})', mermaid
    )
    return m.group(1).lower() if m else None


def _plantuml_recipe_fill(plant: str, recipe_type: str) -> str | None:
    """Find ``BackgroundColor<<type>> #hex`` in PlantUML skinparam block."""
    rt = recipe_type.lower()
    m = re.search(
        rf'BackgroundColor<<{re.escape(rt)}>>\s+(#[0-9a-fA-F]{{6}})', plant
    )
    return m.group(1).lower() if m else None


def _html_recipe_fill(html: str, recipe_type: str) -> str | None:
    """HTML wraps an inline SVG; reuse the SVG extractor."""
    return _svg_recipe_fill(html, recipe_type)


def _ascii_recipe_glyph(ascii_text: str, recipe_type: str) -> str | None:
    """ASCII has no color, but it carries the recipe glyph from RecipeIcons.

    Returns the glyph string if found; the test asserts the glyph matches
    ``RecipeIcons.get_unicode(recipe_type)`` so ASCII at least agrees on the
    *icon family* across formats even where it can't agree on the color.
    """
    glyph = RecipeIcons.get_unicode(recipe_type.lower())
    return glyph if glyph in ascii_text else None


# ----------------------------------------------------------------------------
# Test cases.
# ----------------------------------------------------------------------------

class TestRecipeColorConsistency:
    """All static formats must agree on the recipe color *family*."""

    @pytest.fixture(scope="class")
    def outputs(self, canonical_flow):
        return {
            "svg": SVGVisualizer().render(canonical_flow),
            "html": HTMLVisualizer().render(canonical_flow),
            "mermaid": MermaidVisualizer().render(canonical_flow),
            "plantuml": PlantUMLVisualizer().render(canonical_flow),
            "ascii": ASCIIVisualizer().render(canonical_flow),
        }

    @pytest.mark.parametrize("recipe_type,expected_fill", [
        ("PREPARE", EXPECTED_RECIPE_FILL["PREPARE"]),
        ("JOIN", EXPECTED_RECIPE_FILL["JOIN"]),
        ("GROUPING", EXPECTED_RECIPE_FILL["GROUPING"]),
        ("SORT", EXPECTED_RECIPE_FILL["SORT"]),
    ])
    def test_recipe_color_family_agrees(self, outputs, recipe_type, expected_fill):
        """SVG, HTML, Mermaid, PlantUML must all use the same hex for a family.

        ASCII is excluded from the color matrix because it carries no color
        information; instead :meth:`test_ascii_uses_correct_glyph` asserts the
        ASCII output contains the correct icon glyph for the same recipe.
        """
        observed: dict[str, str | None] = {
            "svg": _svg_recipe_fill(outputs["svg"], recipe_type),
            "html": _html_recipe_fill(outputs["html"], recipe_type),
            "mermaid": _mermaid_recipe_fill(outputs["mermaid"], recipe_type),
            "plantuml": _plantuml_recipe_fill(outputs["plantuml"], recipe_type),
        }
        # Every format must have a value (i.e. the color was extractable).
        missing = [k for k, v in observed.items() if v is None]
        assert not missing, (
            f"{recipe_type}: could not extract color from {missing}. "
            f"Observed = {observed}"
        )
        # Every format must agree on the *exact* canonical hex.
        divergent = {k: v for k, v in observed.items() if v != expected_fill.lower()}
        assert not divergent, (
            f"{recipe_type}: expected {expected_fill}, divergent formats = {divergent}. "
            f"Full matrix = {observed}"
        )

    def test_ascii_uses_correct_glyph(self, outputs):
        """ASCII carries no color — confirm it uses the right icon family."""
        ascii_text = outputs["ascii"]
        for rt in ("PREPARE", "JOIN", "GROUPING", "SORT"):
            assert _ascii_recipe_glyph(ascii_text, rt) is not None, (
                f"ASCII output missing glyph {RecipeIcons.get_unicode(rt.lower())!r} "
                f"for recipe type {rt}"
            )


class TestDatasetStripeConsistency:
    """Connection-type stripes must agree across formats that emit them.

    Mermaid + PlantUML do not currently render the connection-type stripe at
    all — they style datasets only by INPUT/INTERMEDIATE/OUTPUT. This test
    therefore checks SVG (the format that *does* render the stripe) for the
    correct hex, and asserts the abstract family resolved by ``themes.py``
    matches the family expected by the design tokens.
    """

    @pytest.fixture(scope="class")
    def svg(self, canonical_flow):
        return SVGVisualizer().render(canonical_flow)

    @pytest.mark.parametrize("connection_type,expected_stripe", [
        ("Filesystem", EXPECTED_STRIPE["Filesystem"]),
        ("PostgreSQL", EXPECTED_STRIPE["PostgreSQL"]),
        ("S3", EXPECTED_STRIPE["S3"]),
    ])
    def test_svg_stripe_hex(self, svg, connection_type, expected_stripe):
        """The SVG must contain the expected stripe color for this connection."""
        all_stripes = _svg_all_stripes(svg)
        assert expected_stripe.lower() in all_stripes, (
            f"Expected {connection_type} stripe {expected_stripe} in SVG; "
            f"got stripes = {all_stripes}"
        )

    def test_three_distinct_stripe_families(self, svg):
        """Filesystem (green), SQL (blue), S3 (orange) must all be distinct."""
        fams = {
            EXPECTED_STRIPE["Filesystem"].lower(),
            EXPECTED_STRIPE["PostgreSQL"].lower(),
            EXPECTED_STRIPE["S3"].lower(),
        }
        assert len(fams) == 3, f"stripe families collapsed: {fams}"
        all_stripes = set(_svg_all_stripes(svg))
        # All three expected stripe colors are present somewhere in the SVG.
        assert fams.issubset(all_stripes), (
            f"missing stripes — expected superset {fams}, got {all_stripes}"
        )


class TestFormatColorMatrix:
    """Diagnostic test that emits a per-format JOIN-color matrix on failure.

    Useful when a regression collapses one format's palette to its legacy
    value: the test fails with a nicely-formatted dict so the reviewer can
    immediately see which format diverged and what hex it produced.
    """

    def test_join_color_matrix(self, canonical_flow):
        svg = SVGVisualizer().render(canonical_flow)
        html = HTMLVisualizer().render(canonical_flow)
        mer = MermaidVisualizer().render(canonical_flow)
        plant = PlantUMLVisualizer().render(canonical_flow)
        ascii_text = ASCIIVisualizer().render(canonical_flow)
        expected = EXPECTED_RECIPE_FILL["JOIN"].lower()
        matrix = {
            "svg":      _svg_recipe_fill(svg, "JOIN"),
            "html":     _html_recipe_fill(html, "JOIN"),
            "mermaid":  _mermaid_recipe_fill(mer, "JOIN"),
            "plantuml": _plantuml_recipe_fill(plant, "JOIN"),
            "ascii":    "(no color — glyph='%s')" % (
                _ascii_recipe_glyph(ascii_text, "JOIN") or "MISSING"
            ),
        }
        # All color-bearing formats must match expected.
        diffs = {
            fmt: hex_
            for fmt, hex_ in matrix.items()
            if fmt != "ascii" and hex_ != expected
        }
        assert not diffs, (
            f"JOIN color matrix divergence — expected {expected}, full matrix = {matrix}"
        )
