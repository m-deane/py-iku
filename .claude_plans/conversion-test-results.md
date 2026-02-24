# End-to-End Conversion Test Results

**Date:** 2026-02-24
**Tester:** conversion-tester agent
**Method:** Rule-based `convert()` function (AST analysis, no LLM)
**Scripts tested:** 10

---

## Summary Table

| # | Script Description | Recipes | Correct Types? | Round-trip | Validation | Grade |
|---|---|---|---|---|---|---|
| 1 | Simple clean (CSV read, dropna, save) | 1 PREPARE | YES | PASS | PASS | A |
| 2 | Column transforms (rename, astype, computed col) | 2 PREPARE | PARTIAL | PASS | PASS | B- |
| 3 | Filter + sort + head(20) | 1 SPLIT, 1 SORT, 1 PYTHON | PARTIAL | PASS | FAIL (validation errors) | C+ |
| 4 | Groupby aggregation | 1 GROUPING, 1 PYTHON, 1 SORT | PARTIAL | PASS | PASS | C |
| 5 | Multi-table join | 1 JOIN, 1 SPLIT | PARTIAL | PASS | PASS | B |
| 6 | String processing (.str.strip/upper/lower/replace) | 3 PYTHON | NO | PASS | FAIL (missing dataset) | F |
| 7 | Window functions (rolling, cumsum, rank) | 1 PYTHON, 1 GROUPING, 2 PYTHON | NO | PASS | PASS | D |
| 8 | Pivot + stack | 1 PYTHON, 1 STACK | PARTIAL | PASS | PASS | B- |
| 9 | Full ETL pipeline | 1 PREPARE, 2 JOIN, 1 GROUPING, 1 PYTHON, 1 SPLIT, 1 SORT | PARTIAL | PASS | FAIL (cycle) | C- |
| 10 | ML feature engineering | 2 PREPARE, 1 PYTHON | PARTIAL | PASS | PASS | C |

**Overall: 10/10 round-trip serialization passes, 3/10 validation failures, significant mapping gaps.**

---

## Detailed Findings

### Script 1: Simple clean - Read CSV, drop nulls, save

**Code:**
```python
df = pd.read_csv('customers.csv')
df = df.dropna()
df.to_csv('customers_clean.csv')
```

**Result:** 1 PREPARE recipe with 1 `RemoveRowsOnEmpty` step.

**Assessment:**
- Correct recipe type: YES (PREPARE)
- Correct processor: YES (`RemoveRowsOnEmpty`)
- Output dataset correctly marked as OUTPUT
- API output well-formed

**Issues:** None.
**Grade: A**

---

### Script 2: Column transforms - Rename, type cast, computed column

**Code:**
```python
df = df.rename(columns={'old_name': 'new_name', 'col_a': 'col_b'})
df['price'] = df['price'].astype(float)
df['total'] = df['quantity'] * df['price']
```

**Result:** 2 PREPARE recipes.

**Assessment:**
- PREPARE 1 with `ColumnRenamer` - CORRECT
- PREPARE 2 with `TypeSetter` for astype - CORRECT type, but column is `'unknown'` instead of `'price'`
- Computed column (`df['total'] = df['quantity'] * df['price']`) - NOT captured at all
- Optimization did NOT merge the 2 prepare recipes into 1 (should merge)

**Issues:**
1. **CRITICAL:** `TypeSetter` column is `'unknown'` - the AST analyzer fails to extract the column name from `df['price'].astype(float)` because it's a chained subscript+method call
2. **HIGH:** The computed column assignment (`df['total'] = df['quantity'] * df['price']`) is silently missed - no recipe or step generated
3. **MEDIUM:** Two consecutive PREPARE recipes should be merged by the optimizer

**Grade: B-**

---

### Script 3: Filter + sort + head(20)

**Code:**
```python
df = df[df['price'] > 100]
df = df.sort_values('price', ascending=False)
df = df.head(20)
```

**Result:** 1 SPLIT, 1 SORT, 1 PYTHON.

**Assessment:**
- `df[df['price'] > 100]` correctly mapped to SPLIT recipe
- `sort_values` correctly mapped to SORT recipe with `{'column': 'price', 'order': 'DESC'}`
- `head(20)` falls back to PYTHON recipe - should be TOP_N

**Issues:**
1. **HIGH:** `head(20)` should generate a TOP_N recipe, not a Python fallback. The flow generator has no handler for `TransformationType.HEAD` even though the AST analyzer correctly identifies it.
2. **LOW:** Validation reports errors because `head()` creates a disconnected recipe with missing dataset references.

**Grade: C+**

---

### Script 4: Groupby aggregation

**Code:**
```python
result = df.groupby('category').agg({'amount': 'sum', 'quantity': 'mean', 'id': 'count'})
result = result.sort_values('amount', ascending=False)
```

**Result:** 1 GROUPING (0 aggregations!), 1 PYTHON, 1 SORT.

**Assessment:**
- GROUPING recipe has correct group keys (`['category']`) but **0 aggregations**
- The `.agg()` call in the chain is not parsed - it becomes a Python fallback
- SORT recipe correctly generated

**Issues:**
1. **CRITICAL:** Groupby aggregations are not extracted. The GROUPING recipe has `"aggregations": []`. The chained `.agg({'amount': 'sum', ...})` call is not parsed because the AST analyzer creates a GROUPING transformation for `groupby()` and then treats `.agg()` as an unknown method in the chain.
2. **CRITICAL:** An intermediate dataset named `_chain_step_0` is created - this name would be invalid/confusing in Dataiku DSS.
3. **HIGH:** The Python fallback recipe for `.agg()` has code `"# Complex operation"` - not useful.

**Grade: C**

---

### Script 5: Multi-table join

**Code:**
```python
orders = pd.read_csv('orders.csv')
customers = pd.read_csv('customers.csv')
merged = pd.merge(orders, customers, on='customer_id', how='left')
result = merged[['order_id', 'customer_name', 'amount', 'order_date']]
```

**Result:** 1 JOIN, 1 SPLIT.

**Assessment:**
- JOIN recipe correctly generated with `customer_id` key and `LEFT` join type
- API output is well-structured with proper `joinType`, `joins` settings
- Column selection (`merged[['order_id', ...]]`) is incorrectly mapped to a SPLIT recipe

**Issues:**
1. **HIGH:** Column selection (`df[['col1', 'col2']]`) should map to a PREPARE recipe with `DeleteColumns` or `KeepColumns` processor, not a SPLIT recipe. A SPLIT recipe filters rows by condition, not selects columns. The condition field contains `"['order_id', 'customer_name', 'amount', 'order_date']"` which is nonsensical as a split condition.
2. **LOW:** API input/output format uses `{"ref": "name"}` which matches Dataiku DSS API expectations.

**Grade: B**

---

### Script 6: String processing

**Code:**
```python
df['name'] = df['name'].str.strip()
df['name'] = df['name'].str.upper()
df['email'] = df['email'].str.lower()
df['phone'] = df['phone'].str.replace('-', '')
```

**Result:** 3 PYTHON recipes, all marked as unknown.

**Assessment:**
- ALL string operations fall back to Python recipes
- None of the `.str.strip()`, `.str.upper()`, `.str.lower()`, `.str.replace()` are mapped to Dataiku processors
- Expected: PREPARE recipe with `STRING_TRANSFORMER` (TO_UPPER, TO_LOWER, TRIM) and `FIND_REPLACE` processors

**Issues:**
1. **CRITICAL:** The AST analyzer does not properly handle the `df['col'].str.method()` pattern when it appears as `df['col'] = df['col'].str.method()`. The subscript assignment pattern short-circuits to `_handle_binop` or similar before reaching the `.str` accessor handler.
2. **CRITICAL:** Dataset name `df['name']` is generated instead of a clean name - this would fail in Dataiku DSS API.

**Grade: F**

---

### Script 7: Window functions

**Code:**
```python
df['rolling_avg'] = df['value'].rolling(7).mean()
df['cumulative'] = df['value'].cumsum()
df['rank'] = df['value'].rank(method='dense')
```

**Result:** 4 recipes (1 PYTHON, 1 GROUPING, 2 PYTHON).

**Assessment:**
- `rolling(7).mean()` - falls back to PYTHON (should be WINDOW recipe with MOVING_AVG)
- `cumsum()` - incorrectly mapped to GROUPING (should be WINDOW recipe with RUNNING_SUM)
- `rank()` - falls back to PYTHON (should be WINDOW recipe with RANK)
- None of the window operations generate a WINDOW recipe

**Issues:**
1. **CRITICAL:** The flow generator has no handler for `TransformationType.ROLLING` even though the AST analyzer correctly identifies rolling/cumsum/rank as ROLLING transformations with appropriate window_function parameters. They all fall through to the `else` branch and become Python recipes.
2. **HIGH:** `cumsum()` is incorrectly classified as GROUPBY by the dispatch chain (because `sum` matches the aggregation method handler), not as ROLLING.
3. **CRITICAL:** Dataset names like `df['rolling_avg']` are invalid for Dataiku DSS.

**Grade: D**

---

### Script 8: Pivot + stack

**Code:**
```python
pivoted = df.pivot_table(index='region', columns='product', values='amount', aggfunc='sum')
combined = pd.concat([pivoted, df2])
```

**Result:** 1 PYTHON (for pivot), 1 STACK.

**Assessment:**
- `pivot_table()` falls back to PYTHON - should be PIVOT recipe
- `pd.concat()` correctly maps to STACK recipe with correct inputs

**Issues:**
1. **HIGH:** The flow generator has no handler for `TransformationType.PIVOT` - it falls through to Python recipe. The AST analyzer correctly identifies it but the generator doesn't handle it.
2. **LOW:** STACK recipe API output is well-formed.

**Grade: B-**

---

### Script 9: Full ETL pipeline

**Code:** Multi-step pipeline with reads, dropna, drop_duplicates, joins, groupby, filter, sort, save.

**Result:** 7 recipes (1 PREPARE, 2 JOIN, 1 GROUPING, 1 PYTHON, 1 SPLIT, 1 SORT).

**Assessment:**
- PREPARE recipe correctly merges `dropna` + `drop_duplicates` into one recipe with 2 steps
- Both JOIN recipes correctly generated with keys and LEFT join type
- GROUPING recipe has group keys but **0 aggregations** (same bug as Script 4)
- `.agg()` falls through to PYTHON recipe
- Filter (`regional[regional['amount'] > 10000]`) becomes a SPLIT recipe

**Issues:**
1. **CRITICAL:** **DAG CYCLE detected** - the SPLIT recipe for `regional = regional[regional['amount'] > 10000]` generates both input and output as `regional`, creating a cycle. This would break Dataiku DSS which requires DAGs to be acyclic.
2. **CRITICAL:** Aggregations empty in GROUPING recipe (same as Script 4).
3. **HIGH:** `_chain_step_0` intermediate dataset name is generated.
4. **HIGH:** The SPLIT recipe condition is `"regional['amount'] > 10000"` - this is a Python expression, not a Dataiku-compatible filter formula.

**Grade: C-**

---

### Script 10: ML feature engineering

**Code:**
```python
df = df.dropna()
df['category_encoded'] = df['category'].astype(int)
df['amount_log'] = np.log1p(df['amount'])
df['price_quantity'] = df['price'] * df['quantity']
X_train, X_test = train_test_split(df, test_size=0.2, random_state=42)
```

**Result:** 2 PREPARE, 1 PYTHON.

**Assessment:**
- `dropna()` correctly mapped to PREPARE with `RemoveRowsOnEmpty`
- `astype(int)` generates PREPARE with `TypeSetter` but column is `'unknown'` (same bug as Script 2)
- `np.log1p()` correctly identified but falls back to Python recipe (no NUMERIC_TRANSFORM handler in flow generator)
- Computed column (`df['price_quantity']`) is silently missed
- `train_test_split` is silently missed (creates a FILTER transformation but it goes to a different variable group)

**Issues:**
1. **HIGH:** `TypeSetter` column is `'unknown'` - same subscript parsing bug
2. **HIGH:** `np.log1p()` should map to PREPARE recipe with `NumericalTransformer` processor, not Python
3. **HIGH:** `train_test_split` should generate a SPLIT recipe but is lost
4. **MEDIUM:** Interaction feature (`df['price'] * df['quantity']`) is not captured

**Grade: C**

---

## Issue Summary by Severity

### CRITICAL (would break Dataiku API)

| # | Issue | Scripts Affected |
|---|---|---|
| C1 | **DAG cycle when variable is reassigned with filter** - `regional = regional[cond]` creates input=output=same dataset, creating an illegal cycle | 9 |
| C2 | **Groupby aggregations not extracted** - `.agg({})` in method chain not parsed; GROUPING recipes have empty aggregation list | 4, 9 |
| C3 | **Invalid dataset names** - Names like `df['name']`, `df['rolling_avg']`, `_chain_step_0` would fail DSS API validation | 2, 6, 7, 9, 10 |
| C4 | **String operations all fall back to Python** - `.str.strip()`, `.str.upper()`, `.str.lower()`, `.str.replace()` not mapped | 6 |

### HIGH (incorrect mapping, wrong recipe type)

| # | Issue | Scripts Affected |
|---|---|---|
| H1 | **`head(n)` not mapped to TOP_N** - falls to Python recipe | 3 |
| H2 | **Column selection mapped to SPLIT instead of PREPARE** - `df[['col1','col2']]` generates a SPLIT, should be KeepColumns/DeleteColumns | 5, 9 |
| H3 | **Window functions not mapped to WINDOW recipe** - `rolling()`, `cumsum()`, `rank()` all fall to Python despite correct AST analysis | 7 |
| H4 | **Pivot not mapped to PIVOT recipe** - falls to Python | 8 |
| H5 | **`TypeSetter` column is `'unknown'`** - subscript+method chain (`df['col'].astype()`) doesn't extract column name | 2, 10 |
| H6 | **`np.log1p()` and other numeric transforms not mapped** - `TransformationType.NUMERIC_TRANSFORM` has no flow generator handler | 10 |
| H7 | **`train_test_split` not mapped to SPLIT recipe** - transformation is generated but lost in variable grouping | 10 |
| H8 | **Split condition is raw Python expression** - `regional['amount'] > 10000` not converted to Dataiku filter formula | 3, 9 |

### MEDIUM (suboptimal but functional)

| # | Issue | Scripts Affected |
|---|---|---|
| M1 | **Consecutive PREPARE recipes not merged** - optimizer should merge when they share input/output chain | 2, 10 |
| M2 | **Python recipe code is `"# Complex operation"`** - not useful for debugging or manual conversion | 3, 4, 7, 9 |
| M3 | **Computed columns silently dropped** - `df['total'] = df['a'] * df['b']` not captured | 2, 10 |

---

## Root Cause Analysis

### 1. Flow Generator Missing Handlers
The flow generator (`flow_generator.py`) does not handle several `TransformationType` values that the AST analyzer correctly produces:
- `ROLLING` -> should create WINDOW recipe
- `PIVOT` -> should create PIVOT recipe
- `HEAD` -> should create TOP_N recipe
- `NUMERIC_TRANSFORM` -> should create PREPARE step
- `FIT_TRANSFORM`, `FIT`, `PREDICT` -> should create appropriate ML recipes

These all fall through to the `else` branch which creates a Python fallback.

### 2. Method Chain Parsing Limitations
The AST analyzer's method chain handling has gaps:
- `.groupby().agg()` chain: `groupby()` is handled but `.agg()` is treated as unknown
- `.str.strip()`, `.str.upper()`: subscript-based accessor pattern (`df['col'].str.method()`) not properly handled when in assignment context
- `.rolling(7).mean()`: the `.mean()` after `.rolling()` is partially lost

### 3. Variable Reassignment Creates Cycles
When a variable is filtered and reassigned to itself (`df = df[cond]`), the split recipe gets the same name for input and output, creating a DAG cycle. The generator should create a new intermediate dataset name.

### 4. Dataset Naming
Raw Python variable subscript expressions (e.g., `df['name']`) are used directly as dataset names instead of being sanitized to valid Dataiku identifiers.

---

## Phase 2 Readiness Assessment

### Ready for Phase 2 (Dataiku DSS API)
- Simple PREPARE recipes (dropna, drop_duplicates, rename, type cast)
- JOIN recipes (pd.merge with on/left_on/right_on, how)
- SORT recipes
- STACK recipes (pd.concat)
- Basic serialization (to_dict, to_json, to_yaml, round-trip)
- API output format (`to_api_dict()`) matches DSS structure for these recipe types

### NOT Ready for Phase 2
- GROUPING recipes (aggregations always empty)
- WINDOW recipes (never generated)
- PIVOT recipes (never generated)
- TOP_N recipes (never generated from head/nlargest)
- String processing (never mapped to Dataiku processors)
- Numeric transforms (np.log, etc.)
- ML feature engineering (train_test_split, scalers, encoders)
- Any flow where variable reassignment occurs (DAG cycle bug)
- Dataset naming (invalid characters, subscript expressions)

### Recommendation
**The library is NOT ready for Phase 2 in its current state for the rule-based converter.** The critical issues (C1-C4) would cause API failures. The high-priority issues (H1-H8) would produce incorrect or incomplete flows.

Priority fixes before Phase 2:
1. Fix DAG cycle bug (C1) - sanitize output dataset names on reassignment
2. Parse `.agg()` in groupby chains (C2)
3. Sanitize dataset names (C3)
4. Add flow generator handlers for ROLLING->WINDOW, PIVOT, HEAD->TOP_N, NUMERIC_TRANSFORM (H1,H3,H4,H6)
5. Fix column selection mapping (H2)
6. Fix subscript+method column extraction (H5)

The LLM-based converter (`convert_with_llm()`) may handle these cases better but was not tested in this audit.
