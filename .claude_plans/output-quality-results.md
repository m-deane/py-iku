# Output Quality & Dataiku API Compatibility Review

**Date**: 2026-02-24
**Reviewer**: Task #3 - Output Quality & Dataiku API Compatibility
**Scope**: 5 representative conversions tested across 3 output paths

---

## Executive Summary

py-iku has **three distinct output paths**, each with different API compatibility levels:

| Output Path | Method | Target Use Case | API-Ready |
|---|---|---|---|
| `to_api_dict()` / `to_recipe_configs()` | `DataikuRecipe.to_api_dict()` | Direct API calls (`POST /recipes/`) | **~30%** |
| `DSSExporter.export()` | File-based project bundle | DSS project import | **~65%** |
| `to_dict()` | `DataikuRecipe.to_dict()` | Serialization/display | N/A (not API-facing) |

**Overall Phase 2 Readiness Score: ~40%**

There are **6 BLOCKERS** and **12 significant issues** that must be addressed before MCP integration.

---

## Test Results Detail

### Test A: Simple Clean (read CSV, dropna, save)

**Conversion**: 1 PREPARE recipe, 2 datasets -- CORRECT

| Check | `to_api_dict()` | DSSExporter | Issue |
|---|---|---|---|
| Recipe type string | `"prepare"` -- WRONG | `"shaker"` -- CORRECT | **BLOCKER**: `to_api_dict()` uses `"prepare"` but DSS API requires `"shaker"` |
| Inputs structure | Flat list `[{"ref": "df"}]` -- WRONG | Nested `{"main": {"items": [...]}}` -- CORRECT | **BLOCKER**: `to_api_dict()` uses flat list, API requires role-keyed dict |
| Outputs structure | Flat list `[{"ref": "df_prepared"}]` -- WRONG | Nested `{"main": {"items": [...]}}` -- CORRECT | Same as above |
| Settings key | `"settings"` -- WRONG | `"params"` -- CORRECT | **BLOCKER**: API expects `"params"` not `"settings"` |
| Prepare mode | `"NORMAL"` | `"BATCH"` | DSSExporter uses `"BATCH"` which is more standard |
| Prepare steps | Correct structure | Correct structure | OK |
| Processor type `RemoveRowsOnEmpty` | Correct | Correct | OK |
| Processor params `columns: null` | **ISSUE**: `null` should be `[]` or omitted | Same issue | DSS may reject null columns |
| `deps` field in IO items | Missing | Present `"deps": []` | Minor: `to_api_dict()` missing `deps` |

### Test B: Join (2 CSVs, pd.merge on key)

**Conversion**: 1 JOIN recipe, 3 datasets -- CORRECT

| Check | `to_api_dict()` | DSSExporter | Issue |
|---|---|---|---|
| Recipe type string | `"join"` -- CORRECT | `"join"` -- CORRECT | OK |
| Inputs structure | Flat list -- WRONG | Role-keyed dict -- CORRECT | **BLOCKER** (same as Test A) |
| Join settings location | Under `"settings"` -- WRONG | Under `"params"` -- CORRECT | **BLOCKER** (same) |
| Join structure | Simple `{joinType, joins}` | Full structure with `virtualInputs`, `table1/table2`, `conditionsMode`, `on` | **SIGNIFICANT**: `to_api_dict()` missing `virtualInputs`, `table1/table2` mapping, `conditionsMode` |
| Join `on` nesting | Direct array of `{left, right, matchType}` | Nested inside `joins[].on` with `table1`, `table2`, `conditionsMode` | `to_api_dict()` format won't work with DSS API |
| `enableAutoCastInJoinConditions` | Missing | Present | DSS may default correctly |
| `selectedColumns` | Missing | Present (empty) | OK if API defaults |
| `outputColumnsSelectionMode` | Missing | `"MANUAL"` -- **ISSUE**: Should likely be `"ALL"` by default | May cause empty output |

### Test C: Groupby (groupby + agg with multiple functions)

**Conversion**: 1 GROUPING + 1 PYTHON recipe -- **PARTIALLY WRONG**

| Check | Status | Issue |
|---|---|---|
| Aggregations captured | **EMPTY `aggregations: []`** | **BLOCKER**: `df.groupby('region').agg({'amount': 'sum', 'quantity': 'mean', 'price': 'max'})` produces ZERO aggregations |
| Unnecessary Python fallback | YES | Because agg is not parsed, a Python recipe is created for the `.agg()` call |
| Dataset naming | `_chain_step_0` intermediate | Ugly but functional |
| Grouping keys field | `"keys"` uses `[{"column": "region"}]` | DSSExporter adds `"type": "string"` but `to_api_dict()` does not -- minor |
| DSSExporter uses `"values"` key | Yes (`"values": []`) | DSS API uses `"values"` not `"aggregations"` for the grouping payload -- **SIGNIFICANT mismatch** |

### Test D: Full ETL (read, clean, join, aggregate, filter, sort)

**Conversion**: 5 recipes (PREPARE, JOIN, GROUPING, PYTHON, SORT) -- partially correct

| Check | Status | Issue |
|---|---|---|
| Pipeline chaining | Correct flow: prepare -> join -> grouping -> python -> sort | OK |
| PREPARE (dropna subset) | Correct `RemoveRowsOnEmpty` with `columns: ["amount"]` | OK |
| JOIN (inner on cust_id) | Correct type `INNER`, correct key | OK |
| GROUPING aggregations | **EMPTY** | Same **BLOCKER** as Test C |
| SORT settings | `"sortColumns": [{"column": "amount", "order": "DESC"}]` | **SIGNIFICANT**: DSS API expects `"orders"` not `"sortColumns"`, and uses `"desc": true/false` not `"order": "DESC"` |
| DSSExporter SORT | Uses `"orders"` with `"desc": bool` | **CORRECT** -- but inconsistent with `to_api_dict()` |

### Test E: Multi-processor Prepare (rename + fillna + astype + str.upper)

**Conversion**: 2 PREPARE + 1 PYTHON -- **SIGNIFICANTLY WRONG**

| Check | Status | Issue |
|---|---|---|
| FillEmptyWithValue params | `"column": "unknown", "value": "None"` | **BLOCKER**: Should be `column: "age"` with `value: "0"` AND `column: "city"` with `value: "Unknown"`. Parser produced garbage -- `"unknown"` column and `"None"` as literal string |
| TypeSetter params | `"column": "unknown", "type": "int"` | **BLOCKER**: Column name `"unknown"` instead of `"age"` |
| str.upper() | Falls back to Python recipe | Expected given rule-based limitations, but output dataset name is `"df['city']"` -- **INVALID identifier** |
| Dataset name `df['city']` | Invalid Dataiku identifier | **BLOCKER**: Contains `[` and `'` characters -- will fail DSS API validation |
| Optimizer merging | Two separate PREPARE recipes | Should have been merged into one PREPARE with all steps |
| fillna with dict | Not handled | The dict-based `fillna({'age': 0, 'city': 'Unknown'})` is not properly parsed into multiple FillEmptyWithValue steps |

---

## API Compatibility Matrix

### Recipe Type Mapping (`_get_dss_recipe_type`)

| RecipeType | `to_api_dict()` value | DSSExporter value | DSS API expected | Status |
|---|---|---|---|---|
| PREPARE | `"prepare"` | `"shaker"` | `"shaker"` | **MISMATCH in to_api_dict** |
| JOIN | `"join"` | `"join"` | `"join"` | OK |
| GROUPING | `"grouping"` | `"grouping"` | `"grouping"` | OK |
| SORT | `"sort"` | `"sort"` | `"sort"` | OK |
| DISTINCT | `"distinct"` | `"distinct"` | `"distinct"` | OK |
| STACK | `"stack"` | `"vstack"` | `"vstack"` | **MISMATCH in to_api_dict** |
| PYTHON | `"python"` | `"python"` | `"python"` | OK |
| SQL | `"sql_query"` | `"sql_query"` | `"sql_query"` | OK |
| PIVOT | `"pivot"` | N/A (not in exporter) | `"pivot"` | Unknown |
| WINDOW | `"window"` | N/A (not in exporter) | `"window"` | Unknown |
| TOP_N | `"topn"` | `"topn"` | `"topn"` | OK |
| SAMPLING | `"sampling"` | N/A | `"sampling"` | Unknown |
| SPLIT | `"split"` | N/A | `"split"` | Unknown |
| SYNC | `"sync"` | `"sync"` | `"sync"` | OK |
| DOWNLOAD | `"download"` | `"download"` | `"download"` | OK |

### Input/Output Structure

| Aspect | `to_api_dict()` | DSSExporter | DSS API Required |
|---|---|---|---|
| Inputs format | `[{"ref": "name"}]` (flat list) | `{"main": {"items": [{"ref": "name", "deps": []}]}}` | Role-keyed dict with items array |
| Outputs format | `[{"ref": "name"}]` (flat list) | `{"main": {"items": [{"ref": "name", "deps": []}]}}` | Role-keyed dict with items array |
| Join inputs | All in single flat list | All under `"main"` role | All under `"main"` with `virtualInputs` referencing by index |
| `deps` field | Missing | Present (empty `[]`) | Required (can be empty) |

### Settings/Params Structure

| Aspect | `to_api_dict()` | DSSExporter | DSS API Required |
|---|---|---|---|
| Key name | `"settings"` | `"params"` | `"params"` for file-based, varies for API |
| Engine params | Missing | Present (full hive/spark/impala config) | Required for most recipe types |
| Version tags | Missing | Present | Required |
| Project key | Missing | Present | Required |

---

## BLOCKERS (Must Fix Before Phase 2)

### B1: `to_api_dict()` uses wrong recipe type for PREPARE
- **File**: `py2dataiku/models/dataiku_recipe.py:385`
- `RecipeType.PREPARE.value` returns `"prepare"` but DSS API requires `"shaker"`
- DSSExporter correctly maps this via `_get_dss_recipe_type()`
- **Fix**: Either change the enum value or add mapping in `to_api_dict()`

### B2: `to_api_dict()` uses flat list for inputs/outputs instead of role-keyed dict
- **File**: `py2dataiku/models/dataiku_recipe.py:387-388`
- Produces `"inputs": [{"ref": "x"}]` instead of `"inputs": {"main": {"items": [{"ref": "x", "deps": []}]}}`
- **Fix**: Restructure `to_api_dict()` to match DSSExporter's format

### B3: `to_api_dict()` uses `"settings"` key instead of `"params"`
- **File**: `py2dataiku/models/dataiku_recipe.py:392-393`
- DSS API expects recipe-specific configuration under `"params"` not `"settings"`
- **Fix**: Rename key or add both

### B4: Groupby `.agg()` with dict produces empty aggregations
- **File**: `py2dataiku/parser/ast_analyzer.py` (likely)
- `df.groupby('region').agg({'amount': 'sum', 'quantity': 'mean'})` produces `aggregations: []`
- This is a **conversion logic bug**, not just an API format issue
- **Fix**: Parse dict-based agg arguments into `Aggregation` objects

### B5: Invalid dataset names (`df['city']`, `_chain_step_0`)
- **File**: `py2dataiku/generators/flow_generator.py` (likely)
- Dataset names containing `[`, `'`, or starting with `_` may fail DSS API validation
- `df['city']` is clearly a parser artifact leaking through
- **Fix**: Sanitize all dataset names through `_sanitize_name()`

### B6: `fillna()` with dict not properly parsed
- `df.fillna({'age': 0, 'city': 'Unknown'})` produces `column: "unknown"` instead of expanding into multiple FillEmptyWithValue steps
- **Fix**: Handle dict argument in fillna mapping

---

## Significant Issues (Should Fix for Phase 2)

### S1: Two inconsistent output paths with different formats
- `to_api_dict()` and `DSSExporter._build_recipe_config()` produce structurally different JSON
- MCP server needs ONE consistent format
- **Recommendation**: Align `to_api_dict()` with DSSExporter format, or deprecate one path

### S2: Sort recipe `to_api_dict()` uses `sortColumns` instead of `orders`
- DSS API expects `"orders": [{"column": "x", "desc": true}]`
- `to_api_dict()` produces `"sortColumns": [{"column": "x", "order": "DESC"}]`
- DSSExporter correctly uses `"orders"` with boolean `desc`

### S3: Grouping recipe uses `aggregations` key in `to_api_dict()` but DSS expects `values`
- DSSExporter correctly uses `"values"` key
- `to_api_dict()` uses `"aggregations"` key

### S4: STACK recipe type maps to `"stack"` in `to_api_dict()` but should be `"vstack"`
- DSSExporter correctly maps to `"vstack"`

### S5: Missing `engineParams` in `to_api_dict()` for all recipe types
- DSS recipes require engine configuration (hive, spark, etc.)
- DSSExporter includes these; `to_api_dict()` does not

### S6: Join recipe `to_api_dict()` missing critical fields
- Missing `virtualInputs`, `table1/table2` mapping, `conditionsMode`
- These are required for DSS to know which input maps to which side of the join

### S7: `outputColumnsSelectionMode: "MANUAL"` with empty `selectedColumns`
- DSSExporter sets `"MANUAL"` but provides no columns, which would produce empty output
- Should default to `"ALL"` or `"KEEP_ALL"`

### S8: Prepare recipe `mode` inconsistency
- `to_api_dict()` uses `"NORMAL"`, DSSExporter uses `"BATCH"`
- DSS standard is typically `"BATCH"`

### S9: Missing `projectKey` in `to_api_dict()` output
- All DSS API calls require `projectKey` in the recipe config
- Only DSSExporter adds it

### S10: `to_recipe_configs()` calls `to_json()` which aliases `to_api_dict()`
- This means `flow.to_recipe_configs()` returns the WRONG format (the one with all the issues above)
- It should use the DSSExporter format instead

### S11: `str.upper()` not mapped to STRING_TRANSFORMER processor
- Falls back to Python recipe instead of `StringTransformer` with mode `TO_UPPER`
- This is a mapping gap in the parser

### S12: Optimizer not merging consecutive PREPARE recipes
- Test E produces two separate PREPARE recipes that should have been merged into one

---

## Recommendations Ranked by Phase 2 Impact

### Priority 1 (MUST for MCP integration)

1. **Unify output format**: Make `to_api_dict()` produce the same structure as DSSExporter. The MCP server should use a single consistent format.

2. **Fix recipe type strings**: `PREPARE` -> `"shaker"`, `STACK` -> `"vstack"` in `to_api_dict()`

3. **Fix input/output structure**: Use role-keyed dict with items array: `{"main": {"items": [{"ref": "x", "deps": []}]}}`

4. **Fix groupby aggregation parsing**: `.agg({'col': 'func'})` must produce actual aggregation objects

5. **Sanitize all dataset names**: Validate against `[A-Za-z0-9_]+` pattern, strip brackets and quotes

6. **Fix fillna dict parsing**: Expand dict argument into multiple processor steps

### Priority 2 (Important for correctness)

7. **Add `engineParams` to `to_api_dict()`** for all recipe types
8. **Fix Sort recipe field names** (`orders` not `sortColumns`, `desc: bool` not `order: str`)
9. **Fix Grouping recipe field names** (`values` not `aggregations`)
10. **Add `projectKey` parameter** to `to_api_dict()` signature
11. **Fix Join recipe** to include `virtualInputs` and proper `joins` structure
12. **Map `str.upper/lower/strip()`** to STRING_TRANSFORMER processor

### Priority 3 (Nice to have)

13. Fix `outputColumnsSelectionMode` default to `"ALL"`
14. Ensure optimizer merges consecutive PREPARE recipes
15. Add `versionTag`/`creationTag` to `to_api_dict()`
16. Validate recipe/dataset names against DSS naming rules

---

## Phase 2 Readiness Score

| Component | Score | Notes |
|---|---|---|
| DSSExporter file export | 65% | Good structure, but missing some recipe types and has minor field issues |
| `to_api_dict()` / `to_recipe_configs()` | 15% | Wrong recipe types, wrong input/output structure, wrong key names |
| Rule-based parser accuracy | 50% | Simple cases OK, complex patterns (agg dict, fillna dict, str accessor) fail |
| Dataset naming | 40% | Invalid characters leak through in edge cases |
| Recipe type coverage | 70% | Core types mapped, but some (WINDOW, PIVOT, SPLIT, SAMPLING) not in exporter |
| Overall | **~40%** | Functional for demo/preview but NOT production-ready for API integration |

### What works today:
- Simple PREPARE recipes with basic processors (dropna, rename)
- JOIN recipes via DSSExporter (correct structure)
- Basic dataset creation and flow structure
- Project bundle export (directory + zip)

### What does NOT work:
- Direct API integration via `to_api_dict()` (wrong format everywhere)
- Complex pandas patterns (groupby+agg, fillna with dict, str accessor methods)
- Dataset name validation
- `to_recipe_configs()` as a reliable API endpoint

---

## Conclusion

The **DSSExporter** is substantially closer to API-ready than `to_api_dict()`. For Phase 2, the recommended approach is:

1. Either refactor `to_api_dict()` to match DSSExporter's output format
2. Or route all MCP API calls through DSSExporter's `_build_recipe_config()` method

The parser's inability to handle `groupby().agg(dict)` and `fillna(dict)` are conversion-quality blockers independent of API format. These affect both output paths.
