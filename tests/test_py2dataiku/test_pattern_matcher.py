"""Tests for PatternMatcher."""

import pytest

from py2dataiku.parser.pattern_matcher import PatternMatcher, MatchResult
from py2dataiku.models.prepare_step import PrepareStep, ProcessorType, StringTransformerMode


@pytest.fixture
def matcher():
    return PatternMatcher()


# ---------------------------------------------------------------------------
# match_fillna
# ---------------------------------------------------------------------------

class TestMatchFillna:
    """Tests for PatternMatcher.match_fillna()."""

    def test_returns_prepare_step(self, matcher):
        step = matcher.match_fillna("col", 0)
        assert isinstance(step, PrepareStep)

    def test_processor_type_is_fill_empty(self, matcher):
        step = matcher.match_fillna("age", 0)
        assert step.processor_type == ProcessorType.FILL_EMPTY_WITH_VALUE

    def test_column_is_set(self, matcher):
        step = matcher.match_fillna("my_column", "N/A")
        assert step.params["column"] == "my_column"

    def test_value_is_set(self, matcher):
        step = matcher.match_fillna("col", 42)
        assert step.params["value"] == "42"

    def test_string_value(self, matcher):
        step = matcher.match_fillna("col", "UNKNOWN")
        assert step.params["value"] == "UNKNOWN"


# ---------------------------------------------------------------------------
# match_dropna
# ---------------------------------------------------------------------------

class TestMatchDropna:
    """Tests for PatternMatcher.match_dropna()."""

    def test_returns_prepare_step(self, matcher):
        step = matcher.match_dropna([])
        assert isinstance(step, PrepareStep)

    def test_processor_type_is_remove_rows(self, matcher):
        step = matcher.match_dropna(["id"])
        assert step.processor_type == ProcessorType.REMOVE_ROWS_ON_EMPTY

    def test_columns_stored_in_params(self, matcher):
        step = matcher.match_dropna(["a", "b"])
        assert "a" in step.params.get("columns", [])
        assert "b" in step.params.get("columns", [])

    def test_empty_columns_list(self, matcher):
        step = matcher.match_dropna([])
        assert step.processor_type == ProcessorType.REMOVE_ROWS_ON_EMPTY


# ---------------------------------------------------------------------------
# match_drop_duplicates
# ---------------------------------------------------------------------------

class TestMatchDropDuplicates:
    """Tests for PatternMatcher.match_drop_duplicates()."""

    def test_returns_prepare_step(self, matcher):
        step = matcher.match_drop_duplicates()
        assert isinstance(step, PrepareStep)

    def test_processor_type_is_remove_duplicates(self, matcher):
        step = matcher.match_drop_duplicates()
        assert step.processor_type == ProcessorType.REMOVE_DUPLICATES

    def test_no_columns_produces_valid_step(self, matcher):
        step = matcher.match_drop_duplicates()
        assert step is not None

    def test_with_subset_columns(self, matcher):
        step = matcher.match_drop_duplicates(columns=["id", "name"])
        assert step.processor_type == ProcessorType.REMOVE_DUPLICATES


# ---------------------------------------------------------------------------
# match_rename
# ---------------------------------------------------------------------------

class TestMatchRename:
    """Tests for PatternMatcher.match_rename()."""

    def test_returns_prepare_step(self, matcher):
        step = matcher.match_rename({"old": "new"})
        assert isinstance(step, PrepareStep)

    def test_processor_type_is_column_renamer(self, matcher):
        step = matcher.match_rename({"a": "b"})
        assert step.processor_type == ProcessorType.COLUMN_RENAMER

    def test_renamings_param_is_set(self, matcher):
        step = matcher.match_rename({"old_name": "new_name"})
        renamings = step.params.get("renamings", [])
        assert {"from": "old_name", "to": "new_name"} in renamings

    def test_multiple_renames(self, matcher):
        step = matcher.match_rename({"a": "x", "b": "y"})
        renamings = step.params.get("renamings", [])
        assert len(renamings) == 2


# ---------------------------------------------------------------------------
# match_drop_columns
# ---------------------------------------------------------------------------

class TestMatchDropColumns:
    """Tests for PatternMatcher.match_drop_columns()."""

    def test_returns_prepare_step(self, matcher):
        step = matcher.match_drop_columns(["col"])
        assert isinstance(step, PrepareStep)

    def test_processor_type_is_column_deleter(self, matcher):
        step = matcher.match_drop_columns(["col1"])
        assert step.processor_type == ProcessorType.COLUMN_DELETER

    def test_columns_param_is_set(self, matcher):
        step = matcher.match_drop_columns(["a", "b"])
        assert step.params["columns"] == ["a", "b"]


# ---------------------------------------------------------------------------
# match_string_method
# ---------------------------------------------------------------------------

class TestMatchStringMethod:
    """Tests for PatternMatcher.match_string_method()."""

    @pytest.mark.parametrize("method,expected_mode", [
        ("upper", StringTransformerMode.UPPERCASE),
        ("lower", StringTransformerMode.LOWERCASE),
        ("title", StringTransformerMode.TITLECASE),
        ("strip", StringTransformerMode.TRIM),
        ("lstrip", StringTransformerMode.TRIM_LEFT),
        ("rstrip", StringTransformerMode.TRIM_RIGHT),
    ])
    def test_string_methods_return_string_transformer(self, matcher, method, expected_mode):
        step = matcher.match_string_method("col", method)
        assert step is not None
        assert step.processor_type == ProcessorType.STRING_TRANSFORMER

    def test_unknown_method_returns_none(self, matcher):
        step = matcher.match_string_method("col", "zfill")
        assert step is None

    def test_column_is_set_in_params(self, matcher):
        step = matcher.match_string_method("my_col", "upper")
        assert step.params["column"] == "my_col"


# ---------------------------------------------------------------------------
# match_astype
# ---------------------------------------------------------------------------

class TestMatchAstype:
    """Tests for PatternMatcher.match_astype()."""

    def test_returns_prepare_step(self, matcher):
        step = matcher.match_astype("col", "int64")
        assert isinstance(step, PrepareStep)

    def test_processor_type_is_type_setter(self, matcher):
        step = matcher.match_astype("col", "int")
        assert step.processor_type == ProcessorType.TYPE_SETTER

    @pytest.mark.parametrize("dtype,expected", [
        ("int", "bigint"),
        ("int64", "bigint"),
        ("int32", "int"),
        ("float", "double"),
        ("float64", "double"),
        ("str", "string"),
        ("string", "string"),
        ("bool", "boolean"),
        ("datetime64", "date"),
    ])
    def test_dtype_mapping(self, matcher, dtype, expected):
        step = matcher.match_astype("col", dtype)
        assert step.params["type"] == expected

    def test_unknown_dtype_defaults_to_string(self, matcher):
        step = matcher.match_astype("col", "complex128")
        assert step.params["type"] == "string"


# ---------------------------------------------------------------------------
# match_to_datetime
# ---------------------------------------------------------------------------

class TestMatchToDatetime:
    """Tests for PatternMatcher.match_to_datetime()."""

    def test_returns_prepare_step(self, matcher):
        step = matcher.match_to_datetime("date_col")
        assert isinstance(step, PrepareStep)

    def test_processor_type_is_date_parser(self, matcher):
        step = matcher.match_to_datetime("date_col")
        assert step.processor_type == ProcessorType.DATE_PARSER

    def test_column_is_set(self, matcher):
        step = matcher.match_to_datetime("order_date")
        assert step.params["column"] == "order_date"


# ---------------------------------------------------------------------------
# match_filter
# ---------------------------------------------------------------------------

class TestMatchFilter:
    """Tests for PatternMatcher.match_filter()."""

    def test_returns_prepare_step(self, matcher):
        step = matcher.match_filter("status", "==", "active")
        assert isinstance(step, PrepareStep)

    def test_processor_type_is_filter_on_value(self, matcher):
        step = matcher.match_filter("age", ">", 18)
        assert step.processor_type == ProcessorType.FILTER_ON_VALUE

    @pytest.mark.parametrize("operator,expected_mode", [
        ("==", "EQUALS"),
        ("!=", "NOT_EQUALS"),
        (">", "GREATER_THAN"),
        (">=", "GREATER_OR_EQUAL"),
        ("<", "LESS_THAN"),
        ("<=", "LESS_OR_EQUAL"),
        ("in", "IN"),
        ("contains", "CONTAINS"),
    ])
    def test_operator_to_matching_mode(self, matcher, operator, expected_mode):
        step = matcher.match_filter("col", operator, "val")
        assert step.params.get("matchingMode") == expected_mode

    def test_unknown_operator_defaults_to_equals(self, matcher):
        step = matcher.match_filter("col", "~=", "val")
        assert step.params.get("matchingMode") == "EQUALS"

    def test_column_is_set(self, matcher):
        step = matcher.match_filter("my_col", "==", "value")
        assert step.params["column"] == "my_col"


# ---------------------------------------------------------------------------
# match_aggregation
# ---------------------------------------------------------------------------

class TestMatchAggregation:
    """Tests for PatternMatcher.match_aggregation()."""

    @pytest.mark.parametrize("func,expected", [
        ("sum", "SUM"),
        ("mean", "AVG"),
        ("avg", "AVG"),
        ("count", "COUNT"),
        ("min", "MIN"),
        ("max", "MAX"),
        ("first", "FIRST"),
        ("last", "LAST"),
        ("std", "STDDEV"),
        ("var", "VAR"),
        ("median", "MEDIAN"),
    ])
    def test_aggregation_mappings(self, matcher, func, expected):
        result = matcher.match_aggregation(func)
        assert result == expected

    def test_case_insensitive_mapping(self, matcher):
        assert matcher.match_aggregation("SUM") == "SUM"
        assert matcher.match_aggregation("Mean") == "AVG"

    def test_unknown_aggregation_returns_none(self, matcher):
        result = matcher.match_aggregation("mode")
        assert result is None


# ---------------------------------------------------------------------------
# match_join_type
# ---------------------------------------------------------------------------

class TestMatchJoinType:
    """Tests for PatternMatcher.match_join_type()."""

    @pytest.mark.parametrize("pandas_how,expected", [
        ("inner", "INNER"),
        ("left", "LEFT"),
        ("right", "RIGHT"),
        ("outer", "OUTER"),
        ("cross", "CROSS"),
    ])
    def test_join_type_mappings(self, matcher, pandas_how, expected):
        assert matcher.match_join_type(pandas_how) == expected

    def test_unknown_join_type_defaults_to_inner(self, matcher):
        assert matcher.match_join_type("fuzzy") == "INNER"

    def test_case_insensitive(self, matcher):
        assert matcher.match_join_type("LEFT") == "LEFT"
        assert matcher.match_join_type("Inner") == "INNER"


# ---------------------------------------------------------------------------
# match_regex_extract
# ---------------------------------------------------------------------------

class TestMatchRegexExtract:
    """Tests for PatternMatcher.match_regex_extract()."""

    def test_returns_prepare_step(self, matcher):
        step = matcher.match_regex_extract("col", r"(\d+)")
        assert isinstance(step, PrepareStep)

    def test_processor_type_is_regexp_extractor(self, matcher):
        step = matcher.match_regex_extract("col", r"(\w+)")
        assert step.processor_type == ProcessorType.REGEXP_EXTRACTOR

    def test_pattern_is_stored(self, matcher):
        step = matcher.match_regex_extract("col", r"(\d+)")
        assert step.params.get("pattern") == r"(\d+)"

    def test_with_output_columns(self, matcher):
        step = matcher.match_regex_extract("col", r"(\d+)", output_columns=["extracted"])
        assert step is not None


# ---------------------------------------------------------------------------
# match_split
# ---------------------------------------------------------------------------

class TestMatchSplit:
    """Tests for PatternMatcher.match_split()."""

    def test_returns_prepare_step(self, matcher):
        step = matcher.match_split("col", ",")
        assert isinstance(step, PrepareStep)

    def test_processor_type_is_split_column(self, matcher):
        step = matcher.match_split("col", " ")
        assert step.processor_type == ProcessorType.SPLIT_COLUMN

    def test_column_and_separator_stored(self, matcher):
        step = matcher.match_split("full_name", " ")
        assert step.params["column"] == "full_name"
        assert step.params["separator"] == " "


# ---------------------------------------------------------------------------
# requires_python_recipe
# ---------------------------------------------------------------------------

class TestRequiresPythonRecipe:
    """Tests for PatternMatcher.requires_python_recipe()."""

    @pytest.mark.parametrize("method", [
        "apply", "applymap", "transform", "pipe", "eval",
        "query", "assign", "stack", "unstack", "explode",
        "json_normalize",
    ])
    def test_python_only_methods_return_true(self, matcher, method):
        assert matcher.requires_python_recipe(method) is True

    @pytest.mark.parametrize("method", [
        "merge", "groupby", "dropna", "fillna", "rename",
        "sort_values", "drop_duplicates", "astype",
    ])
    def test_mappable_methods_return_false(self, matcher, method):
        assert matcher.requires_python_recipe(method) is False

    def test_unknown_method_returns_false(self, matcher):
        assert matcher.requires_python_recipe("totally_unknown_method") is False
