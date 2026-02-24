# Pandas Mapping Completeness Audit

**Date:** 2026-02-24
**Tested with:** `py2dataiku.convert()` (rule-based mode)
**Total patterns tested:** 45

## Summary Statistics

| Status | Count | Percentage |
|--------|-------|-----------|
| CORRECT | 12 | 26.7% |
| WRONG_TYPE | 2 | 4.4% |
| MISSING | 5 | 11.1% |
| FALLBACK (Python recipe) | 26 | 57.8% |
| ERROR | 0 | 0.0% |

**Overall correctness rate: 26.7%** -- This means nearly three quarters of mappings either fall back to Python recipes, produce the wrong recipe type, or produce no output at all.

---

## Complete Audit Matrix

### Recipe-Level Patterns (23 patterns)

| # | Pandas Pattern | Expected Dataiku Recipe | Actual Output | Status |
|---|---------------|------------------------|---------------|--------|
| 1 | `df.groupby().agg()` | GROUPING | GROUPING (+ Python fallback for `.agg()` chain) | CORRECT* |
| 2 | `pd.merge(df1, df2)` | JOIN | JOIN | CORRECT |
| 3 | `df.merge(df2)` | JOIN | JOIN | CORRECT |
| 4 | `df.join(df2)` | JOIN | Python recipe | FALLBACK |
| 5 | `pd.concat([df1, df2])` | STACK | STACK | CORRECT |
| 6 | `df.drop_duplicates()` | DISTINCT | PREPARE (RemoveDuplicates) | WRONG_TYPE |
| 7 | `df.sort_values()` | SORT | SORT | CORRECT |
| 8 | `df.pivot()` | PIVOT | Python recipe | FALLBACK |
| 9 | `df.pivot_table()` | PIVOT | Python recipe | FALLBACK |
| 10 | `df.rolling().mean()` | WINDOW | Python recipe | FALLBACK |
| 11 | `df.expanding().sum()` | WINDOW | Python recipe | FALLBACK |
| 12 | `df.cumsum()` | WINDOW | Python recipe | FALLBACK |
| 13 | `df.cumprod()` | WINDOW | Python recipe | FALLBACK |
| 14 | `df.rank()` | WINDOW | Python recipe | FALLBACK |
| 15 | `df.nlargest()` | TOP_N | Python recipe | FALLBACK |
| 16 | `df.nsmallest()` | TOP_N | Python recipe | FALLBACK |
| 17 | `df.head()` | TOP_N | Python recipe | FALLBACK |
| 18 | `df.tail()` | TOP_N | Python recipe | FALLBACK |
| 19 | `df.sample()` | SAMPLING | Python recipe | FALLBACK |
| 20 | `df[condition]` | SPLIT | SPLIT | CORRECT |
| 21 | `df.query()` | SPLIT/FILTER | SPLIT | CORRECT |
| 22 | `df.melt()` | PIVOT (unpivot) | Python recipe | FALLBACK |
| 23 | `df.copy()` | SYNC | No output | MISSING |

*Note: Pattern 1 produces a GROUPING recipe correctly but also generates a spurious Python recipe for the `.agg()` method in the chain, since `.agg()` is not recognized by `_dispatch_method_handler`.

### Processor-Level Patterns (22 patterns)

| # | Pandas Pattern | Expected Processor | Actual Output | Status |
|---|---------------|-------------------|---------------|--------|
| 24 | `df.rename(columns=...)` | ColumnRenamer | PREPARE -> ColumnRenamer | CORRECT |
| 25 | `df.fillna(0)` | FillEmptyWithValue | PREPARE -> FillEmptyWithValue | CORRECT |
| 26 | `df.dropna()` | RemoveRowsOnEmpty | PREPARE -> RemoveRowsOnEmpty | CORRECT |
| 27 | `df['col'].str.upper()` | StringTransformer | Python recipe ("Unknown method: upper") | FALLBACK |
| 28 | `df['col'].str.lower()` | StringTransformer | Python recipe ("Unknown method: lower") | FALLBACK |
| 29 | `df['col'].str.title()` | StringTransformer | Python recipe ("Unknown method: title") | FALLBACK |
| 30 | `df['col'].str.strip()` | StringTransformer | Python recipe ("Unknown method: strip") | FALLBACK |
| 31 | `df['col'].str.replace()` | FindReplace | No output (nothing generated) | MISSING |
| 32 | `df['col'].str.extract()` | RegexpExtractor | Python recipe ("Unknown method: extract") | FALLBACK |
| 33 | `df['col'].str.split()` | SplitColumn | Python recipe ("Unknown method: split") | FALLBACK |
| 34 | `df['col'].astype(int)` | TypeSetter | PREPARE -> TypeSetter | CORRECT |
| 35 | `pd.to_datetime()` | DateParser | No output | MISSING |
| 36 | `pd.cut()` | Binner | Python recipe ("Unknown method: cut") | FALLBACK |
| 37 | `pd.qcut()` | Binner | Python recipe ("Unknown method: qcut") | FALLBACK |
| 38 | `pd.get_dummies()` | OneHotEncoder | Python recipe ("Unknown method: get_dummies") | FALLBACK |
| 39 | `df.drop(columns=...)` | ColumnDeleter | PREPARE -> ColumnDeleter | CORRECT |
| 40 | `df[['col1','col2']]` | ColumnsSelector | SPLIT (misidentified as filter) | WRONG_TYPE |
| 41 | `df['new'] = df['a'] + df['b']` | CreateColumnWithGREL/Formula | No output | MISSING |
| 42 | `np.where()` | CreateColumnWithGREL/IfThenElse | No output | MISSING |
| 43 | `df.abs()` | AbsColumn | Python recipe (numeric_transform not handled) | FALLBACK |
| 44 | `df.round()` | RoundColumn | Python recipe (numeric_transform not handled) | FALLBACK |
| 45 | `df.clip()` | ClipColumn | Python recipe (numeric_transform not handled) | FALLBACK |

---

## Root Cause Analysis

### Issue Category 1: FlowGenerator does not handle many TransformationType values (26 FALLBACK patterns)

The `FlowGenerator._process_transformation_group()` method only explicitly routes these TransformationType values:
- `READ_DATA` -> input dataset
- `FILL_NA`, `DROP_NA`, `DROP_DUPLICATES`, `COLUMN_RENAME`, `COLUMN_DROP`, `COLUMN_CREATE`, `STRING_TRANSFORM`, `TYPE_CAST`, `DATE_PARSE` -> Prepare recipe steps
- `MERGE` -> Join recipe
- `GROUPBY` -> Grouping recipe
- `CONCAT` -> Stack recipe
- `FILTER` -> Split recipe
- `SORT` -> Sort recipe
- `WRITE_DATA` -> output dataset
- `requires_python_recipe=True` -> Python recipe

**Everything else falls through to the `else` clause and generates a Python recipe fallback.** This includes:
- `ROLLING` (cumsum, cumprod, rank, rolling, diff, shift) -> should create WINDOW recipe
- `TOP_N` (nlargest, nsmallest) -> should create TOP_N recipe
- `HEAD` / `TAIL` -> should create TOP_N or SAMPLING recipe
- `SAMPLE` -> should create SAMPLING recipe
- `PIVOT` -> should create PIVOT recipe
- `MELT` -> should create PIVOT recipe (unpivot mode)
- `JOIN` (from df.join()) -> should create JOIN recipe (different from MERGE)
- `NUMERIC_TRANSFORM` (abs, round, clip) -> should create Prepare steps
- `UNKNOWN` (for unrecognized chained methods) -> Python recipe (acceptable)

### Issue Category 2: AST analysis does not detect `.str` accessor patterns correctly (7 FALLBACK patterns)

When code like `df['col'].str.upper()` is analyzed, the AST sees a subscript followed by attribute access chain: `df['col']` -> `.str` -> `.upper()`. The analyzer treats `upper()`, `lower()`, `strip()`, etc. as unknown methods on the subscript result rather than routing through `.str` accessor logic. The `_handle_str_accessor` handler exists in `CodeAnalyzer` but is only matched when `.str` is the immediate method on a known DataFrame variable, not on a subscript expression like `df['col']`.

### Issue Category 3: pd.* function calls not detected (4 MISSING/FALLBACK patterns)

Functions called as `pd.to_datetime()`, `pd.cut()`, `pd.qcut()`, `pd.get_dummies()` are not handled in `_handle_call()`. The code checks for `pd.read_csv`, `pd.read_excel`, `pd.merge`, and `pd.concat` specifically, but other `pd.*` functions are not routed.

### Issue Category 4: Assignment to subscript targets not fully handled (3 MISSING patterns)

When the assignment target is `df['col'] = ...`, the `_handle_assignment` method returns the subscript info but the value analysis (`_analyze_value`) may not generate a transformation if the RHS is a BinOp or a function call that doesn't match known patterns. For example:
- `df['new'] = df['a'] + df['b']` -> BinOp handler generates COLUMN_CREATE but it gets assigned to target `df['new']` and `_process_transformation_group` may not find the input dataset
- `np.where(...)` calls from `import numpy as np` -> handled in ast_analyzer when obj_name is "np" but the generated COLUMN_CREATE transformation may not link to an input dataset

### Issue Category 5: DROP_DUPLICATES mapped as Prepare step instead of DISTINCT recipe

The `_prepare_types()` set includes `TransformationType.DROP_DUPLICATES`, so it becomes a `RemoveDuplicates` Prepare step. While this is technically valid (Dataiku Prepare has a RemoveDuplicates processor), the expected mapping is to a DISTINCT recipe. This is a design choice conflict -- both are valid Dataiku representations but DISTINCT is semantically more accurate as a separate recipe node.

### Issue Category 6: Column selection df[['col1','col2']] misidentified as filter

`_handle_filter` is called for any `ast.Subscript` on a DataFrame, but it doesn't distinguish between row filtering (`df[df['col']>0]`) and column selection (`df[['col1','col2']]`). Column selection should produce a PREPARE recipe with ColumnsSelector processor.

---

## Issues by Severity

### CRITICAL (Phase 2 blockers -- wrong or missing core recipe mappings)

1. **WINDOW recipe never generated**: `ROLLING` TransformationType is not handled in FlowGenerator. Affects: cumsum, cumprod, rank, rolling, diff, shift (6 patterns)
2. **TOP_N recipe never generated**: `TOP_N`, `HEAD`, `TAIL` TransformationTypes not handled. Affects: nlargest, nsmallest, head, tail (4 patterns)
3. **SAMPLING recipe never generated**: `SAMPLE` TransformationType not handled. Affects: sample (1 pattern)
4. **PIVOT recipe never generated**: `PIVOT` and `MELT` TransformationTypes not handled. Affects: pivot, pivot_table, melt (3 patterns)
5. **JOIN recipe not generated from df.join()**: `JOIN` TransformationType (as distinct from `MERGE`) not handled in FlowGenerator. Affects: df.join() (1 pattern)

### HIGH (Common operations produce wrong output)

6. **String accessor methods not detected**: `.str.upper()`, `.str.lower()`, `.str.strip()`, `.str.title()`, `.str.replace()`, `.str.extract()`, `.str.split()` all fail when used as `df['col'].str.method()`. Affects 7 patterns.
7. **NUMERIC_TRANSFORM not handled**: abs(), round(), clip() produce correct TransformationType but FlowGenerator doesn't route them to Prepare steps. Affects 3 patterns.
8. **pd.to_datetime(), pd.cut(), pd.qcut(), pd.get_dummies() not detected**: These pd-level functions are not in the AST analyzer's dispatch. Affects 4 patterns.

### MEDIUM (Semantic incorrectness)

9. **drop_duplicates() maps to Prepare step instead of DISTINCT recipe**: Works but semantically wrong for flow representation. Dataiku DISTINCT recipe is the proper equivalent.
10. **Column selection misidentified as row filter**: `df[['col1','col2']]` produces SPLIT recipe instead of PREPARE with ColumnsSelector.

### LOW (Edge cases or acceptable behavior)

11. **df.copy() produces no output**: Acceptable since copy() is a no-op semantically, but a SYNC recipe would be more accurate.
12. **groupby().agg() generates extra Python recipe**: The GROUPING recipe is created correctly, but the `.agg()` chain step also generates a spurious Python fallback.

---

## Phase 2 Impact Assessment

Phase 2 sends generated flows to the Dataiku API. The impact of these mapping issues:

### Blocking Issues for Phase 2

- **5 entire recipe types never created** (WINDOW, TOP_N, SAMPLING, PIVOT, JOIN-from-join): Any pipeline using these operations will have Python recipe fallbacks instead of native visual recipes. The Dataiku API will create runnable Python recipes, but they won't have proper visual recipe settings, making them opaque and non-visual.

- **String operations all fail**: This is the most common data cleaning operation. Users converting pandas pipelines will see ~100% of string operations fall back to Python recipes.

- **Numeric transformations fall back**: abs/round/clip are common operations that should be Prepare steps but fall through.

### Risk Level: HIGH

The current mapping correctness rate of **26.7%** means that a majority of real-world pandas pipelines will produce flows dominated by Python recipe fallbacks rather than native Dataiku visual recipes. This undermines the core value proposition of the library.

### Recommended Fix Priority

1. **Add FlowGenerator handlers for ROLLING, TOP_N, HEAD, TAIL, SAMPLE, PIVOT, MELT, JOIN**: These are straightforward additions -- the TransformationType and suggested_recipe metadata already exist in the Transformation objects.
2. **Fix `.str` accessor detection in AST analyzer**: The pattern `df['col'].str.method()` needs to be handled in `_handle_dataframe_method` or `_dispatch_method_handler`.
3. **Add pd.to_datetime/pd.cut/pd.qcut/pd.get_dummies to AST analyzer dispatch**.
4. **Add NUMERIC_TRANSFORM to FlowGenerator's `_prepare_types()` set**.
5. **Add column selection detection to differentiate from row filtering**.
6. **Consider moving DROP_DUPLICATES from Prepare step to DISTINCT recipe** (design decision).

---

## Appendix: Test Code Used

Each pattern was tested with minimal code following this template:
```python
from py2dataiku import convert
code = "import pandas as pd\ndf = pd.read_csv('data.csv')\n<operation>"
flow = convert(code)
for recipe in flow:
    print(recipe.recipe_type, [s.processor_type for s in recipe.steps] if recipe.steps else 'N/A')
```

Full audit script: `audit_mappings.py` in project root (temporary, should be deleted after review).
