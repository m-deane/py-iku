"""DSS round-trip assertions for visual recipes.

For each recipe fixture, attempt to:
1. Resolve the documented ``type`` against ``RecipeType`` enum (canonical
   value match, e.g. ``"grouping"``, or enum-name match).
2. Build a minimal ``DataikuFlow`` containing this single recipe + its
   declared input/output datasets, then ``flow.to_dict()`` round-trip.
3. Verify the recipe-type string is preserved (no rename).
4. Verify the documented top-level fields (inputs / outputs / type)
   survive the round-trip.

Failures mean py-iku has either renamed a documented recipe field,
collapsed two distinct recipe types into one, or doesn't recognize the
documented type at all. See ``_findings.md`` for the catalogued
blockers.

Fixtures with ``_meta.expected_xfail`` are marked xfail.
"""
from __future__ import annotations

from typing import Any

import pytest

from py2dataiku.models.dataiku_flow import DataikuFlow
from py2dataiku.models.dataiku_dataset import DataikuDataset, DatasetType
from py2dataiku.models.dataiku_recipe import DataikuRecipe, RecipeType

from .conftest import FixtureCase, discover_fixtures


_RECIPE_CASES: list[FixtureCase] = discover_fixtures("recipe")


def _idfn(case: FixtureCase) -> str:
    return case.slug


def _resolve_recipe_type(name: str) -> RecipeType | None:
    """Resolve a documented type string against RecipeType."""
    if not name:
        return None
    # Canonical value (lowercase, e.g. 'grouping')
    for member in RecipeType:
        if member.value == name:
            return member
    upper = name.upper()
    if upper in RecipeType.__members__:
        return RecipeType[upper]
    return None


@pytest.mark.parametrize("case", _RECIPE_CASES, ids=_idfn)
def test_recipe_type_resolves(case: FixtureCase) -> None:
    """The documented recipe type maps to a real RecipeType enum member."""
    if case.expected_xfail_marker:
        pytest.xfail(case.expected_xfail_marker)

    payload: dict[str, Any] = case.payload
    type_name = payload.get("type", "")

    resolved = _resolve_recipe_type(type_name)
    assert resolved is not None, (
        f"Recipe type {type_name!r} (from {case.slug}) does not match any "
        f"RecipeType enum member. See docs/dataiku-reference/_findings.md."
    )


@pytest.mark.parametrize("case", _RECIPE_CASES, ids=_idfn)
def test_recipe_round_trip_preserves_canonical_fields(case: FixtureCase) -> None:
    """A minimal DataikuFlow with this recipe round-trips through to_dict.

    We assert the canonical structural fields (type, inputs, outputs)
    survive serialization. Settings-shape preservation is checked
    separately by the per-settings-class unit tests in
    ``tests/test_py2dataiku/``.
    """
    if case.expected_xfail_marker:
        pytest.xfail(case.expected_xfail_marker)

    payload: dict[str, Any] = case.payload
    recipe_type = _resolve_recipe_type(payload.get("type", ""))
    if recipe_type is None:
        pytest.skip("Type doesn't resolve; covered by test_recipe_type_resolves.")

    name = payload.get("name", f"recipe_for_{case.slug}")
    inputs = list(payload.get("inputs") or [])
    outputs = list(payload.get("outputs") or [])

    flow = DataikuFlow(name=f"flow_for_{case.slug}")
    for ds_name in inputs:
        flow.add_dataset(
            DataikuDataset(name=ds_name, dataset_type=DatasetType.INPUT)
        )
    for ds_name in outputs:
        flow.add_dataset(
            DataikuDataset(name=ds_name, dataset_type=DatasetType.OUTPUT)
        )
    flow.add_recipe(
        DataikuRecipe(
            name=name,
            recipe_type=recipe_type,
            inputs=inputs,
            outputs=outputs,
        )
    )

    serialized = flow.to_dict(include_timestamp=False)

    # Find the recipe in the serialized form.
    serialized_recipes = serialized.get("recipes") or []
    assert len(serialized_recipes) == 1, (
        f"Expected exactly 1 recipe; got {len(serialized_recipes)}"
    )
    serialized_recipe = serialized_recipes[0]

    # Type preserved (string match — no silent rename).
    assert serialized_recipe.get("type") == recipe_type.value, (
        f"Recipe type drifted on round-trip: "
        f"{recipe_type.value!r} -> {serialized_recipe.get('type')!r}"
    )
    # Inputs / outputs preserved.
    assert list(serialized_recipe.get("inputs") or []) == inputs
    assert list(serialized_recipe.get("outputs") or []) == outputs
