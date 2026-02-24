# Flow Optimization Review Results

**Reviewer**: optimizer-reviewer (Task #4)
**Date**: 2026-02-24
**Scope**: FlowOptimizer, RecipeMerger, BaseFlowGenerator optimization hooks, DataikuFlow API output

---

## Results Table

| Scenario | Before (recipes) | After (optimize=True) | After (FlowOptimizer) | Correct? | API Valid? |
|----------|------------------:|----------------------:|----------------------:|----------|-----------|
| A. Consecutive PREPAREs (5 transforms) | 2 | 2 (NO CHANGE) | 1 | PARTIAL | Yes |
| B. Orphan datasets | 3 | 3 (NO CHANGE) | 3 | N/A | Yes |
| C. Filter pushdown (filter after join) | 2 | 2 | 2 (recommendation only) | Yes | Yes |
| D. Parallel branches | 3 | 3 (NO CHANGE) | 2 | PARTIAL | Yes |
| E. Already optimal | 2 | 2 | 2 | Yes | Yes |
| F. Complex pipeline (10+ ops) | 6 | 6 (NO CHANGE) | 6 | PARTIAL | Yes |
| G1. Empty code | 0 | 0 | N/A | Yes | Yes |
| G2. Single operation | 1 | 1 | 1 | Yes | Yes |
| G3. Just import | 0 | 0 | N/A | Yes | Yes |
| G4. Just read, no transform | 0 | 0 | N/A | Yes | Yes |
| G5. Non-python code | ERROR | ERROR | N/A | Yes | N/A |
| H. Round-trip (dict/json/yaml) | 4 | 4 | 3 | Yes | Yes |

---

## Issues Found

### CRITICAL: `convert(optimize=True)` Does Not Actually Optimize

**Severity**: CRITICAL
**Location**: `py2dataiku/generators/base_generator.py:49-55`, `py2dataiku/generators/flow_generator.py:455-464`

The `convert(code, optimize=True)` path calls `BaseFlowGenerator._optimize_flow()` which calls `self._merge_prepare_recipes()`. However, `_merge_prepare_recipes()` in `BaseFlowGenerator` is a **no-op** (just `pass`). The `FlowGenerator._optimize_flow()` overrides the parent to add optimization notes about recipe counts, but **never calls `FlowOptimizer`**.

The actual working optimizer (`FlowOptimizer` in `py2dataiku/optimizer/flow_optimizer.py`) is completely **disconnected** from the `convert()` pipeline. Users must manually instantiate `FlowOptimizer` and call `optimize()` to get actual merging.

**Impact**: The `optimize=True` parameter is misleading. It adds metadata notes but does not merge recipes, remove orphan datasets, or apply any structural optimizations.

**Fix**: Either:
1. Wire `FlowOptimizer.optimize()` into `BaseFlowGenerator._optimize_flow()` or `FlowGenerator._optimize_flow()`
2. Or have `convert()` call `FlowOptimizer.optimize()` after generation

---

### HIGH: Column Detection Failures for `fillna()` and `astype()`

**Severity**: HIGH
**Location**: `py2dataiku/parser/ast_analyzer.py` (CodeAnalyzer)

When code uses `df = df.fillna(0)` or `df['col'] = df['col'].astype(int)`:
- `fillna()` produces `columns=[]` (should detect all columns or mark as "all")
- `astype()` produces `columns=[]` (should detect `'col'`)

This causes the generated PREPARE steps to have `"column": "unknown"` in their API output, which is invalid for Dataiku DSS API.

**API Output**:
```json
{"type": "FillEmptyWithValue", "params": {"column": "unknown", "value": "0"}}
{"type": "TypeSetter", "params": {"column": "unknown", "type": "int"}}
```

**Note**: This is a parser issue, not an optimizer issue, but it affects the API validity of optimized flows.

---

### HIGH: `str.upper()` Falls Back to Python Recipe

**Severity**: HIGH
**Location**: `py2dataiku/parser/ast_analyzer.py`

`df['name'] = df['name'].str.upper()` is parsed as two separate transformations:
1. `string_transform` with `columns=[], params={}`
2. `unknown` with `params={'method': 'upper'}`

Neither produces a proper `STRING_TRANSFORMER` PREPARE step. The code falls back to a Python recipe. This should map to a PREPARE recipe with a `StringTransformer` processor (TO_UPPER mode).

Additionally, the target dataframe is detected as `df['name']` instead of `df`, which creates an output dataset named `df['name']` -- an invalid dataset name containing brackets and quotes.

---

### MEDIUM: `FlowOptimizer.optimize()` Mutates Flow In-Place

**Severity**: MEDIUM
**Location**: `py2dataiku/optimizer/flow_optimizer.py:44-75`

The `optimize()` method mutates the input `DataikuFlow` in place and also returns it. This can cause confusion -- users might expect a new flow to be returned. The docstring says "Returns: The optimized DataikuFlow (same object, mutated in place)" which documents the behavior, but it's still a footgun.

---

### MEDIUM: Merged Recipe Naming Creates Confusing Names

**Severity**: MEDIUM
**Location**: `py2dataiku/optimizer/recipe_merger.py:68-69`

When merging, the resulting recipe is named `prepare_merged_prepare_1` (prefix `prepare_merged_` + original name). For multiple merges this could become `prepare_merged_prepare_merged_prepare_1`. Consider using a simpler naming scheme.

---

### LOW: `_identify_parallel_branches()` Does Not Populate Results

**Severity**: LOW
**Location**: `py2dataiku/optimizer/flow_optimizer.py:203-216`

The `_identify_parallel_branches()` method builds a dependency graph and iterates over recipe pairs, but the `pass` statement on line 214 means it never actually populates the `parallel_groups` list. This is dead code that always returns an empty list.

---

### LOW: `optimize_prepare_steps()` and `remove_redundant_steps()` Are Never Called

**Severity**: LOW
**Location**: `py2dataiku/optimizer/recipe_merger.py:81-148`

Two optimization methods in `RecipeMerger` -- `optimize_prepare_steps()` (reorders steps for efficiency) and `remove_redundant_steps()` (removes contradictory operations) -- are defined but never called anywhere in the codebase. These could improve flow quality if integrated into the merge pipeline.

---

### LOW: FlowOptimizer Only Merges Adjacent Recipes

**Severity**: LOW
**Location**: `py2dataiku/optimizer/flow_optimizer.py:82-124`

The merge algorithm only checks consecutive recipes at positions `i` and `i+1` in the `flow.recipes` list. If two PREPARE recipes are separated by a non-PREPARE recipe in list order but are still connected via datasets (e.g., on different branches), they will never be considered for merging. The algorithm also restarts from position 0 after each merge, which is correct for maintaining consistency but means it only finds strictly sequential pairs.

---

## Optimization Capabilities Summary

| Capability | FlowOptimizer Status | convert() Integration |
|------------|---------------------|----------------------|
| Merge consecutive PREPAREs | Working | NOT CONNECTED |
| Remove orphan datasets | Working | NOT CONNECTED |
| Filter pushdown | Recommendation only (no auto-apply) | NOT CONNECTED |
| Parallel branch detection | Stub (always empty) | NOT CONNECTED |
| Step reordering | Implemented in RecipeMerger, never called | NOT CONNECTED |
| Redundant step removal | Implemented in RecipeMerger, never called | NOT CONNECTED |

---

## Phase 2 Readiness Assessment

### Ready for Phase 2?

**NO** -- with caveats.

**Blockers**:
1. **CRITICAL**: `convert(optimize=True)` does not actually optimize. The FlowOptimizer works correctly when used directly, but the primary API entry point (`convert()`) does not invoke it. Phase 2 sending optimized flows to the Dataiku API will only work if callers explicitly use `FlowOptimizer`, not `convert(optimize=True)`.

2. **HIGH**: Column detection failures produce `"column": "unknown"` in API output. This will cause Dataiku API rejection for `FillEmptyWithValue` and `TypeSetter` processors.

**What Works**:
- `FlowOptimizer.optimize()` correctly merges consecutive PREPARE recipes
- Merged recipes have correct input/output connectivity
- Intermediate datasets are correctly removed after merging
- Round-trip serialization (dict/json/yaml) preserves all optimization results
- Validation passes for optimized flows
- API config structure (`to_recipe_configs()`) follows correct Dataiku format with `settings.steps`
- Edge cases (empty code, single op, no recipes) are handled gracefully
- Filter pushdown generates useful recommendations

**Recommendations for Phase 2 Readiness**:
1. Wire `FlowOptimizer.optimize()` into `convert(optimize=True)` path
2. Fix column detection in `CodeAnalyzer` for `fillna()`, `astype()`, `str.upper()`
3. Activate `optimize_prepare_steps()` and `remove_redundant_steps()` in the merge pipeline
4. Implement parallel branch detection (currently a stub)
5. Consider making `optimize()` return a copy instead of mutating in place
