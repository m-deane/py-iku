"""Tests for PandasMapper – pandas → Dataiku recipe/processor mappings."""

import pytest

from py2dataiku.mappings.pandas_mappings import PandasMapper
from py2dataiku.models.dataiku_recipe import RecipeType
from py2dataiku.models.prepare_step import PrepareStep, ProcessorType, StringTransformerMode


@pytest.fixture
def mapper():
    return PandasMapper()


# ---------------------------------------------------------------------------
# get_recipe_type
# ---------------------------------------------------------------------------

class TestGetRecipeType:
    """Tests for PandasMapper.get_recipe_type()."""

    def test_merge_maps_to_join(self, mapper):
        assert mapper.get_recipe_type("merge") == RecipeType.JOIN

    def test_join_maps_to_join(self, mapper):
        assert mapper.get_recipe_type("join") == RecipeType.JOIN

    def test_concat_maps_to_stack(self, mapper):
        assert mapper.get_recipe_type("concat") == RecipeType.STACK

    def test_groupby_maps_to_grouping(self, mapper):
        assert mapper.get_recipe_type("groupby") == RecipeType.GROUPING

    def test_pivot_maps_to_pivot(self, mapper):
        assert mapper.get_recipe_type("pivot") == RecipeType.PIVOT

    def test_pivot_table_maps_to_pivot(self, mapper):
        assert mapper.get_recipe_type("pivot_table") == RecipeType.PIVOT

    def test_melt_maps_to_pivot(self, mapper):
        assert mapper.get_recipe_type("melt") == RecipeType.PIVOT

    def test_sort_values_maps_to_sort(self, mapper):
        assert mapper.get_recipe_type("sort_values") == RecipeType.SORT

    def test_drop_duplicates_maps_to_distinct(self, mapper):
        assert mapper.get_recipe_type("drop_duplicates") == RecipeType.DISTINCT

    def test_head_maps_to_top_n(self, mapper):
        assert mapper.get_recipe_type("head") == RecipeType.TOP_N

    def test_nlargest_maps_to_top_n(self, mapper):
        assert mapper.get_recipe_type("nlargest") == RecipeType.TOP_N

    def test_nsmallest_maps_to_top_n(self, mapper):
        assert mapper.get_recipe_type("nsmallest") == RecipeType.TOP_N

    def test_sample_maps_to_sampling(self, mapper):
        assert mapper.get_recipe_type("sample") == RecipeType.SAMPLING

    def test_unknown_method_returns_none(self, mapper):
        assert mapper.get_recipe_type("nonexistent_method") is None

    def test_empty_string_returns_none(self, mapper):
        assert mapper.get_recipe_type("") is None


# ---------------------------------------------------------------------------
# get_processor_type
# ---------------------------------------------------------------------------

class TestGetProcessorType:
    """Tests for PandasMapper.get_processor_type()."""

    def test_fillna_maps_to_fill_empty(self, mapper):
        assert mapper.get_processor_type("fillna") == ProcessorType.FILL_EMPTY_WITH_VALUE

    def test_dropna_maps_to_remove_rows(self, mapper):
        assert mapper.get_processor_type("dropna") == ProcessorType.REMOVE_ROWS_ON_EMPTY

    def test_rename_maps_to_column_renamer(self, mapper):
        assert mapper.get_processor_type("rename") == ProcessorType.COLUMN_RENAMER

    def test_drop_maps_to_column_deleter(self, mapper):
        assert mapper.get_processor_type("drop") == ProcessorType.COLUMN_DELETER

    def test_astype_maps_to_type_setter(self, mapper):
        assert mapper.get_processor_type("astype") == ProcessorType.TYPE_SETTER

    def test_to_datetime_maps_to_date_parser(self, mapper):
        assert mapper.get_processor_type("to_datetime") == ProcessorType.DATE_PARSER

    def test_round_maps_to_round_column(self, mapper):
        assert mapper.get_processor_type("round") == ProcessorType.ROUND_COLUMN

    def test_abs_maps_to_abs_column(self, mapper):
        assert mapper.get_processor_type("abs") == ProcessorType.ABS_COLUMN

    def test_clip_maps_to_clip_column(self, mapper):
        assert mapper.get_processor_type("clip") == ProcessorType.CLIP_COLUMN

    def test_unknown_method_returns_none(self, mapper):
        assert mapper.get_processor_type("nonexistent") is None


# ---------------------------------------------------------------------------
# get_string_mode
# ---------------------------------------------------------------------------

class TestGetStringMode:
    """Tests for PandasMapper.get_string_mode()."""

    def test_upper_returns_uppercase(self, mapper):
        assert mapper.get_string_mode("upper") == StringTransformerMode.UPPERCASE

    def test_lower_returns_lowercase(self, mapper):
        assert mapper.get_string_mode("lower") == StringTransformerMode.LOWERCASE

    def test_title_returns_titlecase(self, mapper):
        assert mapper.get_string_mode("title") == StringTransformerMode.TITLECASE

    def test_capitalize_returns_titlecase(self, mapper):
        assert mapper.get_string_mode("capitalize") == StringTransformerMode.TITLECASE

    def test_strip_returns_trim(self, mapper):
        assert mapper.get_string_mode("strip") == StringTransformerMode.TRIM

    def test_lstrip_returns_trim_left(self, mapper):
        assert mapper.get_string_mode("lstrip") == StringTransformerMode.TRIM_LEFT

    def test_rstrip_returns_trim_right(self, mapper):
        assert mapper.get_string_mode("rstrip") == StringTransformerMode.TRIM_RIGHT

    def test_unknown_method_returns_none(self, mapper):
        assert mapper.get_string_mode("nonexistent") is None


# ---------------------------------------------------------------------------
# get_agg_function
# ---------------------------------------------------------------------------

class TestGetAggFunction:
    """Tests for PandasMapper.get_agg_function()."""

    def test_sum_maps_to_SUM(self, mapper):
        assert mapper.get_agg_function("sum") == "SUM"

    def test_mean_maps_to_AVG(self, mapper):
        assert mapper.get_agg_function("mean") == "AVG"

    def test_average_maps_to_AVG(self, mapper):
        assert mapper.get_agg_function("average") == "AVG"

    def test_avg_maps_to_AVG(self, mapper):
        assert mapper.get_agg_function("avg") == "AVG"

    def test_count_maps_to_COUNT(self, mapper):
        assert mapper.get_agg_function("count") == "COUNT"

    def test_size_maps_to_COUNT(self, mapper):
        assert mapper.get_agg_function("size") == "COUNT"

    def test_min_maps_to_MIN(self, mapper):
        assert mapper.get_agg_function("min") == "MIN"

    def test_max_maps_to_MAX(self, mapper):
        assert mapper.get_agg_function("max") == "MAX"

    def test_first_maps_to_FIRST(self, mapper):
        assert mapper.get_agg_function("first") == "FIRST"

    def test_last_maps_to_LAST(self, mapper):
        assert mapper.get_agg_function("last") == "LAST"

    def test_std_maps_to_STDDEV(self, mapper):
        assert mapper.get_agg_function("std") == "STDDEV"

    def test_var_maps_to_VAR(self, mapper):
        assert mapper.get_agg_function("var") == "VAR"

    def test_median_maps_to_MEDIAN(self, mapper):
        assert mapper.get_agg_function("median") == "MEDIAN"

    def test_nunique_maps_to_COUNTDISTINCT(self, mapper):
        assert mapper.get_agg_function("nunique") == "COUNTDISTINCT"

    def test_case_insensitive(self, mapper):
        assert mapper.get_agg_function("SUM") == "SUM"
        assert mapper.get_agg_function("Mean") == "AVG"

    def test_unknown_func_returns_none(self, mapper):
        assert mapper.get_agg_function("mode") is None


# ---------------------------------------------------------------------------
# get_join_type
# ---------------------------------------------------------------------------

class TestGetJoinType:
    """Tests for PandasMapper.get_join_type()."""

    def test_inner_maps_to_INNER(self, mapper):
        assert mapper.get_join_type("inner") == "INNER"

    def test_left_maps_to_LEFT(self, mapper):
        assert mapper.get_join_type("left") == "LEFT"

    def test_right_maps_to_RIGHT(self, mapper):
        assert mapper.get_join_type("right") == "RIGHT"

    def test_outer_maps_to_OUTER(self, mapper):
        assert mapper.get_join_type("outer") == "OUTER"

    def test_cross_maps_to_CROSS(self, mapper):
        assert mapper.get_join_type("cross") == "CROSS"

    def test_unknown_defaults_to_INNER(self, mapper):
        assert mapper.get_join_type("unknown") == "INNER"

    def test_case_insensitive(self, mapper):
        assert mapper.get_join_type("LEFT") == "LEFT"
        assert mapper.get_join_type("Inner") == "INNER"


# ---------------------------------------------------------------------------
# map_fillna
# ---------------------------------------------------------------------------

class TestMapFillna:
    """Tests for PandasMapper.map_fillna()."""

    def test_simple_value_fill(self, mapper):
        step = mapper.map_fillna("age", 0)
        assert step.processor_type == ProcessorType.FILL_EMPTY_WITH_VALUE
        assert step.params["column"] == "age"

    def test_ffill_method(self, mapper):
        step = mapper.map_fillna("price", None, method="ffill")
        assert step.processor_type == ProcessorType.FILL_EMPTY_WITH_PREVIOUS_NEXT
        assert step.params["direction"] == "PREVIOUS"

    def test_bfill_method(self, mapper):
        step = mapper.map_fillna("price", None, method="bfill")
        assert step.processor_type == ProcessorType.FILL_EMPTY_WITH_PREVIOUS_NEXT
        assert step.params["direction"] == "NEXT"

    def test_returns_prepare_step_instance(self, mapper):
        step = mapper.map_fillna("col", "N/A")
        assert isinstance(step, PrepareStep)


# ---------------------------------------------------------------------------
# map_dropna
# ---------------------------------------------------------------------------

class TestMapDropna:
    """Tests for PandasMapper.map_dropna()."""

    def test_no_subset(self, mapper):
        step = mapper.map_dropna()
        assert step.processor_type == ProcessorType.REMOVE_ROWS_ON_EMPTY

    def test_with_subset(self, mapper):
        step = mapper.map_dropna(subset=["id", "name"])
        assert step.processor_type == ProcessorType.REMOVE_ROWS_ON_EMPTY
        assert "id" in step.params.get("columns", [])

    def test_returns_prepare_step_instance(self, mapper):
        step = mapper.map_dropna()
        assert isinstance(step, PrepareStep)


# ---------------------------------------------------------------------------
# map_rename
# ---------------------------------------------------------------------------

class TestMapRename:
    """Tests for PandasMapper.map_rename()."""

    def test_single_rename(self, mapper):
        step = mapper.map_rename({"old_name": "new_name"})
        assert step.processor_type == ProcessorType.COLUMN_RENAMER
        renamings = step.params["renamings"]
        assert {"from": "old_name", "to": "new_name"} in renamings

    def test_multiple_renames(self, mapper):
        step = mapper.map_rename({"a": "x", "b": "y"})
        renamings = step.params["renamings"]
        assert len(renamings) == 2

    def test_returns_prepare_step_instance(self, mapper):
        step = mapper.map_rename({"col": "new_col"})
        assert isinstance(step, PrepareStep)


# ---------------------------------------------------------------------------
# map_drop_columns
# ---------------------------------------------------------------------------

class TestMapDropColumns:
    """Tests for PandasMapper.map_drop_columns()."""

    def test_single_column(self, mapper):
        step = mapper.map_drop_columns(["col1"])
        assert step.processor_type == ProcessorType.COLUMN_DELETER
        assert "col1" in step.params["columns"]

    def test_multiple_columns(self, mapper):
        step = mapper.map_drop_columns(["a", "b", "c"])
        assert step.params["columns"] == ["a", "b", "c"]

    def test_returns_prepare_step_instance(self, mapper):
        step = mapper.map_drop_columns(["col"])
        assert isinstance(step, PrepareStep)


# ---------------------------------------------------------------------------
# map_astype
# ---------------------------------------------------------------------------

class TestMapAstype:
    """Tests for PandasMapper.map_astype()."""

    @pytest.mark.parametrize("pandas_type,expected", [
        ("int", "bigint"),
        ("int64", "bigint"),
        ("int32", "int"),
        ("float", "double"),
        ("float64", "double"),
        ("str", "string"),
        ("string", "string"),
        ("object", "string"),
        ("bool", "boolean"),
        ("boolean", "boolean"),
        ("datetime64", "date"),
        ("datetime64[ns]", "date"),
    ])
    def test_type_mapping(self, mapper, pandas_type, expected):
        step = mapper.map_astype("col", pandas_type)
        assert step.processor_type == ProcessorType.TYPE_SETTER
        assert step.params["type"] == expected

    def test_unknown_type_defaults_to_string(self, mapper):
        step = mapper.map_astype("col", "unknown_type")
        assert step.params["type"] == "string"

    def test_returns_prepare_step_instance(self, mapper):
        step = mapper.map_astype("col", "int")
        assert isinstance(step, PrepareStep)


# ---------------------------------------------------------------------------
# map_string_method
# ---------------------------------------------------------------------------

class TestMapStringMethod:
    """Tests for PandasMapper.map_string_method()."""

    def test_upper_returns_step(self, mapper):
        step = mapper.map_string_method("name", "upper")
        assert step is not None
        assert step.processor_type == ProcessorType.STRING_TRANSFORMER

    def test_lower_returns_step(self, mapper):
        step = mapper.map_string_method("name", "lower")
        assert step is not None
        assert step.processor_type == ProcessorType.STRING_TRANSFORMER

    def test_strip_returns_step(self, mapper):
        step = mapper.map_string_method("col", "strip")
        assert step is not None

    def test_replace_with_args_returns_find_replace(self, mapper):
        step = mapper.map_string_method("col", "replace", ["old", "new"])
        assert step is not None
        assert step.processor_type == ProcessorType.FIND_REPLACE
        assert step.params["find"] == "old"
        assert step.params["replace"] == "new"

    def test_split_returns_split_column(self, mapper):
        step = mapper.map_string_method("col", "split", [","])
        assert step is not None
        assert step.processor_type == ProcessorType.SPLIT_COLUMN

    def test_extract_with_pattern_returns_regexp_extractor(self, mapper):
        step = mapper.map_string_method("col", "extract", [r"(\d+)"])
        assert step is not None
        assert step.processor_type == ProcessorType.REGEXP_EXTRACTOR

    def test_contains_returns_flag_on_value(self, mapper):
        step = mapper.map_string_method("col", "contains", ["pattern"])
        assert step is not None
        assert step.processor_type == ProcessorType.FLAG_ON_VALUE

    def test_unknown_method_returns_none(self, mapper):
        step = mapper.map_string_method("col", "zfill")
        assert step is None


# ---------------------------------------------------------------------------
# requires_python_recipe
# ---------------------------------------------------------------------------

class TestRequiresPythonRecipe:
    """Tests for PandasMapper.requires_python_recipe()."""

    @pytest.mark.parametrize("method", [
        "apply", "applymap", "transform", "pipe", "eval",
        "query", "assign", "stack", "unstack",
        "json_normalize", "resample", "pct_change",
    ])
    def test_python_only_methods(self, mapper, method):
        assert mapper.requires_python_recipe(method) is True

    @pytest.mark.parametrize("method", [
        "merge", "groupby", "dropna", "fillna", "rename",
        "sort_values", "drop_duplicates", "get_dummies",
        "cut", "qcut", "shift", "rank",
    ])
    def test_non_python_methods(self, mapper, method):
        assert mapper.requires_python_recipe(method) is False


# ---------------------------------------------------------------------------
# get_alternative_suggestion
# ---------------------------------------------------------------------------

class TestGetAlternativeSuggestion:
    """Tests for PandasMapper.get_alternative_suggestion()."""

    def test_apply_returns_suggestion(self, mapper):
        suggestion = mapper.get_alternative_suggestion("apply")
        assert suggestion is not None
        assert isinstance(suggestion, str)

    def test_get_dummies_returns_suggestion(self, mapper):
        suggestion = mapper.get_alternative_suggestion("get_dummies")
        assert suggestion is not None

    def test_cut_returns_suggestion(self, mapper):
        suggestion = mapper.get_alternative_suggestion("cut")
        assert suggestion is not None

    def test_qcut_returns_suggestion(self, mapper):
        suggestion = mapper.get_alternative_suggestion("qcut")
        assert suggestion is not None

    def test_interpolate_returns_suggestion(self, mapper):
        suggestion = mapper.get_alternative_suggestion("interpolate")
        assert suggestion is not None

    def test_shift_returns_suggestion(self, mapper):
        suggestion = mapper.get_alternative_suggestion("shift")
        assert "Window" in mapper.get_alternative_suggestion("shift")

    def test_diff_returns_suggestion(self, mapper):
        assert mapper.get_alternative_suggestion("diff") is not None

    def test_rank_returns_suggestion(self, mapper):
        assert mapper.get_alternative_suggestion("rank") is not None

    def test_unknown_method_returns_none(self, mapper):
        assert mapper.get_alternative_suggestion("merge") is None
