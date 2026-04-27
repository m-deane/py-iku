"""Round-trip tests: build DataikuFlow → to_dict() → DataikuFlowModel → re-dump → assert equal.

One example per RecipeSettings subclass (12 total).
"""

from __future__ import annotations

import pytest
from py2dataiku.models.dataiku_dataset import DataikuDataset, DatasetType
from py2dataiku.models.dataiku_flow import DataikuFlow
from py2dataiku.models.dataiku_recipe import (
    Aggregation,
    DataikuRecipe,
    JoinKey,
    RecipeType,
)
from py2dataiku.models.prepare_step import PrepareStep
from py2dataiku.models.recipe_settings import (
    DistinctSettings,
    GroupingSettings,
    JoinSettings,
    PivotSettings,
    PrepareSettings,
    PythonSettings,
    SamplingSettings,
    SortSettings,
    SplitSettings,
    StackSettings,
    TopNSettings,
    WindowSettings,
)

from app.schemas.flow import DataikuFlowModel

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _make_flow_with_recipe(recipe: DataikuRecipe, name: str = "test_flow") -> DataikuFlow:
    """Create a minimal flow containing one recipe with its required datasets."""
    flow = DataikuFlow(name=name)
    # Add input datasets
    for inp in recipe.inputs:
        flow.add_dataset(DataikuDataset(name=inp, dataset_type=DatasetType.INPUT))
    # Add output datasets
    for out in recipe.outputs:
        flow.add_dataset(DataikuDataset(name=out, dataset_type=DatasetType.INTERMEDIATE))
    flow.recipes.append(recipe)
    return flow


def _roundtrip(flow: DataikuFlow) -> None:
    """Assert DataikuFlow.to_dict() round-trips cleanly through DataikuFlowModel."""
    flow_dict = flow.to_dict(include_timestamp=False)
    # Must not raise
    model = DataikuFlowModel.model_validate(flow_dict)
    # Re-dump and compare key fields
    dumped = model.model_dump(by_alias=True)
    assert dumped["flow_name"] == flow.name
    assert len(dumped["recipes"]) == len(flow.recipes)
    assert len(dumped["datasets"]) == len(flow.datasets)


# ---------------------------------------------------------------------------
# 1. PrepareSettings
# ---------------------------------------------------------------------------


def test_roundtrip_prepare_settings() -> None:
    step = PrepareStep.rename_columns({"old": "new"})
    settings = PrepareSettings(steps=[step])
    recipe = DataikuRecipe(
        name="prepare_1",
        recipe_type=RecipeType.PREPARE,
        inputs=["ds_in"],
        outputs=["ds_out"],
        settings=settings,
    )
    _roundtrip(_make_flow_with_recipe(recipe))


# ---------------------------------------------------------------------------
# 2. GroupingSettings
# ---------------------------------------------------------------------------


def test_roundtrip_grouping_settings() -> None:
    agg = Aggregation(column="amount", function="SUM")
    settings = GroupingSettings(keys=["region"], aggregations=[agg])
    recipe = DataikuRecipe(
        name="group_1",
        recipe_type=RecipeType.GROUPING,
        inputs=["ds_in"],
        outputs=["ds_out"],
        settings=settings,
    )
    _roundtrip(_make_flow_with_recipe(recipe))


# ---------------------------------------------------------------------------
# 3. JoinSettings
# ---------------------------------------------------------------------------


def test_roundtrip_join_settings() -> None:
    key = JoinKey(left_column="id", right_column="customer_id")
    settings = JoinSettings(join_type="LEFT", join_keys=[key])
    recipe = DataikuRecipe(
        name="join_1",
        recipe_type=RecipeType.JOIN,
        inputs=["ds_left", "ds_right"],
        outputs=["ds_out"],
        settings=settings,
    )
    _roundtrip(_make_flow_with_recipe(recipe))


# ---------------------------------------------------------------------------
# 4. WindowSettings
# ---------------------------------------------------------------------------


def test_roundtrip_window_settings() -> None:
    settings = WindowSettings(
        partition_columns=["user_id"],
        order_columns=["date"],
        aggregations=[{"type": "RUNNING_SUM", "column": "amount"}],
    )
    recipe = DataikuRecipe(
        name="window_1",
        recipe_type=RecipeType.WINDOW,
        inputs=["ds_in"],
        outputs=["ds_out"],
        settings=settings,
    )
    _roundtrip(_make_flow_with_recipe(recipe))


# ---------------------------------------------------------------------------
# 5. SamplingSettings
# ---------------------------------------------------------------------------


def test_roundtrip_sampling_settings() -> None:
    settings = SamplingSettings(sampling_method="HEAD_SEQUENTIAL", sample_size=1000)
    recipe = DataikuRecipe(
        name="sample_1",
        recipe_type=RecipeType.SAMPLING,
        inputs=["ds_in"],
        outputs=["ds_out"],
        settings=settings,
    )
    _roundtrip(_make_flow_with_recipe(recipe))


# ---------------------------------------------------------------------------
# 6. SplitSettings
# ---------------------------------------------------------------------------


def test_roundtrip_split_settings() -> None:
    settings = SplitSettings(split_mode="FILTER", condition="age > 18")
    recipe = DataikuRecipe(
        name="split_1",
        recipe_type=RecipeType.SPLIT,
        inputs=["ds_in"],
        outputs=["ds_yes", "ds_no"],
        settings=settings,
    )
    _roundtrip(_make_flow_with_recipe(recipe))


# ---------------------------------------------------------------------------
# 7. SortSettings
# ---------------------------------------------------------------------------


def test_roundtrip_sort_settings() -> None:
    settings = SortSettings(sort_columns=[{"column": "price", "order": "desc"}])
    recipe = DataikuRecipe(
        name="sort_1",
        recipe_type=RecipeType.SORT,
        inputs=["ds_in"],
        outputs=["ds_out"],
        settings=settings,
    )
    _roundtrip(_make_flow_with_recipe(recipe))


# ---------------------------------------------------------------------------
# 8. TopNSettings
# ---------------------------------------------------------------------------


def test_roundtrip_topn_settings() -> None:
    settings = TopNSettings(top_n=10, ranking_column="score")
    recipe = DataikuRecipe(
        name="topn_1",
        recipe_type=RecipeType.TOP_N,
        inputs=["ds_in"],
        outputs=["ds_out"],
        settings=settings,
    )
    _roundtrip(_make_flow_with_recipe(recipe))


# ---------------------------------------------------------------------------
# 9. DistinctSettings
# ---------------------------------------------------------------------------


def test_roundtrip_distinct_settings() -> None:
    settings = DistinctSettings(compute_count=True)
    recipe = DataikuRecipe(
        name="distinct_1",
        recipe_type=RecipeType.DISTINCT,
        inputs=["ds_in"],
        outputs=["ds_out"],
        settings=settings,
    )
    _roundtrip(_make_flow_with_recipe(recipe))


# ---------------------------------------------------------------------------
# 10. StackSettings
# ---------------------------------------------------------------------------


def test_roundtrip_stack_settings() -> None:
    settings = StackSettings(mode="UNION")
    recipe = DataikuRecipe(
        name="stack_1",
        recipe_type=RecipeType.STACK,
        inputs=["ds_a", "ds_b"],
        outputs=["ds_out"],
        settings=settings,
    )
    _roundtrip(_make_flow_with_recipe(recipe))


# ---------------------------------------------------------------------------
# 11. PythonSettings
# ---------------------------------------------------------------------------


def test_roundtrip_python_settings() -> None:
    settings = PythonSettings(code="import dataiku\nds = dataiku.Dataset('ds_in')\n")
    recipe = DataikuRecipe(
        name="python_1",
        recipe_type=RecipeType.PYTHON,
        inputs=["ds_in"],
        outputs=["ds_out"],
        settings=settings,
    )
    _roundtrip(_make_flow_with_recipe(recipe))


# ---------------------------------------------------------------------------
# 12. PivotSettings
# ---------------------------------------------------------------------------


def test_roundtrip_pivot_settings() -> None:
    settings = PivotSettings(
        row_columns=["region"],
        column_column="product",
        value_column="revenue",
        aggregation="SUM",
    )
    recipe = DataikuRecipe(
        name="pivot_1",
        recipe_type=RecipeType.PIVOT,
        inputs=["ds_in"],
        outputs=["ds_out"],
        settings=settings,
    )
    _roundtrip(_make_flow_with_recipe(recipe))


# ---------------------------------------------------------------------------
# Extra: unknown dataset reference raises ValueError
# ---------------------------------------------------------------------------


def test_unknown_dataset_ref_raises() -> None:
    """DataikuFlowModel should raise if recipe references unknown dataset."""
    bad_dict = {
        "flow_name": "bad",
        "total_recipes": 1,
        "total_datasets": 1,
        "datasets": [{"name": "ds_in", "type": "input", "connection_type": "Filesystem"}],
        "recipes": [
            {
                "name": "r1",
                "type": "prepare",
                "inputs": ["ds_in"],
                "outputs": ["DOES_NOT_EXIST"],
            }
        ],
        "optimization_notes": [],
        "recommendations": [],
    }
    with pytest.raises(Exception):
        DataikuFlowModel.model_validate(bad_dict)
