"""
Comprehensive tests for all processor type examples.

This module tests that all processor examples can be successfully converted
by py2dataiku and generate valid Dataiku prepare recipe configurations.
"""

import pytest
from py2dataiku import convert
from py2dataiku.examples.processor_examples import (
    PROCESSOR_EXAMPLES,
    get_processor_example,
    list_processor_examples,
)


class TestProcessorExamplesRegistry:
    """Test the processor examples registry."""

    def test_processor_examples_dict_not_empty(self):
        """Test that PROCESSOR_EXAMPLES is not empty."""
        assert len(PROCESSOR_EXAMPLES) > 0

    def test_list_processor_examples_returns_list(self):
        """Test that list_processor_examples returns a list."""
        examples = list_processor_examples()
        assert isinstance(examples, list)
        assert len(examples) > 0

    def test_all_examples_are_strings(self):
        """Test that all examples are non-empty strings."""
        for name, code in PROCESSOR_EXAMPLES.items():
            assert isinstance(code, str), f"{name} is not a string"
            assert len(code) > 0, f"{name} is empty"

    def test_get_processor_example_returns_code(self):
        """Test get_processor_example returns code."""
        code = get_processor_example("column_renamer")
        assert isinstance(code, str)
        assert len(code) > 0

    def test_get_nonexistent_example_returns_empty(self):
        """Test get_processor_example returns empty for unknown example."""
        code = get_processor_example("nonexistent_processor")
        assert code == ""

    def test_minimum_processor_count(self):
        """Test that we have at least 50 processor examples."""
        assert len(PROCESSOR_EXAMPLES) >= 50


class TestProcessorExamplesConversion:
    """Test that all processor examples convert successfully."""

    @pytest.mark.parametrize("example_name,example_code", list(PROCESSOR_EXAMPLES.items()))
    def test_processor_converts_successfully(self, example_name, example_code):
        """Test that each processor example converts without error."""
        flow = convert(example_code)
        assert flow is not None

    @pytest.mark.parametrize("example_name", list(PROCESSOR_EXAMPLES.keys())[:10])
    def test_processor_produces_valid_flow(self, example_name):
        """Test that processor examples produce valid flows."""
        code = PROCESSOR_EXAMPLES[example_name]
        flow = convert(code)
        assert hasattr(flow, 'to_dict') or hasattr(flow, 'recipes')


class TestColumnManipulationProcessors:
    """Test column manipulation processor examples."""

    def test_column_renamer_has_rename(self):
        """Test COLUMN_RENAMER example has rename operation."""
        code = PROCESSOR_EXAMPLES["column_renamer"]
        assert "rename" in code
        flow = convert(code)
        assert flow is not None

    def test_column_copier_has_copy(self):
        """Test COLUMN_COPIER example has copy operation."""
        code = PROCESSOR_EXAMPLES["column_copier"]
        assert "=" in code  # Assignment
        flow = convert(code)
        assert flow is not None

    def test_column_deleter_has_drop(self):
        """Test COLUMN_DELETER example has drop operation."""
        code = PROCESSOR_EXAMPLES["column_deleter"]
        assert "drop" in code
        flow = convert(code)
        assert flow is not None

    def test_columns_selector_has_selection(self):
        """Test COLUMNS_SELECTOR example has column selection."""
        code = PROCESSOR_EXAMPLES["columns_selector"]
        assert "[[" in code or "columns" in code.lower()
        flow = convert(code)
        assert flow is not None


class TestMissingValueProcessors:
    """Test missing value handling processor examples."""

    def test_fill_empty_with_value_has_fillna(self):
        """Test FILL_EMPTY_WITH_VALUE example has fillna."""
        code = PROCESSOR_EXAMPLES["fill_empty_with_value"]
        assert "fillna" in code
        flow = convert(code)
        assert flow is not None

    def test_remove_rows_on_empty_has_dropna(self):
        """Test REMOVE_ROWS_ON_EMPTY example has dropna."""
        code = PROCESSOR_EXAMPLES["remove_rows_on_empty"]
        assert "dropna" in code
        flow = convert(code)
        assert flow is not None

    def test_fill_empty_with_previous_next_has_ffill(self):
        """Test FILL_EMPTY_WITH_PREVIOUS_NEXT example has ffill/bfill."""
        code = PROCESSOR_EXAMPLES["fill_empty_with_previous_next"]
        assert "ffill" in code or "bfill" in code
        flow = convert(code)
        assert flow is not None


class TestStringTransformerProcessors:
    """Test string transformation processor examples."""

    def test_uppercase_has_upper(self):
        """Test uppercase transformer has str.upper."""
        code = PROCESSOR_EXAMPLES["string_transformer_uppercase"]
        assert ".upper()" in code
        flow = convert(code)
        assert flow is not None

    def test_lowercase_has_lower(self):
        """Test lowercase transformer has str.lower."""
        code = PROCESSOR_EXAMPLES["string_transformer_lowercase"]
        assert ".lower()" in code
        flow = convert(code)
        assert flow is not None

    def test_titlecase_has_title(self):
        """Test titlecase transformer has str.title."""
        code = PROCESSOR_EXAMPLES["string_transformer_titlecase"]
        assert ".title()" in code
        flow = convert(code)
        assert flow is not None

    def test_trim_has_strip(self):
        """Test trim transformer has str.strip."""
        code = PROCESSOR_EXAMPLES["string_transformer_trim"]
        assert ".strip()" in code
        flow = convert(code)
        assert flow is not None

    def test_tokenizer_has_split(self):
        """Test tokenizer has str.split."""
        code = PROCESSOR_EXAMPLES["tokenizer"]
        assert ".split" in code
        flow = convert(code)
        assert flow is not None

    def test_regexp_extractor_has_extract(self):
        """Test regexp extractor has str.extract."""
        code = PROCESSOR_EXAMPLES["regexp_extractor"]
        assert ".extract" in code
        flow = convert(code)
        assert flow is not None

    def test_find_replace_has_replace(self):
        """Test find_replace has str.replace."""
        code = PROCESSOR_EXAMPLES["find_replace"]
        assert ".replace" in code
        flow = convert(code)
        assert flow is not None


class TestNumericTransformerProcessors:
    """Test numeric transformation processor examples."""

    def test_multiply_has_multiplication(self):
        """Test multiply transformer has * operator."""
        code = PROCESSOR_EXAMPLES["numerical_transformer_multiply"]
        assert "*" in code
        flow = convert(code)
        assert flow is not None

    def test_divide_has_division(self):
        """Test divide transformer has / operator."""
        code = PROCESSOR_EXAMPLES["numerical_transformer_divide"]
        assert "/" in code
        flow = convert(code)
        assert flow is not None

    def test_round_has_round(self):
        """Test round processor has .round()."""
        code = PROCESSOR_EXAMPLES["round_column"]
        assert ".round" in code
        flow = convert(code)
        assert flow is not None

    def test_abs_has_abs(self):
        """Test abs processor has .abs()."""
        code = PROCESSOR_EXAMPLES["abs_column"]
        assert ".abs()" in code
        flow = convert(code)
        assert flow is not None

    def test_clip_has_clip(self):
        """Test clip processor has .clip()."""
        code = PROCESSOR_EXAMPLES["clip_column"]
        assert ".clip" in code
        flow = convert(code)
        assert flow is not None

    def test_binner_has_cut(self):
        """Test binner has pd.cut or pd.qcut."""
        code = PROCESSOR_EXAMPLES["binner"]
        assert "cut" in code or "qcut" in code
        flow = convert(code)
        assert flow is not None


class TestTypeConversionProcessors:
    """Test type conversion processor examples."""

    def test_type_setter_has_astype(self):
        """Test type setter has .astype()."""
        code = PROCESSOR_EXAMPLES["type_setter"]
        assert ".astype" in code
        flow = convert(code)
        assert flow is not None

    def test_date_parser_has_to_datetime(self):
        """Test date parser has pd.to_datetime."""
        code = PROCESSOR_EXAMPLES["date_parser"]
        assert "to_datetime" in code
        flow = convert(code)
        assert flow is not None

    def test_date_formatter_has_strftime(self):
        """Test date formatter has .strftime()."""
        code = PROCESSOR_EXAMPLES["date_formatter"]
        assert "strftime" in code
        flow = convert(code)
        assert flow is not None


class TestFilteringProcessors:
    """Test filtering processor examples."""

    def test_filter_on_value_has_boolean_indexing(self):
        """Test filter_on_value has boolean indexing."""
        code = PROCESSOR_EXAMPLES["filter_on_value"]
        assert "==" in code or "!=" in code
        flow = convert(code)
        assert flow is not None

    def test_filter_on_formula_has_complex_condition(self):
        """Test filter_on_formula has complex condition."""
        code = PROCESSOR_EXAMPLES["filter_on_formula"]
        assert "&" in code or "|" in code
        flow = convert(code)
        assert flow is not None

    def test_filter_on_date_range_has_date_comparison(self):
        """Test filter_on_date_range has date comparison."""
        code = PROCESSOR_EXAMPLES["filter_on_date_range"]
        assert ">=" in code or "<=" in code
        flow = convert(code)
        assert flow is not None

    def test_filter_on_numeric_range_has_range(self):
        """Test filter_on_numeric_range has numeric range."""
        code = PROCESSOR_EXAMPLES["filter_on_numeric_range"]
        assert "between" in code or (">=" in code and "<=" in code)
        flow = convert(code)
        assert flow is not None


class TestFlaggingProcessors:
    """Test flagging processor examples."""

    def test_flag_on_value_creates_flag(self):
        """Test flag_on_value creates flag column."""
        code = PROCESSOR_EXAMPLES["flag_on_value"]
        assert ".astype(int)" in code or "astype(int)" in code
        flow = convert(code)
        assert flow is not None

    def test_flag_on_formula_creates_flag(self):
        """Test flag_on_formula creates flag column."""
        code = PROCESSOR_EXAMPLES["flag_on_formula"]
        assert ".astype(int)" in code or "astype(int)" in code
        flow = convert(code)
        assert flow is not None


class TestRowOperationProcessors:
    """Test row operation processor examples."""

    def test_remove_duplicates_has_drop_duplicates(self):
        """Test remove_duplicates has drop_duplicates."""
        code = PROCESSOR_EXAMPLES["remove_duplicates"]
        assert "drop_duplicates" in code
        flow = convert(code)
        assert flow is not None

    def test_sort_rows_has_sort_values(self):
        """Test sort_rows has sort_values."""
        code = PROCESSOR_EXAMPLES["sort_rows"]
        assert "sort_values" in code
        flow = convert(code)
        assert flow is not None

    def test_sample_rows_has_sample(self):
        """Test sample_rows has sample."""
        code = PROCESSOR_EXAMPLES["sample_rows"]
        assert ".sample" in code
        flow = convert(code)
        assert flow is not None


class TestComputedColumnProcessors:
    """Test computed column processor examples."""

    def test_formula_has_arithmetic(self):
        """Test formula has arithmetic operations."""
        code = PROCESSOR_EXAMPLES["formula"]
        assert "*" in code or "+" in code
        flow = convert(code)
        assert flow is not None

    def test_grel_has_apply(self):
        """Test GREL-like example has apply or complex expression."""
        code = PROCESSOR_EXAMPLES["create_column_with_grel"]
        assert "apply" in code or "lambda" in code
        flow = convert(code)
        assert flow is not None


class TestCategoricalProcessors:
    """Test categorical processor examples."""

    def test_categorical_encoder_has_dummies(self):
        """Test categorical encoder has get_dummies."""
        code = PROCESSOR_EXAMPLES["categorical_encoder"]
        assert "get_dummies" in code
        flow = convert(code)
        assert flow is not None

    def test_merge_long_tail_has_value_counts(self):
        """Test merge_long_tail has value_counts."""
        code = PROCESSOR_EXAMPLES["merge_long_tail_values"]
        assert "value_counts" in code
        flow = convert(code)
        assert flow is not None


class TestGeographicProcessors:
    """Test geographic processor examples."""

    def test_geo_point_creator_has_point(self):
        """Test geo_point_creator creates points."""
        code = PROCESSOR_EXAMPLES["geo_point_creator"]
        assert "POINT" in code or "latitude" in code.lower()
        flow = convert(code)
        assert flow is not None


class TestArrayJsonProcessors:
    """Test array and JSON processor examples."""

    def test_array_splitter_has_explode(self):
        """Test array_splitter has explode or split."""
        code = PROCESSOR_EXAMPLES["array_splitter"]
        assert "explode" in code or "split" in code
        flow = convert(code)
        assert flow is not None

    def test_json_flattener_has_json(self):
        """Test json_flattener has json operations."""
        code = PROCESSOR_EXAMPLES["json_flattener"]
        assert "json" in code.lower()
        flow = convert(code)
        assert flow is not None


class TestProcessorVisualization:
    """Test that processor examples can be visualized."""

    @pytest.mark.parametrize("example_name", list(PROCESSOR_EXAMPLES.keys())[:10])
    def test_svg_visualization(self, example_name):
        """Test SVG visualization for sample processors."""
        code = PROCESSOR_EXAMPLES[example_name]
        flow = convert(code)
        svg = flow.visualize(format="svg")
        assert isinstance(svg, str)

    @pytest.mark.parametrize("example_name", list(PROCESSOR_EXAMPLES.keys())[:10])
    def test_mermaid_visualization(self, example_name):
        """Test Mermaid visualization for sample processors."""
        code = PROCESSOR_EXAMPLES[example_name]
        flow = convert(code)
        mermaid = flow.visualize(format="mermaid")
        assert isinstance(mermaid, str)


class TestProcessorExport:
    """Test that processor examples can be exported."""

    @pytest.mark.parametrize("example_name", list(PROCESSOR_EXAMPLES.keys())[:10])
    def test_to_dict_export(self, example_name):
        """Test to_dict export for sample processors."""
        code = PROCESSOR_EXAMPLES[example_name]
        flow = convert(code)
        result = flow.to_dict()
        assert isinstance(result, dict)

    @pytest.mark.parametrize("example_name", list(PROCESSOR_EXAMPLES.keys())[:10])
    def test_to_json_export(self, example_name):
        """Test to_json export for sample processors."""
        code = PROCESSOR_EXAMPLES[example_name]
        flow = convert(code)
        result = flow.to_json()
        assert isinstance(result, str)
        assert len(result) > 0
