# Dataiku API Gap Fixes Applied

**Date**: 2026-03-14
**Based on**: `.claude_plans/dataiku-api-gap-analysis.md`
**Test result**: 1955 tests passing (up from 1807 before this work)

---

## Summary

All 7 critical and 10 high-priority gaps identified in the API gap analysis have been resolved. The library now has significantly improved DSS API compatibility for recipe payloads, enum values, and the deployment client.

---

## Critical Fixes (7/7)

### C1 — RecipeType enum values corrected (`models/dataiku_recipe.py`)
| Enum | Before | After (DSS API) |
|------|--------|-----------------|
| `FUZZY_JOIN` | `"fuzzy_join"` | `"fuzzyjoin"` |
| `GEO_JOIN` | `"geo_join"` | `"geojoin"` |
| `SQL` | `"sql_query"` | `"sql_script"` |
| `SPARKSQL` | `"sparksql"` | `"spark_sql_query"` |
| `EVALUATION` | `"evaluation"` | `"standalone_evaluation"` |

### C2 — SamplingMethod enum values corrected (`models/dataiku_recipe.py`)
| Enum | Before | After (DSS API) |
|------|--------|-----------------|
| `RANDOM` | `"RANDOM"` | `"RANDOM_FIXED_NB"` |
| `RANDOM_FIXED` | `"RANDOM_FIXED"` | `"RANDOM_FIXED_RATIO"` |
| `FIRST_ROWS` | `"FIRST_ROWS"` | `"HEAD_SEQUENTIAL"` |
| `LAST_ROWS` | `"LAST_ROWS"` | `"TAIL_SEQUENTIAL"` |

### C3 — `to_api_dict()` output format fixed (`models/dataiku_recipe.py`)
- `{"ref": name, "deps": []}` → `{"ref": name, "appendMode": False}` for all I/O items
- Added `"versionTag": {"versionNumber": 0}` to recipe dict
- `to_api_dict(project_key="")` now accepts optional project key; adds `"projectKey"` when provided
- `to_json()` is now an alias for `to_api_dict()`

### C4 — Join payload restructured (`exporters/dss_exporter.py`)
- Conditions now use `{"type": "EQ", "column1": {"name": ..., "table": 0}, "column2": {"name": ..., "table": 1}}`
- Added `"joinType"` field
- Added `"limitOutputColumns": False`
- Added `"preFilter"` inside each virtual input

### C5 — Grouping payload restructured (`exporters/dss_exporter.py`)
- Aggregations now use boolean flags: `{"column": c, "type": "COLUMN", "sum": true, "avg": false, ...}` instead of a `"function"` string
- Added `"computeMode": "GLOBAL"`

### C6 — Prepare payload field names fixed (`exporters/dss_exporter.py`)
- `"columnsSelection"` → `"colSelection"` (DSS API key)
- Added `"preview": False, "alwaysShowComment": False, "comment": ""` to each step
- Removed top-level `"mode": "BATCH"`

### C7 — Code recipe type mapping added (`exporters/dss_exporter.py`)
- `_get_dss_recipe_type()` extended with: SQL→`"sql_script"`, R→`"r"`, HIVE→`"hive"`, IMPALA→`"impala"`, SPARKSQL→`"spark_sql_query"`, PYSPARK→`"pyspark"`, SPARK_SCALA→`"spark_scala"`, SPARKR→`"sparkr"`, SHELL→`"shell"`

---

## High-Priority Fixes (10/10)

### H1 — Sort payload corrected (`exporters/dss_exporter.py`)
- `"desc": bool` → `"ascending": not desc` (DSS uses ascending flag, not descending)

### H2 — Distinct payload corrected (`exporters/dss_exporter.py`)
- Added `"keepAllColumns": True` to distinct payload

### H3 — Flow zone items populated (`exporters/dss_exporter.py`)
- `_export_flow_zones()` now populates items from `flow.datasets` and `flow.recipes` with `{"objectId", "objectType", "projectKey"}` format (was empty before)

### H4 — Dataset type field fixed (`exporters/dss_exporter.py`)
- Dataset config now uses `dataset.connection_type.value` for the `"type"` field (was hardcoded `"Managed"`)
- Added `"managed": true/false` flag based on connection type
- Added `"projectKey"` to dataset config

### H5 — I/O items format unified (`exporters/dss_exporter.py`)
- All `_format_io_items()` calls now produce `{"ref": name, "appendMode": False}` consistently

### H6 — DSSFlowDeployer connection name fixed (`integrations/dss_client.py`)
- Constructor now takes `connection_name` parameter (default `"filesystem_managed"`) rather than using connection type value
- `deploy_dataset()` passes connection name correctly to `with_store_into()`

### H7 — DSSFlowDeployer deep merge fixed (`integrations/dss_client.py`)
- Recipe settings update uses deep merge of existing payload with new args

### H8 — ProcessorType string values corrected (`models/prepare_step.py`)
14 ProcessorType enum values corrected to match DSS API strings (e.g. `SPLIT_COLUMN: "ColumnsSplitter"`, `ROUND_COLUMN: "Round"`, `FILTER_ON_VALUE: "FilterOnValue"`, etc.)

### H9 — ProcessorCatalog entries updated (`mappings/processor_catalog.py`)
- ProcessorCatalog entries updated to use corrected type strings matching the fixed ProcessorType enum values

### H10 — RecipeSettings `to_dss_builder_args()` added (`models/recipe_settings.py`)
All 12 `RecipeSettings` subclasses now implement `to_dss_builder_args()` returning DSS API-accurate payloads:
- `PrepareSettings` — steps with `preview`, `alwaysShowComment`, `comment` fields
- `GroupingSettings` — boolean aggregation flags, `computeMode`
- `JoinSettings` — EQ conditions with table indices, `joinType`, `limitOutputColumns`
- `WindowSettings` — orders, window frame, partitioning
- `PivotSettings` — row/column key format
- `SplitSettings` — VALUES mode, filter structure
- `SortSettings` — ascending flag, `engineParams`, `preFilter`, `computedColumns`
- `TopNSettings` — order_by, rank column
- `DistinctSettings` — `keepAllColumns`, columns list
- `StackSettings` — UNION_ALL mode mapping
- `PythonSettings` — code, envSelection
- `SamplingSettings` — samplingMethod, targetRatio

---

## Test Coverage Added

- `tests/test_py2dataiku/test_settings_builder_args.py` — 148 tests for all 12 `to_dss_builder_args()` implementations
- `tests/test_py2dataiku/test_integration_module.py` — tests for DSSFlowDeployer (dry run) and MCP tool generation

**Total test count: 1955** (was 1807 before this work cycle)

---

## Remaining Known Gaps (Medium/Low Priority)

See `dataiku-api-gap-analysis.md` for full list. Key remaining items:

- **M1**: ML recipe payloads (PREDICTION_SCORING, CLUSTERING_SCORING) have minimal payload structure
- **M2**: Scenario step types limited (only basic `run_recipe` implemented)
- **M3**: `DataikuMetric`/`DataikuCheck` not yet wired into DSS export
- **L1-L7**: Minor cosmetic/edge-case gaps (chart colors, window frame defaults, etc.)
