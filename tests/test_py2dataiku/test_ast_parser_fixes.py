"""Tests for AST parser fixes: C2, H1, H2, H3."""

import pytest

from py2dataiku import convert
from py2dataiku.parser.ast_analyzer import CodeAnalyzer
from py2dataiku.models.transformation import TransformationType
from py2dataiku.models.dataiku_recipe import RecipeType
from py2dataiku.models.prepare_step import ProcessorType


class TestC2GroupbyAggregations:
    """C2: Groupby .agg() with dict should produce non-empty aggregations."""

    def test_groupby_agg_dict_extracts_aggregations(self):
        """groupby('region').agg({'amount': 'sum', 'price': 'mean'}) should
        produce a GROUPBY transformation with aggregations populated."""
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df.groupby('region').agg({'amount': 'sum', 'price': 'mean'})"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        groupby_trans = [
            t for t in transformations
            if t.transformation_type == TransformationType.GROUPBY
        ]
        assert len(groupby_trans) >= 1

        gb = groupby_trans[0]
        aggs = gb.parameters.get("aggregations", {})
        assert len(aggs) > 0, "Aggregations should not be empty"
        assert aggs.get("amount") == "sum"
        assert aggs.get("price") == "mean"

    def test_groupby_agg_dict_extracts_keys(self):
        """Groupby keys should be extracted from the groupby() call."""
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df.groupby('region').agg({'amount': 'sum'})"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        groupby_trans = [
            t for t in transformations
            if t.transformation_type == TransformationType.GROUPBY
        ]
        assert len(groupby_trans) >= 1

        gb = groupby_trans[0]
        keys = gb.parameters.get("keys", [])
        assert "region" in keys

    def test_groupby_agg_produces_grouping_recipe(self):
        """End-to-end: convert() should produce a GROUPING recipe with aggregations."""
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df.groupby('region').agg({'amount': 'sum', 'price': 'mean'})"
        )
        flow = convert(code)
        grouping_recipes = flow.get_recipes_by_type(RecipeType.GROUPING)
        assert len(grouping_recipes) >= 1

        recipe = grouping_recipes[0]
        assert len(recipe.aggregations) > 0, "GROUPING recipe should have non-empty aggregations"

    def test_groupby_agg_multiple_keys(self):
        """Groupby with multiple keys should extract all keys."""
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df.groupby(['region', 'category']).agg({'amount': 'sum'})"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        groupby_trans = [
            t for t in transformations
            if t.transformation_type == TransformationType.GROUPBY
        ]
        assert len(groupby_trans) >= 1

        gb = groupby_trans[0]
        keys = gb.parameters.get("keys", [])
        assert "region" in keys
        assert "category" in keys


class TestH1StringAccessor:
    """H1: String accessor .str.* methods should be detected."""

    def test_str_upper_detected(self):
        """df['col'].str.upper() should produce STRING_TRANSFORM with UPPERCASE mode."""
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df['name'].str.upper()"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        str_trans = [
            t for t in transformations
            if t.transformation_type == TransformationType.STRING_TRANSFORM
        ]
        assert len(str_trans) >= 1

        st = str_trans[0]
        assert st.parameters.get("mode") == "TO_UPPER"
        assert st.columns == ["name"] or st.parameters.get("column") == "name"
        assert st.suggested_processor == "StringTransformer"

    def test_str_lower_detected(self):
        """df['col'].str.lower() should produce STRING_TRANSFORM with LOWERCASE mode."""
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df['city'].str.lower()"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        str_trans = [
            t for t in transformations
            if t.transformation_type == TransformationType.STRING_TRANSFORM
        ]
        assert len(str_trans) >= 1

        st = str_trans[0]
        assert st.parameters.get("mode") == "TO_LOWER"
        assert "city" in st.columns or st.parameters.get("column") == "city"

    def test_str_strip_detected(self):
        """df['col'].str.strip() should produce STRING_TRANSFORM with TRIM mode."""
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df['text'].str.strip()"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        str_trans = [
            t for t in transformations
            if t.transformation_type == TransformationType.STRING_TRANSFORM
        ]
        assert len(str_trans) >= 1

        st = str_trans[0]
        assert st.parameters.get("mode") == "TRIM"
        assert "text" in st.columns or st.parameters.get("column") == "text"

    def test_str_replace_detected(self):
        """df['col'].str.replace(old, new) should map to FindReplace."""
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df['address'].str.replace('St.', 'Street')"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        str_trans = [
            t for t in transformations
            if t.transformation_type == TransformationType.STRING_TRANSFORM
        ]
        assert len(str_trans) >= 1

        st = str_trans[0]
        assert st.suggested_processor == "FindReplace"
        assert st.parameters.get("find") == "St."
        assert st.parameters.get("replace") == "Street"
        assert "address" in st.columns or st.parameters.get("column") == "address"

    def test_str_extract_detected(self):
        """df['col'].str.extract(pattern) should map to RegexpExtractor."""
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df['email'].str.extract(r'@(\\w+)\\.com')"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        str_trans = [
            t for t in transformations
            if t.transformation_type == TransformationType.STRING_TRANSFORM
        ]
        assert len(str_trans) >= 1

        st = str_trans[0]
        assert st.suggested_processor == "RegexpExtractor"
        assert "email" in st.columns or st.parameters.get("column") == "email"

    def test_str_split_detected(self):
        """df['col'].str.split() should map to SplitColumn."""
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df['tags'].str.split(',')"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        str_trans = [
            t for t in transformations
            if t.transformation_type == TransformationType.STRING_TRANSFORM
        ]
        assert len(str_trans) >= 1

        st = str_trans[0]
        assert st.suggested_processor == "SplitColumn"
        assert st.parameters.get("separator") == ","
        assert "tags" in st.columns or st.parameters.get("column") == "tags"


class TestH2ColumnDetection:
    """H2: fillna()/astype() should detect column from subscript context."""

    def test_fillna_column_detected(self):
        """df['age'].fillna(0) should capture column='age'."""
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df['age'].fillna(0)"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        fillna_trans = [
            t for t in transformations
            if t.transformation_type == TransformationType.FILL_NA
        ]
        assert len(fillna_trans) >= 1

        ft = fillna_trans[0]
        column = ft.parameters.get("column", "unknown")
        assert column == "age", f"Expected column='age', got column='{column}'"
        assert ft.parameters.get("value") == 0

    def test_fillna_column_in_columns_list(self):
        """df['age'].fillna(0) should have 'age' in the columns list."""
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df['age'].fillna(0)"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        fillna_trans = [
            t for t in transformations
            if t.transformation_type == TransformationType.FILL_NA
        ]
        assert len(fillna_trans) >= 1
        assert "age" in fillna_trans[0].columns

    def test_astype_column_detected(self):
        """df['col'].astype(int) should capture column='col'."""
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df['price'].astype(float)"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        astype_trans = [
            t for t in transformations
            if t.transformation_type == TransformationType.TYPE_CAST
        ]
        assert len(astype_trans) >= 1

        at = astype_trans[0]
        column = at.parameters.get("column", "unknown")
        assert column == "price", f"Expected column='price', got column='{column}'"

    def test_astype_column_in_columns_list(self):
        """df['price'].astype(float) should have 'price' in the columns list."""
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df['price'].astype(float)"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        astype_trans = [
            t for t in transformations
            if t.transformation_type == TransformationType.TYPE_CAST
        ]
        assert len(astype_trans) >= 1
        assert "price" in astype_trans[0].columns

    def test_fillna_without_subscript_gets_unknown(self):
        """df.fillna(0) (no column subscript) should get column='unknown'."""
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df.fillna(0)"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        fillna_trans = [
            t for t in transformations
            if t.transformation_type == TransformationType.FILL_NA
        ]
        assert len(fillna_trans) >= 1
        column = fillna_trans[0].parameters.get("column", "unknown")
        assert column == "unknown"


class TestH3ColumnSelectionVsFilter:
    """H3: Column selection df[['col1','col2']] should NOT map to SPLIT."""

    def test_column_selection_maps_to_column_select(self):
        """df[['col1', 'col2']] should produce COLUMN_SELECT, not FILTER."""
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df[['name', 'age', 'city']]"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        # Should have a COLUMN_SELECT transformation
        col_select = [
            t for t in transformations
            if t.transformation_type == TransformationType.COLUMN_SELECT
        ]
        assert len(col_select) >= 1, "Should produce a COLUMN_SELECT transformation"

        cs = col_select[0]
        assert cs.columns == ["name", "age", "city"]
        assert cs.suggested_processor == "ColumnsSelector"

        # Should NOT have a FILTER transformation for this
        filter_trans = [
            t for t in transformations
            if t.transformation_type == TransformationType.FILTER
        ]
        assert len(filter_trans) == 0, "Column selection should not produce FILTER"

    def test_boolean_filter_still_maps_to_filter(self):
        """df[df['age'] > 25] should still produce FILTER."""
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df[df['age'] > 25]"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        filter_trans = [
            t for t in transformations
            if t.transformation_type == TransformationType.FILTER
        ]
        assert len(filter_trans) >= 1, "Boolean condition should produce FILTER"

    def test_column_selection_end_to_end(self):
        """End-to-end: column selection should produce PREPARE recipe, not SPLIT."""
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df[['name', 'age']]"
        )
        flow = convert(code)

        # Should NOT produce a SPLIT recipe
        split_recipes = flow.get_recipes_by_type(RecipeType.SPLIT)
        assert len(split_recipes) == 0, "Column selection should not produce SPLIT recipe"

        # Should produce a PREPARE recipe with ColumnsSelector
        prepare_recipes = flow.get_recipes_by_type(RecipeType.PREPARE)
        assert len(prepare_recipes) >= 1, "Column selection should produce PREPARE recipe"

        # Check that the prepare recipe contains a ColumnsSelector step
        prep = prepare_recipes[0]
        found_selector = False
        for step in prep.steps:
            if step.processor_type == ProcessorType.COLUMNS_SELECTOR:
                found_selector = True
                assert step.params.get("columns") == ["name", "age"]
                break
        assert found_selector, "Prepare recipe should contain ColumnsSelector step"

    def test_single_column_string_subscript_not_column_select(self):
        """df['col'] (single string) is column access, not column selection list.
        This should NOT produce COLUMN_SELECT."""
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df['age']"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        col_select = [
            t for t in transformations
            if t.transformation_type == TransformationType.COLUMN_SELECT
        ]
        # Single string subscript is not a list, so it should NOT be COLUMN_SELECT
        assert len(col_select) == 0


class TestCombinedFixes:
    """Test that all fixes work together in a more complex scenario."""

    def test_pipeline_with_all_fixes(self):
        """Test a pipeline that exercises all four fixes."""
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('sales.csv')\n"
            # H3: column selection
            "df2 = df[['region', 'amount', 'product', 'notes']]\n"
            # H2: fillna with column detection
            "df3 = df2['amount'].fillna(0)\n"
            # H1: string accessor
            "df4 = df2['notes'].str.upper()\n"
            # C2: groupby with agg dict
            "result = df2.groupby('region').agg({'amount': 'sum'})\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        # Check H3: column selection
        col_selects = [
            t for t in transformations
            if t.transformation_type == TransformationType.COLUMN_SELECT
        ]
        assert len(col_selects) >= 1

        # Check H2: fillna column
        fillna_trans = [
            t for t in transformations
            if t.transformation_type == TransformationType.FILL_NA
        ]
        if fillna_trans:
            assert fillna_trans[0].parameters.get("column") == "amount"

        # Check H1: string accessor
        str_trans = [
            t for t in transformations
            if t.transformation_type == TransformationType.STRING_TRANSFORM
        ]
        assert len(str_trans) >= 1

        # Check C2: groupby aggregations
        groupby_trans = [
            t for t in transformations
            if t.transformation_type == TransformationType.GROUPBY
        ]
        assert len(groupby_trans) >= 1
        aggs = groupby_trans[0].parameters.get("aggregations", {})
        assert len(aggs) > 0
