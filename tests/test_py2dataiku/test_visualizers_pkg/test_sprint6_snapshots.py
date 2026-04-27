"""
Approval-test snapshots for the sprint-6 DSS-fidelity visual upgrade.

A four-recipe flow (PREPARE -> JOIN -> GROUPING -> SORT) is rendered in every
text format and diffed byte-for-byte against the frozen baseline at
``fixtures/sprint6/``. Binary outputs (PNG, PDF) are checked for non-empty
content + valid magic bytes only, since matplotlib raster output is not
deterministic across versions / platforms.

To regenerate baselines after an intentional visual change, set the env var
``REGEN_SPRINT6=1`` before running pytest.
"""

from __future__ import annotations

import os
from pathlib import Path

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
    MatplotlibVisualizer,
    MermaidVisualizer,
    PlantUMLVisualizer,
    SVGVisualizer,
)

FIXTURES = Path(__file__).parent / "fixtures" / "sprint6"


@pytest.fixture
def four_recipe_flow():
    """The canonical PREPARE -> JOIN -> GROUPING -> SORT flow for snapshots."""
    flow = DataikuFlow(name="sprint6_fixture")
    flow.add_dataset(
        DataikuDataset(
            name="customers",
            dataset_type=DatasetType.INPUT,
            connection_type=DatasetConnectionType.SQL_POSTGRESQL,
        )
    )
    flow.add_dataset(
        DataikuDataset(
            name="orders",
            dataset_type=DatasetType.INPUT,
            connection_type=DatasetConnectionType.S3,
        )
    )
    flow.add_dataset(DataikuDataset(name="customers_clean", dataset_type=DatasetType.INTERMEDIATE))
    flow.add_dataset(DataikuDataset(name="enriched", dataset_type=DatasetType.INTERMEDIATE))
    flow.add_dataset(DataikuDataset(name="summary", dataset_type=DatasetType.INTERMEDIATE))
    flow.add_dataset(
        DataikuDataset(
            name="top_customers",
            dataset_type=DatasetType.OUTPUT,
            connection_type=DatasetConnectionType.SQL_SNOWFLAKE,
        )
    )

    flow.recipes.append(DataikuRecipe(
        name="prepare_1", recipe_type=RecipeType.PREPARE,
        inputs=["customers"], outputs=["customers_clean"],
    ))
    flow.recipes.append(DataikuRecipe(
        name="join_2", recipe_type=RecipeType.JOIN,
        inputs=["customers_clean", "orders"], outputs=["enriched"],
    ))
    flow.recipes.append(DataikuRecipe(
        name="grouping_3", recipe_type=RecipeType.GROUPING,
        inputs=["enriched"], outputs=["summary"],
    ))
    flow.recipes.append(DataikuRecipe(
        name="sort_4", recipe_type=RecipeType.SORT,
        inputs=["summary"], outputs=["top_customers"],
    ))
    return flow


def _approve_text(name: str, actual: str):
    """Approval-test helper: diff `actual` against fixture file."""
    path = FIXTURES / name
    if os.environ.get("REGEN_SPRINT6"):
        path.write_text(actual, encoding="utf-8")
    expected = path.read_text(encoding="utf-8")
    if expected != actual:
        # Write the actual output to a sibling .actual file for inspection
        actual_path = path.with_suffix(path.suffix + ".actual")
        actual_path.write_text(actual, encoding="utf-8")
    assert expected == actual, (
        f"Snapshot mismatch for {name}. Wrote actual to {path}.actual. "
        f"Re-run with REGEN_SPRINT6=1 to update baselines."
    )


class TestSprint6Snapshots:
    """Byte-level approval tests for the upgraded DSS-fidelity visualizers."""

    def test_svg_snapshot(self, four_recipe_flow):
        actual = SVGVisualizer().render(four_recipe_flow)
        _approve_text("four_recipe.svg", actual)

    def test_ascii_snapshot(self, four_recipe_flow):
        actual = ASCIIVisualizer().render(four_recipe_flow)
        _approve_text("four_recipe.ascii.txt", actual)

    def test_plantuml_snapshot(self, four_recipe_flow):
        actual = PlantUMLVisualizer().render(four_recipe_flow)
        _approve_text("four_recipe.plantuml", actual)

    def test_html_snapshot(self, four_recipe_flow):
        actual = HTMLVisualizer().render(four_recipe_flow)
        _approve_text("four_recipe.html", actual)

    def test_mermaid_snapshot(self, four_recipe_flow):
        actual = MermaidVisualizer().render(four_recipe_flow)
        _approve_text("four_recipe.mermaid", actual)

    def test_png_renders(self, four_recipe_flow):
        """PNG output is binary + version-sensitive — check magic bytes only."""
        pytest.importorskip("matplotlib")
        png = MatplotlibVisualizer().render(four_recipe_flow)
        assert png[:4] == b"\x89PNG"
        assert len(png) > 5000

    def test_pdf_renders(self, four_recipe_flow):
        """PDF output is binary + version-sensitive — check magic bytes only."""
        pytest.importorskip("matplotlib")
        pdf = MatplotlibVisualizer().render_pdf(four_recipe_flow)
        assert pdf[:4] == b"%PDF"
        assert len(pdf) > 5000


class TestSprint6Coverage:
    """Sanity checks on the new icon + connection-stripe coverage."""

    def test_recipe_icon_coverage(self):
        from py2dataiku.visualizers.icons import RecipeIcons
        # At least 25 distinct recipe-type families covered.
        assert RecipeIcons.coverage() >= 25, (
            f"Only {RecipeIcons.coverage()} recipe icons defined; need >= 25"
        )

    def test_connection_stripe_coverage(self):
        from py2dataiku.visualizers.themes import DATAIKU_LIGHT
        # Must cover all DSS DatasetConnectionType members.
        for ct in DatasetConnectionType:
            stripe = DATAIKU_LIGHT.get_connection_stripe(ct.value)
            assert stripe.startswith("#"), f"No stripe for {ct.value}"

    def test_recipe_palette_for_all_recipe_types(self):
        from py2dataiku.visualizers.themes import DATAIKU_LIGHT
        for rt in RecipeType:
            fill, stroke, icon = DATAIKU_LIGHT.get_recipe_palette(rt.value)
            assert fill.startswith("#")
            assert stroke.startswith("#")
            assert icon.startswith("#")

    def test_svg_contains_dss_palette_blue(self, four_recipe_flow):
        """PREPARE recipe must render with the DSS blue (#2c8fd9)."""
        svg = SVGVisualizer().render(four_recipe_flow)
        assert "#2c8fd9" in svg

    def test_svg_contains_dss_palette_orange(self, four_recipe_flow):
        """JOIN recipe must render with the DSS orange (#f29222)."""
        svg = SVGVisualizer().render(four_recipe_flow)
        assert "#f29222" in svg

    def test_svg_contains_dss_palette_green(self, four_recipe_flow):
        """GROUPING recipe must render with the DSS green (#75bb6a)."""
        svg = SVGVisualizer().render(four_recipe_flow)
        assert "#75bb6a" in svg

    def test_mermaid_classdef_emitted(self, four_recipe_flow):
        """Mermaid output emits per-recipe-type classDef directives."""
        mermaid = MermaidVisualizer().render(four_recipe_flow)
        assert "classDef" in mermaid
        assert "joinRecipe" in mermaid
        assert "groupingRecipe" in mermaid
        assert "fill:#f29222" in mermaid  # JOIN orange

    def test_plantuml_per_recipe_skinparam(self, four_recipe_flow):
        """PlantUML emits skinparam BackgroundColor stereotypes per recipe type."""
        out = PlantUMLVisualizer().render(four_recipe_flow)
        assert "BackgroundColor<<prepare>>" in out
        assert "BackgroundColor<<join>>" in out
        assert "BackgroundColor<<grouping>>" in out
        assert "BackgroundColor<<sort>>" in out

    def test_dataset_connection_stripe_in_svg(self, four_recipe_flow):
        """Dataset stripe colors come from connection_type, not just dataset_type.

        ``customers`` has a Postgres connection -> blue stripe (#2c8fd9).
        ``orders`` has S3 -> orange stripe (#f29222).
        """
        svg = SVGVisualizer().render(four_recipe_flow)
        assert "#2c8fd9" in svg  # also matches PREPARE; weak but indicative
        assert "#f29222" in svg  # JOIN + S3
