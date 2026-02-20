"""Tests for ProcessorCatalog."""

import pytest

from py2dataiku.mappings.processor_catalog import ProcessorCatalog, ProcessorInfo


class TestGetProcessor:
    """Tests for ProcessorCatalog.get_processor()."""

    def test_get_known_processor_returns_info(self):
        info = ProcessorCatalog.get_processor("ColumnRenamer")
        assert info is not None
        assert isinstance(info, ProcessorInfo)

    def test_get_unknown_processor_returns_none(self):
        info = ProcessorCatalog.get_processor("NonExistentProcessor")
        assert info is None

    def test_get_fill_empty_with_value(self):
        info = ProcessorCatalog.get_processor("FillEmptyWithValue")
        assert info is not None
        assert info.name == "FillEmptyWithValue"

    def test_get_string_transformer(self):
        info = ProcessorCatalog.get_processor("StringTransformer")
        assert info is not None
        assert "String" in info.category

    def test_get_filter_on_value(self):
        info = ProcessorCatalog.get_processor("FilterOnValue")
        assert info is not None

    def test_get_type_setter(self):
        info = ProcessorCatalog.get_processor("TypeSetter")
        assert info is not None

    @pytest.mark.parametrize("name", [
        "ColumnRenamer", "ColumnCopier", "ColumnDeleter", "ColumnsSelector",
        "FillEmptyWithValue", "RemoveRowsOnEmpty", "FillEmptyWithPreviousNext",
        "StringTransformer", "FindReplace", "RegexpExtractor", "SplitColumn",
        "ConcatColumns", "Tokenizer", "NumericalTransformer", "RoundColumn",
        "Binner", "Normalizer", "TypeSetter", "DateParser", "DateFormatter",
        "FilterOnValue", "FilterOnFormula", "FilterOnNumericRange",
        "RemoveDuplicates", "SortRows", "CreateColumnWithGREL", "Formula",
        "FlagOnValue", "MergeLongTailValues", "PythonUDF",
    ])
    def test_all_catalog_processors_are_retrievable(self, name):
        info = ProcessorCatalog.get_processor(name)
        assert info is not None, f"{name} should be in catalog"


class TestListProcessors:
    """Tests for ProcessorCatalog.list_processors()."""

    def test_list_all_returns_non_empty(self):
        names = ProcessorCatalog.list_processors()
        assert len(names) > 0

    def test_list_all_returns_list_of_strings(self):
        names = ProcessorCatalog.list_processors()
        assert all(isinstance(n, str) for n in names)

    def test_list_with_valid_category_filters(self):
        names = ProcessorCatalog.list_processors(category="Column Manipulation")
        assert len(names) > 0
        # Verify returned processors actually belong to this category
        for name in names:
            info = ProcessorCatalog.get_processor(name)
            assert info.category == "Column Manipulation"

    def test_list_with_unknown_category_returns_empty(self):
        names = ProcessorCatalog.list_processors(category="NonExistentCategory")
        assert names == []

    def test_list_missing_values_category(self):
        names = ProcessorCatalog.list_processors(category="Missing Values")
        assert len(names) > 0

    def test_list_string_operations_category(self):
        names = ProcessorCatalog.list_processors(category="String Operations")
        assert "StringTransformer" in names

    def test_list_numeric_operations_category(self):
        names = ProcessorCatalog.list_processors(category="Numeric Operations")
        assert len(names) > 0

    def test_list_filtering_category(self):
        names = ProcessorCatalog.list_processors(category="Filtering")
        assert "FilterOnValue" in names

    def test_list_no_category_includes_all_processors(self):
        all_names = ProcessorCatalog.list_processors()
        for category in ProcessorCatalog.list_categories():
            category_names = ProcessorCatalog.list_processors(category=category)
            for name in category_names:
                assert name in all_names


class TestGetRequiredParams:
    """Tests for ProcessorCatalog.get_required_params()."""

    def test_column_renamer_requires_renamings(self):
        params = ProcessorCatalog.get_required_params("ColumnRenamer")
        assert "renamings" in params

    def test_fill_empty_requires_column_and_value(self):
        params = ProcessorCatalog.get_required_params("FillEmptyWithValue")
        assert "column" in params
        assert "value" in params

    def test_string_transformer_requires_column_and_mode(self):
        params = ProcessorCatalog.get_required_params("StringTransformer")
        assert "column" in params
        assert "mode" in params

    def test_filter_on_value_requires_column_matching_mode_values(self):
        params = ProcessorCatalog.get_required_params("FilterOnValue")
        assert "column" in params
        assert "matchingMode" in params
        assert "values" in params

    def test_unknown_processor_returns_empty_list(self):
        params = ProcessorCatalog.get_required_params("NoSuchProcessor")
        assert params == []

    def test_returns_list(self):
        params = ProcessorCatalog.get_required_params("ColumnRenamer")
        assert isinstance(params, list)


class TestGetExample:
    """Tests for ProcessorCatalog.get_example()."""

    def test_column_renamer_example_has_renamings(self):
        example = ProcessorCatalog.get_example("ColumnRenamer")
        assert "renamings" in example

    def test_fill_empty_example_has_column_and_value(self):
        example = ProcessorCatalog.get_example("FillEmptyWithValue")
        assert "column" in example
        assert "value" in example

    def test_unknown_processor_returns_empty_dict(self):
        example = ProcessorCatalog.get_example("NoSuchProcessor")
        assert example == {}

    def test_returns_dict(self):
        example = ProcessorCatalog.get_example("StringTransformer")
        assert isinstance(example, dict)

    def test_all_processors_have_examples(self):
        for name in ProcessorCatalog.list_processors():
            example = ProcessorCatalog.get_example(name)
            assert isinstance(example, dict), f"{name} example should be a dict"


class TestListCategories:
    """Tests for ProcessorCatalog.list_categories()."""

    def test_returns_non_empty_list(self):
        categories = ProcessorCatalog.list_categories()
        assert len(categories) > 0

    def test_returns_sorted_list(self):
        categories = ProcessorCatalog.list_categories()
        assert categories == sorted(categories)

    def test_contains_expected_categories(self):
        categories = ProcessorCatalog.list_categories()
        assert "Column Manipulation" in categories
        assert "Missing Values" in categories
        assert "String Operations" in categories
