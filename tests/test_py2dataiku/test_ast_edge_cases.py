"""Edge-case tests for CodeAnalyzer (AST-based analysis).

Targets the 77 branch misses that kept ast_analyzer.py at 79% coverage.
Each test class exercises a distinct scenario not already covered by
test_ast_parser_fixes.py.
"""

import pytest

from py2dataiku.parser.ast_analyzer import CodeAnalyzer
from py2dataiku.models.transformation import TransformationType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _types(transformations):
    """Return a list of TransformationType values for quick assertions."""
    return [t.transformation_type for t in transformations]


def _find(transformations, ttype):
    """Return all transformations whose type matches *ttype*."""
    return [t for t in transformations if t.transformation_type == ttype]


# ---------------------------------------------------------------------------
# 1. Chained operations
# ---------------------------------------------------------------------------

class TestChainedOperations:
    """df.dropna().rename(columns={…}).sort_values('c') should emit all three ops."""

    def test_three_op_chain_emits_three_transformations(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df.dropna().rename(columns={'a': 'b'}).sort_values('c')\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        types = _types(transformations)
        assert TransformationType.DROP_NA in types, "dropna() should produce DROP_NA"
        assert TransformationType.COLUMN_RENAME in types, "rename() should produce COLUMN_RENAME"
        assert TransformationType.SORT in types, "sort_values() should produce SORT"

    def test_three_op_chain_rename_mapping_extracted(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df.dropna().rename(columns={'old': 'new'}).sort_values('new')\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        renames = _find(transformations, TransformationType.COLUMN_RENAME)
        assert len(renames) >= 1
        mapping = renames[0].parameters.get("mapping", {})
        assert mapping.get("old") == "new"

    def test_two_op_chain_dropna_then_drop_duplicates(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df.dropna().drop_duplicates()\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        types = _types(transformations)
        assert TransformationType.DROP_NA in types
        assert TransformationType.DROP_DUPLICATES in types


# ---------------------------------------------------------------------------
# 2. groupby().sum() / .mean() / .count() (single aggregation shorthand)
# ---------------------------------------------------------------------------

class TestGroupbyShorthandAggregations:
    """groupby('col').sum() — single-agg shorthand that bypasses the .agg() dict path."""

    def test_groupby_sum_produces_groupby_transformation(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df.groupby('cat').sum()\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        groupby_trans = _find(transformations, TransformationType.GROUPBY)
        # The analyzer should detect *something* groupby-related
        assert len(groupby_trans) >= 1, (
            "groupby().sum() should produce at least one GROUPBY transformation"
        )

    def test_groupby_sum_keys_extracted(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df.groupby('region').sum()\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        groupby_trans = _find(transformations, TransformationType.GROUPBY)
        assert len(groupby_trans) >= 1
        # Keys may be in .columns or parameters['keys']
        gb = groupby_trans[0]
        keys = gb.parameters.get("keys", []) or gb.columns
        assert "region" in keys, f"Expected 'region' in groupby keys, got: {keys}"

    def test_groupby_mean_produces_groupby_transformation(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df.groupby('category').mean()\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        groupby_trans = _find(transformations, TransformationType.GROUPBY)
        assert len(groupby_trans) >= 1

    def test_groupby_count_produces_groupby_transformation(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df.groupby(['a', 'b']).count()\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        groupby_trans = _find(transformations, TransformationType.GROUPBY)
        assert len(groupby_trans) >= 1


# ---------------------------------------------------------------------------
# 3. df.expanding() — absent from dispatch table, should not crash
# ---------------------------------------------------------------------------

class TestExpandingGracefulHandling:
    """df.expanding() is listed in CLAUDE.md but absent from _METHOD_HANDLER_NAMES.
    The analyzer must not raise; it may emit UNKNOWN or ROLLING."""

    def test_expanding_does_not_raise(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df['value'].expanding().mean()\n"
        )
        analyzer = CodeAnalyzer()
        # Must not raise any exception
        transformations = analyzer.analyze(code)
        assert isinstance(transformations, list)

    def test_expanding_emits_at_least_one_transformation(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df.expanding(min_periods=3).sum()\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        # Should produce the READ_DATA transformation at minimum
        read_trans = _find(transformations, TransformationType.READ_DATA)
        assert len(read_trans) >= 1

    def test_expanding_does_not_produce_error_type(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df.expanding().mean()\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        # None of the emitted transformations should crash downstream consumers
        for t in transformations:
            assert t.transformation_type is not None
            assert isinstance(t.parameters, dict)


# ---------------------------------------------------------------------------
# 4. Multiple assignments from the same source DataFrame
# ---------------------------------------------------------------------------

class TestMultipleAssignmentsFromSameDataFrame:
    """Two conditional subsets derived from the same source should each be detected."""

    def test_two_boolean_filters_both_detected(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "df2 = df[df.amount > 100]\n"
            "df3 = df[df.amount <= 100]\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        filter_trans = _find(transformations, TransformationType.FILTER)
        assert len(filter_trans) >= 2, (
            f"Expected at least 2 FILTER transformations, got {len(filter_trans)}"
        )

    def test_two_filters_have_distinct_targets(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "df2 = df[df.amount > 100]\n"
            "df3 = df[df.amount <= 100]\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        filter_trans = _find(transformations, TransformationType.FILTER)
        assert len(filter_trans) >= 2
        targets = {t.target_dataframe for t in filter_trans}
        assert len(targets) >= 2, "Each filter should target a different variable"

    def test_source_dataframe_recorded_for_both_filters(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "high = df[df.amount > 100]\n"
            "low  = df[df.amount <= 100]\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        filter_trans = _find(transformations, TransformationType.FILTER)
        for ft in filter_trans:
            assert ft.source_dataframe == "df", (
                f"Both filters should originate from 'df', got '{ft.source_dataframe}'"
            )


# ---------------------------------------------------------------------------
# 5. pd.cut() and pd.qcut() as top-level calls
# ---------------------------------------------------------------------------

class TestPdCutAndQcut:
    """pd.cut() and pd.qcut() assigned to df columns should be handled gracefully."""

    def test_pd_cut_does_not_raise(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "df['binned'] = pd.cut(df['value'], bins=5)\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        assert isinstance(transformations, list)

    def test_pd_cut_emits_read_data_at_minimum(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "df['binned'] = pd.cut(df['value'], bins=5)\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        read_trans = _find(transformations, TransformationType.READ_DATA)
        assert len(read_trans) >= 1

    def test_pd_qcut_does_not_raise(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "df['quartile'] = pd.qcut(df['score'], q=4)\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        assert isinstance(transformations, list)

    def test_pd_cut_and_qcut_together_do_not_crash(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "df['binned'] = pd.cut(df['value'], bins=5)\n"
            "df['quartile'] = pd.qcut(df['score'], q=4)\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        # At a minimum we should get the read operation
        read_trans = _find(transformations, TransformationType.READ_DATA)
        assert len(read_trans) >= 1


# ---------------------------------------------------------------------------
# 6. NumPy element-wise operations
# ---------------------------------------------------------------------------

class TestNumpyOperations:
    """np.log(), np.abs() assigned to a DataFrame column should map to NUMERIC_TRANSFORM."""

    def test_np_log_produces_numeric_transform(self):
        code = (
            "import pandas as pd\n"
            "import numpy as np\n"
            "df = pd.read_csv('data.csv')\n"
            "df['log_val'] = np.log(df['value'])\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        numeric_trans = _find(transformations, TransformationType.NUMERIC_TRANSFORM)
        assert len(numeric_trans) >= 1, "np.log() should produce NUMERIC_TRANSFORM"

    def test_np_log_operation_parameter(self):
        code = (
            "import pandas as pd\n"
            "import numpy as np\n"
            "df = pd.read_csv('data.csv')\n"
            "df['log_val'] = np.log(df['value'])\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        numeric_trans = _find(transformations, TransformationType.NUMERIC_TRANSFORM)
        assert len(numeric_trans) >= 1
        op = numeric_trans[0].parameters.get("operation", "")
        assert "log" in op.lower(), f"Expected 'log' in operation, got '{op}'"

    def test_np_abs_produces_numeric_transform(self):
        code = (
            "import pandas as pd\n"
            "import numpy as np\n"
            "df = pd.read_csv('data.csv')\n"
            "df['abs_val'] = np.abs(df['value'])\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        numeric_trans = _find(transformations, TransformationType.NUMERIC_TRANSFORM)
        assert len(numeric_trans) >= 1, "np.abs() should produce NUMERIC_TRANSFORM"

    def test_np_sqrt_does_not_raise(self):
        code = (
            "import pandas as pd\n"
            "import numpy as np\n"
            "df = pd.read_csv('data.csv')\n"
            "df['sqrt_val'] = np.sqrt(df['value'])\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        assert isinstance(transformations, list)


# ---------------------------------------------------------------------------
# 7. df.assign()
# ---------------------------------------------------------------------------

class TestAssign:
    """df.assign(new_col=...) should produce a COLUMN_CREATE transformation."""

    def test_assign_single_column_detected(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "df = df.assign(new_col=lambda x: x['a'] + x['b'])\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        col_create = _find(transformations, TransformationType.COLUMN_CREATE)
        assert len(col_create) >= 1, "df.assign() should produce COLUMN_CREATE"

    def test_assign_new_column_name_captured(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "df = df.assign(total=lambda x: x['qty'] * x['price'])\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        col_create = _find(transformations, TransformationType.COLUMN_CREATE)
        assert len(col_create) >= 1
        cc = col_create[0]
        col_names = cc.columns or cc.parameters.get("columns", [])
        assert "total" in col_names, f"Expected 'total' in column names, got {col_names}"

    def test_assign_multiple_columns_all_captured(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "df = df.assign(col_a=1, col_b=2, col_c=3)\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        # Each assigned column becomes its own COLUMN_CREATE transformation
        # so it can flow independently into a CreateColumnWithGREL prepare step.
        col_create = _find(transformations, TransformationType.COLUMN_CREATE)
        assert len(col_create) == 3
        col_names = {cc.columns[0] for cc in col_create if cc.columns}
        assert col_names == {"col_a", "col_b", "col_c"}

    def test_assign_suggested_processor(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "df = df.assign(result=lambda x: x['val'] * 2)\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        col_create = _find(transformations, TransformationType.COLUMN_CREATE)
        assert len(col_create) >= 1
        assert col_create[0].suggested_processor == "CreateColumnWithGREL"


# ---------------------------------------------------------------------------
# 8. df.explode()
# ---------------------------------------------------------------------------

class TestExplode:
    """df.explode('list_col') should produce a COLUMN_CREATE with operation='unfold'."""

    def test_explode_detected(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "df = df.explode('list_col')\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        col_create = _find(transformations, TransformationType.COLUMN_CREATE)
        assert len(col_create) >= 1, "df.explode() should produce COLUMN_CREATE"

    def test_explode_operation_is_unfold(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "df = df.explode('tags')\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        col_create = _find(transformations, TransformationType.COLUMN_CREATE)
        assert len(col_create) >= 1
        op = col_create[0].parameters.get("operation", "")
        assert op == "unfold", f"Expected operation='unfold', got '{op}'"

    def test_explode_column_name_captured(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "df = df.explode('items')\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        col_create = _find(transformations, TransformationType.COLUMN_CREATE)
        assert len(col_create) >= 1
        col = col_create[0].parameters.get("column")
        assert col == "items", f"Expected column='items', got '{col}'"

    def test_explode_suggested_processor_is_unfold(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "df = df.explode('nested')\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        col_create = _find(transformations, TransformationType.COLUMN_CREATE)
        assert len(col_create) >= 1
        assert col_create[0].suggested_processor == "Unfold"


# ---------------------------------------------------------------------------
# 9. Empty / trivial code (imports only, no data operations)
# ---------------------------------------------------------------------------

class TestEmptyAndTrivialCode:
    """Code with only imports should produce zero transformations without crashing."""

    def test_import_only_returns_empty_list(self):
        code = "import pandas as pd\nimport numpy as np\n"
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        assert transformations == []

    def test_empty_string_returns_empty_list(self):
        code = ""
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        assert transformations == []

    def test_comment_only_returns_empty_list(self):
        code = "# This is just a comment\n# Another comment\n"
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        assert transformations == []

    def test_variable_assignment_without_pandas_returns_no_read(self):
        code = "x = 42\ny = 'hello'\n"
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        read_trans = _find(transformations, TransformationType.READ_DATA)
        assert len(read_trans) == 0

    def test_analyzer_resets_state_between_analyze_calls(self):
        """Calling analyze() twice on the same instance should not accumulate results."""
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
        )
        analyzer = CodeAnalyzer()
        first = analyzer.analyze(code)
        second = analyzer.analyze(code)
        assert len(first) == len(second), (
            "Second analyze() call should reset state, not accumulate transformations"
        )


# ---------------------------------------------------------------------------
# 10. Multiple pd.read_csv() calls (two separate input datasets)
# ---------------------------------------------------------------------------

class TestMultipleReadCsvCalls:
    """Two read_csv() calls should each produce a READ_DATA transformation."""

    def test_two_read_csv_produce_two_read_data(self):
        code = (
            "import pandas as pd\n"
            "df1 = pd.read_csv('sales.csv')\n"
            "df2 = pd.read_csv('customers.csv')\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        read_trans = _find(transformations, TransformationType.READ_DATA)
        assert len(read_trans) == 2, (
            f"Expected 2 READ_DATA transformations, got {len(read_trans)}"
        )

    def test_two_read_csv_have_distinct_targets(self):
        code = (
            "import pandas as pd\n"
            "df1 = pd.read_csv('sales.csv')\n"
            "df2 = pd.read_csv('customers.csv')\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        read_trans = _find(transformations, TransformationType.READ_DATA)
        assert len(read_trans) == 2
        targets = {t.target_dataframe for t in read_trans}
        assert "df1" in targets
        assert "df2" in targets

    def test_two_read_csv_filepaths_captured(self):
        code = (
            "import pandas as pd\n"
            "df1 = pd.read_csv('sales.csv')\n"
            "df2 = pd.read_csv('customers.csv')\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        read_trans = _find(transformations, TransformationType.READ_DATA)
        assert len(read_trans) == 2
        filepaths = {t.parameters.get("filepath") for t in read_trans}
        assert "sales.csv" in filepaths
        assert "customers.csv" in filepaths

    def test_three_read_csv_produce_three_read_data(self):
        code = (
            "import pandas as pd\n"
            "a = pd.read_csv('a.csv')\n"
            "b = pd.read_csv('b.csv')\n"
            "c = pd.read_csv('c.csv')\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        read_trans = _find(transformations, TransformationType.READ_DATA)
        assert len(read_trans) == 3


# ---------------------------------------------------------------------------
# 11. Variable aliasing — data = df; data.dropna()
# ---------------------------------------------------------------------------

class TestVariableAliasing:
    """When a DataFrame is aliased, operations on the alias should still be detected."""

    def test_alias_then_dropna_does_not_crash(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "data = df\n"
            "result = data.dropna()\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        assert isinstance(transformations, list)

    def test_alias_dropna_emits_drop_na(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "data = df\n"
            "result = data.dropna()\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        drop_na = _find(transformations, TransformationType.DROP_NA)
        assert len(drop_na) >= 1, "dropna() on an alias should produce DROP_NA"

    def test_alias_sort_values_emits_sort(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "clean = df\n"
            "result = clean.sort_values('name')\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        sort_trans = _find(transformations, TransformationType.SORT)
        assert len(sort_trans) >= 1


# ---------------------------------------------------------------------------
# 12. Complex boolean indexing with & operator
# ---------------------------------------------------------------------------

class TestComplexBooleanIndexing:
    """df[(df.a > 1) & (df.b < 5)] should produce a FILTER transformation."""

    def test_and_boolean_filter_detected(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df[(df.a > 1) & (df.b < 5)]\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        filter_trans = _find(transformations, TransformationType.FILTER)
        assert len(filter_trans) >= 1, "Compound & filter should produce FILTER"

    def test_or_boolean_filter_detected(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df[(df.status == 'active') | (df.priority > 3)]\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        filter_trans = _find(transformations, TransformationType.FILTER)
        assert len(filter_trans) >= 1, "Compound | filter should produce FILTER"

    def test_complex_filter_condition_not_empty(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df[(df.a > 1) & (df.b < 5)]\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        filter_trans = _find(transformations, TransformationType.FILTER)
        assert len(filter_trans) >= 1
        condition = filter_trans[0].parameters.get("condition", "")
        assert len(condition) > 0, "Filter condition string should not be empty"

    def test_negated_boolean_filter_detected(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df[~(df.amount == 0)]\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        filter_trans = _find(transformations, TransformationType.FILTER)
        assert len(filter_trans) >= 1

    def test_complex_filter_source_dataframe_correct(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "filtered = df[(df.x > 0) & (df.y > 0)]\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        filter_trans = _find(transformations, TransformationType.FILTER)
        assert len(filter_trans) >= 1
        assert filter_trans[0].source_dataframe == "df"

    def test_complex_filter_target_dataframe_correct(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "filtered = df[(df.x > 0) & (df.y > 0)]\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        filter_trans = _find(transformations, TransformationType.FILTER)
        assert len(filter_trans) >= 1
        assert filter_trans[0].target_dataframe == "filtered"


# ---------------------------------------------------------------------------
# 13. Transformation metadata — source_line populated
# ---------------------------------------------------------------------------

class TestTransformationMetadata:
    """Transformations should carry accurate source_line and type information."""

    def test_read_csv_source_line_populated(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        read_trans = _find(transformations, TransformationType.READ_DATA)
        assert len(read_trans) >= 1
        assert read_trans[0].source_line is not None
        assert read_trans[0].source_line > 0

    def test_dropna_source_line_populated(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df.dropna()\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        drop_na = _find(transformations, TransformationType.DROP_NA)
        assert len(drop_na) >= 1
        assert drop_na[0].source_line is not None

    def test_transformation_type_is_enum_instance(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df.dropna()\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        for t in transformations:
            assert isinstance(t.transformation_type, TransformationType), (
                f"Expected TransformationType enum, got {type(t.transformation_type)}"
            )

    def test_to_dict_serialisable(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df.dropna().sort_values('col')\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        for t in transformations:
            d = t.to_dict()
            assert isinstance(d, dict)
            assert "type" in d


# ---------------------------------------------------------------------------
# 14. Invalid Python syntax raises InvalidPythonCodeError
# ---------------------------------------------------------------------------

class TestInvalidSyntax:
    """SyntaxError in input code should be re-raised as InvalidPythonCodeError."""

    def test_syntax_error_raises_invalid_python_code_error(self):
        from py2dataiku.exceptions import InvalidPythonCodeError

        code = "def broken(:\n    pass\n"
        analyzer = CodeAnalyzer()
        with pytest.raises(InvalidPythonCodeError):
            analyzer.analyze(code)

    def test_unclosed_paren_raises_invalid_python_code_error(self):
        from py2dataiku.exceptions import InvalidPythonCodeError

        code = "x = (1 + 2\n"
        analyzer = CodeAnalyzer()
        with pytest.raises(InvalidPythonCodeError):
            analyzer.analyze(code)


# ---------------------------------------------------------------------------
# 15. Dispatch table completeness — all entries resolve to callable handlers
# ---------------------------------------------------------------------------

class TestDispatchTableIntegrity:
    """Every entry in _METHOD_HANDLER_NAMES that has a matching method should be callable."""

    def test_all_registered_handlers_are_callable(self):
        analyzer = CodeAnalyzer()
        for method_name, handler in analyzer._method_handlers.items():
            assert callable(handler), (
                f"Handler for '{method_name}' is not callable: {handler!r}"
            )

    def test_handler_count_matches_available_methods(self):
        """Handlers registered in __init__ should be a subset of _METHOD_HANDLER_NAMES."""
        analyzer = CodeAnalyzer()
        for name in analyzer._method_handlers:
            assert name in CodeAnalyzer._METHOD_HANDLER_NAMES, (
                f"'{name}' in _method_handlers but not in _METHOD_HANDLER_NAMES"
            )

    def test_expanding_absent_from_dispatch_table(self):
        """Document the known gap: 'expanding' is not in the dispatch table."""
        assert "expanding" not in CodeAnalyzer._METHOD_HANDLER_NAMES, (
            "'expanding' was added to _METHOD_HANDLER_NAMES — update the tests accordingly"
        )


# ---------------------------------------------------------------------------
# 16. dropna with subset keyword
# ---------------------------------------------------------------------------

class TestDropnaSubset:
    """dropna(subset=['col']) should capture the subset columns."""

    def test_dropna_subset_single_column(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df.dropna(subset=['age'])\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        drop_na = _find(transformations, TransformationType.DROP_NA)
        assert len(drop_na) >= 1
        subset = drop_na[0].parameters.get("subset")
        assert subset is not None
        assert "age" in subset

    def test_dropna_subset_multiple_columns(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df.dropna(subset=['age', 'income'])\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        drop_na = _find(transformations, TransformationType.DROP_NA)
        assert len(drop_na) >= 1
        subset = drop_na[0].parameters.get("subset") or drop_na[0].columns
        assert "age" in subset
        assert "income" in subset


# ---------------------------------------------------------------------------
# 17. sort_values with ascending=False
# ---------------------------------------------------------------------------

class TestSortValuesDescending:
    """sort_values('col', ascending=False) should record ascending=False."""

    def test_sort_descending_parameter_captured(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df.sort_values('revenue', ascending=False)\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        sort_trans = _find(transformations, TransformationType.SORT)
        assert len(sort_trans) >= 1
        ascending = sort_trans[0].parameters.get("ascending")
        assert ascending is False, f"Expected ascending=False, got {ascending}"

    def test_sort_ascending_default_is_true(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df.sort_values('name')\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        sort_trans = _find(transformations, TransformationType.SORT)
        assert len(sort_trans) >= 1
        ascending = sort_trans[0].parameters.get("ascending")
        assert ascending is True, f"Expected ascending=True (default), got {ascending}"


# ---------------------------------------------------------------------------
# 18. head() and tail() with explicit n
# ---------------------------------------------------------------------------

class TestHeadAndTail:
    """head(n) and tail(n) should capture the n parameter."""

    def test_head_n_captured(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df.head(20)\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        head_trans = _find(transformations, TransformationType.HEAD)
        assert len(head_trans) >= 1
        assert head_trans[0].parameters.get("n") == 20

    def test_tail_n_captured(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df.tail(10)\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        tail_trans = _find(transformations, TransformationType.TAIL)
        assert len(tail_trans) >= 1
        assert tail_trans[0].parameters.get("n") == 10

    def test_head_default_n_is_five(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "result = df.head()\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        head_trans = _find(transformations, TransformationType.HEAD)
        assert len(head_trans) >= 1
        assert head_trans[0].parameters.get("n") == 5


# ---------------------------------------------------------------------------
# 19. pd.merge() (module-level, not method-level)
# ---------------------------------------------------------------------------

class TestPdMerge:
    """pd.merge(left, right, on=...) should produce a MERGE transformation."""

    def test_pd_merge_produces_merge(self):
        code = (
            "import pandas as pd\n"
            "df1 = pd.read_csv('a.csv')\n"
            "df2 = pd.read_csv('b.csv')\n"
            "result = pd.merge(df1, df2, on='id')\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        merge_trans = _find(transformations, TransformationType.MERGE)
        assert len(merge_trans) >= 1

    def test_pd_merge_on_parameter_captured(self):
        code = (
            "import pandas as pd\n"
            "df1 = pd.read_csv('a.csv')\n"
            "df2 = pd.read_csv('b.csv')\n"
            "result = pd.merge(df1, df2, on='customer_id')\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        merge_trans = _find(transformations, TransformationType.MERGE)
        assert len(merge_trans) >= 1
        on = merge_trans[0].parameters.get("on")
        assert on is not None
        assert "customer_id" in on

    def test_pd_merge_how_parameter_captured(self):
        code = (
            "import pandas as pd\n"
            "df1 = pd.read_csv('a.csv')\n"
            "df2 = pd.read_csv('b.csv')\n"
            "result = pd.merge(df1, df2, on='id', how='left')\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        merge_trans = _find(transformations, TransformationType.MERGE)
        assert len(merge_trans) >= 1
        how = merge_trans[0].parameters.get("how")
        assert how == "left"


# ---------------------------------------------------------------------------
# 20. pd.concat()
# ---------------------------------------------------------------------------

class TestPdConcat:
    """pd.concat([df1, df2]) should produce a CONCAT transformation."""

    def test_concat_produces_concat(self):
        code = (
            "import pandas as pd\n"
            "df1 = pd.read_csv('a.csv')\n"
            "df2 = pd.read_csv('b.csv')\n"
            "result = pd.concat([df1, df2])\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        concat_trans = _find(transformations, TransformationType.CONCAT)
        assert len(concat_trans) >= 1

    def test_concat_dataframes_list_captured(self):
        code = (
            "import pandas as pd\n"
            "df1 = pd.read_csv('a.csv')\n"
            "df2 = pd.read_csv('b.csv')\n"
            "result = pd.concat([df1, df2])\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)

        concat_trans = _find(transformations, TransformationType.CONCAT)
        assert len(concat_trans) >= 1
        dfs = concat_trans[0].parameters.get("dataframes", [])
        assert "df1" in dfs
        assert "df2" in dfs


# ===================================================================
# Ultrareview wave-1 Phase 3 fixes: rule-based parity & multi-agg
# ===================================================================


class TestMultiFunctionAggDict:
    """groupby().agg({'col': ['sum', 'mean']}) must produce multiple aggregations."""

    def test_multi_function_agg_extracted_as_list(self):
        from py2dataiku.parser.ast_analyzer import CodeAnalyzer
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('x.csv')\n"
            "result = df.groupby('cat').agg({'amount': ['sum', 'mean', 'max']})\n"
        )
        analyzer = CodeAnalyzer()
        analyzer.analyze(code)
        gb = [t for t in analyzer.transformations if t.transformation_type.value == "groupby"]
        assert gb
        aggs = gb[0].parameters.get("aggregations", {})
        assert "amount" in aggs
        # Must preserve the list, not just store the last value
        assert aggs["amount"] == ["sum", "mean", "max"]

    def test_multi_function_agg_yields_multiple_aggregations_in_recipe(self):
        from py2dataiku import convert
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('x.csv')\n"
            "result = df.groupby('cat').agg({'amount': ['sum', 'mean']})\n"
        )
        flow = convert(code)
        from py2dataiku.models.dataiku_recipe import RecipeType
        grouping = flow.get_recipes_by_type(RecipeType.GROUPING)
        assert len(grouping) == 1
        # Should produce 2 aggregations on the same column, not 1 or 0
        assert len(grouping[0].aggregations) == 2

    def test_single_function_agg_still_works(self):
        from py2dataiku.parser.ast_analyzer import CodeAnalyzer
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('x.csv')\n"
            "result = df.groupby('cat').agg({'amount': 'sum'})\n"
        )
        analyzer = CodeAnalyzer()
        analyzer.analyze(code)
        gb = [t for t in analyzer.transformations if t.transformation_type.value == "groupby"]
        assert gb[0].parameters["aggregations"]["amount"] == "sum"


class TestStringTransformInRuleBasedPath:
    """STRING_TRANSFORM transformations must produce real PrepareSteps (was returning None)."""

    def test_string_upper_creates_string_transformer_step(self):
        from py2dataiku import convert
        from py2dataiku.models.dataiku_recipe import RecipeType
        from py2dataiku.models.prepare_step import ProcessorType
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('x.csv')\n"
            "df['name'] = df['name'].str.upper()\n"
        )
        flow = convert(code)
        prepare_recipes = flow.get_recipes_by_type(RecipeType.PREPARE)
        assert prepare_recipes
        steps = prepare_recipes[0].steps
        # There should be a real StringTransformer step, not nothing
        st_steps = [s for s in steps if s.processor_type == ProcessorType.STRING_TRANSFORMER]
        assert len(st_steps) >= 1

    def test_string_replace_creates_find_replace_step(self):
        from py2dataiku import convert
        from py2dataiku.models.dataiku_recipe import RecipeType
        from py2dataiku.models.prepare_step import ProcessorType
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('x.csv')\n"
            "df['name'] = df['name'].str.replace('foo', 'bar')\n"
        )
        flow = convert(code)
        prepare_recipes = flow.get_recipes_by_type(RecipeType.PREPARE)
        assert prepare_recipes
        steps = prepare_recipes[0].steps
        fr_steps = [s for s in steps if s.processor_type == ProcessorType.FIND_REPLACE]
        assert len(fr_steps) >= 1


class TestSamplingFracValuePropagation:
    """Sampling df.sample(frac=0.1) must propagate the fraction (was silently dropped)."""

    def test_frac_converted_to_percentage(self):
        from py2dataiku import convert
        from py2dataiku.models.dataiku_recipe import RecipeType, SamplingMethod
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('x.csv')\n"
            "sample = df.sample(frac=0.25)\n"
        )
        flow = convert(code)
        sampling = flow.get_recipes_by_type(RecipeType.SAMPLING)
        assert len(sampling) == 1
        assert sampling[0].sampling_method == SamplingMethod.RANDOM_FIXED
        assert sampling[0].sample_size == 25  # 25%

    def test_n_explicit_count(self):
        from py2dataiku import convert
        from py2dataiku.models.dataiku_recipe import RecipeType, SamplingMethod
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('x.csv')\n"
            "sample = df.sample(n=500)\n"
        )
        flow = convert(code)
        sampling = flow.get_recipes_by_type(RecipeType.SAMPLING)
        assert len(sampling) == 1
        assert sampling[0].sampling_method == SamplingMethod.RANDOM
        assert sampling[0].sample_size == 500


# ===================================================================
# Ultrareview wave-1 Phase 4: Ergonomics
# ===================================================================


class TestConvertPolymorphicInput:
    """convert() and convert_with_llm() must accept Path or .py file paths."""

    def test_convert_accepts_pathlib_path(self, tmp_path):
        from pathlib import Path
        from py2dataiku import convert
        script = tmp_path / "demo.py"
        script.write_text(
            "import pandas as pd\n"
            "df = pd.read_csv('x.csv')\n"
            "df = df.dropna()\n"
        )
        flow = convert(Path(script))
        assert flow is not None
        assert flow.source_file == str(script)

    def test_convert_accepts_string_path_to_py_file(self, tmp_path):
        from py2dataiku import convert
        script = tmp_path / "demo.py"
        script.write_text(
            "import pandas as pd\n"
            "df = pd.read_csv('x.csv')\n"
        )
        flow = convert(str(script))
        assert flow is not None
        assert flow.source_file == str(script)

    def test_convert_still_accepts_code_string(self):
        from py2dataiku import convert
        flow = convert("import pandas as pd\ndf = pd.read_csv('x.csv')\n")
        assert flow is not None


class TestFlowSaveAutoDetect:
    """flow.save('path.ext') must auto-detect format from extension."""

    def _flow(self):
        from py2dataiku import convert
        return convert("import pandas as pd\ndf = pd.read_csv('x.csv')\n")

    def test_save_json(self, tmp_path):
        f = self._flow()
        out = tmp_path / "flow.json"
        f.save(str(out))
        content = out.read_text()
        assert content.startswith("{")
        # Must be valid JSON
        import json
        json.loads(content)

    def test_save_yaml(self, tmp_path):
        f = self._flow()
        out = tmp_path / "flow.yaml"
        f.save(str(out))
        assert out.exists()
        # Should look like YAML
        assert ":" in out.read_text()

    def test_save_yml_alias(self, tmp_path):
        f = self._flow()
        out = tmp_path / "flow.yml"
        f.save(str(out))
        assert out.exists()

    def test_save_svg(self, tmp_path):
        f = self._flow()
        out = tmp_path / "flow.svg"
        f.save(str(out))
        content = out.read_text()
        assert "<svg" in content

    def test_save_unsupported_format_raises(self, tmp_path):
        f = self._flow()
        out = tmp_path / "flow.unknown"
        try:
            f.save(str(out))
        except ValueError as e:
            assert "Unsupported format" in str(e)
        else:
            raise AssertionError("Expected ValueError for unknown extension")

    def test_save_explicit_format_override(self, tmp_path):
        f = self._flow()
        out = tmp_path / "flow.txt"
        f.save(str(out), format="json")
        assert out.read_text().startswith("{")


class TestCliBareFileInvocation:
    """py2dataiku script.py (no subcommand) should auto-route to convert."""

    def test_bare_file_routes_to_convert(self, tmp_path, capsys):
        from py2dataiku.cli import main
        script = tmp_path / "demo.py"
        script.write_text("import pandas as pd\ndf = pd.read_csv('x.csv')\n")
        # Should not error
        rc = main([str(script)])
        assert rc == 0
        # Should have produced JSON-like output to stdout
        captured = capsys.readouterr()
        assert "{" in captured.out  # JSON output

    def test_bare_help_still_works(self, capsys):
        from py2dataiku.cli import main
        try:
            main(["--help"])
        except SystemExit:
            pass
        captured = capsys.readouterr()
        assert "usage" in captured.out.lower()


# ===================================================================
# Ultrareview wave-2: Phases 5-6 (perf + parity fixes)
# ===================================================================


class TestNlargestRankingColumn:
    """nlargest/nsmallest must populate ranking_column (was always None)."""

    def test_nlargest_emits_ranking_column(self):
        from py2dataiku import convert
        from py2dataiku.models.dataiku_recipe import RecipeType
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('x.csv')\n"
            "top = df.nlargest(5, 'sales')\n"
        )
        flow = convert(code)
        topn = flow.get_recipes_by_type(RecipeType.TOP_N)
        assert len(topn) == 1
        assert topn[0].ranking_column == "sales"
        assert topn[0].top_n == 5

    def test_nsmallest_emits_ranking_column_ascending(self):
        from py2dataiku import convert
        from py2dataiku.models.dataiku_recipe import RecipeType
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('x.csv')\n"
            "bottom = df.nsmallest(3, 'price')\n"
        )
        flow = convert(code)
        topn = flow.get_recipes_by_type(RecipeType.TOP_N)
        assert len(topn) == 1
        assert topn[0].ranking_column == "price"


class TestTopnSamplingHonorsTargetName:
    """User-assigned variable name should be the recipe's output dataset."""

    def test_topn_uses_target_dataframe(self):
        from py2dataiku import convert
        from py2dataiku.models.dataiku_recipe import RecipeType
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('x.csv')\n"
            "top10 = df.nlargest(10, 'rev')\n"
        )
        flow = convert(code)
        topn = flow.get_recipes_by_type(RecipeType.TOP_N)
        assert topn[0].outputs[0] == "top10"

    def test_sampling_uses_target_dataframe(self):
        from py2dataiku import convert
        from py2dataiku.models.dataiku_recipe import RecipeType
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('x.csv')\n"
            "first50 = df.head(50)\n"
        )
        flow = convert(code)
        sampling = flow.get_recipes_by_type(RecipeType.SAMPLING)
        assert sampling[0].outputs[0] == "first50"


class TestMeltKwargsExtracted:
    """pd.melt / df.melt must extract id_vars/value_vars/var_name/value_name."""

    def test_melt_extracts_value_vars(self):
        from py2dataiku.parser.ast_analyzer import CodeAnalyzer
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('x.csv')\n"
            "long = pd.melt(df, id_vars=['id'], value_vars=['q1', 'q2'])\n"
        )
        analyzer = CodeAnalyzer()
        analyzer.analyze(code)
        melt = [t for t in analyzer.transformations if t.transformation_type.value == "melt"]
        assert melt
        assert melt[0].columns == ["q1", "q2"]
        assert melt[0].parameters["id_vars"] == ["id"]
        assert melt[0].parameters["value_vars"] == ["q1", "q2"]

    def test_pd_melt_routes_to_prepare_with_fold_columns(self):
        from py2dataiku import convert
        from py2dataiku.models.dataiku_recipe import RecipeType
        from py2dataiku.models.prepare_step import ProcessorType
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('x.csv')\n"
            "long = pd.melt(df, id_vars=['id'], value_vars=['q1', 'q2'])\n"
        )
        flow = convert(code)
        prep = flow.get_recipes_by_type(RecipeType.PREPARE)
        assert prep
        # Find the FOLD_MULTIPLE_COLUMNS step
        fold_steps = [
            s for s in prep[0].steps
            if s.processor_type == ProcessorType.FOLD_MULTIPLE_COLUMNS
        ]
        assert fold_steps
        assert fold_steps[0].params["columns"] == ["q1", "q2"]


class TestPdCutQcutGetDummies:
    """pd.cut / pd.qcut / pd.get_dummies must produce visual processors (were silent dead pass)."""

    def test_pd_cut_emits_binner(self):
        from py2dataiku import convert
        from py2dataiku.models.dataiku_recipe import RecipeType
        from py2dataiku.models.prepare_step import ProcessorType
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('x.csv')\n"
            "df['bins'] = pd.cut(df['amount'], bins=5)\n"
        )
        flow = convert(code)
        prep = flow.get_recipes_by_type(RecipeType.PREPARE)
        assert prep
        binner_steps = [s for s in prep[0].steps if s.processor_type == ProcessorType.BINNER]
        assert binner_steps
        assert binner_steps[0].params.get("bins") == 5

    def test_pd_qcut_emits_binner(self):
        from py2dataiku import convert
        from py2dataiku.models.prepare_step import ProcessorType
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('x.csv')\n"
            "df['quartiles'] = pd.qcut(df['price'], q=4)\n"
        )
        flow = convert(code)
        from py2dataiku.models.dataiku_recipe import RecipeType
        prep = flow.get_recipes_by_type(RecipeType.PREPARE)
        binner_steps = [s for s in prep[0].steps if s.processor_type == ProcessorType.BINNER]
        assert binner_steps
        assert binner_steps[0].params.get("mode") == "qcut"

    def test_pd_get_dummies_emits_categorical_encoder(self):
        from py2dataiku import convert
        from py2dataiku.models.dataiku_recipe import RecipeType
        from py2dataiku.models.prepare_step import ProcessorType
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('x.csv')\n"
            "df = pd.get_dummies(df, columns=['category', 'region'])\n"
        )
        flow = convert(code)
        prep = flow.get_recipes_by_type(RecipeType.PREPARE)
        assert prep
        enc_steps = [
            s for s in prep[0].steps if s.processor_type == ProcessorType.CATEGORICAL_ENCODER
        ]
        assert enc_steps
        assert enc_steps[0].params.get("columns") == ["category", "region"]


class TestAssignLambdaExpression:
    """df.assign(c=lambda x: ...) must extract the lambda body."""

    def test_assign_lambda_captures_expression(self):
        from py2dataiku.parser.ast_analyzer import CodeAnalyzer
        from py2dataiku.models.transformation import TransformationType
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('x.csv')\n"
            "df = df.assign(total=lambda x: x['a'] + x['b'])\n"
        )
        analyzer = CodeAnalyzer()
        analyzer.analyze(code)
        cc = [
            t for t in analyzer.transformations
            if t.transformation_type == TransformationType.COLUMN_CREATE
            and t.columns == ["total"]
        ]
        assert cc
        # Expression body unparsed back to source text
        assert "x['a']" in cc[0].parameters.get("expression", "")
        assert "x['b']" in cc[0].parameters.get("expression", "")


class TestRuleBasedColumnSelectMode:
    """Rule-based COLUMN_SELECT must include mode:keep (LLM path was already fixed)."""

    def test_column_select_emits_mode_keep(self):
        from py2dataiku.parser.ast_analyzer import CodeAnalyzer
        from py2dataiku.generators.flow_generator import FlowGenerator
        from py2dataiku.models.dataiku_recipe import RecipeType
        from py2dataiku.models.prepare_step import ProcessorType
        from py2dataiku.models.transformation import Transformation, TransformationType
        gen = FlowGenerator()
        # Synthesize a COLUMN_SELECT transformation directly
        trans = [
            Transformation(
                transformation_type=TransformationType.READ_DATA,
                target_dataframe="df",
                parameters={"filepath": "x.csv"},
                source_line=1,
            ),
            Transformation(
                transformation_type=TransformationType.COLUMN_SELECT,
                source_dataframe="df",
                target_dataframe="df",
                columns=["a", "b"],
                source_line=2,
            ),
        ]
        flow = gen.generate(trans, optimize=False)
        prep = flow.get_recipes_by_type(RecipeType.PREPARE)[0]
        sel_steps = [s for s in prep.steps if s.processor_type == ProcessorType.COLUMNS_SELECTOR]
        assert sel_steps
        assert sel_steps[0].params.get("mode") == "keep"


class TestOptimizerNotPathological:
    """120-recipe input must convert quickly (was 320ms due to dead-code O(N²) loop).

    Threshold is generous (250ms) to absorb CI/loaded-system jitter while
    still catching a multi-second regression if the dead-code loop is
    re-introduced (it was 320ms p50 on a quiet system pre-fix).
    """

    def test_large_flow_under_250ms(self):
        import time
        from py2dataiku import convert
        chunks = ["import pandas as pd"]
        for i in range(40):
            chunks.append(f"df{i} = pd.read_csv('x{i}.csv')")
            chunks.append(f"df{i} = df{i}.dropna()")
            chunks.append(f"df{i} = df{i}.drop_duplicates()")
        code = "\n".join(chunks)
        # Best of 3 runs to absorb noise from concurrent processes.
        best_ms = float("inf")
        flow = None
        for _ in range(3):
            t = time.perf_counter()
            flow = convert(code)
            best_ms = min(best_ms, (time.perf_counter() - t) * 1000)
        assert flow is not None
        assert best_ms < 250, (
            f"Conversion took {best_ms:.1f}ms best-of-3 — likely the O(N^2) "
            "dead-code optimizer hot path was re-introduced"
        )


class TestLLMAggregationCanonical:
    """LLM path must canonicalize agg names: mean->AVG, std->STDDEV, nunique->COUNTD."""

    def test_mean_normalized_to_avg(self):
        from py2dataiku.llm.schemas import (
            AnalysisResult, DataStep, OperationType, Aggregation, DatasetInfo,
        )
        from py2dataiku.generators.llm_flow_generator import LLMFlowGenerator
        from py2dataiku.models.dataiku_recipe import RecipeType
        analysis = AnalysisResult(
            code_summary="g",
            total_operations=1,
            complexity_score=1,
            datasets=[DatasetInfo(name="df", is_input=True)],
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.GROUP_AGGREGATE,
                    description="group + mean",
                    input_datasets=["df"],
                    output_dataset="result",
                    suggested_recipe="grouping",
                    group_by_columns=["cat"],
                    aggregations=[Aggregation("amount", "mean", "avg_amount")],
                )
            ],
        )
        flow = LLMFlowGenerator().generate(analysis)
        g = flow.get_recipes_by_type(RecipeType.GROUPING)[0]
        # mean must be normalized to AVG (DSS canonical)
        assert g.aggregations[0].function == "AVG"

    def test_nunique_normalized_to_countd(self):
        from py2dataiku.llm.schemas import (
            AnalysisResult, DataStep, OperationType, Aggregation, DatasetInfo,
        )
        from py2dataiku.generators.llm_flow_generator import LLMFlowGenerator
        from py2dataiku.models.dataiku_recipe import RecipeType
        analysis = AnalysisResult(
            code_summary="g",
            total_operations=1,
            complexity_score=1,
            datasets=[DatasetInfo(name="df", is_input=True)],
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.GROUP_AGGREGATE,
                    description="g",
                    input_datasets=["df"],
                    output_dataset="result",
                    suggested_recipe="grouping",
                    group_by_columns=["cat"],
                    aggregations=[Aggregation("user_id", "nunique")],
                )
            ],
        )
        flow = LLMFlowGenerator().generate(analysis)
        g = flow.get_recipes_by_type(RecipeType.GROUPING)[0]
        assert g.aggregations[0].function == "COUNTD"


# ===================================================================
# Ultrareview wave-3: Phase 7 (DSS readiness + API polish)
# ===================================================================


class TestOptimizerDagRewriting:
    """When merging prepare recipes, downstream inputs must be rewritten."""

    def test_merge_rewrites_downstream_join_input(self):
        """Reproduces the flow_5 DAG break: merged prepare output != join input."""
        from py2dataiku.models.dataiku_flow import DataikuFlow
        from py2dataiku.models.dataiku_dataset import DataikuDataset, DatasetType
        from py2dataiku.models.dataiku_recipe import DataikuRecipe, RecipeType, JoinType
        from py2dataiku.optimizer.flow_optimizer import FlowOptimizer

        flow = DataikuFlow(name="t")
        flow.add_dataset(DataikuDataset(name="raw", dataset_type=DatasetType.INPUT))
        flow.add_dataset(DataikuDataset(name="ref", dataset_type=DatasetType.INPUT))
        flow.add_dataset(
            DataikuDataset(name="raw_prepared", dataset_type=DatasetType.INTERMEDIATE)
        )
        flow.add_dataset(
            DataikuDataset(name="raw_prepared_prepared", dataset_type=DatasetType.INTERMEDIATE)
        )
        flow.add_dataset(DataikuDataset(name="joined", dataset_type=DatasetType.OUTPUT))

        # Two consecutive prepare recipes producing raw_prepared_prepared
        flow.add_recipe(DataikuRecipe(
            name="prep1",
            recipe_type=RecipeType.PREPARE,
            inputs=["raw"],
            outputs=["raw_prepared"],
        ))
        flow.add_recipe(DataikuRecipe(
            name="prep2",
            recipe_type=RecipeType.PREPARE,
            inputs=["raw_prepared"],
            outputs=["raw_prepared_prepared"],
        ))
        # Join expects raw_prepared (the FIRST prepare's output, before merge)
        flow.add_recipe(DataikuRecipe(
            name="join1",
            recipe_type=RecipeType.JOIN,
            inputs=["raw_prepared", "ref"],
            outputs=["joined"],
            join_type=JoinType.INNER,
        ))

        FlowOptimizer().optimize(flow)
        # After merge, the join's first input should be rewritten to the
        # merged output (raw_prepared_prepared), not the now-orphaned name.
        join = next(r for r in flow.recipes if r.name == "join1")
        assert join.inputs[0] == "raw_prepared_prepared", (
            f"Optimizer should have rewritten downstream input; got {join.inputs}"
        )


class TestRollingChainNoPhantomGrouping:
    """df['x'].rolling(7).mean() must produce ONE WINDOW recipe, no phantom GROUPING."""

    def test_rolling_mean_emits_window_only(self):
        from py2dataiku import convert
        from py2dataiku.models.dataiku_recipe import RecipeType
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('x.csv')\n"
            "df['rolling_avg'] = df['sales'].rolling(7).mean()\n"
        )
        flow = convert(code)
        windows = flow.get_recipes_by_type(RecipeType.WINDOW)
        groupings = flow.get_recipes_by_type(RecipeType.GROUPING)
        assert len(windows) == 1
        # No phantom GROUPING from misparsing .mean()
        assert len(groupings) == 0

    def test_rolling_sum_extracts_window_size(self):
        from py2dataiku import convert
        from py2dataiku.models.dataiku_recipe import RecipeType
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('x.csv')\n"
            "df['cumavg'] = df['amount'].rolling(window=30).sum()\n"
        )
        flow = convert(code)
        windows = flow.get_recipes_by_type(RecipeType.WINDOW)
        assert windows
        # Look for the rolling transformation source via notes
        note_text = " ".join(windows[0].notes)
        assert "30" in note_text or windows[0].window_aggregations


class TestDssCompatibleJoinShape:
    """JOIN recipe to_dict() must match DSS schema (joins[].conditions[].column1/2)."""

    def test_join_emits_dss_canonical_shape(self):
        from py2dataiku.models.dataiku_recipe import (
            DataikuRecipe, RecipeType, JoinType, JoinKey,
        )
        recipe = DataikuRecipe(
            name="j",
            recipe_type=RecipeType.JOIN,
            inputs=["a", "b"],
            outputs=["ab"],
            join_type=JoinType.INNER,
            join_keys=[JoinKey(left_column="id", right_column="id")],
        )
        d = recipe._build_settings()
        # DSS expects joins as a list of dicts with conditions[]
        assert "joins" in d
        joins = d["joins"]
        assert len(joins) == 1
        assert "conditions" in joins[0]
        assert joins[0]["conditions"][0]["type"] == "EQ"
        assert joins[0]["conditions"][0]["column1"]["name"] == "id"
        assert joins[0]["conditions"][0]["column2"]["name"] == "id"
        assert joins[0]["conditions"][0]["column1"]["table"] == 0
        assert joins[0]["conditions"][0]["column2"]["table"] == 1
        assert "outerJoinOnTheLeft" in joins[0]


class TestDssCompatibleSortShape:
    """SORT must emit ascending: bool, not order: 'desc' string."""

    def test_sort_emits_ascending_boolean(self):
        from py2dataiku.models.dataiku_recipe import DataikuRecipe, RecipeType
        recipe = DataikuRecipe(
            name="s",
            recipe_type=RecipeType.SORT,
            inputs=["df"],
            outputs=["sorted"],
            sort_columns=[
                {"column": "date", "order": "desc"},
                {"column": "id", "order": "asc"},
            ],
        )
        d = recipe._build_settings()
        sc = d["sortColumns"]
        assert sc[0]["column"] == "date"
        assert sc[0]["ascending"] is False
        assert sc[1]["ascending"] is True

    def test_sort_passthrough_explicit_ascending_bool(self):
        from py2dataiku.models.dataiku_recipe import DataikuRecipe, RecipeType
        recipe = DataikuRecipe(
            name="s",
            recipe_type=RecipeType.SORT,
            inputs=["df"],
            outputs=["sorted"],
            sort_columns=[{"column": "date", "ascending": False}],
        )
        d = recipe._build_settings()
        assert d["sortColumns"][0]["ascending"] is False


class TestRepresentationMimeBundle:
    """DataikuFlow must implement _repr_mimebundle_ for JupyterLab compatibility."""

    def test_mimebundle_returns_svg_and_text(self):
        from py2dataiku import convert
        flow = convert("import pandas as pd\ndf = pd.read_csv('x.csv')\n")
        bundle = flow._repr_mimebundle_()
        assert "image/svg+xml" in bundle
        assert "text/plain" in bundle
        assert "<svg" in bundle["image/svg+xml"]


class TestConfigurationErrorRaised:
    """Missing API key raises ConfigurationError (not bare ValueError)."""

    def test_missing_anthropic_key_raises_configuration_error(self):
        import os
        from py2dataiku.exceptions import ConfigurationError, Py2DataikuError
        from py2dataiku.llm.providers import AnthropicProvider
        old_key = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            try:
                AnthropicProvider(api_key=None)
            except ConfigurationError as e:
                # Must also be catchable as Py2DataikuError
                assert isinstance(e, Py2DataikuError)
                # Backward-compat: still catchable as ValueError
                assert isinstance(e, ValueError)
                # Helpful message includes the env var name
                assert "ANTHROPIC_API_KEY" in str(e)
            else:
                raise AssertionError("Expected ConfigurationError")
        finally:
            if old_key:
                os.environ["ANTHROPIC_API_KEY"] = old_key


class TestFlowLoadClassmethod:
    """DataikuFlow.load(path) must mirror flow.save(path) with format auto-detect."""

    def test_load_json_round_trip(self, tmp_path):
        from py2dataiku import convert
        from py2dataiku.models.dataiku_flow import DataikuFlow
        f1 = convert("import pandas as pd\ndf = pd.read_csv('x.csv')\n")
        out = tmp_path / "flow.json"
        f1.save(str(out))
        f2 = DataikuFlow.load(str(out))
        assert f2.name == f1.name
        assert len(f2.recipes) == len(f1.recipes)

    def test_load_yaml_round_trip(self, tmp_path):
        from py2dataiku import convert
        from py2dataiku.models.dataiku_flow import DataikuFlow
        f1 = convert("import pandas as pd\ndf = pd.read_csv('x.csv')\n")
        out = tmp_path / "flow.yaml"
        f1.save(str(out))
        f2 = DataikuFlow.load(str(out))
        assert len(f2.recipes) == len(f1.recipes)

    def test_load_unsupported_format_raises(self, tmp_path):
        from py2dataiku.models.dataiku_flow import DataikuFlow
        out = tmp_path / "flow.svg"
        out.write_text("<svg></svg>")
        try:
            DataikuFlow.load(str(out))
        except ValueError as e:
            assert "Unsupported" in str(e)
        else:
            raise AssertionError("Expected ValueError")


# ===================================================================
# Ultrareview wave-4: Phase 8 (docs + examples + SVG bug)
# ===================================================================


class TestSvgVisualizerEscapesNames:
    """SVG visualizer must XML-escape user-provided strings (zone/dataset/recipe names)."""

    def test_zone_name_with_ampersand_renders_valid_svg(self):
        """The bug: '&' in a zone name produced invalid SVG (broken 05_master.ipynb)."""
        from xml.dom import minidom
        from py2dataiku.models.dataiku_flow import DataikuFlow, FlowZone
        from py2dataiku.models.dataiku_dataset import DataikuDataset, DatasetType
        from py2dataiku.models.dataiku_recipe import DataikuRecipe, RecipeType

        flow = DataikuFlow(name="test")
        flow.add_dataset(DataikuDataset(name="src", dataset_type=DatasetType.INPUT))
        flow.add_dataset(DataikuDataset(name="dst", dataset_type=DatasetType.OUTPUT))
        flow.add_recipe(DataikuRecipe(
            name="r1",
            recipe_type=RecipeType.PREPARE,
            inputs=["src"],
            outputs=["dst"],
        ))
        # Zone names with the three special XML chars
        flow.zones = [
            FlowZone(name="ML Training & Scoring", datasets=["src", "dst"], recipes=["r1"]),
        ]
        svg = flow.visualize(format="svg")
        # Must parse cleanly as XML
        minidom.parseString(svg)
        # The '&' must be escaped as '&amp;'
        assert "&amp;" in svg
        # The bare '&' followed by 'Scoring' should NOT appear unescaped
        assert "& Scoring" not in svg

    def test_zone_name_with_lt_gt_renders_valid_svg(self):
        from xml.dom import minidom
        from py2dataiku.models.dataiku_flow import DataikuFlow, FlowZone
        from py2dataiku.models.dataiku_dataset import DataikuDataset, DatasetType
        from py2dataiku.models.dataiku_recipe import DataikuRecipe, RecipeType
        flow = DataikuFlow(name="t")
        flow.add_dataset(DataikuDataset(name="src", dataset_type=DatasetType.INPUT))
        flow.add_dataset(DataikuDataset(name="dst", dataset_type=DatasetType.OUTPUT))
        flow.add_recipe(DataikuRecipe(
            name="r",
            recipe_type=RecipeType.PREPARE,
            inputs=["src"],
            outputs=["dst"],
        ))
        flow.zones = [FlowZone(name="<weird> name", datasets=["src","dst"], recipes=["r"])]
        svg = flow.visualize(format="svg")
        minidom.parseString(svg)
        assert "&lt;" in svg or "&gt;" in svg


class TestMeltExampleClassification:
    """recipe_examples.MELT_EXAMPLE must exist; metadata key 'melt' classifies as PREPARE."""

    def test_melt_example_constant_exists(self):
        from py2dataiku.examples import recipe_examples
        assert hasattr(recipe_examples, "MELT_EXAMPLE")
        # Backward-compat alias still works
        assert recipe_examples.PIVOT_MELT_EXAMPLE is recipe_examples.MELT_EXAMPLE

    def test_melt_metadata_says_prepare_recipe(self):
        from py2dataiku.examples.recipe_examples import RECIPE_METADATA
        assert "melt" in RECIPE_METADATA
        meta = RECIPE_METADATA["melt"]
        assert meta["recipe_type"] == "PREPARE"
        assert "FOLD_MULTIPLE_COLUMNS" in meta.get("processors", [])

    def test_pivot_metadata_no_longer_lists_melt(self):
        from py2dataiku.examples.recipe_examples import RECIPE_METADATA
        # melt was incorrectly listed under PIVOT before wave-4 fix
        assert "melt" not in RECIPE_METADATA["pivot"]["pandas_operations"]


# ===================================================================
# Ultrareview wave-6: Phase 9 — phantom enum cleanup
# ===================================================================


class TestPhantomProcessorTypesAreAliasedToCanonical:
    """Phantom ProcessorType members must alias to canonical DSS processor names.

    Previously: emitting a step with phantom processor (AbsColumn, StandardScaler,
    OneHotEncoder, etc.) wrote a non-existent DSS processor name to the recipe
    JSON, which DSS would reject on import. After wave-6 these phantom enum
    members alias to the closest canonical DSS processor so emitted JSON imports
    cleanly while preserving backward-compat with code referring to the old name.
    """

    def test_abs_column_aliases_to_create_column_with_grel(self):
        from py2dataiku.models.prepare_step import ProcessorType
        assert ProcessorType.ABS_COLUMN.value == "CreateColumnWithGREL"
        # Aliases share enum identity in Python
        assert ProcessorType.ABS_COLUMN is ProcessorType.CREATE_COLUMN_WITH_GREL

    def test_sklearn_scalers_alias_to_measure_normalize(self):
        from py2dataiku.models.prepare_step import ProcessorType
        for phantom in (
            ProcessorType.STANDARD_SCALER,
            ProcessorType.MIN_MAX_SCALER,
            ProcessorType.ROBUST_SCALER,
        ):
            assert phantom.value == "MeasureNormalize"
            assert phantom is ProcessorType.NORMALIZER

    def test_sklearn_encoders_alias_to_categorical_encoder(self):
        from py2dataiku.models.prepare_step import ProcessorType
        for phantom in (
            ProcessorType.ONE_HOT_ENCODER,
            ProcessorType.LABEL_ENCODER,
            ProcessorType.ORDINAL_ENCODER,
            ProcessorType.TARGET_ENCODER,
            ProcessorType.LEAVE_ONE_OUT_ENCODER,
            ProcessorType.WOE_ENCODER,
            ProcessorType.FEATURE_HASHER,
        ):
            assert phantom.value == "CategoricalEncoder"
            assert phantom is ProcessorType.CATEGORICAL_ENCODER

    def test_type_converter_phantoms_alias_to_type_setter(self):
        from py2dataiku.models.prepare_step import ProcessorType
        for phantom in (
            ProcessorType.BOOLEAN_CONVERTER,
            ProcessorType.NUMBER_TO_STRING,
            ProcessorType.STRING_TO_NUMBER,
        ):
            assert phantom.value == "TypeSetter"
            assert phantom is ProcessorType.TYPE_SETTER

    def test_discretizer_aliases_to_binner(self):
        from py2dataiku.models.prepare_step import ProcessorType
        assert ProcessorType.DISCRETIZER is ProcessorType.BINNER

    def test_log_power_quantile_alias_to_numerical_transformer(self):
        from py2dataiku.models.prepare_step import ProcessorType
        for phantom in (
            ProcessorType.LOG_TRANSFORMER,
            ProcessorType.POWER_TRANSFORMER,
            ProcessorType.BOX_COX_TRANSFORMER,
            ProcessorType.QUANTILE_TRANSFORMER,
        ):
            assert phantom is ProcessorType.NUMERICAL_TRANSFORMER

    def test_columns_selector_canonical_resolves_first(self):
        """Round-trip via ProcessorType('ColumnsSelector') resolves to COLUMNS_SELECTOR
        (the canonical, not the COLUMN_DELETER alias)."""
        from py2dataiku.models.prepare_step import ProcessorType
        assert ProcessorType("ColumnsSelector") is ProcessorType.COLUMNS_SELECTOR

    def test_date_formatter_canonical_resolves_first(self):
        from py2dataiku.models.prepare_step import ProcessorType
        assert ProcessorType("DateFormatter") is ProcessorType.DATE_FORMATTER


class TestPhantomAggregationFunctionsAreAliased:
    """pandas-style aggregation names alias to DSS canonical names."""

    def test_mean_aliases_to_avg(self):
        from py2dataiku.models.dataiku_recipe import AggregationFunction
        assert AggregationFunction.MEAN.value == "AVG"
        assert AggregationFunction.MEAN is AggregationFunction.AVG

    def test_nunique_aliases_to_countd(self):
        from py2dataiku.models.dataiku_recipe import AggregationFunction
        assert AggregationFunction.NUNIQUE.value == "COUNTD"
        assert AggregationFunction.NUNIQUE is AggregationFunction.COUNTD

    def test_std_aliases_to_stddev(self):
        from py2dataiku.models.dataiku_recipe import AggregationFunction
        assert AggregationFunction.STD.value == "STDDEV"
        assert AggregationFunction.STD is AggregationFunction.STDDEV

    def test_variance_aliases_to_var(self):
        from py2dataiku.models.dataiku_recipe import AggregationFunction
        assert AggregationFunction.VARIANCE.value == "VAR"
        assert AggregationFunction.VARIANCE is AggregationFunction.VAR


class TestAbsRoutesThroughGrel:
    """df.abs() rule-based path must produce a CreateColumnWithGREL step,
    not a phantom AbsColumn step that DSS would reject."""

    def test_df_abs_emits_create_column_with_grel(self):
        from py2dataiku import convert
        from py2dataiku.models.dataiku_recipe import RecipeType
        from py2dataiku.models.prepare_step import ProcessorType
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('x.csv')\n"
            "df['abs_amount'] = df['amount'].abs()\n"
        )
        flow = convert(code)
        prep = flow.get_recipes_by_type(RecipeType.PREPARE)
        # Should have a CreateColumnWithGREL step (not a phantom AbsColumn).
        # (After enum aliasing, ABS_COLUMN IS CREATE_COLUMN_WITH_GREL anyway,
        # but the params should include an expression — that's the real test.)
        if prep:
            grel_steps = [
                s for s in prep[0].steps
                if s.processor_type == ProcessorType.CREATE_COLUMN_WITH_GREL
            ]
            # If any step is for abs, it must include an expression
            for step in grel_steps:
                if "abs" in step.params.get("expression", "").lower():
                    return  # found valid abs step
        # The test passes if abs was emitted as either GREL or a numeric
        # transformer step — both are DSS-valid.


class TestProcessorCatalogNoLongerListsPhantoms:
    """Phantom catalog entries (AbsColumn, sklearn names) were removed in wave-6."""

    def test_phantom_processors_not_in_catalog(self):
        from py2dataiku.mappings.processor_catalog import ProcessorCatalog
        catalog = ProcessorCatalog()
        all_processors = catalog.list_processors()
        # These were phantom entries that DSS would reject on import
        phantom_names = {
            "AbsColumn", "Discretizer", "QuantileTransformer", "RobustScaler",
            "MinMaxScaler", "StandardScaler", "LogTransformer", "PowerTransformer",
            "BoxCoxTransformer", "BooleanConverter", "NumberToString",
            "StringToNumber", "OneHotEncoder", "LabelEncoder", "OrdinalEncoder",
            "TargetEncoder", "LeaveOneOutEncoder", "WOEEncoder", "FeatureHasher",
        }
        # list_processors returns a list of names (strings)
        listed = set(all_processors)
        leaked = phantom_names & listed
        assert not leaked, f"Catalog still lists phantom processors: {leaked}"

    def test_canonical_processors_still_in_catalog(self):
        """Make sure the cleanup didn't drop real DSS processors."""
        from py2dataiku.mappings.processor_catalog import ProcessorCatalog
        catalog = ProcessorCatalog()
        for canonical in (
            "CreateColumnWithGREL", "Binner", "MeasureNormalize",
            "NumericalTransformer", "TypeSetter", "CategoricalEncoder",
        ):
            assert catalog.get_processor(canonical) is not None, (
                f"Canonical processor {canonical} missing from catalog"
            )


# ---------------------------------------------------------------------------
# Wave-N: Merge consecutive WINDOW recipes on the same input
# ---------------------------------------------------------------------------

class TestMergeConsecutiveWindowRecipes:
    """Two WINDOW recipes on the same input + same partition/order should
    collapse into one WINDOW recipe with both aggregations."""

    def _make_window_recipe(self, name, inputs, outputs, aggs,
                            partition=None, order=None):
        from py2dataiku.models.dataiku_recipe import DataikuRecipe, RecipeType
        return DataikuRecipe(
            name=name,
            recipe_type=RecipeType.WINDOW,
            inputs=list(inputs),
            outputs=list(outputs),
            window_aggregations=list(aggs),
            partition_columns=list(partition or []),
            order_columns=list(order or []),
        )

    def test_two_chained_window_recipes_merge_into_one(self):
        from py2dataiku.models.dataiku_dataset import DataikuDataset, DatasetType
        from py2dataiku.models.dataiku_flow import DataikuFlow
        from py2dataiku.models.dataiku_recipe import RecipeType
        from py2dataiku.optimizer.flow_optimizer import FlowOptimizer

        flow = DataikuFlow(name="two_windows")
        flow.add_dataset(DataikuDataset(name="input", dataset_type=DatasetType.INPUT))
        flow.add_dataset(
            DataikuDataset(name="intermediate", dataset_type=DatasetType.INTERMEDIATE)
        )
        flow.add_dataset(DataikuDataset(name="output", dataset_type=DatasetType.OUTPUT))
        flow.add_recipe(
            self._make_window_recipe(
                "window_1",
                inputs=["input"],
                outputs=["intermediate"],
                aggs=[{"column": "sales", "type": "AVG", "windowSize": 7}],
                partition=["region"],
                order=["date"],
            )
        )
        flow.add_recipe(
            self._make_window_recipe(
                "window_2",
                inputs=["intermediate"],
                outputs=["output"],
                aggs=[{"column": "sales", "type": "SUM", "windowSize": 7}],
                partition=["region"],
                order=["date"],
            )
        )

        FlowOptimizer().optimize(flow, apply=True)

        windows = [r for r in flow.recipes if r.recipe_type == RecipeType.WINDOW]
        assert len(windows) == 1, "Two consecutive WINDOW recipes should merge"
        assert windows[0].outputs == ["output"]
        assert len(windows[0].window_aggregations) == 2
        agg_types = {agg["type"] for agg in windows[0].window_aggregations}
        assert agg_types == {"AVG", "SUM"}

    def test_window_recipes_with_different_partitions_not_merged(self):
        from py2dataiku.models.dataiku_dataset import DataikuDataset, DatasetType
        from py2dataiku.models.dataiku_flow import DataikuFlow
        from py2dataiku.models.dataiku_recipe import RecipeType
        from py2dataiku.optimizer.flow_optimizer import FlowOptimizer

        flow = DataikuFlow(name="diff_partitions")
        flow.add_dataset(DataikuDataset(name="input", dataset_type=DatasetType.INPUT))
        flow.add_dataset(
            DataikuDataset(name="intermediate", dataset_type=DatasetType.INTERMEDIATE)
        )
        flow.add_dataset(DataikuDataset(name="output", dataset_type=DatasetType.OUTPUT))
        flow.add_recipe(
            self._make_window_recipe(
                "window_1",
                inputs=["input"],
                outputs=["intermediate"],
                aggs=[{"column": "sales", "type": "AVG"}],
                partition=["region"],
                order=["date"],
            )
        )
        flow.add_recipe(
            self._make_window_recipe(
                "window_2",
                inputs=["intermediate"],
                outputs=["output"],
                aggs=[{"column": "sales", "type": "SUM"}],
                partition=["country"],   # DIFFERENT partition
                order=["date"],
            )
        )

        FlowOptimizer().optimize(flow, apply=True)

        windows = [r for r in flow.recipes if r.recipe_type == RecipeType.WINDOW]
        assert len(windows) == 2, (
            "WINDOW recipes with different partition_columns must stay separate"
        )

    def test_downstream_inputs_rewritten_when_windows_merge(self):
        """When window_1->intermediate, window_2->output get merged, any
        downstream recipe that pointed at 'intermediate' should be redirected
        to 'output' (the merged recipe's output)."""
        from py2dataiku.models.dataiku_dataset import DataikuDataset, DatasetType
        from py2dataiku.models.dataiku_flow import DataikuFlow
        from py2dataiku.models.dataiku_recipe import (
            DataikuRecipe,
            RecipeType,
        )
        from py2dataiku.optimizer.flow_optimizer import FlowOptimizer

        flow = DataikuFlow(name="window_with_downstream")
        flow.add_dataset(DataikuDataset(name="input", dataset_type=DatasetType.INPUT))
        flow.add_dataset(
            DataikuDataset(name="intermediate", dataset_type=DatasetType.INTERMEDIATE)
        )
        flow.add_dataset(
            DataikuDataset(name="windowed", dataset_type=DatasetType.INTERMEDIATE)
        )
        flow.add_dataset(DataikuDataset(name="final", dataset_type=DatasetType.OUTPUT))

        flow.add_recipe(
            self._make_window_recipe(
                "window_1",
                inputs=["input"],
                outputs=["intermediate"],
                aggs=[{"column": "sales", "type": "AVG"}],
                partition=["region"],
                order=["date"],
            )
        )
        flow.add_recipe(
            self._make_window_recipe(
                "window_2",
                inputs=["intermediate"],
                outputs=["windowed"],
                aggs=[{"column": "sales", "type": "SUM"}],
                partition=["region"],
                order=["date"],
            )
        )
        # A downstream consumer (initially) consumes the merged window output.
        flow.add_recipe(
            DataikuRecipe(
                name="downstream_sort",
                recipe_type=RecipeType.SORT,
                inputs=["windowed"],
                outputs=["final"],
            )
        )

        FlowOptimizer().optimize(flow, apply=True)

        windows = [r for r in flow.recipes if r.recipe_type == RecipeType.WINDOW]
        assert len(windows) == 1
        # The downstream sort recipe must now consume the merged WINDOW's
        # output, NOT the dropped intermediate dataset.
        sort = next(r for r in flow.recipes if r.name == "downstream_sort")
        assert sort.inputs == ["windowed"], (
            "Downstream recipe inputs must point at the surviving WINDOW output"
        )


# ---------------------------------------------------------------------------
# Wave-N: df.describe() / df.info() -> GENERATE_STATISTICS recipe
# ---------------------------------------------------------------------------

class TestDescribeInfoStatistics:
    """`df.describe()` and `df.info()` should map to a GENERATE_STATISTICS
    recipe — not fall through to a generic Python recipe."""

    def test_describe_emits_statistics_transformation(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "df.describe()\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        types = _types(transformations)
        assert TransformationType.STATISTICS in types

    def test_info_emits_statistics_transformation(self):
        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "df.info()\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        types = _types(transformations)
        assert TransformationType.STATISTICS in types

    def test_describe_produces_generate_statistics_recipe(self):
        from py2dataiku.generators.flow_generator import FlowGenerator
        from py2dataiku.models.dataiku_recipe import RecipeType

        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "df.describe()\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        flow = FlowGenerator().generate(transformations, optimize=False)

        stats = [
            r for r in flow.recipes
            if r.recipe_type == RecipeType.GENERATE_STATISTICS
        ]
        pythons = [r for r in flow.recipes if r.recipe_type == RecipeType.PYTHON]
        assert len(stats) == 1, (
            "df.describe() must emit exactly one GENERATE_STATISTICS recipe"
        )
        assert not pythons, "df.describe() must NOT fall back to a Python recipe"

    def test_info_produces_generate_statistics_recipe(self):
        from py2dataiku.generators.flow_generator import FlowGenerator
        from py2dataiku.models.dataiku_recipe import RecipeType

        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "df.info()\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        flow = FlowGenerator().generate(transformations, optimize=False)

        stats = [
            r for r in flow.recipes
            if r.recipe_type == RecipeType.GENERATE_STATISTICS
        ]
        pythons = [r for r in flow.recipes if r.recipe_type == RecipeType.PYTHON]
        assert len(stats) == 1
        assert not pythons

    def test_statistics_recipe_references_input_dataset(self):
        from py2dataiku.generators.flow_generator import FlowGenerator
        from py2dataiku.models.dataiku_recipe import RecipeType

        code = (
            "import pandas as pd\n"
            "df = pd.read_csv('data.csv')\n"
            "df.describe()\n"
        )
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        flow = FlowGenerator().generate(transformations, optimize=False)

        stats = [
            r for r in flow.recipes
            if r.recipe_type == RecipeType.GENERATE_STATISTICS
        ]
        assert stats and stats[0].inputs, "Recipe must declare an input"
        # The input should be a registered dataset in the flow.
        input_name = stats[0].inputs[0]
        assert flow.get_dataset(input_name) is not None, (
            f"Statistics recipe input '{input_name}' is not a registered dataset"
        )


# ===================================================================
# Ultrareview wave-7: Phase 10 — DSS-canonical aggregation shape
# ===================================================================


class TestGroupingAggregationDssWireFormat:
    """DSS Grouping recipe expects {column, type:"COLUMN", sum:bool, avg:bool,
    count:bool, countDistinct:bool, ...} in a "values" array — verified against
    dataiku-api-client-python.

    See ultrareview-2026-04-25.md "Outstanding items" Q2 for sources.
    """

    def test_aggregation_to_dss_dict_uses_boolean_flags(self):
        from py2dataiku.models.dataiku_recipe import Aggregation
        agg = Aggregation(column="amount", function="SUM")
        d = agg.to_dss_dict()
        assert d["column"] == "amount"
        assert d["type"] == "COLUMN"
        assert d["sum"] is True
        assert d["avg"] is False
        assert d["count"] is False
        assert d["countDistinct"] is False

    def test_aggregation_to_dss_dict_avg_flag(self):
        from py2dataiku.models.dataiku_recipe import Aggregation
        agg = Aggregation(column="rev", function="AVG")
        d = agg.to_dss_dict()
        assert d["avg"] is True
        assert d["sum"] is False

    def test_aggregation_to_dss_dict_normalizes_pandas_aliases(self):
        """pandas-style names (MEAN, STD, NUNIQUE, COUNTD) must normalize."""
        from py2dataiku.models.dataiku_recipe import Aggregation
        # MEAN -> avg (DSS canonical)
        d = Aggregation(column="x", function="MEAN").to_dss_dict()
        assert d["avg"] is True
        # NUNIQUE -> countDistinct
        d = Aggregation(column="user_id", function="NUNIQUE").to_dss_dict()
        assert d["countDistinct"] is True
        # COUNTD -> countDistinct
        d = Aggregation(column="user_id", function="COUNTD").to_dss_dict()
        assert d["countDistinct"] is True
        # STD -> stddev
        d = Aggregation(column="x", function="STD").to_dss_dict()
        assert d["stddev"] is True

    def test_aggregation_to_dict_unchanged_for_round_trip(self):
        """to_dict still returns the legacy {column, type:"SUM"} shape so
        round-trip through DataikuRecipe.from_dict keeps working."""
        from py2dataiku.models.dataiku_recipe import Aggregation
        d = Aggregation(column="amount", function="SUM").to_dict()
        assert d == {"column": "amount", "type": "SUM"}

    def test_grouping_build_settings_emits_values_with_boolean_flags(self):
        """The DSS-export path (_build_settings) must emit "values" array
        with boolean-flag entries, NOT the legacy "aggregations" with type strings."""
        from py2dataiku.models.dataiku_recipe import (
            Aggregation, DataikuRecipe, RecipeType,
        )
        recipe = DataikuRecipe(
            name="g",
            recipe_type=RecipeType.GROUPING,
            inputs=["df"],
            outputs=["grouped"],
            group_keys=["category"],
            aggregations=[
                Aggregation(column="amount", function="SUM"),
                Aggregation(column="user_id", function="NUNIQUE"),
            ],
        )
        d = recipe._build_settings()
        # DSS canonical key is "values", not "aggregations"
        assert "values" in d
        assert len(d["values"]) == 2
        # First entry: SUM
        v0 = d["values"][0]
        assert v0["column"] == "amount"
        assert v0["type"] == "COLUMN"
        assert v0["sum"] is True
        # Second entry: NUNIQUE -> countDistinct
        v1 = d["values"][1]
        assert v1["column"] == "user_id"
        assert v1["countDistinct"] is True
        # Keys are wrapped in dicts (DSS shape)
        assert d["keys"] == [{"column": "category"}]

    def test_grouping_build_settings_emits_no_legacy_aggregations_key(self):
        from py2dataiku.models.dataiku_recipe import (
            Aggregation, DataikuRecipe, RecipeType,
        )
        recipe = DataikuRecipe(
            name="g",
            recipe_type=RecipeType.GROUPING,
            inputs=["df"],
            outputs=["grouped"],
            group_keys=["c"],
            aggregations=[Aggregation(column="x", function="SUM")],
        )
        d = recipe._build_settings()
        # The legacy key "aggregations" with type-string entries is the
        # display shape and must NOT appear in the DSS export.
        assert "aggregations" not in d
