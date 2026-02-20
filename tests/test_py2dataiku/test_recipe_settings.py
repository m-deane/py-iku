"""Tests for RecipeSettings composition pattern."""

import pytest

from py2dataiku.models.dataiku_recipe import (
    DataikuRecipe, RecipeType, Aggregation, JoinKey, JoinType,
)
from py2dataiku.models.prepare_step import PrepareStep, ProcessorType
from py2dataiku.models.recipe_settings import (
    RecipeSettings,
    PrepareSettings,
    GroupingSettings,
    JoinSettings,
    WindowSettings,
    SplitSettings,
    SortSettings,
    TopNSettings,
    DistinctSettings,
    StackSettings,
    PythonSettings,
    PivotSettings,
    SamplingSettings,
)


class TestPrepareSettings:
    """Tests for PrepareSettings."""

    def test_to_dict(self):
        step = PrepareStep(
            processor_type=ProcessorType.COLUMN_RENAMER,
            params={"column": "a", "new_name": "b"},
        )
        settings = PrepareSettings(steps=[step])
        d = settings.to_dict()
        assert d["mode"] == "NORMAL"
        assert len(d["steps"]) == 1

    def test_to_display_dict(self):
        step = PrepareStep(
            processor_type=ProcessorType.COLUMN_RENAMER,
            params={"column": "a", "new_name": "b"},
        )
        settings = PrepareSettings(steps=[step])
        d = settings.to_display_dict()
        assert "steps" in d
        assert d["step_count"] == 1

    def test_recipe_with_settings(self):
        """Recipe constructed with settings object produces correct API output."""
        step = PrepareStep(
            processor_type=ProcessorType.FILL_EMPTY_WITH_VALUE,
            params={"column": "x", "value": 0},
        )
        recipe = DataikuRecipe(
            name="prep",
            recipe_type=RecipeType.PREPARE,
            inputs=["in"],
            outputs=["out"],
            settings=PrepareSettings(steps=[step]),
        )
        api = recipe.to_api_dict()
        assert api["settings"]["mode"] == "NORMAL"
        assert len(api["settings"]["steps"]) == 1


class TestGroupingSettings:
    """Tests for GroupingSettings."""

    def test_to_dict(self):
        settings = GroupingSettings(
            keys=["category"],
            aggregations=[Aggregation(column="amount", function="SUM")],
        )
        d = settings.to_dict()
        assert d["keys"] == [{"column": "category"}]
        assert len(d["aggregations"]) == 1

    def test_recipe_with_settings(self):
        recipe = DataikuRecipe(
            name="group",
            recipe_type=RecipeType.GROUPING,
            inputs=["in"],
            outputs=["out"],
            settings=GroupingSettings(
                keys=["cat"],
                aggregations=[Aggregation(column="val", function="AVG")],
            ),
        )
        api = recipe.to_api_dict()
        assert api["settings"]["keys"] == [{"column": "cat"}]


class TestJoinSettings:
    """Tests for JoinSettings."""

    def test_to_dict(self):
        settings = JoinSettings(
            join_type="LEFT",
            join_keys=[JoinKey(left_column="id", right_column="id")],
        )
        d = settings.to_dict()
        assert d["joinType"] == "LEFT"
        assert len(d["joins"]) == 1

    def test_with_selected_columns(self):
        settings = JoinSettings(
            join_type="INNER",
            join_keys=[JoinKey(left_column="id", right_column="id")],
            selected_columns={"left": ["id", "name"], "right": ["value"]},
        )
        d = settings.to_dict()
        assert "selectedColumns" in d


class TestWindowSettings:
    """Tests for WindowSettings."""

    def test_to_dict(self):
        settings = WindowSettings(
            partition_columns=["group"],
            order_columns=["date"],
            aggregations=[{"type": "RUNNING_SUM", "column": "value"}],
        )
        d = settings.to_dict()
        assert d["partitionColumns"] == [{"column": "group"}]
        assert d["orderColumns"] == [{"column": "date"}]


class TestSimpleSettings:
    """Tests for simple settings classes."""

    def test_split_settings(self):
        d = SplitSettings(condition="col > 5").to_dict()
        assert d["splitMode"] == "FILTER"
        assert d["condition"] == "col > 5"

    def test_sort_settings(self):
        d = SortSettings(
            sort_columns=[{"column": "name", "order": "ASC"}]
        ).to_dict()
        assert len(d["sortColumns"]) == 1

    def test_top_n_settings(self):
        d = TopNSettings(top_n=5, ranking_column="score").to_dict()
        assert d["topN"] == 5
        assert d["rankingColumn"] == "score"

    def test_distinct_settings(self):
        d = DistinctSettings(compute_count=True).to_dict()
        assert d["computeCount"] is True

    def test_stack_settings(self):
        d = StackSettings(mode="UNION").to_dict()
        assert d["mode"] == "UNION"

    def test_python_settings(self):
        d = PythonSettings(code="print('hello')").to_dict()
        assert d["code"] == "print('hello')"

    def test_sampling_settings(self):
        d = SamplingSettings(sampling_method="RANDOM_FIXED", sample_size=100).to_dict()
        assert d["samplingMethod"] == "RANDOM_FIXED"
        assert d["sampleSize"] == 100

    def test_pivot_settings(self):
        d = PivotSettings(
            row_columns=["a"],
            column_column="b",
            value_column="c",
            aggregation="SUM",
        ).to_dict()
        assert d["rowColumns"] == ["a"]


class TestBackwardCompatibility:
    """Verify that existing recipe construction still works."""

    def test_legacy_prepare(self):
        """Legacy flat-field construction produces same output as settings."""
        step = PrepareStep(
            processor_type=ProcessorType.COLUMN_RENAMER,
            params={"column": "a", "new_name": "b"},
        )
        legacy = DataikuRecipe(
            name="prep",
            recipe_type=RecipeType.PREPARE,
            inputs=["in"],
            outputs=["out"],
            steps=[step],
        )
        api = legacy.to_api_dict()
        assert "settings" in api
        assert api["settings"]["mode"] == "NORMAL"
        assert len(api["settings"]["steps"]) == 1

    def test_legacy_grouping(self):
        legacy = DataikuRecipe(
            name="group",
            recipe_type=RecipeType.GROUPING,
            inputs=["in"],
            outputs=["out"],
            group_keys=["cat"],
            aggregations=[Aggregation(column="val", function="SUM")],
        )
        api = legacy.to_api_dict()
        assert api["settings"]["keys"] == [{"column": "cat"}]

    def test_legacy_join(self):
        legacy = DataikuRecipe(
            name="join",
            recipe_type=RecipeType.JOIN,
            inputs=["left", "right"],
            outputs=["out"],
            join_type=JoinType.LEFT,
            join_keys=[JoinKey(left_column="id", right_column="id")],
        )
        api = legacy.to_api_dict()
        assert api["settings"]["joinType"] == "LEFT"

    def test_legacy_python(self):
        legacy = DataikuRecipe(
            name="py",
            recipe_type=RecipeType.PYTHON,
            inputs=["in"],
            outputs=["out"],
            code="df = dataiku.Dataset('in').get_dataframe()",
        )
        api = legacy.to_api_dict()
        assert api["settings"]["code"] != ""

    def test_settings_takes_precedence(self):
        """When both settings and flat fields are set, settings wins."""
        recipe = DataikuRecipe(
            name="prep",
            recipe_type=RecipeType.PREPARE,
            inputs=["in"],
            outputs=["out"],
            steps=[],  # flat field has no steps
            settings=PrepareSettings(steps=[
                PrepareStep(processor_type=ProcessorType.COLUMN_RENAMER, params={})
            ]),
        )
        api = recipe.to_api_dict()
        # settings has 1 step, flat has 0 - settings should win
        assert len(api["settings"]["steps"]) == 1

    def test_factory_methods_still_work(self):
        """Factory methods produce valid recipes."""
        prep = DataikuRecipe.create_prepare("p", "in", "out")
        assert prep.recipe_type == RecipeType.PREPARE

        group = DataikuRecipe.create_grouping("g", "in", "out", keys=["k"])
        assert group.recipe_type == RecipeType.GROUPING

        join = DataikuRecipe.create_join(
            "j", "left", "right", "out",
            join_keys=[JoinKey(left_column="id", right_column="id")],
        )
        assert join.recipe_type == RecipeType.JOIN

        py = DataikuRecipe.create_python("p", ["in"], ["out"], code="pass")
        assert py.recipe_type == RecipeType.PYTHON

    def test_to_dict_display_with_settings(self):
        """to_dict() produces clean display output when using settings."""
        recipe = DataikuRecipe(
            name="prep",
            recipe_type=RecipeType.PREPARE,
            inputs=["in"],
            outputs=["out"],
            settings=PrepareSettings(steps=[
                PrepareStep(processor_type=ProcessorType.COLUMN_RENAMER, params={})
            ]),
        )
        d = recipe.to_dict()
        assert "steps" in d
        assert d["step_count"] == 1

    def test_no_settings_field_in_output(self):
        """The raw settings object should not appear in to_dict() or to_api_dict()."""
        recipe = DataikuRecipe(
            name="prep",
            recipe_type=RecipeType.PREPARE,
            inputs=["in"],
            outputs=["out"],
            settings=PrepareSettings(steps=[]),
        )
        d = recipe.to_dict()
        # The settings object itself should not leak into the dict
        assert "settings" not in d or not isinstance(d.get("settings"), RecipeSettings)
