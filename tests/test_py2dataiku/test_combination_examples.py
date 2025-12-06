"""
Comprehensive tests for all combination examples.

This module tests that all combination examples (recipe combinations and
processor combinations) can be successfully converted by py2dataiku and
generate valid Dataiku flow configurations.
"""

import pytest
from py2dataiku import convert
from py2dataiku.examples.combination_examples import (
    COMBINATION_EXAMPLES,
    get_combination_example,
    list_combination_examples,
)
from py2dataiku.examples.settings_examples import (
    SETTINGS_EXAMPLES,
    get_settings_example,
    list_settings_examples,
)


class TestCombinationExamplesRegistry:
    """Test the combination examples registry."""

    def test_combination_examples_dict_not_empty(self):
        """Test that COMBINATION_EXAMPLES is not empty."""
        assert len(COMBINATION_EXAMPLES) > 0

    def test_list_combination_examples_returns_list(self):
        """Test that list_combination_examples returns a list."""
        examples = list_combination_examples()
        assert isinstance(examples, list)
        assert len(examples) > 0

    def test_all_examples_are_strings(self):
        """Test that all examples are non-empty strings."""
        for name, code in COMBINATION_EXAMPLES.items():
            assert isinstance(code, str), f"{name} is not a string"
            assert len(code) > 0, f"{name} is empty"

    def test_get_combination_example_returns_code(self):
        """Test get_combination_example returns code."""
        code = get_combination_example("prepare_grouping_prepare")
        assert isinstance(code, str)
        assert len(code) > 0

    def test_get_nonexistent_example_returns_empty(self):
        """Test get_combination_example returns empty for unknown example."""
        code = get_combination_example("nonexistent_combination")
        assert code == ""

    def test_minimum_combination_count(self):
        """Test that we have at least 15 combination examples."""
        assert len(COMBINATION_EXAMPLES) >= 15


class TestSettingsExamplesRegistry:
    """Test the settings examples registry."""

    def test_settings_examples_dict_not_empty(self):
        """Test that SETTINGS_EXAMPLES is not empty."""
        assert len(SETTINGS_EXAMPLES) > 0

    def test_list_settings_examples_returns_list(self):
        """Test that list_settings_examples returns a list."""
        examples = list_settings_examples()
        assert isinstance(examples, list)
        assert len(examples) > 0

    def test_all_settings_examples_are_strings(self):
        """Test that all settings examples are non-empty strings."""
        for name, code in SETTINGS_EXAMPLES.items():
            assert isinstance(code, str), f"{name} is not a string"
            assert len(code) > 0, f"{name} is empty"


class TestCombinationExamplesConversion:
    """Test that all combination examples convert successfully."""

    @pytest.mark.parametrize("example_name,example_code", list(COMBINATION_EXAMPLES.items()))
    def test_combination_converts_successfully(self, example_name, example_code):
        """Test that each combination example converts without error."""
        flow = convert(example_code)
        assert flow is not None
        assert hasattr(flow, 'to_dict') or hasattr(flow, 'recipes')

    @pytest.mark.parametrize("example_name,example_code", list(COMBINATION_EXAMPLES.items()))
    def test_combination_produces_flow(self, example_name, example_code):
        """Test that each combination example produces a flow."""
        flow = convert(example_code)
        # Should be able to convert to dict
        result = flow.to_dict()
        assert isinstance(result, dict)


class TestSettingsExamplesConversion:
    """Test that all settings examples convert successfully."""

    @pytest.mark.parametrize("example_name,example_code", list(SETTINGS_EXAMPLES.items()))
    def test_settings_converts_successfully(self, example_name, example_code):
        """Test that each settings example converts without error."""
        flow = convert(example_code)
        assert flow is not None


class TestRecipeCombinations:
    """Test specific recipe combination examples."""

    def test_prepare_grouping_prepare_has_all_operations(self):
        """Test PREPARE -> GROUPING -> PREPARE combination."""
        code = COMBINATION_EXAMPLES["prepare_grouping_prepare"]
        assert "groupby" in code
        assert "str." in code or "fillna" in code
        flow = convert(code)
        assert flow is not None

    def test_join_window_split_has_all_operations(self):
        """Test JOIN -> WINDOW -> SPLIT combination."""
        code = COMBINATION_EXAMPLES["join_window_split"]
        assert "merge" in code
        assert "cumsum" in code or "cumcount" in code
        # Split via boolean indexing
        assert "==" in code
        flow = convert(code)
        assert flow is not None

    def test_stack_distinct_sort_has_all_operations(self):
        """Test STACK -> DISTINCT -> SORT combination."""
        code = COMBINATION_EXAMPLES["stack_distinct_sort"]
        assert "concat" in code
        assert "drop_duplicates" in code
        assert "sort_values" in code
        flow = convert(code)
        assert flow is not None

    def test_grouping_pivot_prepare_has_all_operations(self):
        """Test GROUPING -> PIVOT -> PREPARE combination."""
        code = COMBINATION_EXAMPLES["grouping_pivot_prepare"]
        assert "groupby" in code
        assert "pivot" in code
        assert "fillna" in code or "round" in code
        flow = convert(code)
        assert flow is not None

    def test_split_join_grouping_has_all_operations(self):
        """Test SPLIT -> JOIN -> GROUPING combination."""
        code = COMBINATION_EXAMPLES["split_join_grouping"]
        # Split via filtering
        assert ">=" in code or "==" in code
        assert "merge" in code
        assert "groupby" in code
        flow = convert(code)
        assert flow is not None

    def test_multi_join_grouping_has_multiple_joins(self):
        """Test multiple JOINs followed by GROUPING."""
        code = COMBINATION_EXAMPLES["multi_join_grouping"]
        # Should have multiple merge calls
        assert code.count("merge") >= 2
        assert "groupby" in code
        flow = convert(code)
        assert flow is not None

    def test_full_etl_pipeline_is_comprehensive(self):
        """Test full ETL pipeline has many operations."""
        code = COMBINATION_EXAMPLES["full_etl_pipeline"]
        # Should have multiple operation types
        assert "merge" in code
        assert "groupby" in code
        assert "str." in code
        assert "fillna" in code or "dropna" in code
        flow = convert(code)
        assert flow is not None


class TestProcessorCombinations:
    """Test specific processor combination examples."""

    def test_text_pipeline_has_string_operations(self):
        """Test text pipeline has string operations."""
        code = COMBINATION_EXAMPLES["text_pipeline"]
        assert "str." in code
        assert "fillna" in code
        assert "astype" in code
        flow = convert(code)
        assert flow is not None

    def test_date_pipeline_has_date_operations(self):
        """Test date pipeline has date operations."""
        code = COMBINATION_EXAMPLES["date_pipeline"]
        assert "to_datetime" in code
        assert ".dt." in code
        flow = convert(code)
        assert flow is not None

    def test_column_pipeline_has_column_operations(self):
        """Test column pipeline has column operations."""
        code = COMBINATION_EXAMPLES["column_pipeline"]
        assert "rename" in code
        assert "drop" in code
        flow = convert(code)
        assert flow is not None

    def test_numeric_pipeline_has_numeric_operations(self):
        """Test numeric pipeline has numeric operations."""
        code = COMBINATION_EXAMPLES["numeric_pipeline"]
        assert "log" in code.lower() or "np.log" in code
        assert "round" in code
        assert "clip" in code
        flow = convert(code)
        assert flow is not None

    def test_cleaning_pipeline_has_cleaning_operations(self):
        """Test cleaning pipeline has cleaning operations."""
        code = COMBINATION_EXAMPLES["cleaning_pipeline"]
        assert "fillna" in code
        assert "dropna" in code
        assert "drop_duplicates" in code
        flow = convert(code)
        assert flow is not None

    def test_flagging_pipeline_has_flag_operations(self):
        """Test flagging pipeline has flagging operations."""
        code = COMBINATION_EXAMPLES["flagging_pipeline"]
        assert "astype(int)" in code
        assert "apply" in code or "==" in code
        flow = convert(code)
        assert flow is not None

    def test_ml_prep_pipeline_has_ml_operations(self):
        """Test ML prep pipeline has ML preprocessing."""
        code = COMBINATION_EXAMPLES["ml_prep_pipeline"]
        assert "astype" in code
        assert "get_dummies" in code or "mean()" in code
        flow = convert(code)
        assert flow is not None


class TestAllProcessorTypes:
    """Test examples that cover all processor types of a category."""

    def test_all_filter_processors(self):
        """Test all filter processors example."""
        code = COMBINATION_EXAMPLES["all_filter_processors"]
        assert "==" in code  # FILTER_ON_VALUE
        assert "&" in code or "|" in code  # FILTER_ON_FORMULA
        assert ">=" in code  # Date/numeric range
        assert "between" in code  # FILTER_ON_NUMERIC_RANGE
        flow = convert(code)
        assert flow is not None

    def test_all_flag_processors(self):
        """Test all flag processors example."""
        code = COMBINATION_EXAMPLES["all_flag_processors"]
        assert "astype(int)" in code
        # Should have multiple flag columns
        assert code.count("astype(int)") >= 3
        flow = convert(code)
        assert flow is not None

    def test_all_missing_value_processors(self):
        """Test all missing value processors example."""
        code = COMBINATION_EXAMPLES["all_missing_value_processors"]
        assert "fillna" in code
        assert "ffill" in code or "bfill" in code
        assert "dropna" in code
        flow = convert(code)
        assert flow is not None


class TestJoinTypeSettings:
    """Test all join type settings examples."""

    def test_inner_join_settings(self):
        """Test inner join settings."""
        code = SETTINGS_EXAMPLES["join_inner"]
        assert "how='inner'" in code
        flow = convert(code)
        assert flow is not None

    def test_left_join_settings(self):
        """Test left join settings."""
        code = SETTINGS_EXAMPLES["join_left"]
        assert "how='left'" in code
        flow = convert(code)
        assert flow is not None

    def test_right_join_settings(self):
        """Test right join settings."""
        code = SETTINGS_EXAMPLES["join_right"]
        assert "how='right'" in code
        flow = convert(code)
        assert flow is not None

    def test_outer_join_settings(self):
        """Test outer join settings."""
        code = SETTINGS_EXAMPLES["join_outer"]
        assert "how='outer'" in code
        flow = convert(code)
        assert flow is not None

    def test_cross_join_settings(self):
        """Test cross join settings."""
        code = SETTINGS_EXAMPLES["join_cross"]
        assert "how='cross'" in code
        flow = convert(code)
        assert flow is not None


class TestAggregationSettings:
    """Test all aggregation function settings examples."""

    def test_sum_aggregation(self):
        """Test SUM aggregation."""
        code = SETTINGS_EXAMPLES["agg_sum"]
        assert "'sum'" in code or '"sum"' in code
        flow = convert(code)
        assert flow is not None

    def test_avg_aggregation(self):
        """Test AVG/MEAN aggregation."""
        code = SETTINGS_EXAMPLES["agg_avg"]
        assert "'mean'" in code or '"mean"' in code
        flow = convert(code)
        assert flow is not None

    def test_count_aggregation(self):
        """Test COUNT aggregation."""
        code = SETTINGS_EXAMPLES["agg_count"]
        assert "'count'" in code or '"count"' in code
        flow = convert(code)
        assert flow is not None

    def test_min_aggregation(self):
        """Test MIN aggregation."""
        code = SETTINGS_EXAMPLES["agg_min"]
        assert "'min'" in code or '"min"' in code
        flow = convert(code)
        assert flow is not None

    def test_max_aggregation(self):
        """Test MAX aggregation."""
        code = SETTINGS_EXAMPLES["agg_max"]
        assert "'max'" in code or '"max"' in code
        flow = convert(code)
        assert flow is not None

    def test_mixed_aggregation(self):
        """Test mixed aggregations."""
        code = SETTINGS_EXAMPLES["agg_mixed"]
        assert "'sum'" in code or '"sum"' in code
        assert "'mean'" in code or '"mean"' in code
        flow = convert(code)
        assert flow is not None


class TestStringModeSettings:
    """Test string transformer mode settings examples."""

    def test_upper_mode(self):
        """Test TO_UPPER mode."""
        code = SETTINGS_EXAMPLES["string_upper"]
        assert ".upper()" in code
        flow = convert(code)
        assert flow is not None

    def test_lower_mode(self):
        """Test TO_LOWER mode."""
        code = SETTINGS_EXAMPLES["string_lower"]
        assert ".lower()" in code
        flow = convert(code)
        assert flow is not None

    def test_title_mode(self):
        """Test TITLECASE mode."""
        code = SETTINGS_EXAMPLES["string_title"]
        assert ".title()" in code
        flow = convert(code)
        assert flow is not None

    def test_trim_mode(self):
        """Test TRIM mode."""
        code = SETTINGS_EXAMPLES["string_trim"]
        assert ".strip()" in code
        flow = convert(code)
        assert flow is not None

    def test_all_string_modes(self):
        """Test all string modes example."""
        code = SETTINGS_EXAMPLES["string_all_modes"]
        assert ".upper()" in code
        assert ".lower()" in code
        assert ".title()" in code
        assert ".strip()" in code
        flow = convert(code)
        assert flow is not None


class TestNumericalModeSettings:
    """Test numerical transformer mode settings examples."""

    def test_multiply_mode(self):
        """Test MULTIPLY mode."""
        code = SETTINGS_EXAMPLES["num_multiply"]
        assert "*" in code
        flow = convert(code)
        assert flow is not None

    def test_divide_mode(self):
        """Test DIVIDE mode."""
        code = SETTINGS_EXAMPLES["num_divide"]
        assert "/" in code
        flow = convert(code)
        assert flow is not None

    def test_add_mode(self):
        """Test ADD mode."""
        code = SETTINGS_EXAMPLES["num_add"]
        assert "+" in code
        flow = convert(code)
        assert flow is not None

    def test_log_mode(self):
        """Test LOG mode."""
        code = SETTINGS_EXAMPLES["num_log"]
        assert "log" in code.lower()
        flow = convert(code)
        assert flow is not None

    def test_all_numerical_modes(self):
        """Test all numerical modes example."""
        code = SETTINGS_EXAMPLES["num_all_modes"]
        assert "*" in code
        assert "/" in code
        assert "+" in code
        assert ".round" in code
        flow = convert(code)
        assert flow is not None


class TestWindowFunctionSettings:
    """Test window function settings examples."""

    def test_row_number_window(self):
        """Test ROW_NUMBER window function."""
        code = SETTINGS_EXAMPLES["window_row_number"]
        assert "cumcount" in code
        flow = convert(code)
        assert flow is not None

    def test_rank_window(self):
        """Test RANK window function."""
        code = SETTINGS_EXAMPLES["window_rank"]
        assert "rank" in code
        flow = convert(code)
        assert flow is not None

    def test_lag_window(self):
        """Test LAG window function."""
        code = SETTINGS_EXAMPLES["window_lag"]
        assert "shift" in code
        flow = convert(code)
        assert flow is not None

    def test_lead_window(self):
        """Test LEAD window function."""
        code = SETTINGS_EXAMPLES["window_lead"]
        assert "shift(-" in code
        flow = convert(code)
        assert flow is not None

    def test_moving_avg_window(self):
        """Test MOVING_AVG window function."""
        code = SETTINGS_EXAMPLES["window_moving_avg"]
        assert "rolling" in code
        assert "mean" in code
        flow = convert(code)
        assert flow is not None


class TestCombinationVisualization:
    """Test that combination examples can be visualized."""

    @pytest.mark.parametrize("example_name", list(COMBINATION_EXAMPLES.keys())[:5])
    def test_svg_visualization(self, example_name):
        """Test SVG visualization for sample combinations."""
        code = COMBINATION_EXAMPLES[example_name]
        flow = convert(code)
        svg = flow.visualize(format="svg")
        assert isinstance(svg, str)

    @pytest.mark.parametrize("example_name", list(COMBINATION_EXAMPLES.keys())[:5])
    def test_mermaid_visualization(self, example_name):
        """Test Mermaid visualization for sample combinations."""
        code = COMBINATION_EXAMPLES[example_name]
        flow = convert(code)
        mermaid = flow.visualize(format="mermaid")
        assert isinstance(mermaid, str)

    @pytest.mark.parametrize("example_name", list(COMBINATION_EXAMPLES.keys())[:5])
    def test_ascii_visualization(self, example_name):
        """Test ASCII visualization for sample combinations."""
        code = COMBINATION_EXAMPLES[example_name]
        flow = convert(code)
        ascii_art = flow.visualize(format="ascii")
        assert isinstance(ascii_art, str)


class TestCombinationExport:
    """Test that combination examples can be exported."""

    @pytest.mark.parametrize("example_name", list(COMBINATION_EXAMPLES.keys())[:5])
    def test_to_dict_export(self, example_name):
        """Test to_dict export for sample combinations."""
        code = COMBINATION_EXAMPLES[example_name]
        flow = convert(code)
        result = flow.to_dict()
        assert isinstance(result, dict)

    @pytest.mark.parametrize("example_name", list(COMBINATION_EXAMPLES.keys())[:5])
    def test_to_json_export(self, example_name):
        """Test to_json export for sample combinations."""
        code = COMBINATION_EXAMPLES[example_name]
        flow = convert(code)
        result = flow.to_json()
        assert isinstance(result, str)
        assert len(result) > 0
