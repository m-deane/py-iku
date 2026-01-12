# Comprehensive Testing & Enhancement Prompt for py-iku

Use this prompt to thoroughly test the py-iku library and identify areas for improvement.

---

## TESTING INSTRUCTIONS

You are tasked with comprehensively testing **py-iku**, a Python library that converts Python data processing code (pandas, numpy, scikit-learn) to Dataiku DSS recipes, flows, and visual diagrams.

### Phase 1: Environment Setup & Baseline Verification

```bash
# 1. Verify the environment
cd /home/user/py-iku
python --version  # Should be 3.9+

# 2. Install dependencies
pip install -e ".[dev]"  # or: pip install -e . && pip install pytest pytest-cov

# 3. Run the full test suite to establish baseline
python -m pytest tests/ -v --tb=short 2>&1 | tee baseline_test_results.txt

# 4. Generate coverage report
python -m pytest tests/ --cov=py2dataiku --cov-report=html --cov-report=term-missing
```

**Expected Outcome:** 843 tests should pass. Document any failures.

---

### Phase 2: Module-by-Module Deep Testing

#### 2.1 Core Models Testing

Test all data model classes for correctness, edge cases, and serialization:

```python
from py2dataiku.models import (
    DataikuFlow, DataikuRecipe, DataikuDataset, PrepareStep,
    RecipeType, ProcessorType, DatasetType
)

# Test 1: RecipeType enum completeness
print(f"Total RecipeType values: {len(RecipeType)}")
for rt in RecipeType:
    assert rt.value is not None, f"RecipeType {rt.name} has no value"
    print(f"  {rt.name}: {rt.value}")

# Test 2: ProcessorType enum completeness
print(f"\nTotal ProcessorType values: {len(ProcessorType)}")
for pt in ProcessorType:
    assert pt.value is not None, f"ProcessorType {pt.name} has no value"

# Test 3: DataikuRecipe creation and serialization
recipe = DataikuRecipe(
    name="test_recipe",
    recipe_type=RecipeType.PREPARE,
    inputs=["input_dataset"],
    outputs=["output_dataset"],
    settings={"steps": []}
)
assert recipe.to_dict() is not None
assert recipe.to_json() is not None

# Test 4: DataikuFlow creation and all export formats
flow = DataikuFlow(name="test_flow")
flow.add_dataset(DataikuDataset(name="input", dataset_type=DatasetType.INPUT))
flow.add_dataset(DataikuDataset(name="output", dataset_type=DatasetType.OUTPUT))
flow.add_recipe(recipe)

# Test all export methods
assert flow.to_dict() is not None
assert flow.to_json() is not None
assert flow.to_yaml() is not None
assert flow.validate() == []  # No validation errors
print(flow.get_summary())

# Test 5: PrepareStep creation for each ProcessorType
for processor_type in ProcessorType:
    try:
        step = PrepareStep(
            processor_type=processor_type,
            settings={}
        )
        assert step.to_dict() is not None
    except Exception as e:
        print(f"FAILED: {processor_type.name} - {e}")
```

#### 2.2 Parser/AST Analyzer Testing

Test the rule-based code analyzer with various pandas patterns:

```python
from py2dataiku.parser import CodeAnalyzer
from py2dataiku import convert

# Test comprehensive pandas operations
test_cases = [
    # Basic operations
    ("df = pd.read_csv('data.csv')", "read"),
    ("df.to_csv('output.csv')", "write"),
    ("df.dropna()", "PREPARE/REMOVE_ROWS_ON_EMPTY"),
    ("df.fillna(0)", "PREPARE/FILL_EMPTY_WITH_VALUE"),

    # Transformations
    ("df.rename(columns={'a': 'b'})", "PREPARE/COLUMN_RENAMER"),
    ("df.drop(columns=['col'])", "PREPARE/COLUMN_DELETER"),
    ("df['col'].str.upper()", "PREPARE/STRING_TRANSFORMER"),
    ("df['col'].str.lower()", "PREPARE/STRING_TRANSFORMER"),
    ("df['col'].str.strip()", "PREPARE/STRING_TRANSFORMER"),

    # Aggregations
    ("df.groupby('cat').agg({'val': 'sum'})", "GROUPING"),
    ("df.groupby(['a', 'b']).mean()", "GROUPING"),
    ("df.pivot_table(index='a', columns='b', values='c')", "PIVOT"),

    # Joins
    ("pd.merge(df1, df2, on='key')", "JOIN"),
    ("df1.merge(df2, left_on='a', right_on='b')", "JOIN"),
    ("pd.concat([df1, df2])", "STACK"),

    # Sorting and filtering
    ("df.sort_values('col')", "SORT"),
    ("df.sort_values(['a', 'b'], ascending=[True, False])", "SORT"),
    ("df.drop_duplicates()", "DISTINCT"),
    ("df.drop_duplicates(subset=['col'])", "DISTINCT"),
    ("df.nlargest(10, 'col')", "TOP_N"),
    ("df.head(100)", "TOP_N"),

    # Window functions
    ("df['col'].rolling(7).mean()", "WINDOW"),
    ("df['col'].cumsum()", "WINDOW"),
    ("df.groupby('cat')['val'].rank()", "WINDOW"),

    # Type conversions
    ("df['col'].astype(int)", "PREPARE/TYPE_SETTER"),
    ("pd.to_datetime(df['col'])", "PREPARE/DATE_PARSER"),
    ("df['col'].dt.strftime('%Y-%m-%d')", "PREPARE/DATE_FORMATTER"),

    # Binning and encoding
    ("pd.cut(df['col'], bins=5)", "PREPARE/BINNER"),
    ("pd.qcut(df['col'], q=4)", "PREPARE/BINNER"),
    ("pd.get_dummies(df['col'])", "PREPARE/CATEGORICAL_ENCODER"),
]

for code, expected_type in test_cases:
    full_code = f"import pandas as pd\n{code}"
    try:
        flow = convert(full_code)
        print(f"PASS: {code[:50]}... -> {expected_type}")
    except Exception as e:
        print(f"FAIL: {code[:50]}... -> {e}")
```

#### 2.3 LLM Analyzer Testing (if API keys available)

```python
import os
from py2dataiku import convert_with_llm

# Set API key (use environment variable)
# os.environ["ANTHROPIC_API_KEY"] = "your-key"

# Test LLM conversion with complex code
complex_code = '''
import pandas as pd
import numpy as np

# Load data
df = pd.read_csv('sales.csv')

# Clean data
df = df.dropna(subset=['amount', 'date'])
df['date'] = pd.to_datetime(df['date'])
df['amount'] = df['amount'].astype(float)

# Feature engineering
df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month
df['quarter'] = df['date'].dt.quarter

# Aggregation
monthly = df.groupby(['year', 'month', 'category']).agg({
    'amount': ['sum', 'mean', 'count'],
    'quantity': 'sum'
}).reset_index()

# Join with reference data
categories = pd.read_csv('categories.csv')
result = monthly.merge(categories, on='category', how='left')

# Save
result.to_csv('monthly_summary.csv', index=False)
'''

try:
    flow = convert_with_llm(complex_code, provider="anthropic")
    print(f"LLM conversion produced {len(flow.recipes)} recipes")
    print(flow.visualize(format="ascii"))
except Exception as e:
    print(f"LLM conversion failed: {e}")
```

#### 2.4 Visualization Testing

Test all visualization formats with various flow configurations:

```python
from py2dataiku import convert
from py2dataiku.visualizers import SVGVisualizer, HTMLVisualizer, ASCIIVisualizer

# Create a multi-recipe flow
code = '''
import pandas as pd

# Input
df1 = pd.read_csv('customers.csv')
df2 = pd.read_csv('orders.csv')

# Clean
df1 = df1.dropna()
df1['name'] = df1['name'].str.strip()

# Join
merged = df1.merge(df2, on='customer_id')

# Aggregate
summary = merged.groupby('customer_id').agg({'amount': 'sum'})

# Output
summary.to_csv('customer_summary.csv')
'''

flow = convert(code)

# Test all visualization formats
print("=" * 50)
print("ASCII Visualization:")
print("=" * 50)
print(flow.visualize(format="ascii"))

print("\n" + "=" * 50)
print("SVG Visualization (first 500 chars):")
print("=" * 50)
svg = flow.visualize(format="svg")
print(svg[:500] + "..." if len(svg) > 500 else svg)

print("\n" + "=" * 50)
print("HTML Visualization (first 500 chars):")
print("=" * 50)
html = flow.visualize(format="html")
print(html[:500] + "..." if len(html) > 500 else html)

print("\n" + "=" * 50)
print("PlantUML Visualization:")
print("=" * 50)
print(flow.visualize(format="plantuml"))

print("\n" + "=" * 50)
print("Mermaid Visualization:")
print("=" * 50)
print(flow.visualize(format="mermaid"))

# Test theme variations
from py2dataiku.visualizers.themes import DATAIKU_LIGHT, DATAIKU_DARK
print("\nTheme test: Light and Dark themes loaded successfully")
```

#### 2.5 Examples Registry Testing

Verify all examples compile and convert correctly:

```python
from py2dataiku.examples.recipe_examples import RECIPE_EXAMPLES, list_recipe_examples
from py2dataiku.examples.processor_examples import PROCESSOR_EXAMPLES, list_processor_examples
from py2dataiku.examples.combination_examples import COMBINATION_EXAMPLES
from py2dataiku.examples.settings_examples import SETTINGS_EXAMPLES
from py2dataiku import convert

print(f"Testing {len(RECIPE_EXAMPLES)} recipe examples...")
for name, code in RECIPE_EXAMPLES.items():
    try:
        flow = convert(code)
        print(f"  PASS: {name} -> {len(flow.recipes)} recipes")
    except Exception as e:
        print(f"  FAIL: {name} -> {e}")

print(f"\nTesting {len(PROCESSOR_EXAMPLES)} processor examples...")
for name, code in PROCESSOR_EXAMPLES.items():
    try:
        flow = convert(code)
        print(f"  PASS: {name}")
    except Exception as e:
        print(f"  FAIL: {name} -> {e}")

print(f"\nTesting {len(COMBINATION_EXAMPLES)} combination examples...")
for name, code in COMBINATION_EXAMPLES.items():
    try:
        flow = convert(code)
        print(f"  PASS: {name} -> {len(flow.recipes)} recipes, {len(flow.datasets)} datasets")
    except Exception as e:
        print(f"  FAIL: {name} -> {e}")
```

---

### Phase 3: Edge Case & Error Handling Testing

#### 3.1 Invalid Input Handling

```python
from py2dataiku import convert

edge_cases = [
    ("", "Empty code"),
    ("   \n\n  ", "Whitespace only"),
    ("print('hello')", "No pandas operations"),
    ("import pandas as pd", "Import only, no operations"),
    ("x = 1 + 2", "Non-pandas code"),
    ("df = invalid_syntax(", "Syntax error"),
    ("from pandas import *\ndf.nonexistent_method()", "Unknown method"),
    ("df = pd.DataFrame()\n" * 1000, "Very long code"),
]

for code, description in edge_cases:
    try:
        flow = convert(code)
        print(f"HANDLED: {description} -> {len(flow.recipes)} recipes")
    except SyntaxError as e:
        print(f"SYNTAX ERROR (expected): {description}")
    except Exception as e:
        print(f"ERROR: {description} -> {type(e).__name__}: {e}")
```

#### 3.2 Complex Nested Operations

```python
from py2dataiku import convert

# Deeply nested operations
nested_code = '''
import pandas as pd

df = pd.read_csv('data.csv')

# Nested transformations in single statement
result = (
    df
    .dropna()
    .assign(
        new_col=lambda x: x['a'] + x['b'],
        upper_name=lambda x: x['name'].str.upper()
    )
    .query('amount > 100')
    .groupby('category')
    .agg({'amount': 'sum', 'new_col': 'mean'})
    .reset_index()
    .sort_values('amount', ascending=False)
    .head(10)
)
'''

flow = convert(nested_code)
print(f"Nested operations: {len(flow.recipes)} recipes generated")
for recipe in flow.recipes:
    print(f"  - {recipe.recipe_type.value}: {recipe.name}")
```

#### 3.3 Multiple DataFrames and Complex Joins

```python
from py2dataiku import convert

multi_df_code = '''
import pandas as pd

# Multiple inputs
customers = pd.read_csv('customers.csv')
orders = pd.read_csv('orders.csv')
products = pd.read_csv('products.csv')
regions = pd.read_csv('regions.csv')

# Chain of joins
df = customers.merge(orders, on='customer_id')
df = df.merge(products, on='product_id')
df = df.merge(regions, on='region_id')

# Self-join scenario
df2 = df.merge(df, left_on='referrer_id', right_on='customer_id', suffixes=('', '_ref'))

# Output
df2.to_csv('enriched_data.csv')
'''

flow = convert(multi_df_code)
print(f"Multi-join flow: {len(flow.recipes)} recipes, {len(flow.datasets)} datasets")
print(flow.visualize(format="ascii"))
```

---

### Phase 4: Performance Testing

```python
import time
from py2dataiku import convert

# Generate large code samples
def generate_large_pipeline(n_operations):
    lines = ["import pandas as pd", "df = pd.read_csv('data.csv')"]
    for i in range(n_operations):
        lines.append(f"df['col_{i}'] = df['value'] * {i}")
        if i % 10 == 0:
            lines.append(f"df = df.dropna(subset=['col_{i}'])")
    lines.append("df.to_csv('output.csv')")
    return "\n".join(lines)

# Benchmark
sizes = [10, 50, 100, 200, 500]
for size in sizes:
    code = generate_large_pipeline(size)
    start = time.time()
    flow = convert(code)
    elapsed = time.time() - start
    print(f"Operations: {size:3d} | Time: {elapsed:.3f}s | Recipes: {len(flow.recipes)}")
```

---

### Phase 5: Integration Testing

#### 5.1 Full Roundtrip Test

```python
from py2dataiku import convert, Py2Dataiku
import json
import yaml

code = '''
import pandas as pd

df = pd.read_csv('sales.csv')
df = df.dropna()
df['date'] = pd.to_datetime(df['date'])
monthly = df.groupby(df['date'].dt.to_period('M')).sum()
monthly.to_csv('monthly_sales.csv')
'''

# Test all conversion methods
flow1 = convert(code)
flow2 = convert(code, optimize=True)

converter = Py2Dataiku()
flow3 = converter.convert(code)

# Test serialization roundtrip
dict_repr = flow1.to_dict()
json_repr = flow1.to_json()
yaml_repr = flow1.to_yaml()

# Validate JSON is parseable
parsed = json.loads(json_repr)
assert 'datasets' in parsed
assert 'recipes' in parsed

# Validate YAML is parseable
parsed_yaml = yaml.safe_load(yaml_repr)
assert 'datasets' in parsed_yaml

print("All integration tests passed!")
```

---

### Phase 6: Document Test Results

Create a test report documenting:

1. **Test Summary**
   - Total tests run
   - Pass/fail counts
   - Coverage percentage

2. **Failing Tests**
   - Test name
   - Error message
   - Steps to reproduce

3. **Edge Cases Discovered**
   - Inputs that cause unexpected behavior
   - Missing functionality

4. **Performance Metrics**
   - Conversion time for various input sizes
   - Memory usage if measurable

---

## ENHANCEMENT SUGGESTIONS

After testing, evaluate and suggest improvements in these areas:

### A. Feature Enhancements

1. **Additional Recipe Types**
   - Support for more Dataiku plugin recipes
   - Custom recipe template generation
   - Support for SPARK_SCALA and HIVE recipes

2. **Additional Processor Types**
   - ML preprocessing processors (PCA, feature selection)
   - Geospatial processors (geo_join, distance calculations)
   - Advanced text processors (NER, sentiment)

3. **Enhanced pandas Support**
   - `df.apply()` with lambda functions
   - `df.pipe()` for chained operations
   - `df.transform()` for grouped transformations
   - `df.explode()` for list columns
   - `df.melt()` and `df.wide_to_long()`

4. **NumPy Operations**
   - `np.where()` for conditional operations
   - Array operations that map to Dataiku formulas
   - Broadcasting operations

5. **scikit-learn Support**
   - StandardScaler, MinMaxScaler mapping
   - LabelEncoder, OneHotEncoder mapping
   - train_test_split to Split recipe
   - Model.fit() to training recipes

### B. Architecture Improvements

1. **Plugin System**
   - Allow custom recipe type definitions
   - Custom processor type definitions
   - Custom pandas → Dataiku mappings

2. **Incremental Analysis**
   - Cache AST analysis results
   - Support for analyzing code changes only
   - Incremental flow updates

3. **Error Recovery**
   - Graceful degradation for unsupported operations
   - Partial flow generation with warnings
   - Suggested manual interventions

4. **Configuration**
   - YAML/JSON configuration file support
   - Per-project settings
   - Default recipe settings customization

### C. Output Enhancements

1. **Dataiku Export**
   - Direct DSS project export format
   - Flow zone support
   - Recipe code generation for code recipes

2. **Interactive Visualization**
   - Drag-and-drop flow editor
   - Real-time code → flow preview
   - Click-to-inspect recipe details

3. **Documentation Generation**
   - Auto-generate flow documentation
   - Column lineage reports
   - Data quality expectations

### D. Testing Improvements

1. **Property-Based Testing**
   - Use hypothesis for fuzzing
   - Generate random valid pandas code
   - Test invariants across conversions

2. **Snapshot Testing**
   - Golden file tests for visualizations
   - Regression detection for flow structure

3. **Integration Tests**
   - Test against actual Dataiku DSS instance
   - Validate generated recipes execute correctly

### E. Developer Experience

1. **CLI Improvements**
   - `py2dataiku convert input.py --output flow.json`
   - Watch mode for development
   - Config file support

2. **IDE Integration**
   - VS Code extension
   - Jupyter notebook integration
   - Real-time flow preview

3. **Debugging**
   - Verbose logging mode
   - Step-by-step conversion trace
   - Mapping explanation output

---

## PRIORITY MATRIX

| Enhancement | Impact | Effort | Priority |
|-------------|--------|--------|----------|
| scikit-learn support | High | Medium | P1 |
| Plugin system | High | High | P1 |
| More pandas operations | High | Low | P1 |
| Interactive visualization | Medium | High | P2 |
| Direct DSS export | High | Medium | P2 |
| Property-based testing | Medium | Medium | P2 |
| CLI improvements | Medium | Low | P3 |
| IDE integration | Medium | High | P3 |

---

## DELIVERABLES

After completing the testing and analysis, provide:

1. **Test Results Report** (`.claude_plans/test_results_report.md`)
   - Summary statistics
   - Detailed failure analysis
   - Coverage gaps identified

2. **Enhancement Proposal** (`.claude_plans/enhancement_proposal.md`)
   - Prioritized feature list
   - Implementation approach for top 3 features
   - Estimated complexity for each

3. **Bug/Issue List** (`.claude_plans/issues_found.md`)
   - Reproducible bug reports
   - Edge cases to handle
   - Documentation gaps

4. **Code Changes**
   - Fix critical bugs found
   - Add missing test cases
   - Improve error messages

---

## EXECUTION COMMAND

Run this full test suite:

```bash
cd /home/user/py-iku

# Run all phases
python -m pytest tests/ -v --tb=short 2>&1 | tee .claude_plans/test_output.txt
python -m pytest tests/ --cov=py2dataiku --cov-report=html

# Run custom comprehensive tests
python -c "
# Paste the test code from Phase 2-5 above
"
```

Good luck testing!
