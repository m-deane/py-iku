"""Tests for FlowGenerator recipe type handlers.

Tests the new handlers added for TransformationTypes that previously
fell through to Python recipe fallback.
"""

import pytest

from py2dataiku.generators.flow_generator import FlowGenerator
from py2dataiku.models.dataiku_recipe import RecipeType, SamplingMethod
from py2dataiku.models.prepare_step import ProcessorType
from py2dataiku.models.transformation import Transformation, TransformationType


def make_read_transform(var_name="df"):
    """Helper to create a READ_DATA transformation."""
    return Transformation(
        transformation_type=TransformationType.READ_DATA,
        target_dataframe=var_name,
        parameters={"filepath": "data.csv", "format": "csv"},
        source_line=1,
    )


class TestWindowRecipeHandler:
    """Tests for ROLLING and WINDOW transformation handlers."""

    def test_rolling_creates_window_recipe(self):
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.ROLLING,
                source_dataframe="df",
                target_dataframe="df",
                columns=["price"],
                parameters={
                    "method": "cumsum",
                    "window": 3,
                    "partition_columns": ["category"],
                    "order_columns": ["date"],
                },
                source_line=2,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        window_recipes = flow.get_recipes_by_type(RecipeType.WINDOW)
        assert len(window_recipes) == 1
        recipe = window_recipes[0]
        assert recipe.partition_columns == ["category"]
        assert recipe.order_columns == ["date"]
        assert len(recipe.window_aggregations) == 1
        assert recipe.window_aggregations[0]["column"] == "price"
        assert recipe.window_aggregations[0]["type"] == "RUNNING_SUM"
        assert recipe.window_aggregations[0]["windowSize"] == 3

    def test_window_cumsum_creates_window_recipe(self):
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.WINDOW,
                source_dataframe="df",
                target_dataframe="df",
                columns=["amount"],
                parameters={"method": "cumsum"},
                source_line=2,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        window_recipes = flow.get_recipes_by_type(RecipeType.WINDOW)
        assert len(window_recipes) == 1
        assert window_recipes[0].window_aggregations[0]["type"] == "RUNNING_SUM"

    def test_window_rank_creates_window_recipe(self):
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.WINDOW,
                source_dataframe="df",
                target_dataframe="df",
                columns=["score"],
                parameters={"method": "rank"},
                source_line=2,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        window_recipes = flow.get_recipes_by_type(RecipeType.WINDOW)
        assert len(window_recipes) == 1
        assert window_recipes[0].window_aggregations[0]["type"] == "RANK"

    def test_window_diff_creates_window_recipe(self):
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.WINDOW,
                source_dataframe="df",
                target_dataframe="df",
                columns=["value"],
                parameters={"method": "diff"},
                source_line=2,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        window_recipes = flow.get_recipes_by_type(RecipeType.WINDOW)
        assert len(window_recipes) == 1
        assert window_recipes[0].window_aggregations[0]["type"] == "LAG_DIFF"

    def test_window_shift_creates_window_recipe(self):
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.WINDOW,
                source_dataframe="df",
                target_dataframe="df",
                columns=["value"],
                parameters={"method": "shift"},
                source_line=2,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        window_recipes = flow.get_recipes_by_type(RecipeType.WINDOW)
        assert len(window_recipes) == 1
        assert window_recipes[0].window_aggregations[0]["type"] == "LAG"

    def test_window_no_column_no_aggs(self):
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.WINDOW,
                source_dataframe="df",
                target_dataframe="df",
                columns=[],
                parameters={"method": "cumsum"},
                source_line=2,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        window_recipes = flow.get_recipes_by_type(RecipeType.WINDOW)
        assert len(window_recipes) == 1
        assert window_recipes[0].window_aggregations == []

    def test_window_flushes_pending_prepare_steps(self):
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.FILL_NA,
                source_dataframe="df",
                target_dataframe="df",
                columns=["col"],
                parameters={"value": 0},
                source_line=2,
            ),
            Transformation(
                transformation_type=TransformationType.WINDOW,
                source_dataframe="df",
                target_dataframe="df",
                columns=["col"],
                parameters={"method": "cumsum"},
                source_line=3,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        prepare_recipes = flow.get_recipes_by_type(RecipeType.PREPARE)
        window_recipes = flow.get_recipes_by_type(RecipeType.WINDOW)
        assert len(prepare_recipes) == 1
        assert len(window_recipes) == 1

    def test_window_source_line_captured(self):
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.WINDOW,
                source_dataframe="df",
                target_dataframe="df",
                columns=["val"],
                parameters={"method": "cumsum"},
                source_line=42,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        window_recipes = flow.get_recipes_by_type(RecipeType.WINDOW)
        assert window_recipes[0].source_lines == [42]


class TestTopNRecipeHandler:
    """Tests for TOP_N transformation handler."""

    def test_topn_creates_topn_recipe(self):
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.TOP_N,
                source_dataframe="df",
                target_dataframe="df",
                columns=["score"],
                parameters={"n": 5},
                source_line=2,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        topn_recipes = flow.get_recipes_by_type(RecipeType.TOP_N)
        assert len(topn_recipes) == 1
        assert topn_recipes[0].top_n == 5
        assert topn_recipes[0].ranking_column == "score"

    def test_topn_defaults_to_10(self):
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.TOP_N,
                source_dataframe="df",
                target_dataframe="df",
                columns=["score"],
                parameters={},
                source_line=2,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        topn_recipes = flow.get_recipes_by_type(RecipeType.TOP_N)
        assert topn_recipes[0].top_n == 10

    def test_topn_no_column_sets_none_ranking(self):
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.TOP_N,
                source_dataframe="df",
                target_dataframe="df",
                columns=[],
                parameters={"n": 3},
                source_line=2,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        topn_recipes = flow.get_recipes_by_type(RecipeType.TOP_N)
        assert topn_recipes[0].ranking_column is None

    def test_topn_flushes_pending_prepare_steps(self):
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.DROP_NA,
                source_dataframe="df",
                target_dataframe="df",
                columns=["col"],
                parameters={},
                source_line=2,
            ),
            Transformation(
                transformation_type=TransformationType.TOP_N,
                source_dataframe="df",
                target_dataframe="df",
                columns=["col"],
                parameters={"n": 10},
                source_line=3,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        prepare_recipes = flow.get_recipes_by_type(RecipeType.PREPARE)
        topn_recipes = flow.get_recipes_by_type(RecipeType.TOP_N)
        assert len(prepare_recipes) == 1
        assert len(topn_recipes) == 1


class TestHeadTailSamplingHandler:
    """Tests for HEAD, TAIL, and SAMPLE transformation handlers."""

    def test_head_creates_sampling_first_rows(self):
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.HEAD,
                source_dataframe="df",
                target_dataframe="df",
                parameters={"n": 100},
                source_line=2,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        sampling_recipes = flow.get_recipes_by_type(RecipeType.SAMPLING)
        assert len(sampling_recipes) == 1
        assert sampling_recipes[0].sampling_method == SamplingMethod.FIRST_ROWS
        assert sampling_recipes[0].sample_size == 100

    def test_head_defaults_to_5(self):
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.HEAD,
                source_dataframe="df",
                target_dataframe="df",
                parameters={},
                source_line=2,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        sampling_recipes = flow.get_recipes_by_type(RecipeType.SAMPLING)
        assert sampling_recipes[0].sample_size == 5

    def test_tail_creates_sampling_last_rows(self):
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.TAIL,
                source_dataframe="df",
                target_dataframe="df",
                parameters={"n": 50},
                source_line=2,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        sampling_recipes = flow.get_recipes_by_type(RecipeType.SAMPLING)
        assert len(sampling_recipes) == 1
        assert sampling_recipes[0].sampling_method == SamplingMethod.LAST_ROWS
        assert sampling_recipes[0].sample_size == 50

    def test_sample_with_n_creates_random_fixed_nb(self):
        # n=200 is a fixed-row-count random sample.
        # In DSS this is RANDOM_FIXED_NB (SamplingMethod.RANDOM in the enum).
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.SAMPLE,
                source_dataframe="df",
                target_dataframe="df",
                parameters={"n": 200},
                source_line=2,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        sampling_recipes = flow.get_recipes_by_type(RecipeType.SAMPLING)
        assert len(sampling_recipes) == 1
        assert sampling_recipes[0].sampling_method == SamplingMethod.RANDOM
        assert sampling_recipes[0].sample_size == 200

    def test_sample_with_frac_creates_random_fixed_ratio(self):
        # frac=0.1 is a fixed-fraction random sample.
        # In DSS this is RANDOM_FIXED_RATIO (SamplingMethod.RANDOM_FIXED in enum).
        # The fraction is converted to a percentage (0-100).
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.SAMPLE,
                source_dataframe="df",
                target_dataframe="df",
                parameters={"frac": 0.1},
                source_line=2,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        sampling_recipes = flow.get_recipes_by_type(RecipeType.SAMPLING)
        assert len(sampling_recipes) == 1
        assert sampling_recipes[0].sampling_method == SamplingMethod.RANDOM_FIXED
        assert sampling_recipes[0].sample_size == 10  # 0.1 -> 10%

    def test_head_flushes_pending_prepare_steps(self):
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.FILL_NA,
                source_dataframe="df",
                target_dataframe="df",
                columns=["x"],
                parameters={"value": 0},
                source_line=2,
            ),
            Transformation(
                transformation_type=TransformationType.HEAD,
                source_dataframe="df",
                target_dataframe="df",
                parameters={"n": 10},
                source_line=3,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        prepare_recipes = flow.get_recipes_by_type(RecipeType.PREPARE)
        sampling_recipes = flow.get_recipes_by_type(RecipeType.SAMPLING)
        assert len(prepare_recipes) == 1
        assert len(sampling_recipes) == 1


class TestPivotRecipeHandler:
    """Tests for PIVOT transformation handler."""

    def test_pivot_creates_pivot_recipe(self):
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.PIVOT,
                source_dataframe="df",
                target_dataframe="df",
                parameters={
                    "index": ["date"],
                    "columns": "category",
                    "values": "amount",
                    "aggfunc": "sum",
                },
                source_line=2,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        pivot_recipes = flow.get_recipes_by_type(RecipeType.PIVOT)
        assert len(pivot_recipes) == 1
        recipe = pivot_recipes[0]
        assert recipe.settings is not None
        settings = recipe.settings
        assert settings.row_columns == ["date"]
        assert settings.column_column == "category"
        assert settings.value_column == "amount"
        assert settings.aggregation == "SUM"

    def test_pivot_with_list_columns(self):
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.PIVOT,
                source_dataframe="df",
                target_dataframe="df",
                parameters={
                    "index": "date",
                    "columns": ["category"],
                    "values": ["amount"],
                    "aggfunc": "mean",
                },
                source_line=2,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        pivot_recipes = flow.get_recipes_by_type(RecipeType.PIVOT)
        assert len(pivot_recipes) == 1
        settings = pivot_recipes[0].settings
        assert settings.row_columns == ["date"]
        assert settings.column_column == "category"
        assert settings.value_column == "amount"
        assert settings.aggregation == "AVG"

    def test_pivot_default_aggfunc(self):
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.PIVOT,
                source_dataframe="df",
                target_dataframe="df",
                parameters={
                    "index": ["row"],
                    "columns": "col",
                    "values": "val",
                },
                source_line=2,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        pivot_recipes = flow.get_recipes_by_type(RecipeType.PIVOT)
        assert pivot_recipes[0].settings.aggregation == "SUM"

    def test_pivot_flushes_pending_prepare_steps(self):
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.COLUMN_DROP,
                source_dataframe="df",
                target_dataframe="df",
                columns=["extra"],
                parameters={},
                source_line=2,
            ),
            Transformation(
                transformation_type=TransformationType.PIVOT,
                source_dataframe="df",
                target_dataframe="df",
                parameters={
                    "index": ["a"],
                    "columns": "b",
                    "values": "c",
                },
                source_line=3,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        prepare_recipes = flow.get_recipes_by_type(RecipeType.PREPARE)
        pivot_recipes = flow.get_recipes_by_type(RecipeType.PIVOT)
        assert len(prepare_recipes) == 1
        assert len(pivot_recipes) == 1


class TestMeltRecipeHandler:
    """Tests for MELT transformation handler."""

    def test_melt_creates_prepare_with_fold(self):
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.MELT,
                source_dataframe="df",
                target_dataframe="df",
                columns=["col_a", "col_b", "col_c"],
                parameters={
                    "value_vars": ["col_a", "col_b", "col_c"],
                    "var_name": "metric",
                    "value_name": "measurement",
                },
                source_line=2,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        prepare_recipes = flow.get_recipes_by_type(RecipeType.PREPARE)
        assert len(prepare_recipes) == 1
        steps = prepare_recipes[0].steps
        assert len(steps) == 1
        assert steps[0].processor_type == ProcessorType.FOLD_MULTIPLE_COLUMNS
        assert steps[0].params["columns"] == ["col_a", "col_b", "col_c"]
        assert steps[0].params["varName"] == "metric"
        assert steps[0].params["valueName"] == "measurement"

    def test_melt_defaults(self):
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.MELT,
                source_dataframe="df",
                target_dataframe="df",
                columns=["x", "y"],
                parameters={},
                source_line=2,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        prepare_recipes = flow.get_recipes_by_type(RecipeType.PREPARE)
        assert len(prepare_recipes) == 1
        step = prepare_recipes[0].steps[0]
        assert step.params["varName"] == "variable"
        assert step.params["valueName"] == "value"
        assert step.params["columns"] == ["x", "y"]

    def test_melt_flushes_pending_prepare_steps(self):
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.FILL_NA,
                source_dataframe="df",
                target_dataframe="df",
                columns=["a"],
                parameters={"value": 0},
                source_line=2,
            ),
            Transformation(
                transformation_type=TransformationType.MELT,
                source_dataframe="df",
                target_dataframe="df",
                columns=["x", "y"],
                parameters={"value_vars": ["x", "y"]},
                source_line=3,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        prepare_recipes = flow.get_recipes_by_type(RecipeType.PREPARE)
        # Two prepare recipes: one for fillna flush, one for the melt fold
        assert len(prepare_recipes) == 2


class TestJoinTransformationHandler:
    """Tests for JOIN (df.join()) transformation handler."""

    def test_join_creates_join_recipe(self):
        gen = FlowGenerator()
        transformations = [
            make_read_transform("df1"),
            make_read_transform("df2"),
            Transformation(
                transformation_type=TransformationType.JOIN,
                source_dataframe="df1",
                target_dataframe="result",
                parameters={
                    "right": "df2",
                    "on": "id",
                    "how": "left",
                },
                source_line=3,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        join_recipes = flow.get_recipes_by_type(RecipeType.JOIN)
        assert len(join_recipes) == 1
        assert join_recipes[0].join_type.value == "LEFT"

    def test_join_default_inner(self):
        gen = FlowGenerator()
        transformations = [
            make_read_transform("df1"),
            make_read_transform("df2"),
            Transformation(
                transformation_type=TransformationType.JOIN,
                source_dataframe="df1",
                target_dataframe="result",
                parameters={
                    "right": "df2",
                    "on": "key",
                },
                source_line=3,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        join_recipes = flow.get_recipes_by_type(RecipeType.JOIN)
        assert join_recipes[0].join_type.value == "INNER"


class TestNumericTransformHandler:
    """Tests for NUMERIC_TRANSFORM handler."""

    def test_round_creates_prepare_step(self):
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.NUMERIC_TRANSFORM,
                source_dataframe="df",
                target_dataframe="df",
                columns=["price"],
                parameters={"method": "round", "decimals": 2},
                source_line=2,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        prepare_recipes = flow.get_recipes_by_type(RecipeType.PREPARE)
        assert len(prepare_recipes) == 1
        step = prepare_recipes[0].steps[0]
        assert step.processor_type == ProcessorType.ROUND_COLUMN
        assert step.params["column"] == "price"
        assert step.params["precision"] == 2

    def test_abs_creates_prepare_step(self):
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.NUMERIC_TRANSFORM,
                source_dataframe="df",
                target_dataframe="df",
                columns=["value"],
                parameters={"method": "abs"},
                source_line=2,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        prepare_recipes = flow.get_recipes_by_type(RecipeType.PREPARE)
        assert len(prepare_recipes) == 1
        assert prepare_recipes[0].steps[0].processor_type == ProcessorType.ABS_COLUMN

    def test_clip_creates_prepare_step(self):
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.NUMERIC_TRANSFORM,
                source_dataframe="df",
                target_dataframe="df",
                columns=["val"],
                parameters={"method": "clip", "lower": 0, "upper": 100},
                source_line=2,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        prepare_recipes = flow.get_recipes_by_type(RecipeType.PREPARE)
        assert len(prepare_recipes) == 1
        step = prepare_recipes[0].steps[0]
        assert step.processor_type == ProcessorType.CLIP_COLUMN
        assert step.params["min"] == 0
        assert step.params["max"] == 100

    def test_unknown_numeric_uses_numerical_transformer(self):
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.NUMERIC_TRANSFORM,
                source_dataframe="df",
                target_dataframe="df",
                columns=["x"],
                parameters={"method": "log"},
                source_line=2,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        prepare_recipes = flow.get_recipes_by_type(RecipeType.PREPARE)
        assert len(prepare_recipes) == 1
        step = prepare_recipes[0].steps[0]
        assert step.processor_type == ProcessorType.NUMERICAL_TRANSFORMER
        assert step.params["mode"] == "LOG"

    def test_numeric_batches_with_other_prepare_steps(self):
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.FILL_NA,
                source_dataframe="df",
                target_dataframe="df",
                columns=["a"],
                parameters={"value": 0},
                source_line=2,
            ),
            Transformation(
                transformation_type=TransformationType.NUMERIC_TRANSFORM,
                source_dataframe="df",
                target_dataframe="df",
                columns=["a"],
                parameters={"method": "abs"},
                source_line=3,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        prepare_recipes = flow.get_recipes_by_type(RecipeType.PREPARE)
        # Both should be in a single prepare recipe
        assert len(prepare_recipes) == 1
        assert len(prepare_recipes[0].steps) == 2


class TestNoFallbackWarnings:
    """Tests that new handlers do not produce Python fallback warnings."""

    @pytest.mark.parametrize(
        "trans_type,params",
        [
            (TransformationType.ROLLING, {"method": "cumsum", "window": 5}),
            (TransformationType.WINDOW, {"method": "rank"}),
            (TransformationType.TOP_N, {"n": 10}),
            (TransformationType.HEAD, {"n": 5}),
            (TransformationType.TAIL, {"n": 5}),
            (TransformationType.SAMPLE, {"n": 100}),
            (TransformationType.PIVOT, {"index": ["a"], "columns": "b", "values": "c"}),
            (TransformationType.MELT, {"value_vars": ["x", "y"]}),
            (TransformationType.NUMERIC_TRANSFORM, {"method": "round", "decimals": 2}),
        ],
    )
    def test_no_python_fallback_warning(self, trans_type, params):
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=trans_type,
                source_dataframe="df",
                target_dataframe="df",
                columns=["col"],
                parameters=params,
                source_line=2,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        python_recipes = flow.get_recipes_by_type(RecipeType.PYTHON)
        assert len(python_recipes) == 0, (
            f"TransformationType.{trans_type.name} should not fall back to Python recipe"
        )
        fallback_warnings = [
            w for w in flow.warnings if "fell back to Python recipe" in w
        ]
        assert len(fallback_warnings) == 0, (
            f"TransformationType.{trans_type.name} produced fallback warning"
        )


class TestOutputDatasetNames:
    """Tests that output dataset names are correctly formed."""

    def test_window_output_name(self):
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.WINDOW,
                source_dataframe="df",
                target_dataframe="df",
                columns=["x"],
                parameters={"method": "cumsum"},
                source_line=2,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        recipe = flow.get_recipes_by_type(RecipeType.WINDOW)[0]
        assert recipe.outputs[0].endswith("_windowed")

    def test_topn_output_name(self):
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.TOP_N,
                source_dataframe="df",
                target_dataframe="df",
                columns=["x"],
                parameters={"n": 5},
                source_line=2,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        recipe = flow.get_recipes_by_type(RecipeType.TOP_N)[0]
        assert recipe.outputs[0].endswith("_topn")

    def test_sampling_output_name(self):
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.HEAD,
                source_dataframe="df",
                target_dataframe="df",
                parameters={"n": 10},
                source_line=2,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        recipe = flow.get_recipes_by_type(RecipeType.SAMPLING)[0]
        assert recipe.outputs[0].endswith("_sampled")

    def test_pivot_output_name(self):
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.PIVOT,
                source_dataframe="df",
                target_dataframe="df",
                parameters={
                    "index": ["a"],
                    "columns": "b",
                    "values": "c",
                },
                source_line=2,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        recipe = flow.get_recipes_by_type(RecipeType.PIVOT)[0]
        assert recipe.outputs[0].endswith("_pivoted")


class TestRecipeInputOutput:
    """Tests that recipes have correct input/output dataset wiring."""

    def test_window_recipe_wiring(self):
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.WINDOW,
                source_dataframe="df",
                target_dataframe="df",
                columns=["x"],
                parameters={"method": "cumsum"},
                source_line=2,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        recipe = flow.get_recipes_by_type(RecipeType.WINDOW)[0]
        assert len(recipe.inputs) == 1
        assert len(recipe.outputs) == 1
        assert recipe.inputs[0] == "df"
        assert recipe.outputs[0] == "df_windowed"

    def test_chained_handlers_wiring(self):
        """Test that output of one handler flows as input to the next."""
        gen = FlowGenerator()
        transformations = [
            make_read_transform(),
            Transformation(
                transformation_type=TransformationType.WINDOW,
                source_dataframe="df",
                target_dataframe="df",
                columns=["x"],
                parameters={"method": "cumsum"},
                source_line=2,
            ),
            Transformation(
                transformation_type=TransformationType.TOP_N,
                source_dataframe="df",
                target_dataframe="df",
                columns=["x"],
                parameters={"n": 5},
                source_line=3,
            ),
        ]
        flow = gen.generate(transformations, optimize=False)
        window_recipe = flow.get_recipes_by_type(RecipeType.WINDOW)[0]
        topn_recipe = flow.get_recipes_by_type(RecipeType.TOP_N)[0]
        # TopN input should be the window output
        assert topn_recipe.inputs[0] == window_recipe.outputs[0]
