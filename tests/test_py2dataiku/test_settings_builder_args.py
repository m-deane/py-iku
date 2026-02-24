"""Tests for to_dss_builder_args() on all 12 RecipeSettings subclasses."""

import pytest

from py2dataiku.models.recipe_settings import (
    RecipeSettings,
    PrepareSettings,
    GroupingSettings,
    JoinSettings,
    WindowSettings,
    SamplingSettings,
    SplitSettings,
    SortSettings,
    TopNSettings,
    DistinctSettings,
    StackSettings,
    PythonSettings,
    PivotSettings,
    _default_engine_params,
)
from py2dataiku.models.prepare_step import PrepareStep, ProcessorType
from py2dataiku.models.dataiku_recipe import Aggregation, JoinKey


# ---------------------------------------------------------------------------
# Helper: verify the abstract method exists on the base class
# ---------------------------------------------------------------------------
class TestRecipeSettingsABC:
    """Verify RecipeSettings declares to_dss_builder_args as abstract."""

    def test_abstract_method_exists(self):
        assert hasattr(RecipeSettings, "to_dss_builder_args")

    def test_cannot_instantiate_without_implementation(self):
        class IncompleteSettings(RecipeSettings):
            def to_dict(self):
                return {}

            def to_display_dict(self):
                return {}

        with pytest.raises(TypeError):
            IncompleteSettings()


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------
class TestDefaultEngineParams:
    """Verify _default_engine_params returns expected structure."""

    def test_has_hive(self):
        params = _default_engine_params()
        assert "hive" in params
        assert params["hive"]["skipPrerunValidate"] is False

    def test_has_sql_pipeline(self):
        params = _default_engine_params()
        assert params["sqlPipelineParams"]["pipelineAllowMerge"] is True
        assert params["sqlPipelineParams"]["pipelineAllowStart"] is True

    def test_has_impala(self):
        params = _default_engine_params()
        assert params["impala"]["forceStreamMode"] is True

    def test_has_spark(self):
        params = _default_engine_params()
        assert params["spark"]["inheritConf"] == "default"


# ---------------------------------------------------------------------------
# 1. PrepareSettings
# ---------------------------------------------------------------------------
class TestPrepareSettingsBuilderArgs:
    """Tests for PrepareSettings.to_dss_builder_args()."""

    def test_empty_steps(self):
        settings = PrepareSettings()
        result = settings.to_dss_builder_args()
        assert result["mode"] == "BATCH"
        assert result["steps"] == []
        assert "engineParams" in result
        assert result["columnsSelection"] == {"mode": "ALL"}
        assert result["virtualInputs"] == []
        assert result["filterExpression"] == {}

    def test_mode_is_batch_not_normal(self):
        settings = PrepareSettings(mode="NORMAL")
        result = settings.to_dss_builder_args()
        assert result["mode"] == "BATCH"

    def test_with_steps(self):
        step = PrepareStep(
            processor_type=ProcessorType.COLUMN_RENAMER,
            params={"inputColumn": "old_name", "outputColumn": "new_name"},
        )
        settings = PrepareSettings(steps=[step])
        result = settings.to_dss_builder_args()
        assert len(result["steps"]) == 1
        assert result["steps"][0]["type"] == "ColumnRenamer"
        assert result["steps"][0]["params"]["inputColumn"] == "old_name"
        assert result["steps"][0]["disabled"] is False

    def test_engine_params_structure(self):
        settings = PrepareSettings()
        result = settings.to_dss_builder_args()
        ep = result["engineParams"]
        assert ep["hive"]["addDkuUdf"] is False
        assert ep["hive"]["executionEngine"] == "HIVESERVER2"
        assert "dkuHadoop" in ep
        assert ep["dkuHadoop"]["inheritConf"] == "default"

    def test_max_jobs_per_category(self):
        settings = PrepareSettings()
        result = settings.to_dss_builder_args()
        jobs = result["maxJobsPerCategory"]
        assert jobs["PREPARE_FILTERING"] == 1
        assert jobs["PREPARE_PARSING"] == 1
        assert jobs["PREPARE_OTHERS"] == 1

    def test_multiple_steps(self):
        steps = [
            PrepareStep(
                processor_type=ProcessorType.COLUMN_RENAMER,
                params={"inputColumn": "a", "outputColumn": "b"},
            ),
            PrepareStep(
                processor_type=ProcessorType.FILL_EMPTY_WITH_VALUE,
                params={"columns": ["x"], "value": "0"},
            ),
        ]
        settings = PrepareSettings(steps=steps)
        result = settings.to_dss_builder_args()
        assert len(result["steps"]) == 2
        assert result["steps"][0]["type"] == "ColumnRenamer"
        assert result["steps"][1]["type"] == "FillEmptyWithValue"


# ---------------------------------------------------------------------------
# 2. GroupingSettings
# ---------------------------------------------------------------------------
class TestGroupingSettingsBuilderArgs:
    """Tests for GroupingSettings.to_dss_builder_args()."""

    def test_empty(self):
        settings = GroupingSettings()
        result = settings.to_dss_builder_args()
        assert result["keys"] == []
        assert result["values"] == []
        assert result["globalCount"] is False
        assert "engineParams" in result
        assert result["preFilter"] == {}
        assert result["postFilter"] == {}
        assert result["computedColumns"] == []

    def test_keys_have_type_field(self):
        settings = GroupingSettings(keys=["category", "region"])
        result = settings.to_dss_builder_args()
        assert result["keys"] == [
            {"column": "category", "type": "string"},
            {"column": "region", "type": "string"},
        ]

    def test_values_have_idx(self):
        aggs = [
            Aggregation(column="amount", function="SUM"),
            Aggregation(column="count", function="AVG"),
        ]
        settings = GroupingSettings(keys=["category"], aggregations=aggs)
        result = settings.to_dss_builder_args()
        assert len(result["values"]) == 2
        assert result["values"][0]["$idx"] == 0
        assert result["values"][0]["column"] == "amount"
        assert result["values"][0]["function"] == "SUM"
        assert result["values"][1]["$idx"] == 1
        assert result["values"][1]["column"] == "count"
        assert result["values"][1]["function"] == "AVG"

    def test_global_count_true(self):
        settings = GroupingSettings(global_count=True)
        result = settings.to_dss_builder_args()
        assert result["globalCount"] is True

    def test_function_uppercased(self):
        aggs = [Aggregation(column="val", function="sum")]
        settings = GroupingSettings(aggregations=aggs)
        result = settings.to_dss_builder_args()
        assert result["values"][0]["function"] == "SUM"


# ---------------------------------------------------------------------------
# 3. JoinSettings
# ---------------------------------------------------------------------------
class TestJoinSettingsBuilderArgs:
    """Tests for JoinSettings.to_dss_builder_args()."""

    def test_empty(self):
        settings = JoinSettings()
        result = settings.to_dss_builder_args()
        assert result["mode"] == "LEFT"
        assert "engineParams" in result
        assert result["preFilter"] == {}
        assert result["postFilter"] == {}
        assert result["enableAutoCastInJoinConditions"] is False
        assert result["computedColumns"] == []
        assert result["outputColumnsSelectionMode"] == "MANUAL"

    def test_virtual_inputs(self):
        keys = [JoinKey(left_column="id", right_column="id")]
        settings = JoinSettings(join_keys=keys)
        result = settings.to_dss_builder_args()
        assert len(result["virtualInputs"]) == 2
        assert result["virtualInputs"][0]["index"] == 0
        assert result["virtualInputs"][1]["index"] == 1

    def test_join_condition(self):
        keys = [JoinKey(left_column="id", right_column="user_id")]
        settings = JoinSettings(join_type="INNER", join_keys=keys)
        result = settings.to_dss_builder_args()
        assert result["mode"] == "INNER"
        assert len(result["joins"]) == 1
        join = result["joins"][0]
        assert join["table1"] == 0
        assert join["table2"] == 1
        assert join["conditionsMode"] == "AND"
        assert join["type"] == "INNER"
        assert join["outerJoinOnTheLeft"] is True

    def test_selected_columns(self):
        settings = JoinSettings(
            selected_columns={"left": ["id", "name"], "right": ["value"]}
        )
        result = settings.to_dss_builder_args()
        assert result["selectedColumns"] == {
            "left": ["id", "name"],
            "right": ["value"],
        }

    def test_no_selected_columns(self):
        settings = JoinSettings()
        result = settings.to_dss_builder_args()
        assert result["selectedColumns"] == []


# ---------------------------------------------------------------------------
# 4. WindowSettings
# ---------------------------------------------------------------------------
class TestWindowSettingsBuilderArgs:
    """Tests for WindowSettings.to_dss_builder_args()."""

    def test_empty(self):
        settings = WindowSettings()
        result = settings.to_dss_builder_args()
        assert result["partitionColumns"] == []
        assert result["orderColumns"] == []
        assert result["aggregations"] == []

    def test_partition_and_order(self):
        settings = WindowSettings(
            partition_columns=["category"],
            order_columns=["date"],
        )
        result = settings.to_dss_builder_args()
        assert result["partitionColumns"] == [{"column": "category"}]
        assert result["orderColumns"] == [{"column": "date"}]

    def test_aggregations_with_enum_type(self):
        from py2dataiku.models.dataiku_recipe import WindowFunctionType

        aggs = [{"type": WindowFunctionType.RUNNING_SUM, "column": "amount"}]
        settings = WindowSettings(aggregations=aggs)
        result = settings.to_dss_builder_args()
        assert result["aggregations"][0]["type"] == "RUNNING_SUM"
        assert result["aggregations"][0]["column"] == "amount"

    def test_aggregations_with_string_type(self):
        aggs = [{"type": "RANK", "column": "score"}]
        settings = WindowSettings(aggregations=aggs)
        result = settings.to_dss_builder_args()
        assert result["aggregations"][0]["type"] == "RANK"

    def test_multiple_partition_columns(self):
        settings = WindowSettings(
            partition_columns=["region", "category", "year"],
        )
        result = settings.to_dss_builder_args()
        assert len(result["partitionColumns"]) == 3


# ---------------------------------------------------------------------------
# 5. SamplingSettings
# ---------------------------------------------------------------------------
class TestSamplingSettingsBuilderArgs:
    """Tests for SamplingSettings.to_dss_builder_args()."""

    def test_default(self):
        settings = SamplingSettings()
        result = settings.to_dss_builder_args()
        assert result["samplingMethod"] == "RANDOM"
        assert "sampleSize" not in result

    def test_with_sample_size(self):
        settings = SamplingSettings(sample_size=1000)
        result = settings.to_dss_builder_args()
        assert result["samplingMethod"] == "RANDOM"
        assert result["sampleSize"] == 1000

    def test_first_rows(self):
        settings = SamplingSettings(sampling_method="FIRST_ROWS", sample_size=500)
        result = settings.to_dss_builder_args()
        assert result["samplingMethod"] == "FIRST_ROWS"
        assert result["sampleSize"] == 500

    def test_sample_size_zero(self):
        settings = SamplingSettings(sample_size=0)
        result = settings.to_dss_builder_args()
        assert result["sampleSize"] == 0


# ---------------------------------------------------------------------------
# 6. SplitSettings
# ---------------------------------------------------------------------------
class TestSplitSettingsBuilderArgs:
    """Tests for SplitSettings.to_dss_builder_args()."""

    def test_default(self):
        settings = SplitSettings()
        result = settings.to_dss_builder_args()
        assert result["splitMode"] == "FILTER"
        assert result["condition"] == ""

    def test_with_condition(self):
        settings = SplitSettings(condition="val(age) > 18")
        result = settings.to_dss_builder_args()
        assert result["condition"] == "val(age) > 18"

    def test_column_value_mode(self):
        settings = SplitSettings(split_mode="COLUMN_VALUE", condition="status == 'active'")
        result = settings.to_dss_builder_args()
        assert result["splitMode"] == "COLUMN_VALUE"


# ---------------------------------------------------------------------------
# 7. SortSettings
# ---------------------------------------------------------------------------
class TestSortSettingsBuilderArgs:
    """Tests for SortSettings.to_dss_builder_args()."""

    def test_empty(self):
        settings = SortSettings()
        result = settings.to_dss_builder_args()
        assert result["orders"] == []
        assert "engineParams" in result
        assert result["preFilter"] == {}
        assert result["computedColumns"] == []

    def test_single_ascending(self):
        settings = SortSettings(sort_columns=[{"column": "name", "order": "asc"}])
        result = settings.to_dss_builder_args()
        assert len(result["orders"]) == 1
        assert result["orders"][0]["column"] == "name"
        assert result["orders"][0]["desc"] is False

    def test_single_descending(self):
        settings = SortSettings(sort_columns=[{"column": "price", "order": "desc"}])
        result = settings.to_dss_builder_args()
        assert result["orders"][0]["column"] == "price"
        assert result["orders"][0]["desc"] is True

    def test_multiple_columns(self):
        settings = SortSettings(
            sort_columns=[
                {"column": "category", "order": "asc"},
                {"column": "amount", "order": "desc"},
            ]
        )
        result = settings.to_dss_builder_args()
        assert len(result["orders"]) == 2
        assert result["orders"][0]["desc"] is False
        assert result["orders"][1]["desc"] is True

    def test_default_order_is_asc(self):
        settings = SortSettings(sort_columns=[{"column": "x"}])
        result = settings.to_dss_builder_args()
        assert result["orders"][0]["desc"] is False


# ---------------------------------------------------------------------------
# 8. TopNSettings
# ---------------------------------------------------------------------------
class TestTopNSettingsBuilderArgs:
    """Tests for TopNSettings.to_dss_builder_args()."""

    def test_default(self):
        settings = TopNSettings()
        result = settings.to_dss_builder_args()
        assert result["topN"] == 10
        assert result["rankingColumn"] is None

    def test_custom(self):
        settings = TopNSettings(top_n=5, ranking_column="score")
        result = settings.to_dss_builder_args()
        assert result["topN"] == 5
        assert result["rankingColumn"] == "score"

    def test_top_n_one(self):
        settings = TopNSettings(top_n=1, ranking_column="revenue")
        result = settings.to_dss_builder_args()
        assert result["topN"] == 1


# ---------------------------------------------------------------------------
# 9. DistinctSettings
# ---------------------------------------------------------------------------
class TestDistinctSettingsBuilderArgs:
    """Tests for DistinctSettings.to_dss_builder_args()."""

    def test_default(self):
        settings = DistinctSettings()
        result = settings.to_dss_builder_args()
        assert "engineParams" in result
        assert result["columns"] == []
        assert result["preFilter"] == {}
        assert result["computedColumns"] == []
        assert result["postFilter"] == {}

    def test_compute_count_not_in_builder_args(self):
        settings = DistinctSettings(compute_count=True)
        result = settings.to_dss_builder_args()
        assert "computeCount" not in result


# ---------------------------------------------------------------------------
# 10. StackSettings
# ---------------------------------------------------------------------------
class TestStackSettingsBuilderArgs:
    """Tests for StackSettings.to_dss_builder_args()."""

    def test_default(self):
        settings = StackSettings()
        result = settings.to_dss_builder_args()
        assert result["mode"] == "UNION"

    def test_custom_mode(self):
        settings = StackSettings(mode="INTERSECT")
        result = settings.to_dss_builder_args()
        assert result["mode"] == "INTERSECT"


# ---------------------------------------------------------------------------
# 11. PythonSettings
# ---------------------------------------------------------------------------
class TestPythonSettingsBuilderArgs:
    """Tests for PythonSettings.to_dss_builder_args()."""

    def test_empty_code(self):
        settings = PythonSettings()
        result = settings.to_dss_builder_args()
        assert result["code"] == ""
        assert result["envSelection"] == {"envMode": "INHERIT"}
        assert result["pythonParams"]["pythonVersion"] == "python3"
        assert result["pythonParams"]["runAsUser"] is False

    def test_with_code(self):
        code = "import dataiku\ndf = dataiku.Dataset('input').get_dataframe()"
        settings = PythonSettings(code=code)
        result = settings.to_dss_builder_args()
        assert result["code"] == code

    def test_env_selection_present(self):
        settings = PythonSettings(code="pass")
        result = settings.to_dss_builder_args()
        assert "envSelection" in result
        assert result["envSelection"]["envMode"] == "INHERIT"


# ---------------------------------------------------------------------------
# 12. PivotSettings
# ---------------------------------------------------------------------------
class TestPivotSettingsBuilderArgs:
    """Tests for PivotSettings.to_dss_builder_args()."""

    def test_default(self):
        settings = PivotSettings()
        result = settings.to_dss_builder_args()
        assert result["rowColumns"] == []
        assert result["columnColumn"] == ""
        assert result["valueColumn"] == ""
        assert result["aggregation"] == "SUM"

    def test_custom(self):
        settings = PivotSettings(
            row_columns=["region", "year"],
            column_column="product",
            value_column="revenue",
            aggregation="AVG",
        )
        result = settings.to_dss_builder_args()
        assert result["rowColumns"] == ["region", "year"]
        assert result["columnColumn"] == "product"
        assert result["valueColumn"] == "revenue"
        assert result["aggregation"] == "AVG"


# ---------------------------------------------------------------------------
# Cross-cutting: every subclass implements to_dss_builder_args
# ---------------------------------------------------------------------------
class TestAllSubclassesImplement:
    """Verify all 12 subclasses implement to_dss_builder_args and return dicts."""

    @pytest.mark.parametrize(
        "cls",
        [
            PrepareSettings,
            GroupingSettings,
            JoinSettings,
            WindowSettings,
            SamplingSettings,
            SplitSettings,
            SortSettings,
            TopNSettings,
            DistinctSettings,
            StackSettings,
            PythonSettings,
            PivotSettings,
        ],
    )
    def test_returns_dict(self, cls):
        instance = cls()
        result = instance.to_dss_builder_args()
        assert isinstance(result, dict)

    @pytest.mark.parametrize(
        "cls",
        [
            PrepareSettings,
            GroupingSettings,
            JoinSettings,
            WindowSettings,
            SamplingSettings,
            SplitSettings,
            SortSettings,
            TopNSettings,
            DistinctSettings,
            StackSettings,
            PythonSettings,
            PivotSettings,
        ],
    )
    def test_to_dss_builder_args_differs_from_to_dict_where_expected(self, cls):
        """Verify that to_dss_builder_args() is callable alongside to_dict()."""
        instance = cls()
        builder = instance.to_dss_builder_args()
        display = instance.to_dict()
        assert isinstance(builder, dict)
        assert isinstance(display, dict)
