# Comprehensive Dataiku Recipe, Processor & Settings Examples Generator

## Objective

Create a complete set of Python code examples and tests that cover **every** Dataiku DSS recipe type, processor type, and setting - both individually and in combination. These examples should be convertible by py2dataiku and generate the corresponding Dataiku flow configurations.

---

## Part 1: Recipe Types

Generate Python code examples that map to each of these Dataiku recipe types:

### Visual Recipes (15 types)

| Recipe Type | Dataiku Purpose | Python Pattern to Detect |
|-------------|-----------------|-------------------------|
| **PREPARE** | Data transformation with processors | Column transformations, string ops, type conversions |
| **SYNC** | Copy data between datasets | `df.copy()`, dataset replication |
| **GROUPING** | Aggregate data by groups | `df.groupby().agg()` |
| **WINDOW** | Window/analytic functions | `df.groupby().transform()`, `.rolling()`, `.expanding()`, `.cumsum()` |
| **JOIN** | Combine datasets | `pd.merge()`, `df.join()` |
| **FUZZY_JOIN** | Approximate matching joins | Fuzzy string matching with joins |
| **GEO_JOIN** | Geographic spatial joins | Geospatial joins using lat/lon |
| **STACK** | Vertically combine datasets | `pd.concat([df1, df2])` |
| **SPLIT** | Filter/partition data | `df[condition]`, boolean filtering |
| **SORT** | Order rows | `df.sort_values()` |
| **DISTINCT** | Remove duplicates | `df.drop_duplicates()` |
| **TOP_N** | Select top/bottom N rows | `df.head()`, `df.nlargest()`, `df.nsmallest()` |
| **PIVOT** | Reshape data | `df.pivot()`, `df.pivot_table()`, `df.melt()` |
| **SAMPLING** | Random sampling | `df.sample()` |
| **DOWNLOAD** | Download from external source | URL/API data fetching |

### Code Recipes (3 types)

| Recipe Type | Purpose | Python Pattern |
|-------------|---------|----------------|
| **PYTHON** | Custom Python code | Complex operations not mappable to visual recipes |
| **SQL** | SQL queries | SQL-like operations, `pd.read_sql()` |
| **R** | R code | R integration patterns |

### ML Recipes (3 types)

| Recipe Type | Purpose | Python Pattern |
|-------------|---------|----------------|
| **PREDICTION_SCORING** | Apply trained model | `model.predict()` |
| **CLUSTERING_SCORING** | Apply clustering model | `kmeans.predict()` |
| **EVALUATION** | Model evaluation | `accuracy_score()`, `classification_report()` |

---

## Part 2: Processor Types (for Prepare Recipe)

Generate Python code examples that map to each processor type:

### Column Manipulation (4 types)

| Processor | Dataiku Purpose | Python Pattern |
|-----------|-----------------|----------------|
| **COLUMN_RENAMER** | Rename columns | `df.rename(columns={...})` |
| **COLUMN_COPIER** | Duplicate columns | `df['new'] = df['old']` |
| **COLUMN_DELETER** | Remove columns | `df.drop(columns=[...])` |
| **COLUMNS_SELECTOR** | Select subset of columns | `df[['col1', 'col2']]` |

### Missing Value Handling (3 types)

| Processor | Dataiku Purpose | Python Pattern |
|-----------|-----------------|----------------|
| **FILL_EMPTY_WITH_VALUE** | Fill with constant | `df.fillna(value)` |
| **REMOVE_ROWS_ON_EMPTY** | Drop rows with nulls | `df.dropna()` |
| **FILL_EMPTY_WITH_PREVIOUS_NEXT** | Forward/backward fill | `df.fillna(method='ffill')`, `df.fillna(method='bfill')` |

### String Transformations (7 types)

| Processor | Dataiku Purpose | Python Pattern |
|-----------|-----------------|----------------|
| **STRING_TRANSFORMER** | Case, trim, normalize | `str.upper()`, `str.lower()`, `str.strip()`, `str.title()` |
| **TOKENIZER** | Split into tokens | `str.split()` |
| **REGEXP_EXTRACTOR** | Extract with regex | `str.extract(pattern)` |
| **FIND_REPLACE** | Find and replace | `str.replace()` |
| **SPLIT_COLUMN** | Split column into multiple | `str.split(expand=True)` |
| **CONCAT_COLUMNS** | Combine columns | String concatenation with `+` |
| **HTML_STRIPPER** | Remove HTML tags | HTML/tag removal patterns |

### Numeric Transformations (6 types)

| Processor | Dataiku Purpose | Python Pattern |
|-----------|-----------------|----------------|
| **NUMERICAL_TRANSFORMER** | Math operations | `* / + - **` on columns |
| **ROUND_COLUMN** | Round numbers | `df.round()` |
| **ABS_COLUMN** | Absolute value | `df.abs()` |
| **CLIP_COLUMN** | Clip to range | `df.clip(lower, upper)` |
| **BINNER** | Create bins/buckets | `pd.cut()`, `pd.qcut()` |
| **NORMALIZER** | Normalize/scale values | Min-max scaling, z-score |

### Type Conversion (3 types)

| Processor | Dataiku Purpose | Python Pattern |
|-----------|-----------------|----------------|
| **TYPE_SETTER** | Change column type | `df.astype()` |
| **DATE_PARSER** | Parse date strings | `pd.to_datetime()` |
| **DATE_FORMATTER** | Format dates | `dt.strftime()` |

### Filtering Processors (5 types)

| Processor | Dataiku Purpose | Python Pattern |
|-----------|-----------------|----------------|
| **FILTER_ON_VALUE** | Filter by value | `df[df['col'] == value]` |
| **FILTER_ON_BAD_TYPE** | Filter type mismatches | Type validation filters |
| **FILTER_ON_FORMULA** | Filter by expression | Complex boolean expressions |
| **FILTER_ON_DATE_RANGE** | Filter by date range | Date range comparisons |
| **FILTER_ON_NUMERIC_RANGE** | Filter by numeric range | `df[(df['x'] >= a) & (df['x'] <= b)]` |

### Flagging Processors (3 types)

| Processor | Dataiku Purpose | Python Pattern |
|-----------|-----------------|----------------|
| **FLAG_ON_VALUE** | Create flag column | `df['flag'] = (df['col'] == val).astype(int)` |
| **FLAG_ON_FORMULA** | Flag by expression | Boolean column creation |
| **FLAG_ON_BAD_TYPE** | Flag type issues | Type checking flags |

### Row Operations (3 types)

| Processor | Dataiku Purpose | Python Pattern |
|-----------|-----------------|----------------|
| **REMOVE_DUPLICATES** | Remove duplicate rows | `df.drop_duplicates()` |
| **SORT_ROWS** | Sort rows | `df.sort_values()` |
| **SAMPLE_ROWS** | Sample rows | `df.sample()` |

### Computed Columns (2 types)

| Processor | Dataiku Purpose | Python Pattern |
|-----------|-----------------|----------------|
| **CREATE_COLUMN_WITH_GREL** | GREL expression column | Complex column formulas |
| **FORMULA** | Formula column | `df['new'] = df['a'] + df['b']` |

### Categorical Processors (2 types)

| Processor | Dataiku Purpose | Python Pattern |
|-----------|-----------------|----------------|
| **MERGE_LONG_TAIL_VALUES** | Combine rare categories | Category aggregation |
| **CATEGORICAL_ENCODER** | Encode categories | `pd.get_dummies()`, label encoding |

### Geographic Processors (2 types)

| Processor | Dataiku Purpose | Python Pattern |
|-----------|-----------------|----------------|
| **GEO_POINT_CREATOR** | Create geo points | Lat/lon to point conversion |
| **GEO_ENCODER** | Geocode addresses | Address to coordinates |

### Fallback (1 type)

| Processor | Dataiku Purpose | Python Pattern |
|-----------|-----------------|----------------|
| **PYTHON_UDF** | Custom Python function | `df.apply(custom_func)` |

---

## Part 3: Recipe Settings

### Join Settings

| Setting | Values | Python Pattern |
|---------|--------|----------------|
| **JoinType** | INNER, LEFT, RIGHT, OUTER, CROSS | `how='inner/left/right/outer/cross'` |
| **JoinKey** | Column pairs | `on='col'`, `left_on/right_on` |

### Aggregation Functions (for Grouping)

| Function | Purpose | Python Pattern |
|----------|---------|----------------|
| SUM | Sum values | `.sum()` |
| AVG/MEAN | Average | `.mean()` |
| COUNT | Count rows | `.count()` |
| MIN | Minimum | `.min()` |
| MAX | Maximum | `.max()` |
| FIRST | First value | `.first()` |
| LAST | Last value | `.last()` |
| STD | Standard deviation | `.std()` |
| VAR | Variance | `.var()` |
| NUNIQUE | Count unique | `.nunique()` |
| MEDIAN | Median value | `.median()` |

### String Transformer Modes

| Mode | Purpose | Python Pattern |
|------|---------|----------------|
| TO_UPPER | Uppercase | `str.upper()` |
| TO_LOWER | Lowercase | `str.lower()` |
| TITLECASE | Title case | `str.title()` |
| TRIM | Remove whitespace | `str.strip()` |
| TRIM_LEFT | Left trim | `str.lstrip()` |
| TRIM_RIGHT | Right trim | `str.rstrip()` |
| NORMALIZE_WHITESPACE | Normalize spaces | Multiple space removal |
| REMOVE_WHITESPACE | Remove all spaces | `str.replace(' ', '')` |

### Numerical Transformer Modes

| Mode | Purpose | Python Pattern |
|------|---------|----------------|
| MULTIPLY | Multiply by constant | `df['col'] * n` |
| DIVIDE | Divide by constant | `df['col'] / n` |
| ADD | Add constant | `df['col'] + n` |
| SUBTRACT | Subtract constant | `df['col'] - n` |
| POWER | Raise to power | `df['col'] ** n` |
| ROUND | Round to decimals | `df['col'].round(n)` |
| FLOOR | Floor division | `np.floor(df['col'])` |
| CEIL | Ceiling | `np.ceil(df['col'])` |

---

## Part 4: Example Generation Requirements

For each recipe type, processor type, and setting, generate:

### A. Individual Examples

```python
# Example structure for each component
EXAMPLE_NAME = """
import pandas as pd
import numpy as np

# Load input data
df = pd.read_csv('input.csv')

# [Specific operation that maps to the recipe/processor]
result = df.[operation]

# Save output
result.to_csv('output.csv', index=False)
"""
```

### B. Combination Examples

Create examples that combine multiple components:

1. **Prepare + Grouping**: Clean data then aggregate
2. **Join + Window**: Combine datasets then calculate rolling metrics
3. **Stack + Split**: Combine datasets then partition
4. **Multiple Processors**: Chain 3+ processors in one prepare recipe
5. **Full Pipeline**: 5+ recipe flow with all recipe types

### C. Test Cases

For each example, generate tests that verify:

```python
def test_example_conversion():
    """Test that code converts to expected Dataiku flow."""
    flow = convert(EXAMPLE_CODE)

    # Verify recipe types generated
    assert any(r.recipe_type == RecipeType.EXPECTED for r in flow.recipes)

    # Verify processors (for Prepare recipes)
    prepare_recipes = [r for r in flow.recipes if r.recipe_type == RecipeType.PREPARE]
    if prepare_recipes:
        steps = prepare_recipes[0].steps
        assert any(s.processor_type == ProcessorType.EXPECTED for s in steps)

    # Verify settings
    assert recipe.join_type == JoinType.EXPECTED  # for joins
    assert aggregation.function == "SUM"  # for grouping

def test_example_visualization():
    """Test that flow can be visualized."""
    flow = convert(EXAMPLE_CODE)
    svg = flow.to_svg()
    assert "<svg" in svg

def test_example_export():
    """Test that flow can be exported."""
    flow = convert(EXAMPLE_CODE)
    json_str = flow.to_json()
    assert len(json_str) > 0
```

---

## Part 5: Comprehensive Combination Matrix

Generate examples for these specific combinations:

### Recipe Combinations (20 combinations)

1. PREPARE → GROUPING → PREPARE (clean → aggregate → format)
2. JOIN → WINDOW → SPLIT (combine → calculate → partition)
3. STACK → DISTINCT → SORT (combine → dedupe → order)
4. GROUPING → PIVOT → PREPARE (aggregate → reshape → clean)
5. SPLIT → JOIN → GROUPING (filter → combine → aggregate)
6. PREPARE → TOP_N → PREPARE (clean → limit → format)
7. SAMPLING → PREPARE → GROUPING (sample → clean → aggregate)
8. JOIN → JOIN → GROUPING (multi-join → aggregate)
9. STACK → STACK → DISTINCT (multi-stack → dedupe)
10. WINDOW → GROUPING → SORT (window → aggregate → order)
11. PREPARE → PYTHON → PREPARE (clean → custom → format)
12. JOIN → SPLIT → STACK (combine → partition → recombine)
13. GROUPING → JOIN → WINDOW (aggregate → combine → window)
14. PIVOT → GROUPING → PIVOT (reshape → aggregate → reshape)
15. DISTINCT → SORT → TOP_N (dedupe → order → limit)
16. PREPARE → JOIN → GROUPING → WINDOW → PREPARE (full ETL)
17. STACK → PREPARE → SPLIT → GROUPING (multi-source ETL)
18. SAMPLING → PREPARE → GROUPING → PIVOT (ML prep pipeline)
19. JOIN → WINDOW → WINDOW → GROUPING (multi-window analytics)
20. PREPARE → DISTINCT → JOIN → GROUPING → TOP_N (complete pipeline)

### Processor Combinations (15 combinations)

1. STRING_TRANSFORMER → FILL_EMPTY → TYPE_SETTER (text pipeline)
2. DATE_PARSER → FORMULA → FILTER_ON_DATE_RANGE (date pipeline)
3. COLUMN_RENAMER → COLUMN_DELETER → COLUMNS_SELECTOR (column pipeline)
4. NUMERICAL_TRANSFORMER → ROUND → CLIP → BINNER (numeric pipeline)
5. REGEXP_EXTRACTOR → SPLIT_COLUMN → CONCAT_COLUMNS (text extraction)
6. FILL_EMPTY → REMOVE_ROWS_ON_EMPTY → REMOVE_DUPLICATES (cleaning)
7. FILTER_ON_VALUE → FLAG_ON_VALUE → CREATE_COLUMN_WITH_GREL (flagging)
8. TYPE_SETTER → NORMALIZER → CATEGORICAL_ENCODER (ML prep)
9. STRING_TRANSFORMER → TOKENIZER → FIND_REPLACE (NLP prep)
10. DATE_PARSER → DATE_FORMATTER → FORMULA (date calculation)
11. All STRING_TRANSFORMER modes in sequence
12. All NUMERICAL_TRANSFORMER modes in sequence
13. All FILTER processors in sequence
14. All FLAG processors in sequence
15. All missing value processors in sequence

### Settings Combinations

1. All JoinType values with same join pattern
2. All aggregation functions on same groupby
3. All StringTransformerMode values on same column
4. All NumericalTransformerMode values on same column
5. Mixed aggregations (SUM + COUNT + AVG + MAX + MIN)
6. Multi-key joins with different JoinTypes
7. Nested groupby with multiple aggregation levels

---

## Part 6: Output Format

Generate the following files:

### 1. `py2dataiku/examples/recipe_examples.py`
```python
"""Examples for every Dataiku recipe type."""

# Individual recipe examples
PREPARE_EXAMPLE = """..."""
GROUPING_EXAMPLE = """..."""
# ... all 21 recipe types

# Recipe combinations
RECIPE_EXAMPLES = {
    "prepare": PREPARE_EXAMPLE,
    "grouping": GROUPING_EXAMPLE,
    # ...
}
```

### 2. `py2dataiku/examples/processor_examples.py`
```python
"""Examples for every Dataiku processor type."""

# Individual processor examples
COLUMN_RENAMER_EXAMPLE = """..."""
FILL_EMPTY_EXAMPLE = """..."""
# ... all 31 processor types

PROCESSOR_EXAMPLES = {
    "column_renamer": COLUMN_RENAMER_EXAMPLE,
    # ...
}
```

### 3. `py2dataiku/examples/settings_examples.py`
```python
"""Examples for every Dataiku recipe setting."""

# Join type examples
INNER_JOIN_EXAMPLE = """..."""
LEFT_JOIN_EXAMPLE = """..."""
# ...

# Aggregation examples
SUM_AGG_EXAMPLE = """..."""
# ...
```

### 4. `py2dataiku/examples/combination_examples.py`
```python
"""Examples combining multiple recipes, processors, and settings."""

# Recipe combinations
PREPARE_GROUPING_PREPARE = """..."""
# ...

# Processor combinations
TEXT_PIPELINE = """..."""
# ...
```

### 5. `tests/test_py2dataiku/test_recipe_examples.py`
```python
"""Tests for all recipe type examples."""

class TestPrepareRecipe:
    def test_conversion(self): ...
    def test_visualization(self): ...
    def test_export(self): ...

# ... for all recipe types
```

### 6. `tests/test_py2dataiku/test_processor_examples.py`
```python
"""Tests for all processor type examples."""
# ... similar structure
```

### 7. `tests/test_py2dataiku/test_combination_examples.py`
```python
"""Tests for all combination examples."""
# ... similar structure
```

---

## Part 7: Metadata and Documentation

For each example, include:

```python
EXAMPLE_METADATA = {
    "name": "example_name",
    "description": "What this example demonstrates",
    "recipe_types": [RecipeType.PREPARE, RecipeType.GROUPING],
    "processor_types": [ProcessorType.FILL_EMPTY, ProcessorType.STRING_TRANSFORMER],
    "settings": {
        "join_type": JoinType.LEFT,
        "aggregations": ["SUM", "COUNT"],
    },
    "pandas_operations": ["fillna", "groupby", "merge"],
    "complexity": "basic|intermediate|advanced",
    "use_case": "Data cleaning and aggregation for reporting",
}
```

---

## Execution Instructions

1. **Generate all individual examples** covering every recipe type, processor type, and setting value
2. **Generate combination examples** covering all specified combinations
3. **Create comprehensive tests** for each example
4. **Verify all examples convert** successfully with py2dataiku
5. **Verify all visualizations** generate correctly
6. **Run complete test suite** and ensure 100% pass rate
7. **Document** any patterns that cannot be automatically detected

---

## Success Criteria

- [ ] All 21 recipe types have at least one example
- [ ] All 31 processor types have at least one example
- [ ] All join types (5) have examples
- [ ] All aggregation functions (11+) have examples
- [ ] All string transformer modes (8) have examples
- [ ] All numerical transformer modes (8) have examples
- [ ] All 20 recipe combinations have examples
- [ ] All 15 processor combinations have examples
- [ ] All tests pass (100%)
- [ ] All examples generate valid visualizations
- [ ] All examples export to valid JSON/YAML

---

## Notes

- Focus on realistic data processing patterns
- Include edge cases (empty data, single row, large datasets)
- Document any patterns that require PYTHON recipe fallback
- Ensure examples are self-contained and runnable
- Use consistent naming conventions
- Include inline comments explaining the Dataiku mapping
