# Comprehensive Project Review — py-iku

**Date**: 2026-04-04
**Scope**: Architecture, tests, code quality, notebooks, mappings, documentation
**Method**: 6 parallel review agents + direct static analysis
**Status**: Phases 1-4 COMPLETE, Phase 5 partial

---

## Results Summary

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Tests | 1984 | 2219 | +235 |
| Overall coverage | 85% | 87% | +2% |
| `llm_flow_generator.py` | 56% | 91% | +35% |
| `cli.py` | 59% | 89% | +30% |
| `ast_analyzer.py` | 79% | 80% | +1% |
| Ruff violations | 695 | 0 | -695 |
| Critical mapping bugs | 4 | 0 | -4 |

---

## Executive Summary

py-iku is a well-structured library with **1984 passing tests**, **85% overall coverage**, and solid architectural foundations. The main areas needing attention are: **mapping accuracy** (several incorrect DSS mappings that would produce invalid output), **LLM pipeline gaps** (56% coverage, routing issues), and **code modernization** (695 ruff warnings, mostly auto-fixable).

---

## 1. Critical Issues

### 1.1 `melt` incorrectly mapped to `RecipeType.PIVOT`
**File**: `mappings/pandas_mappings.py` line 25
`melt` (wide-to-long / unpivot) is mapped to `RecipeType.PIVOT` (long-to-wide). In DSS, unpivot is handled via `FoldMultipleColumns` processor in a PREPARE recipe. The runtime `FlowGenerator._create_melt_recipe` does the right thing, but the static `RECIPE_MAPPINGS` entry is wrong and misleading.
**Fix**: Change mapping to `RecipeType.PREPARE` with a comment about FOLD_MULTIPLE_COLUMNS.

### 1.2 `AGG_MAPPINGS["nunique"]` produces `"COUNTDISTINCT"` — DSS uses `"COUNTD"`
**File**: `mappings/pandas_mappings.py`
The `AggregationFunction` enum defines `COUNTD = "COUNTD"` but the mapping produces `"COUNTDISTINCT"`. Any generated grouping recipe JSON will be invalid in DSS.
**Fix**: Change to `"COUNTD"` to match the enum.

### 1.3 Phantom processors in `ProcessorCatalog`
**File**: `mappings/processor_catalog.py`
~19 processors (ABS_COLUMN, BOOLEAN_CONVERTER, NUMBER_TO_STRING, various sklearn-derived ones) are tagged "No DSS Prepare equivalent" in comments but have full catalog entries with DSS-style names. Using these produces invalid DSS API JSON.
**Fix**: Tag these entries clearly or separate them into a "virtual processors" section.

### 1.4 `AbsColumn` is not a real DSS processor
**File**: `models/prepare_step.py`
`ProcessorType.ABS_COLUMN = "AbsColumn"` — no such processor exists in DSS 14. Code emitting `"type": "AbsColumn"` will fail on DSS import.
**Fix**: Route `df.abs()` through `CreateColumnWithGREL` with `abs()` expression.

### 1.5 LLM pipeline `OperationType` doesn't drive recipe routing
**File**: `generators/llm_flow_generator.py`
The LLM generator routes recipes based on `step.suggested_recipe` (free text from LLM), not on `step.operation` (the typed enum). If the LLM returns a valid `operation="top_n"` but no `suggested_recipe`, it silently falls through to a Python recipe. There is no `OperationType → RecipeType` mapping table.
**Fix**: Add a fallback `OperationType → RecipeType` lookup table.

---

## 2. Architecture Assessment

### Strengths
- **Clean pipeline separation**: Rule-based and LLM paths share `BaseFlowGenerator` ABC without coupling
- **Rich model layer**: `DataikuFlow` with DAG graph, serialization, iteration protocol, Jupyter integration
- **Composition over inheritance**: `RecipeSettings` ABC with 12 typed subclasses
- **Good optimizer**: `FlowOptimizer` + `RecipeMerger` correctly merge consecutive PREPARE recipes
- **Plugin system**: Instance-based `PluginRegistry` with backward-compatible global default

### Weaknesses
- **AST analyzer is monolithic**: `ast_analyzer.py` at 2225+ lines with 50+ handler methods. Hard to extend.
- **Duplicate enum values**: `COLUMN_DELETER` and `COLUMNS_SELECTOR` both map to `"ColumnsSelector"` — `ProcessorType("ColumnsSelector")` always resolves to whichever is defined first. Same issue with `DATE_FORMATTER`/`DATETIME_FORMATTER`.
- **Inconsistency between parser and pattern_matcher**: `df.assign()` is "python-only" in `PatternMatcher.requires_python_recipe` but mapped to a visual processor in `CodeAnalyzer`. Same for `df.explode()`.
- **LLM flow generator low coverage**: Only 8 of 25 `OperationType` values handled in `_convert_to_prepare_steps`.
- **Multi-output Split not modeled**: DSS SPLIT recipes produce 2+ outputs but neither generator creates multi-output recipes.

---

## 3. Test Suite

### Results
- **1984 passed**, 0 failed, 4 warnings (all about missing ANTHROPIC_API_KEY)
- Test count has grown from 1807 → 1984

### Coverage by Module

| Module | Coverage | Notes |
|--------|----------|-------|
| `examples/` | 98-100% | Excellent |
| `models/` | 92-100% | Strong |
| `optimizer/` | 98-99% | Excellent |
| `visualizers/` | 84-100% | Good |
| `parser/ast_analyzer.py` | **79%** | 132 missed lines, many branch misses |
| `generators/flow_generator.py` | 94% | Good |
| `generators/llm_flow_generator.py` | **56%** | Major gap — entire LLM pipeline undertested |
| `llm/providers.py` | **50%** | No real provider tests (requires API keys) |
| `cli.py` | **59%** | Many CLI paths untested |
| `integrations/dss_client.py` | **59%** | Integration client undertested |
| `examples/demo.py` | **0%** | Not tested at all |
| `examples/llm_demo.py` | **0%** | Not tested at all |

### Key Gaps
- **LLM pipeline**: 56% coverage on `llm_flow_generator.py`, 50% on `providers.py`. The entire LLM analysis → generation path is the weakest tested area.
- **CLI**: 59% — many subcommands and error paths not exercised.
- **AST edge cases**: 79% coverage with 77 branch misses — chained operations, complex numpy, sklearn pipelines have gaps.
- **DSS export/import**: `dss_client.py` at 59% — the actual DSS interaction layer is poorly tested.

---

## 4. Code Quality

### Static Analysis (ruff)
**695 violations** found:

| Rule | Count | Description |
|------|-------|-------------|
| UP006 | 508 | Use `list` instead of `List` (Python 3.9+ type annotations) |
| UP035 | 87 | Deprecated imports from `typing` |
| F401 | 40 | Unused imports |
| I001 | 38 | Unsorted imports |
| B904 | 8 | Missing `raise ... from err` in exception chains |
| Others | 14 | Minor issues (unused vars, unnecessary comprehensions) |

**85 auto-fixable**, 514 more with `--unsafe-fixes`. The bulk (595/695) are type annotation modernization — switching from `typing.List/Dict/Optional` to native `list/dict/X | None`.

### Assessment
- **Type annotations**: Present on most public APIs but use legacy `typing` imports
- **Docstrings**: Good coverage on public classes/functions
- **Exception handling**: 8 places missing `raise X from Y` for proper exception chaining
- **40 unused imports**: Accumulated over time, easy cleanup
- **No security concerns** found in LLM providers — API keys handled via env vars, no hardcoding

---

## 5. Mapping & Conversion Fidelity

### Recipe Coverage
14 of 37 `RecipeType` values have pandas mappings. The unmapped 23 are correctly omitted (ML recipes, code recipes, admin recipes with no pandas equivalent).

### Gaps Found

| Issue | Severity |
|-------|----------|
| `melt` → `PIVOT` (should be PREPARE + FoldMultipleColumns) | Critical |
| `COUNTDISTINCT` vs `COUNTD` mismatch | Critical |
| `OperationType` not driving LLM routing | Critical |
| `AbsColumn` is not a real DSS processor | High |
| `COLUMN_DELETER`/`COLUMNS_SELECTOR` share enum value | High |
| `tail` transformations silently dropped (no handler) | High |
| `cummin`/`cummax` unregistered in AST dispatch table | High |
| `cut`/`qcut`/`get_dummies` no AST handler for `pd.X()` form | Medium |
| `groupby().sum()` chain not detected (only `.agg()`) | Medium |
| `df[condition]` never generates SPLIT recipe | Medium |
| Multi-output Split recipe not modeled | Medium |
| ~19 phantom processors in catalog | Medium |
| `assign`/`explode` contradictions between files | Low |
| `rolling` absent from RECIPE_MAPPINGS | Low |
| `head()` mapped to TOP_N (SAMPLING more accurate) | Low |

---

## 6. Documentation Gaps

### README.md
- States "34+ recipe types, 76+ processor types" — actual counts are 37 and 122. Out of date.

### TODO.md
- Only 7 lines. Should be cross-referenced against completed work.

### mkdocs site
- Structure exists with `docs/api/`, `docs/getting-started/`, `docs/reference/`. Need to verify page content matches current API.

### CLAUDE.md
- Recently updated (this session). Accurate.

### Examples Library
- `examples/demo.py` and `examples/llm_demo.py` have **0% test coverage** — may contain outdated code.

---

## 7. Recommended Action Plan

### Phase 1: Fix Critical Mapping Errors (Immediate)
1. Fix `melt` → `RecipeType.PREPARE` in `pandas_mappings.py`
2. Fix `AGG_MAPPINGS["nunique"]` → `"COUNTD"`
3. Fix `AbsColumn` → route through `CreateColumnWithGREL`
4. Add `OperationType → RecipeType` fallback table in `LLMFlowGenerator`

### Phase 2: Code Modernization (Quick Win)
5. Run `ruff check --fix py2dataiku/` to auto-fix 85 issues
6. Run `ruff check --unsafe-fixes --fix py2dataiku/` for the 508 UP006 + 87 UP035 type annotation fixes
7. Clean up 40 unused imports (F401)
8. Fix 8 exception chaining issues (B904)

### Phase 3: Coverage Improvements (Medium-Term)
9. Add tests for `llm_flow_generator.py` (56% → target 85%) using `MockProvider`
10. Add tests for `cli.py` (59% → target 80%) using `subprocess` or click testing
11. Add tests for `ast_analyzer.py` branch misses — chained ops, numpy, sklearn
12. Test or remove `examples/demo.py` and `examples/llm_demo.py`

### Phase 4: AST & Mapping Completeness (Medium-Term)
13. Register `cummin`/`cummax` in `_METHOD_HANDLER_NAMES`
14. Add AST handlers for `pd.cut()`, `pd.qcut()`, `pd.get_dummies()` top-level call forms
15. Handle `groupby().sum()` / `.mean()` / `.count()` chain pattern
16. Add `tail` → recipe generation (SAMPLING with last-rows or TOP_N with reverse sort)
17. Consider SPLIT recipe generation for complementary boolean filters

### Phase 5: Cleanup & Documentation (Low Priority)
18. Resolve `COLUMN_DELETER`/`COLUMNS_SELECTOR` enum aliasing
19. Tag or separate phantom processors in catalog
20. Update README.md counts (37 recipe types, 122 processor types)
21. Reconcile `assign`/`explode` handling between parser and pattern_matcher
