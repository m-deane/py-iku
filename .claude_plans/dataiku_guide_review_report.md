# py-iku vs Dataiku Developer Guide: Unified Gap Report

**Date**: 2026-03-09
**Scope**: Full library audit against https://developer.dataiku.com/latest/

---

## Executive Summary

Five specialized agents reviewed py-iku against the Dataiku DSS 14 developer guide across recipes, processors, API models, documentation, and visualization. The library has strong foundational coverage but contains **critical export/serialization issues** that would produce invalid DSS imports, **wrong enum values** for scenarios, and **visual misrepresentations** of DSS concepts.

| Area | Coverage | Fidelity | Priority Issues |
|------|----------|----------|-----------------|
| Recipe Types | 30/37 enums (81%) | Medium-High | 3 wrong internal names, 7 missing types |
| Recipe Settings | 12/37 subclasses (32%) | Medium | 25 types have no typed settings class |
| Processors | 99/127 DSS confirmed (78%) | Medium | 23 questionable, 27 missing from DSS |
| API Models | 10 model files | Medium | Scenario enums wrong, join serialization wrong |
| DSS Exporter | Partial | Low-Medium | Empty payloads for 6 recipe types, type map covers 15/37 |
| Visualization | 5 formats | Low-Medium | Wrong shapes, wrong colors, rendering bugs |
| Documentation | CLAUDE.md + examples | Medium | Inaccurate claims, mapping contradictions |

---

## CRITICAL Issues (13) — Would produce invalid DSS imports

### C1. Exporter `_get_dss_recipe_type()` maps only 15 of 37 RecipeTypes
**File**: `py2dataiku/exporters/dss_exporter.py`
**Impact**: All unmapped types default to `"python"` — WINDOW, SORT, PIVOT, SAMPLING, SPLIT, TOP_N, STACK, DISTINCT exports are corrupt.
**Fix**: Expand the type map to cover all 37 RecipeType values.

### C2. Exporter `_build_recipe_payload()` returns `{}` for 6 recipe types
**File**: `py2dataiku/exporters/dss_exporter.py`
**Impact**: WINDOW, SAMPLING, SPLIT, TOP_N, STACK, PIVOT recipes export with empty params — DSS will reject them.
**Fix**: Add dedicated `_build_*_payload()` methods for each.

### C3. `RecipeType.SPARKSQL` has wrong enum value
**File**: `py2dataiku/models/dataiku_recipe.py`
**Impact**: Value is `"sparksql"` but DSS expects `"spark_sql_query"`. Not corrected in any type map.
**Fix**: Change value or add to `_DSS_TYPE_MAP`.

### C4. JOIN recipe inputs use wrong role structure
**File**: `py2dataiku/exporters/dss_exporter.py`
**Impact**: Both inputs go under `"main"` role. DSS JOIN requires left in `"main"`, right in `"join"` role.
**Fix**: Update `_format_io_items()` to handle JOIN-specific input roles.

### C5. JoinKey serialization format is wrong
**File**: `py2dataiku/models/dataiku_recipe.py`
**Impact**: `JoinKey.to_dict()` produces `{left: {column}, right: {column}, matchType}` — DSS expects `{column1, column2, type}`.
**Fix**: Rewrite `JoinKey.to_dict()` to match DSS wire format.

### C6. Grouping recipe has two divergent serialization paths
**File**: `py2dataiku/models/dataiku_recipe.py` + `py2dataiku/exporters/dss_exporter.py`
**Impact**: `_build_settings()` uses `aggregations` key with `type` field; exporter uses `values` key with `function` field. Inconsistent JSON output.
**Fix**: Unify to use `values` with `function` and `$idx` (DSS format).

### C7. FlowZone serialization is wrong + zones lost on export
**File**: `py2dataiku/models/dataiku_flow.py` + `py2dataiku/exporters/dss_exporter.py`
**Impact**: Uses separate `datasets`/`recipes` lists instead of DSS unified `items: [{ref, type}]`. Exporter exports empty `items: []`, silently losing all zone memberships. Missing required `id` field.
**Fix**: Rewrite `FlowZone.to_dict()` and `_export_flow_zones()` to match DSS `zones.json` format.

### C8. Scenario TriggerType enum values are wrong
**File**: `py2dataiku/models/dataiku_scenario.py`
**Impact**: `"time_based"` should be `"temporal"`, `"dataset_change"` should be `"dataset_modified"`. Exported scenarios will fail DSS import.
**Fix**: Correct enum values.

### C9. Scenario StepType enum values are wrong
**File**: `py2dataiku/models/dataiku_scenario.py`
**Impact**: `"build_dataset"` should be `"build_flowitem"`, `"execute_sql"` should be `"exec_sql"`, `"execute_python"` should be `"custom_python"`.
**Fix**: Correct enum values.

### C10. Split recipe generator creates only one output dataset
**File**: `py2dataiku/generators/flow_generator.py`
**Impact**: DSS Split recipes require at minimum 2 output datasets. Single-output Split is invalid.
**Fix**: Generate a second output for unmatched rows.

### C11. `pd.melt()` incorrectly mapped to PIVOT recipe
**File**: `py2dataiku/mappings/pandas_mappings.py` (line 25)
**Impact**: `melt()` is an unpivot (wide-to-long). Should map to PREPARE with `FoldMultipleColumns`, not PIVOT. Contradicts CLAUDE.md's own documentation.
**Fix**: Change mapping to PREPARE recipe type and add FoldMultipleColumns processor step.

### C12. LLM generator routes `topn` and `sampling` to Python recipe
**File**: `py2dataiku/generators/llm_flow_generator.py` (lines 174-181)
**Impact**: When the LLM suggests these recipe types, they become Python recipes instead of using dedicated visual recipe creators. `FlowGenerator` has proper methods for these but they're never called in the LLM path.
**Fix**: Add routing for `topn` and `sampling` to dedicated recipe creation methods.

### C13. `FUZZY_JOIN` enum value may be wrong
**File**: `py2dataiku/models/dataiku_recipe.py`
**Impact**: py-iku uses `"fuzzy_join"` but DSS likely uses `"fuzzyjoin"` (no underscore). Needs verification.
**Fix**: Verify against DSS API and correct if needed.

---

## HIGH Issues (12) — Significant gaps affecting completeness

### H1. Missing `SyncSettings` class
Core visual recipe with no typed settings subclass. SYNC is one of the most commonly used recipes.

### H2. Missing `FuzzyJoinSettings` and `GeoJoinSettings` classes
These have distinct parameters (similarity threshold, spatial operators) not covered by `JoinSettings`.

### H3. Missing 7 RecipeType enum values
`continuous_sync`, `sql_script`, `prediction_training`, `clustering_training`, `standalone_evaluation`, `export`, `pig`

### H4. 23 questionable processors not confirmed in DSS
sklearn-inspired types (`MinMaxScaler`, `StandardScaler`, `BoxCoxTransformer`, `RobustScaler`, `QuantileTransformer`, `PowerTransformer`, `LogTransformer`) and ML encoders (`LabelEncoder`, `OrdinalEncoder`, `TargetEncoder`, `LeaveOneOutEncoder`, `WOEEncoder`, `FeatureHasher`) may not exist as DSS processor type strings.

### H5. 27 DSS processors missing from py-iku
Including: Extract with grok, Negate boolean, Nest columns, Split HTTP query string, Join/Fuzzy join/Geo join with other dataset (in-prepare variants), and others.

### H6. `ProcessorGroup` modeled as processor type, should be `metaType: "GROUP"`
DSS groups use `metaType: "GROUP"` with a `steps` list, not a separate processor type string.

### H7. `ConcatColumns` / `ColumnsConcatenator` are duplicates
Both exist in enum and catalog with identical schemas. DSS has one processor.

### H8. `str.capitalize()` wrongly mapped to `TITLECASE`
**File**: `py2dataiku/mappings/pandas_mappings.py`
Should use `StringTransformerMode.CAPITALIZE`. `capitalize()` uppercases only the first character; TITLECASE uppercases every word.

### H9. Dataset `to_json()` missing required DSS fields
Missing: `managed`, `formatType`, `formatParams`, `params`, `partitioning`, `flowOptions`, `versionTag`, `creationTag`. Exporter adds some but not all.

### H10. Recipe `to_api_dict()` missing required DSS fields
Missing: `projectKey`, `versionTag`, `creationTag`. Exporter adds these.

### H11. Python recipe code stored in `params.code` instead of as separate payload file
DSS stores Python recipe code as a `.py` file, not inside `params`. The `params` field holds engine settings only.

### H12. `RecipeGenerator` class is dead code with wrong field names
Orphaned utility class not called from any public API. Uses different field names than the exporter (e.g., `"partitionColumns"` vs DSS's `"windowDefinition"`).

---

## MEDIUM Issues (15) — Should fix for quality

### M1. Recipe shape wrong in all visualizers
DSS uses circles for recipes, rectangles for datasets. py-iku uses rectangles for both.

### M2. Recipe colors are pale washes, not vivid fills
DSS uses solid vivid colored circles. py-iku uses `#E*F*` pale backgrounds with colored borders.

### M3. `"sample"` key in themes.py doesn't match `"sampling"` enum
Theme lookup `get_recipe_colors("sampling")` returns default gray.

### M4. Mermaid `\\n` renders literally, not as newline
**File**: `py2dataiku/generators/diagram_generator.py`
Should use `<br/>` for Mermaid node labels.

### M5. HTML tooltip `\\n` doesn't create newlines
**File**: `py2dataiku/visualizers/html_visualizer.py`
Template literal `\\n` renders as literal backslash-n.

### M6. Optimizer reorder rule is unsafe for column renames
**File**: `py2dataiku/optimizer/recipe_merger.py`
Moving `COLUMN_RENAMER` to end breaks forward column references.

### M7. `_identify_parallel_branches()` is a no-op (dead code)
**File**: `py2dataiku/optimizer/flow_optimizer.py`
Inner loop has only `pass`; always returns empty.

### M8. PlantUML `skinparam arrow { }` block syntax may be invalid
**File**: `py2dataiku/visualizers/plantuml_visualizer.py`
PlantUML expects flat key-value pairs, not block form.

### M9. PlantUML only styles 5 recipe types
WINDOW, SORT, DISTINCT, STACK, etc. receive no card styling.

### M10. `DiagramGenerator.RECIPE_COLORS` not synchronized with `themes.py`
Two separate color dictionaries with different values for the same recipe types.

### M11. MetricType enum values don't match DSS compound format
DSS uses `"records:COUNT_RECORDS"`, py-iku uses flat `"row_count"`.

### M12. `Py2Dataiku` class missing from `__all__`
Advertised in docs but not exported by `from py2dataiku import *`.

### M13. 12 RecipeTypes have no examples (32% gap)
GENERATE_STATISTICS, PUSH_TO_EDITABLE, LIST_FOLDER_CONTENTS, DYNAMIC_REPEAT, EXTRACT_FAILED_ROWS, LIST_ACCESS, IMPALA, SPARKSQL, SPARK_SCALA, SPARKR, SHELL, AI_ASSISTANT_GENERATE.

### M14. 32 of 122 processors have no examples (26% gap)
Primarily geographic, array/JSON, ML-specific scalers/encoders, and NLP processors.

### M15. ASCII visualizer draws single-column arrows for all connections
Multi-input recipes (JOIN, STACK) cannot be properly represented.

---

## LOW Issues (10) — Documentation and polish

### L1. CLAUDE.md claims "7 exception types" — actually 8
### L2. CLAUDE.md claims method `_merge_prepare_recipes()` — actually `_optimize_prepare_steps()`
### L3. CLAUDE.md claims "1807 tests" — actual count is ~1,329
### L4. CLAUDE.md melt mapping contradicts actual code
### L5. "Rule-based (fallback)" vs code comments saying "legacy" — inconsistent terminology
### L6. Public API functions missing `Raises:` docstring sections
### L7. `convert()` and `convert_file()` have no `>>>` usage examples in docstrings
### L8. SVG dataset icon is always a database cylinder regardless of connection type
### L9. HTML legend truncates to 8 items, silently dropping recipe types
### L10. `DateFormatter` / `DatetimeFormatter` are duplicate processor entries

---

## Recommended Fix Priority

### Phase 1: Export Correctness (Critical)
Fix C1-C9 to make DSS exports valid. This is the library's core value proposition.

### Phase 2: Generator Correctness (Critical + High)
Fix C10-C12, H1-H3 to ensure both rule-based and LLM generators produce correct flows.

### Phase 3: Mapping Accuracy (Critical + High)
Fix C11, C13, H4-H8 to ensure pandas-to-Dataiku translations are semantically correct.

### Phase 4: Model Fidelity (High)
Fix H9-H11 to ensure model serialization matches DSS wire formats.

### Phase 5: Visualization (Medium)
Fix M1-M5, M8-M10 to make visual output resemble actual DSS UI.

### Phase 6: Documentation & Cleanup (Medium + Low)
Fix M7, M12-M14, H12, L1-L10 to improve accuracy and remove dead code.

---

## Sources

- [Dataiku Developer Guide — Recipes](https://developer.dataiku.com/latest/concepts-and-examples/recipes.html)
- [Dataiku Developer Guide — Flow](https://developer.dataiku.com/latest/concepts-and-examples/flow.html)
- [Dataiku Developer Guide — Datasets](https://developer.dataiku.com/latest/concepts-and-examples/datasets.html)
- [Dataiku Developer Guide — Scenarios](https://developer.dataiku.com/latest/concepts-and-examples/scenarios.html)
- [Dataiku Developer Guide — Metrics & Checks](https://developer.dataiku.com/latest/concepts-and-examples/metrics-and-checks.html)
- [Dataiku API Reference — Recipes](https://developer.dataiku.com/latest/api-reference/python/recipes.html)
- [Dataiku DSS 14 — Processors Index](https://doc.dataiku.com/dss/latest/preparation/processors/index.html)
- [dataiku-api-client-python on GitHub](https://github.com/dataiku/dataiku-api-client-python)
