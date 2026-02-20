# py-iku Enhancement Roadmap

**Compiled:** 2026-02-19
**Source Reviews:** Architecture, Code Quality, Test Coverage, Feature Gaps, API/UX
**Library Version:** 0.3.0

---

## Overview

This roadmap synthesizes findings from 5 independent reviews of the py-iku library. Items are organized into 4 priority tiers based on impact and effort. Each item links to its source review(s).

**Review Summary:**
- **Architecture Review:** 8 strengths, 8 weaknesses, 10 recommendations
- **Code Quality Review:** 4 critical issues, 6 warnings, 7 suggestions (17 total)
- **Test Coverage Analysis:** 71% coverage, 1000 tests, 13 gaps identified, ~340 new tests recommended
- **Feature Gap Analysis:** 92% recipe coverage, 69% processor coverage, 0% automation/scenarios
- **API/UX Review:** 8 strengths, 10 weaknesses, 16 recommendations

---

## Tier 1: High Impact, Low Effort (Quick Wins)

These items address bugs, correctness issues, or provide outsized value for minimal work. Start here.

### T1.1 Fix DSSExporter recipe payload bugs
- **Description:** `_build_join_payload()` and `_build_grouping_payload()` reference `recipe.parameters` which does not exist on `DataikuRecipe`. DSS exports for join and grouping recipes produce incorrect configurations.
- **Source:** API/UX (R2), Code Quality (#12)
- **Impact:** HIGH - broken DSS exports for two major recipe types
- **Effort:** Small (fix attribute references)

### T1.2 Fix silent error swallowing in LLM analyzer
- **Description:** Bare `except Exception` in `LLMCodeAnalyzer.analyze()` converts API failures, auth errors, rate limits, and bugs into empty results. Callers cannot distinguish error types. Replace with specific exception handlers.
- **Source:** Code Quality (#2), Architecture (R5), API/UX (R3)
- **Impact:** HIGH - users get empty flows with no indication of failure
- **Effort:** Small (refactor exception handling)

### T1.3 Fix version inconsistency
- **Description:** `pyproject.toml` says 0.2.0, `__init__.py` says 0.3.0, `cli.py` hardcodes 0.3.0. Use `importlib.metadata.version()` for single-source versioning.
- **Source:** API/UX (R1)
- **Impact:** HIGH - packaging/release confusion
- **Effort:** Small

### T1.4 Fix `nlargest()`/`nsmallest()` mapped to wrong TransformationType
- **Description:** These are Top-N operations but mapped to `TransformationType.HEAD`, causing incorrect recipe generation.
- **Source:** Code Quality (#9)
- **Impact:** MEDIUM - incorrect recipe output for common operations
- **Effort:** Small

### T1.5 Fix type annotations (`str = None` -> `Optional[str]`)
- **Description:** `api_key: str = None` and `model: str = None` in public API are incorrect type annotations. Fails mypy strict mode.
- **Source:** Code Quality (#5)
- **Impact:** MEDIUM - type checker failures
- **Effort:** Small

### T1.6 Normalize LLM recipe routing strings
- **Description:** `LLMFlowGenerator` routes on plain string comparison (`"prepare"`, `"grouping"`). If the LLM returns `"Prepare"` or `"GROUP_BY"`, it falls through silently to Python recipe. Add `.lower().strip()` normalization.
- **Source:** Code Quality (#13)
- **Impact:** MEDIUM - silent recipe type mismatch
- **Effort:** Small (one-line fix)

### T1.7 Fix `DataStep.from_dict()` ValueError escape
- **Description:** Invalid `OperationType` values from LLM raise `ValueError` that propagates unhandled. Should catch and default to `OperationType.UNKNOWN`.
- **Source:** Code Quality (#14)
- **Impact:** MEDIUM - unhandled exceptions from LLM responses
- **Effort:** Small

### T1.8 Mark `get_column_lineage()` as NotImplementedError
- **Description:** Public method permanently returns `None` with no indication it's unimplemented. Should raise `NotImplementedError` with a clear message.
- **Source:** Code Quality (#1), API/UX (R10), Architecture (R8)
- **Impact:** MEDIUM - misleading API surface
- **Effort:** Small

### T1.9 Wire existing enums into recipe builders
- **Description:** `SamplingMethod` and `WindowFunctionType` enums are defined but not wired into `DataikuRecipe._build_settings()`. Already-defined code is unused.
- **Source:** Feature Gaps (Tier 1 items 3-4)
- **Impact:** MEDIUM - existing enum definitions go to waste
- **Effort:** Small

### T1.10 Add catch-all fallback in FlowGenerator for unhandled TransformationTypes
- **Description:** Types like `NUMERIC_TRANSFORM`, `ROLLING`, `PIVOT`, `SAMPLE`, `HEAD` are silently dropped when not matched. Add an `else` branch creating a Python recipe or logging a warning.
- **Source:** Code Quality (#10)
- **Impact:** MEDIUM - silent data loss in conversion
- **Effort:** Small

### T1.11 Export commonly needed types from top-level `__init__.py`
- **Description:** `Aggregation`, `JoinKey`, `JoinType`, `AggregationFunction`, `StringTransformerMode`, `ColumnSchema`, `MockProvider`, and other supporting enums require deep imports. Export from top level.
- **Source:** API/UX (Import ergonomics)
- **Impact:** MEDIUM - reduces friction for programmatic use
- **Effort:** Small

### T1.12 Add `IF_THEN_ELSE` and `SWITCH_CASE` processors
- **Description:** `np.where()` and chained conditionals are extremely common. These two processors cover a large percentage of unmapped patterns.
- **Source:** Feature Gaps (Tier 1 item 1)
- **Impact:** HIGH - common pattern coverage
- **Effort:** Low

### T1.13 Add `TRANSLATE_VALUES` processor
- **Description:** Maps `df.map(dict)` and `df.replace(dict)`, which are very frequent operations with no current DSS mapping.
- **Source:** Feature Gaps (Tier 1 item 2)
- **Impact:** HIGH - common pattern coverage
- **Effort:** Low

---

## Tier 2: High Impact, High Effort (Strategic Investments)

These items require more work but significantly improve the library's capabilities and architecture.

### T2.1 Create custom exception hierarchy
- **Description:** Add `Py2DataikuError > ConversionError, ProviderError, ValidationError, ExportError`. Replace generic exceptions throughout. Enables users to handle errors programmatically.
- **Source:** Architecture (R5), API/UX (R3), Code Quality (#2)
- **Impact:** HIGH
- **Effort:** Medium
- **Dependencies:** Pairs with T1.2 (LLM error handling fix)

### T2.2 Extract shared recipe creation into base generator class
- **Description:** `FlowGenerator` and `LLMFlowGenerator` share ~60% identical code. Create `BaseFlowGenerator` with shared methods (`_create_join_recipe`, `_create_grouping_recipe`, `_sanitize_name`, etc.). Both generators inherit from it.
- **Source:** Architecture (R1), Code Quality (#6, #7)
- **Impact:** HIGH - eliminates ~300 lines of duplication, prevents drift
- **Effort:** Medium

### T2.3 Implement DAG data structure for flows
- **Description:** Replace flat `List[DataikuRecipe]` + `List[DataikuDataset]` with explicit DAG. Enables graph traversal, topological sorting, cycle detection, and optimization transformations.
- **Source:** Architecture (R4)
- **Impact:** HIGH - foundational for optimizer, validation, lineage
- **Effort:** Medium
- **Dependencies:** Should precede T2.5 (optimizer strengthening)

### T2.4 Unify mapping dictionaries
- **Description:** Consolidate duplicated mapping dicts (string methods, aggregations, join types, recipe inference) from `PatternMatcher`, `CodeAnalyzer`, `LLMFlowGenerator` into single source of truth in `PandasMapper`.
- **Source:** Architecture (R2), Code Quality (#7)
- **Impact:** MEDIUM - prevents maintenance drift
- **Effort:** Small-Medium

### T2.5 Strengthen optimizer to actually perform transformations
- **Description:** Implement `_merge_prepare_recipes()` (currently a no-op). Add filter pushdown, redundant dataset elimination. Provide before/after summary.
- **Source:** Architecture (R10), Code Quality (#3), API/UX (R7)
- **Impact:** HIGH - `optimize=True` currently does nothing
- **Effort:** Medium
- **Dependencies:** Best after T2.3 (DAG data structure)

### T2.6 Add `DataikuFlow.from_dict()` / `from_json()` for round-trip serialization
- **Description:** Flows can be serialized but not deserialized. Breaks save/load workflows.
- **Source:** API/UX (R9)
- **Impact:** MEDIUM - enables flow persistence and manipulation
- **Effort:** Medium

### T2.7 Create 5 new test files for zero-coverage modules
- **Description:** Add `test_validation.py` (~40 tests), `test_pandas_mapper.py` (~50 tests), `test_processor_catalog.py` (~20 tests), `test_dataflow_tracker.py` (~30 tests), `test_pattern_matcher.py` (~35 tests). Total: ~175 new tests, coverage from 71% to ~79%.
- **Source:** Test Coverage (Priority 1)
- **Impact:** HIGH - 3 modules with 0% coverage including validation
- **Effort:** Medium (straightforward but voluminous)

### T2.8 Populate ProcessorCatalog for all 76+ defined types
- **Description:** Catalog only has 27/76+ entries. Severe inconsistency between what's defined and what's documented.
- **Source:** Feature Gaps (Tier 2 item 9)
- **Impact:** MEDIUM
- **Effort:** Medium

### T2.9 Map `df.map()`, `df.where()`, `df.cumsum()`, `df.diff()`, `df.rank()`, `df.shift()` in PandasMapper
- **Description:** High-frequency pandas methods with no current DSS mapping. These should map to existing DSS processors/recipes.
- **Source:** Feature Gaps (Tier 1 item 6, Part 7 table)
- **Impact:** HIGH - fills ~50% of missing pandas method coverage
- **Effort:** Medium

### T2.10 Add `DatasetConnectionType` enum and wire into dataset model
- **Description:** 0% coverage of DSS connection types (SQL, S3, HDFS, etc.). Required for realistic project exports.
- **Source:** Feature Gaps (Part 3)
- **Impact:** MEDIUM
- **Effort:** Medium

### T2.11 Fix duplicate method handler dispatch table in parser
- **Description:** `method_handlers` dict appears twice in `ast_analyzer.py` with the second copy missing 4 methods. Causes inconsistent handling depending on code path.
- **Source:** Code Quality (#7), Code Quality (#4)
- **Impact:** MEDIUM - correctness bug
- **Effort:** Medium

### T2.12 Add `EXTRACT_WITH_JSONPATH`, `SPLIT_URL`, `FOLD_MULTIPLE_COLUMNS` processors
- **Description:** High-priority missing processors that cover common data transformation patterns (JSON, URLs, reshaping).
- **Source:** Feature Gaps (Tier 1 items 5, 8; Tier 2 items 10-12)
- **Impact:** MEDIUM
- **Effort:** Medium

---

## Tier 3: Low Impact, Low Effort (Nice-to-Haves)

Low-risk improvements that can be done opportunistically.

### T3.1 Consolidate visualization dispatch
- **Description:** Move mermaid generation into `visualizers/` module. Deprecate legacy `DiagramGenerator`. Remove special-case handling from `DataikuFlow.visualize()`.
- **Source:** Architecture (R7)
- **Impact:** LOW - cleanup, no new functionality
- **Effort:** Small

### T3.2 Add analyzer protocol/interface
- **Description:** Define `Protocol` for code analyzers so `Py2Dataiku` and CLI can work with any analyzer polymorphically.
- **Source:** Architecture (R9)
- **Impact:** LOW
- **Effort:** Small

### T3.3 Improve JSON extraction robustness in LLM providers
- **Description:** Ad-hoc code fence stripping is fragile. Use regex for JSON extraction and add error context on parse failure.
- **Source:** Code Quality (#8)
- **Impact:** LOW - edge case hardening
- **Effort:** Small

### T3.4 Add `convert_file()` convenience function
- **Description:** `convert_file(path)` and `convert_file_with_llm(path)` for direct file conversion without manual open/read.
- **Source:** API/UX (R5)
- **Impact:** LOW - convenience
- **Effort:** Small

### T3.5 Fix `DataikuRecipe.to_json()` naming confusion
- **Description:** Returns a dict, not a JSON string. Rename to `to_api_dict()` or make it return actual JSON.
- **Source:** API/UX (R4)
- **Impact:** LOW - API consistency
- **Effort:** Small

### T3.6 Add `DataikuFlow.__len__()` and `__iter__()`
- **Description:** Pythonic convenience: `len(flow)` returns recipe count, `for recipe in flow` iterates recipes.
- **Source:** API/UX (R11)
- **Impact:** LOW
- **Effort:** Small

### T3.7 Add Jupyter `_repr_svg_()` to DataikuFlow
- **Description:** Automatic visual rendering when a flow object is the last expression in a Jupyter cell.
- **Source:** API/UX (Output format gaps)
- **Impact:** LOW - nice for notebook users
- **Effort:** Small

### T3.8 Add timeout and retry to LLM providers
- **Description:** Add `timeout` and `max_retries` parameters to providers. Critical for production but low impact for current usage.
- **Source:** API/UX (R6)
- **Impact:** LOW-MEDIUM
- **Effort:** Small

### T3.9 Add `COALESCE`, `FILL_COLUMN`, `UNFOLD` processors
- **Description:** Common data operations with straightforward DSS processor mappings.
- **Source:** Feature Gaps (Tier 3 items 22, 25)
- **Impact:** LOW
- **Effort:** Small

### T3.10 Strengthen existing shallow tests
- **Description:** Fix assertions like `len() >= 1` to verify specific transformation types and parameters. Fix CLI tests that only check output exists.
- **Source:** Test Coverage (Section 5)
- **Impact:** LOW - improves test quality without new coverage
- **Effort:** Small

### T3.11 Add missing LLM `OperationType` values
- **Description:** Add `SPLIT_COLUMN`, `ENCODE_CATEGORICAL`, `NORMALIZE_SCALE`, `GEO_OPERATION` to improve LLM analysis completeness.
- **Source:** Feature Gaps (Part 5)
- **Impact:** LOW
- **Effort:** Small

---

## Tier 4: Low Impact, High Effort (Backlog)

Items with significant implementation cost relative to their immediate value. Worth tracking but not prioritizing.

### T4.1 Refactor DataikuRecipe using composition
- **Description:** Replace monolithic recipe class with base + recipe-specific settings classes. Eliminates unused fields per instance and the long `_build_settings()` if/elif chain.
- **Source:** Architecture (R3)
- **Impact:** MEDIUM - cleaner architecture but breaking change
- **Effort:** Large
- **Risk:** Breaking API change for all recipe construction

### T4.2 Implement column lineage tracking
- **Description:** Integrate `DataFlowTracker` into the main pipeline. Implement schema propagation through recipes. Make `get_column_lineage()` functional.
- **Source:** Architecture (R8), Code Quality (#1)
- **Impact:** MEDIUM - significant feature but niche use case
- **Effort:** Large

### T4.3 Make PluginRegistry instance-based
- **Description:** Convert from class-level mutable state to instance-based. Improves testability and allows multiple independent converter configurations.
- **Source:** Architecture (R6)
- **Impact:** MEDIUM
- **Effort:** Medium
- **Risk:** Backwards-incompatible change

### T4.4 Add DataikuScenario model (automation layer)
- **Description:** Model Dataiku scenarios with triggers, steps, and reporters. Currently 0% coverage of DSS automation.
- **Source:** Feature Gaps (Part 4)
- **Impact:** MEDIUM - enables full project export
- **Effort:** High

### T4.5 Add Metrics and Checks models
- **Description:** Model dataset metrics, checks, and data quality rules.
- **Source:** Feature Gaps (Part 4)
- **Impact:** MEDIUM
- **Effort:** High

### T4.6 Add sklearn ML model training -> ML recipe mapping
- **Description:** Map `RandomForestClassifier`, `GradientBoosting*`, `KMeans`, `cross_val_score` to DSS ML recipes.
- **Source:** Feature Gaps (Part 5)
- **Impact:** MEDIUM - completes sklearn pipeline support
- **Effort:** Medium-High

### T4.7 Add Flow Zones support
- **Description:** Group flow nodes into named zones for large project organization.
- **Source:** Feature Gaps (Part 4)
- **Impact:** LOW
- **Effort:** Medium

### T4.8 Expand LLM flow generator test coverage
- **Description:** Add tests for SORT, SPLIT, DISTINCT, PIVOT, STACK, WINDOW recipe generation. Add error path tests.
- **Source:** Test Coverage (Gap 7)
- **Impact:** MEDIUM
- **Effort:** Medium

### T4.9 Add MLOps / model deployment features
- **Description:** API node endpoints, model comparison, drift monitoring.
- **Source:** Feature Gaps (Part 4)
- **Impact:** LOW - niche use case
- **Effort:** Very High

### T4.10 Add configuration file support
- **Description:** `.py2dataikurc` or `py2dataiku.toml` for persistent settings (default provider, project key, optimization level, etc.)
- **Source:** API/UX (Missing configuration)
- **Impact:** LOW
- **Effort:** Medium

---

## Implementation Sequence (Recommended)

### Phase 1: Bug Fixes & Quick Wins (1-2 days)
Items: T1.1 through T1.13

These are independent and can be done in any order. Addresses all critical bugs and low-hanging fruit. Expected outcome: a more correct and robust library with no new features.

### Phase 2: Foundation (3-5 days)
Items: T2.1, T2.2, T2.4, T2.7, T2.11

Create exception hierarchy, extract base generator, unify mappings, fix parser dispatch table, add tests for zero-coverage modules. Expected outcome: cleaner architecture, better test coverage (~79%), consistent error handling.

### Phase 3: Features & Coverage (5-7 days)
Items: T2.3, T2.5, T2.6, T2.8, T2.9, T2.10, T2.12

DAG data structure, functional optimizer, round-trip serialization, expanded processor catalog, pandas/numpy mappings, connection types. Expected outcome: significantly more capable library with better DSS fidelity.

### Phase 4: Polish (ongoing)
Items: Tier 3 items as time permits

Visualization consolidation, convenience methods, Jupyter integration, shallow test fixes.

### Phase 5: Platform Completeness (future)
Items: Tier 4 items based on user demand

Automation layer, column lineage, MLOps features, configuration files.

---

## Metrics

| Metric | Current | After Phase 1 | After Phase 2 | After Phase 3 |
|--------|---------|---------------|---------------|---------------|
| Tests | 1000 | 1000 | ~1175 | ~1300 |
| Coverage | 71% | 72% | ~79% | ~84% |
| Critical bugs | 4 | 0 | 0 | 0 |
| Recipe type coverage | 92% | 92% | 92% | 92% |
| Processor type coverage | 69% | 72% | 72% | 75% |
| Pandas method coverage | ~50% | ~50% | ~50% | ~70% |
| ProcessorCatalog entries | 27/76 | 27/76 | 27/76 | 76/76 |

---

*This roadmap was compiled from 5 independent review reports. Individual reports are available in `.claude_plans/` for full details.*
