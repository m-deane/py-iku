"""Drift-prevention test for the recipe-color palette across surfaces.

The same recipe family (PREPARE, JOIN, GROUPING, …) appears in *four*
different sources today:

    1. Python theme dict     — ``py2dataiku.visualizers.themes.DataikuTheme``
    2. CSS custom properties — ``apps/web/src/styles/tokens.css``
    3. Mermaid classDef      — emitted by ``MermaidVisualizer`` at render time
    4. PlantUML skinparam    — emitted by ``PlantUMLVisualizer`` at render time

The Mermaid + PlantUML emitters already pull from the Python theme
(``get_recipe_palette``), so they are guaranteed-consistent with source #1.
The SHIM today therefore checks #1 == #3 == #4 (already strict) and reports
the relationship between #1 and #2 as DIVERGENT-BY-DESIGN — Std-A's parallel
work is consolidating the two palettes and the test will tighten when the
single ``docs/design/tokens.json`` source-of-truth is finalised.

This file is intentionally kept SHIM-shaped: when consolidation lands, only
the ``EXPECTED_HARD_FAIL_ON_DRIFT`` flag flips to ``True`` and the four-way
agreement becomes a hard assertion.

`tokens.json` is read first; if missing, the test falls back to themes.py +
tokens.css scan as documented in the task brief.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from py2dataiku.visualizers.themes import DATAIKU_LIGHT


REPO_ROOT = Path(__file__).resolve().parents[3]
TOKENS_JSON = REPO_ROOT / "docs" / "design" / "tokens.json"
TOKENS_CSS = REPO_ROOT / "apps" / "web" / "src" / "styles" / "tokens.css"

# When Std-A finishes, set this to True; the SHIM tests will then start to
# enforce four-way agreement (Python ↔ JSON ↔ CSS ↔ Mermaid/PlantUML).
EXPECTED_HARD_FAIL_ON_DRIFT = False

# Recipe types we baseline. Keep this minimal — the same set the cross-format
# consistency test exercises. Phantom aliases (FUZZY_JOIN→JOIN, etc.) are not
# included because they collapse to canonical members under the enum.
BASELINE_TYPES = ["PREPARE", "JOIN", "GROUPING", "SORT", "WINDOW", "SPLIT"]


@pytest.fixture(scope="module")
def tokens_json() -> dict | None:
    """Parsed tokens.json — None if Std-A hasn't shipped yet."""
    if not TOKENS_JSON.exists():
        return None
    return json.loads(TOKENS_JSON.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def tokens_css() -> str | None:
    """Raw tokens.css contents — None if the studio CSS isn't generated yet."""
    if not TOKENS_CSS.exists():
        return None
    return TOKENS_CSS.read_text(encoding="utf-8")


def _css_recipe_border(css: str, recipe_type_kebab: str, theme: str) -> str | None:
    """Pull ``--color-recipe-<type>-<theme>-border: #hex;`` out of tokens.css."""
    pattern = (
        rf"--color-recipe-{re.escape(recipe_type_kebab)}-{theme}-border:\s*"
        rf"(#[0-9a-fA-F]{{6}})"
    )
    m = re.search(pattern, css)
    return m.group(1).lower() if m else None


def _python_theme_border(recipe_type: str) -> str:
    """Border hex from the legacy Material-style ``recipe_colors`` dict."""
    # The legacy palette is what tokens.json + tokens.css mirror today.
    bg, border, text = DATAIKU_LIGHT.get_recipe_colors(recipe_type)
    return border.lower()


def _python_palette_fill(recipe_type: str) -> str:
    """Fill hex from the new DSS-fidelity ``recipe_palette`` dict."""
    fill, stroke, icon = DATAIKU_LIGHT.get_recipe_palette(recipe_type)
    return fill.lower()


# ---------------------------------------------------------------------------
# Strict tests (already true today).
# ---------------------------------------------------------------------------

class TestMermaidPlantUMLAgreeWithPython:
    """Mermaid + PlantUML emitters must always agree with the Python palette.

    These tests are *strict* — the emitters consume ``get_recipe_palette``
    directly, so any drift here is a real bug.
    """

    @pytest.mark.parametrize("recipe_type", BASELINE_TYPES)
    def test_mermaid_classdef_matches_python(self, recipe_type):
        # Build a minimal flow with the recipe in question and render it.
        from py2dataiku.models.dataiku_dataset import DataikuDataset, DatasetType
        from py2dataiku.models.dataiku_flow import DataikuFlow
        from py2dataiku.models.dataiku_recipe import DataikuRecipe, RecipeType
        from py2dataiku.visualizers import MermaidVisualizer

        flow = DataikuFlow(name="drift_check")
        flow.add_dataset(DataikuDataset(name="a", dataset_type=DatasetType.INPUT))
        flow.add_dataset(DataikuDataset(name="b", dataset_type=DatasetType.OUTPUT))
        flow.recipes.append(DataikuRecipe(
            name="r", recipe_type=RecipeType[recipe_type],
            inputs=["a"], outputs=["b"],
        ))
        mermaid = MermaidVisualizer().render(flow)
        expected = _python_palette_fill(recipe_type)
        assert f"fill:{expected}" in mermaid.lower(), (
            f"Mermaid classDef for {recipe_type} did not contain expected "
            f"{expected}. Mermaid output excerpt:\n{mermaid[-400:]}"
        )

    @pytest.mark.parametrize("recipe_type", BASELINE_TYPES)
    def test_plantuml_skinparam_matches_python(self, recipe_type):
        from py2dataiku.models.dataiku_dataset import DataikuDataset, DatasetType
        from py2dataiku.models.dataiku_flow import DataikuFlow
        from py2dataiku.models.dataiku_recipe import DataikuRecipe, RecipeType
        from py2dataiku.visualizers import PlantUMLVisualizer

        flow = DataikuFlow(name="drift_check")
        flow.add_dataset(DataikuDataset(name="a", dataset_type=DatasetType.INPUT))
        flow.add_dataset(DataikuDataset(name="b", dataset_type=DatasetType.OUTPUT))
        flow.recipes.append(DataikuRecipe(
            name="r", recipe_type=RecipeType[recipe_type],
            inputs=["a"], outputs=["b"],
        ))
        plant = PlantUMLVisualizer().render(flow)
        expected = _python_palette_fill(recipe_type)
        rt = recipe_type.lower()
        m = re.search(
            rf"BackgroundColor<<{rt}>>\s+(#[0-9a-fA-F]{{6}})", plant
        )
        assert m is not None, f"PlantUML skinparam missing for {recipe_type}"
        assert m.group(1).lower() == expected


# ---------------------------------------------------------------------------
# SHIM tests (intentionally lenient until Std-A consolidates the palettes).
# ---------------------------------------------------------------------------

class TestPaletteShim:
    """Lenient agreement check between Python theme and the studio CSS.

    Today the Python theme exposes TWO palettes:
      * ``recipe_colors`` — Material-style (matches ``tokens.css`` byte-for-byte).
      * ``recipe_palette`` — DSS-fidelity (used by the Python visualizers).

    When Std-A consolidates these into one source the test will flip to a
    strict four-way comparison (see ``EXPECTED_HARD_FAIL_ON_DRIFT``). Until
    then, the SHIM only asserts that the legacy ``recipe_colors`` border hex
    matches the studio CSS — and *records* (does not enforce) the divergence
    between ``recipe_palette`` and the legacy/CSS pair so the report is
    visible to reviewers.
    """

    @pytest.mark.parametrize("recipe_type", BASELINE_TYPES)
    def test_python_legacy_matches_tokens_css(self, recipe_type, tokens_css):
        if tokens_css is None:
            pytest.skip("apps/web/src/styles/tokens.css not generated yet")
        kebab = recipe_type.lower().replace("_", "-")
        css_border = _css_recipe_border(tokens_css, kebab, "light")
        assert css_border is not None, (
            f"tokens.css missing --color-recipe-{kebab}-light-border"
        )
        py_border = _python_theme_border(recipe_type)
        assert css_border == py_border, (
            f"{recipe_type} border drift — tokens.css has {css_border}, "
            f"Python recipe_colors has {py_border}"
        )

    @pytest.mark.parametrize("recipe_type", BASELINE_TYPES)
    def test_python_legacy_matches_tokens_json(self, recipe_type, tokens_json):
        if tokens_json is None:
            pytest.skip("docs/design/tokens.json not present")
        entry = tokens_json.get("color", {}).get("recipe", {}).get(recipe_type)
        if entry is None:
            pytest.skip(f"tokens.json has no entry for {recipe_type}")
        json_border = entry["light"]["border"].lower()
        py_border = _python_theme_border(recipe_type)
        assert json_border == py_border, (
            f"{recipe_type} border drift — tokens.json has {json_border}, "
            f"Python recipe_colors has {py_border}"
        )

    def test_palette_consolidation_status(self, tokens_json):
        """Reports (does not enforce) the recipe_palette ↔ tokens.json gap.

        Std-A's parallel work consolidates the DSS-fidelity ``recipe_palette``
        into ``tokens.json``. Until that lands, the two intentionally diverge
        — JOIN is ``#2196F3`` in tokens.json (Material) and ``#f29222`` in
        ``recipe_palette`` (DSS). When Std-A finishes, set
        ``EXPECTED_HARD_FAIL_ON_DRIFT = True`` to flip this to a strict check.
        """
        if tokens_json is None:
            pytest.skip("docs/design/tokens.json not present")
        divergent: dict[str, tuple[str, str]] = {}
        for rt in BASELINE_TYPES:
            entry = tokens_json.get("color", {}).get("recipe", {}).get(rt)
            if entry is None:
                continue
            json_fill = entry["light"]["bg"].lower()  # tokens.json uses "bg"
            py_palette_fill = _python_palette_fill(rt)
            if json_fill != py_palette_fill:
                divergent[rt] = (json_fill, py_palette_fill)
        if EXPECTED_HARD_FAIL_ON_DRIFT:
            assert not divergent, (
                f"recipe_palette ↔ tokens.json drift — {divergent}"
            )
        else:
            # SHIM: divergence is *expected* today. Just record it for review.
            # (Use a soft signal rather than xfail so the report is visible
            # in test output without polluting the pass/fail count.)
            print(
                f"[SHIM] recipe_palette ↔ tokens.json divergence — "
                f"{len(divergent)} type(s): {sorted(divergent)}"
            )
