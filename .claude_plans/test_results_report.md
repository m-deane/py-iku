# py-iku Comprehensive Test Results Report

**Date:** 2026-01-12
**Library Version:** 0.3.0
**Python Version:** 3.11.14
**Test Framework:** pytest 9.0.2

---

## Executive Summary

| Metric | Result |
|--------|--------|
| Total pytest tests | 843 |
| Tests passed | 843 (100%) |
| Tests failed | 0 |
| Test duration | 2.06s |
| Code coverage | 66% |
| Recipe types | 37 |
| Processor types | 112 |
| Example count | 197 |

**Overall Status:** PASS - All tests passing, library functional

---

## Phase 1: Baseline Test Results

### Test Suite Execution

```
============================= test session starts ==============================
platform linux -- Python 3.11.14, pytest-9.0.2, pluggy-1.6.0
843 passed in 2.06s
==============================
```

### Code Coverage Analysis

| Module | Coverage | Notes |
|--------|----------|-------|
| py2dataiku/__init__.py | 46% | Main API, some paths untested |
| py2dataiku/examples/ | 98-100% | Excellent coverage |
| py2dataiku/generators/ | 51-87% | LLM generator less tested |
| py2dataiku/llm/ | 46-52% | Requires API keys |
| py2dataiku/models/ | 67-100% | Good coverage |
| py2dataiku/visualizers/ | 69-100% | Good coverage |
| py2dataiku/optimizer/ | 0% | NOT TESTED |
| py2dataiku/mappings/ | 0% | NOT TESTED |
| py2dataiku/utils/validation.py | 0% | NOT TESTED |

**Coverage Gaps Identified:**
1. `optimizer/` module - 0% coverage (flow_optimizer.py, recipe_merger.py)
2. `mappings/` module - 0% coverage (pandas_mappings.py, processor_catalog.py)
3. `utils/validation.py` - 0% coverage
4. `dataflow_tracker.py` - 23% coverage
5. LLM components - ~50% (requires API keys)

---

## Phase 2: Module Testing Results

### 2.1 Core Models

| Component | Test Result | Notes |
|-----------|-------------|-------|
| RecipeType enum | PASS | 37 recipe types validated |
| ProcessorType enum | PASS | 112 processor types validated |
| DataikuRecipe | PASS | All serialization methods work |
| DataikuFlow | PASS | to_dict, to_json, to_yaml all work |
| DataikuDataset | PASS | All dataset types supported |
| PrepareStep | PASS | Uses `params` not `settings` |

**Finding:** PrepareStep uses `params` parameter, not `settings` as documented in some places.

### 2.2 Parser/AST Analyzer

| Operation Category | Pass Rate | Notes |
|-------------------|-----------|-------|
| Basic operations | 30/30 | All handled without errors |
| Transformations | 100% | May produce 0 recipes for isolated ops |
| Aggregations | 100% | GroupBy, pivot work |
| Joins | 100% | Merge, concat work |
| Window functions | 100% | Rolling, cumsum work |

**Finding:** Single-line operations return 0R/0D - requires full pipeline context.

### 2.3 Complete Pipeline Testing

| Pipeline Type | Recipes | Datasets | Status |
|--------------|---------|----------|--------|
| ETL Pipeline | 2 | 3 | PASS |
| Join Pipeline | 1 | 3 | PASS |
| Multi-step Transform | 1 | 2 | PASS |
| Window Functions | 1 | 2 | PASS |
| Stack and Dedupe | 2 | 5 | PASS |

### 2.4 Visualization Testing

| Format | Output Size | Status |
|--------|-------------|--------|
| ASCII | 1,811 chars | PASS |
| SVG | 5,954 chars | PASS |
| HTML | 13,274 chars | PASS |
| PlantUML | 1,308 chars | PASS |
| Mermaid | 356 chars | PASS |

All visualization formats produce valid, consistent output.

### 2.5 Examples Registry

| Category | Count | Test Result |
|----------|-------|-------------|
| Recipe examples | 39 | 10/10 sampled PASS |
| Processor examples | 80 | 10/10 sampled PASS |
| Combination examples | 22 | 10/10 sampled PASS |
| Settings examples | 56 | Not individually tested |

---

## Phase 3: Edge Case Results

### 3.1 Invalid Input Handling

| Input Type | Behavior | Rating |
|------------|----------|--------|
| Empty code | Returns 0R/0D | Good |
| Whitespace only | Returns 0R/0D | Good |
| No pandas ops | Returns 0R/0D | Good |
| Import only | Returns 0R/0D | Good |
| Syntax error | Returns 0R/0D | **Should raise error** |
| Unknown method | Returns 0R/0D | Good |

**Issue Found:** Syntax errors silently return empty flow instead of raising exception.

### 3.2 Complex Operations

| Scenario | Result |
|----------|--------|
| Nested method chains | 0 recipes (gap) |
| Multi-join (4 joins) | 3 recipes, 5 datasets (PASS) |
| Special characters | PASS |
| Long column names | PASS |
| Empty flow visualization | PASS |
| Single dataset flow | PASS |

**Issue Found:** Chained method calls like `df.dropna().assign().query()...` produce 0 recipes.

---

## Phase 4: Performance Results

### 4.1 Scaling with Operations

| Operations | Time (s) | Recipes |
|------------|----------|---------|
| 10 | 0.0004 | 1 |
| 50 | 0.0011 | 1 |
| 100 | 0.0020 | 1 |
| 200 | 0.0049 | 1 |
| 500 | 0.0104 | 1 |

**Performance:** Linear scaling, excellent performance even at 500 operations.

### 4.2 Scaling with Joins

| Joins | Time (s) | Recipes |
|-------|----------|---------|
| 2 | 0.0002 | 2 |
| 5 | 0.0002 | 5 |
| 10 | 0.0003 | 10 |
| 20 | 0.0008 | 20 |

**Performance:** Sub-millisecond for 20 joins.

### 4.3 Visualization Performance

| Format | Time (ms) |
|--------|-----------|
| Mermaid | 0.06 |
| PlantUML | 0.21 |
| SVG | 0.37 |
| ASCII | 0.38 |
| HTML | 0.50 |

### 4.4 Serialization Performance

| Format | Time (ms) |
|--------|-----------|
| to_dict | 0.04 |
| to_json | 0.30 |
| to_yaml | 6.66 |

**Note:** YAML serialization is slowest (but still fast).

---

## Phase 5: Integration Test Results

### 5.1 Conversion Methods

| Method | Result |
|--------|--------|
| convert() | PASS |
| convert(optimize=True) | PASS |
| Py2Dataiku.convert() | PASS (falls back to rule-based) |

### 5.2 Serialization Roundtrip

| Format | Roundtrip | Size |
|--------|-----------|------|
| JSON | PASS | 1,031 chars |
| YAML | PASS | 650 chars |
| Dict | PASS | 9 keys |

### 5.3 Visualization Consistency

All 5 formats produce identical output on repeated calls - PASS

### 5.4 Public API Check

**Missing from public API:**
- `PrepareStep`
- `RecipeType`
- `ProcessorType`
- `DatasetType`

These are importable from `py2dataiku.models` but not from `py2dataiku` directly.

---

## Issues Found

### Critical Issues (0)

None - library is stable and functional.

### Major Issues (3)

1. **Syntax errors not raised** - Invalid Python syntax returns empty flow instead of raising exception
2. **Chained methods not parsed** - `df.dropna().fillna().sort()` chains produce 0 recipes
3. **Missing public exports** - PrepareStep, RecipeType, ProcessorType, DatasetType not in `__init__.py`

### Minor Issues (5)

1. **Validation returns unexpected format** - Returns ['valid', 'errors', 'warnings', 'info'] instead of actual errors
2. **0% coverage on optimizer module** - flow_optimizer.py and recipe_merger.py untested
3. **0% coverage on mappings module** - pandas_mappings.py untested
4. **PrepareStep API discrepancy** - Uses `params` but some docs mention `settings`
5. **YAML serialization slower** - 6.66ms vs 0.04ms for dict

---

## Recommendations

### Immediate (P0)

1. Add missing exports to `py2dataiku/__init__.py`:
   ```python
   from .models import PrepareStep, RecipeType, ProcessorType, DatasetType
   ```

2. Fix syntax error handling to raise `SyntaxError`

3. Add tests for optimizer module

### Short-term (P1)

1. Improve chained method parsing (`.dropna().fillna()...`)
2. Add tests for mappings module
3. Fix validation return format
4. Update documentation for PrepareStep `params` parameter

### Long-term (P2)

1. Implement LLM fallback tests with mocked providers
2. Add property-based testing with hypothesis
3. Increase coverage to >80%

---

## Test Artifacts

- Baseline test output: `.claude_plans/test_output.txt`
- Coverage report: `htmlcov/index.html` (when generated)
- This report: `.claude_plans/test_results_report.md`
