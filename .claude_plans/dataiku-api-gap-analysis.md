# Dataiku API Gap Analysis

**Date**: 2026-03-14
**Scope**: py2dataiku vs Dataiku DSS 14 API (dataikuapi v14.4.2)
**Sources**: dataikuapi GitHub, developer.dataiku.com, direct source code analysis

---

## Executive Summary

**Overall API Compatibility**: ~35%

- **Recipe type coverage**: 12 of 37 RecipeType values have full Settings + payload support (32%). 19 have MCP mapping (51%).
- **Payload accuracy**: Of the 6 implemented `_build_*_payload` methods, ALL 6 produce payloads with structural errors that would cause DSS import/API failures. Key mismatches include wrong field names, wrong data structures, and invalid enum values.
- **Deployment readiness**: DSSFlowDeployer has fundamental issues (passes connection type as connection name, uses shallow `.update()` for nested payloads, always creates managed datasets even for inputs).

### Top 3 Critical Findings

1. **Join and Grouping payloads are structurally incompatible** -- Join conditions use a completely different schema (`on` array vs `conditions` with typed columns), and Grouping aggregations use a single `function` string instead of DSS's boolean flags per aggregation type.
2. **10+ processor type strings are wrong** -- Values like `"SplitColumn"`, `"ConcatColumns"`, `"RoundColumn"`, `"ClipColumn"` do not match DSS's actual strings (`"ColumnsSplitter"`, `"ColumnsConcat"`, `"Round"`, `"NumberClipping"`). DSS will reject these processors.
3. **19 ProcessorType enum values have no DSS equivalent** -- Scikit-learn concepts (RobustScaler, StandardScaler, PowerTransformer, etc.) are listed as Prepare processors but do not exist in DSS.

### Gaps by Severity

| Severity | Count |
|----------|-------|
| Critical (DSS import/API failure) | 7 |
| High (invalid/incomplete output) | 10 |
| Medium (missing functionality) | 8 |
| Low (missing optional fields) | 7 |
| **Total** | **32** |

---

## 1. Recipe Type Coverage

| Recipe Type | DSS type string | Enum | Handler | Settings | API format | MCP | Priority |
|---|---|---|---|---|---|---|---|
| PREPARE | `"shaker"` / `"prepare"` | Yes | Yes | Yes (PrepareSettings) | Yes (_build_prepare_payload) -- **has errors** | Yes | Critical |
| GROUPING | `"grouping"` | Yes | Yes | Yes (GroupingSettings) | Yes (_build_grouping_payload) -- **has errors** | Yes | Critical |
| JOIN | `"join"` | Yes | Yes | Yes (JoinSettings) | Yes (_build_join_payload) -- **has errors** | Yes | Critical |
| WINDOW | `"window"` | Yes | Yes | Yes (WindowSettings) | No -- **to_dss_builder_args() structure wrong** | Yes | Critical |
| STACK | `"vstack"` | Yes | Yes | Yes (StackSettings) | No -- **to_dss_builder_args() values wrong** | Yes | High |
| SPLIT | `"split"` | Yes | Yes | Yes (SplitSettings) | No -- **to_dss_builder_args() structure wrong** | Yes | High |
| SORT | `"sort"` | Yes | Yes | Yes (SortSettings) | Yes (_build_sort_payload) -- **has errors** | Yes | High |
| DISTINCT | `"distinct"` | Yes | Yes | Yes (DistinctSettings) | Yes (_build_distinct_payload) -- **minor gap** | Yes | Medium |
| TOP_N | `"topn"` | Yes | Yes | Yes (TopNSettings) | No -- **to_dss_builder_args() keys wrong** | Yes | High |
| PIVOT | `"pivot"` | Yes | Yes | Yes (PivotSettings) | No -- **to_dss_builder_args() keys wrong** | Yes | High |
| SAMPLING | `"sampling"` | Yes | Yes | Yes (SamplingSettings) | No -- **to_dss_builder_args() values wrong** | Yes | High |
| PYTHON | `"python"` | Yes | Yes | Yes (PythonSettings) | Yes (_build_python_payload) -- **format issue** | Yes | Medium |
| SYNC | `"sync"` | Yes | Yes | No | No | Yes | Medium |
| DOWNLOAD | `"download"` | Yes | No | No | No | Yes | Low |
| FUZZY_JOIN | `"fuzzyjoin"` | Yes -- **wrong value** (`"fuzzy_join"`) | Yes | No | No | No | Medium |
| GEO_JOIN | `"geojoin"` | Yes -- **wrong value** (`"geo_join"`) | Yes | No | No | No | Medium |
| R | `"r"` | Yes | Yes | No | No | Yes | Low |
| SQL | `"sql_script"` | Yes -- **wrong value** (`"sql_query"`) | Yes | No | No | Yes | Medium |
| HIVE | `"hive"` | Yes | Yes | No | No | Yes | Low |
| IMPALA | `"impala"` | Yes | Yes | No | No | Yes | Low |
| SPARKSQL | `"spark_sql_query"` | Yes -- **wrong value** (`"sparksql"`) | Yes | No | No | Yes | Medium |
| PYSPARK | `"pyspark"` | Yes | Yes | No | No | Yes | Low |
| SPARK_SCALA | `"spark_scala"` | Yes | Yes | No | No | Yes | Low |
| SPARKR | `"sparkr"` | Yes | Yes | No | No | Yes | Low |
| SHELL | `"shell"` | Yes | Yes | No | No | Yes | Low |
| GENERATE_FEATURES | `"generate_features"` | Yes | No | No | No | No | Low |
| GENERATE_STATISTICS | `"generate_statistics"` | Yes | No | No | No | No | Low |
| PUSH_TO_EDITABLE | `"push_to_editable"` | Yes | No | No | No | No | Low |
| LIST_FOLDER_CONTENTS | `"list_folder_contents"` | Yes | No | No | No | No | Low |
| DYNAMIC_REPEAT | `"dynamic_repeat"` | Yes | No | No | No | No | Low |
| EXTRACT_FAILED_ROWS | `"extract_failed_rows"` | Yes | No | No | No | No | Low |
| UPSERT | `"upsert"` | Yes | No | No | No | No | Low |
| LIST_ACCESS | `"list_access"` | Yes | No | No | No | No | Low |
| PREDICTION_SCORING | `"prediction_scoring"` | Yes | No | No | No | No | Medium |
| CLUSTERING_SCORING | `"clustering_scoring"` | Yes | No | No | No | No | Medium |
| EVALUATION | `"standalone_evaluation"` | Yes -- **wrong value** (`"evaluation"`) | No | No | No | No | Medium |
| AI_ASSISTANT_GENERATE | `"ai_assistant_generate"` | Yes | No | No | No | No | Low |

### Missing from py2dataiku entirely (DSS supports, no RecipeType enum value)

| DSS Type String | Description | Impact |
|---|---|---|
| `"csync"` | Continuous Sync | Medium -- streaming pipelines |
| `"export"` | Export recipe | Medium -- data output pipelines |
| `"embed_documents"` | Embed Documents (LLM) | Low -- newer AI feature |
| `"extract_content"` | Extract Content | Low -- document processing |
| `"nlp_llm_rag_embedding"` | RAG Embedding | Low -- newer AI feature |

---

## 2. Recipe Payload Accuracy Issues

### 2.1 JOIN Recipe -- Completely Wrong Condition Structure

**File**: `py2dataiku/exporters/dss_exporter.py:438-466`

| Field | py2dataiku sends | DSS expects | Fix |
|---|---|---|---|
| Join type key | `"type": "LEFT"` | `"joinType": "LEFT"` | Rename key |
| Conditions array key | `"on": [...]` | `"conditions": [...]` | Rename key |
| Condition item format | `{"left": {"column": "id"}, "right": {"column": "id"}, "matchType": "EXACT"}` | `{"type": "EQ", "column1": {"name": "id", "table": 0}, "column2": {"name": "id", "table": 1}}` | Restructure completely |
| Top-level mode | `"mode": "LEFT"` | _(not expected)_ | Remove |
| VirtualInput contents | `"originLabel": "input_0"` | `"preFilter": {}` | Replace field |
| Output column mode | `"outputColumnsSelectionMode": "MANUAL"` | `"limitOutputColumns": false` | Replace key/type (string -> boolean) |
| PreFilter location | Top-level `"preFilter": {}` | Inside each virtualInput | Move to correct location |

### 2.2 GROUPING Recipe -- Wrong Aggregation Format

**File**: `py2dataiku/exporters/dss_exporter.py:468-486`

| Field | py2dataiku sends | DSS expects | Fix |
|---|---|---|---|
| Aggregation format | `{"column": "c", "function": "SUM"}` | `{"column": "c", "type": "COLUMN", "sum": true, "avg": false, "count": false, ...}` | Restructure: single function string -> boolean flags per aggregation |
| Extra field | `"$idx": 0` | _(not expected)_ | Remove |
| Value type | `"type": "string"` | `"type": "COLUMN"` | Change value |
| Key format | `{"column": "k", "type": "string"}` | `{"column": "k"}` | Remove `type` from keys |
| Compute mode | _(missing)_ | `"computeMode": "GLOBAL"` | Add field |

### 2.3 PREPARE Recipe -- Wrong Field Names and Missing Fields

**File**: `py2dataiku/exporters/dss_exporter.py:390-436`

| Field | py2dataiku sends | DSS expects | Fix |
|---|---|---|---|
| Top-level mode | `"mode": "BATCH"` | _(not expected)_ | Remove |
| Column selection key | `"columnsSelection"` | `"colSelection"` | Rename key |
| Sampling config | _(missing)_ | `"samplingMethod": "HEAD_SEQUENTIAL"`, `"maxRecords": 10000`, `"targetRatio": 0.02` | Add fields |
| Selection object | _(missing)_ | `"selection": {"samplingMethod": "HEAD_SEQUENTIAL", "maxRecords": 10000}` | Add object |
| Context project | _(missing)_ | `"contextProjectKey": "PROJECT_KEY"` | Add field |
| Exploration filters | _(missing)_ | `"explorationFilters": []` | Add field |
| Step extra fields | _(missing)_ | `"preview": false`, `"alwaysShowComment": false`, `"comment": ""` | Add to each step |

### 2.4 SORT Recipe -- Inverted Boolean Key

**File**: `py2dataiku/exporters/dss_exporter.py:488-506`

| Field | py2dataiku sends | DSS expects | Fix |
|---|---|---|---|
| Order direction key | `"desc": true` | `"ascending": false` | Rename key and invert value |
| Rank columns | _(missing)_ | `"rowNumber": {"enabled": false, "name": "row_number"}`, `"rank": {...}`, `"denseRank": {...}` | Add optional fields |

### 2.5 WINDOW Recipe -- Completely Different Structure

**File**: `py2dataiku/models/recipe_settings.py:238-249` (via `to_dss_builder_args()`)

| Field | py2dataiku sends | DSS expects | Fix |
|---|---|---|---|
| Partition key | `"partitionColumns": [...]` | `"windowDefinitions": [{"partitionBy": [...]}]` | Nest inside windowDefinitions |
| Order key | `"orderColumns": [...]` | `"orderBy": [...]` inside windowDefinitions | Nest and rename |
| Frame spec | _(missing)_ | `"frameType": "ROWS"`, `"frameStart": {"mode": "UNBOUNDED_PRECEDING"}`, `"frameEnd": {"mode": "CURRENT_ROW"}` | Add frame spec |
| Aggregations key | `"aggregations": [...]` | `"values": [{"column": "...", "windowAggregation": "SUM", "outputColumn": "...", "windowDefinitionIndex": 0}]` | Restructure completely |

### 2.6 STACK Recipe -- Wrong Enum Value and Missing Structure

**File**: `py2dataiku/models/recipe_settings.py:392-395`

| Field | py2dataiku sends | DSS expects | Fix |
|---|---|---|---|
| Mode value | `"UNION"` | `"UNION_ALL"` | Change value |
| Virtual inputs | _(missing)_ | `"virtualInputs": [{"index": 0}, {"index": 1}]` | Add |
| Selected columns | _(missing)_ | `"selectedColumns": []` | Add |
| Origin column | _(missing)_ | `"originColumn": {"name": "__dku_input_origin", "enabled": false}` | Add |

### 2.7 SPLIT Recipe -- Completely Different Structure

**File**: `py2dataiku/models/recipe_settings.py:296-299`

| Field | py2dataiku sends | DSS expects | Fix |
|---|---|---|---|
| Mode key | `"splitMode": "FILTER"` | `"mode": "VALUES"` | Rename key |
| Condition format | `"condition": ""` (single string) | `"splits": [{"filter": {"conditions": [...], "enabled": true}, "output": {...}}]` | Restructure completely |
| Column / defaults | _(missing)_ | `"column": "...", "defaultOutputIndex": -1` | Add |

### 2.8 SAMPLING Recipe -- Wrong Method Values and Key Names

**File**: `py2dataiku/models/recipe_settings.py:270-276`

| Field | py2dataiku sends | DSS expects | Fix |
|---|---|---|---|
| Method value | `"RANDOM"` | `"RANDOM_FIXED_NB"` | Fix enum values |
| Size key | `"sampleSize"` | `"maxRecords"` | Rename key |
| Additional fields | _(missing)_ | `targetRatio`, `column`, `partitionByColumn`, `seed`, `ascendingOrder` | Add |

**SamplingMethod enum (`dataiku_recipe.py:208-217`) value mismatches**:

| py2dataiku value | DSS expected |
|---|---|
| `RANDOM` | `RANDOM_FIXED_NB` |
| `RANDOM_FIXED` | `RANDOM_FIXED_RATIO` |
| `FIRST_ROWS` | `HEAD_SEQUENTIAL` |
| `LAST_ROWS` | `TAIL_SEQUENTIAL` |

### 2.9 TOP_N Recipe -- Wrong Key Names

**File**: `py2dataiku/models/recipe_settings.py:347-351`

| Field | py2dataiku sends | DSS expects | Fix |
|---|---|---|---|
| Limit key | `"topN": 10` | `"limit": 10` | Rename key |
| Column key | `"rankingColumn": "col"` (string) | `"orderBy": [{"column": "col", "ascending": false}]` (array of objects) | Restructure |
| Group by | _(missing)_ | `"groupBy": []` | Add |

### 2.10 PIVOT Recipe -- Wrong Key Names

**File**: `py2dataiku/models/recipe_settings.py:443-449`

| Field | py2dataiku sends | DSS expects | Fix |
|---|---|---|---|
| Row columns key | `"rowColumns"` | `"keyColumns"` | Rename |
| Column key | `"columnColumn"` | `"pivotColumn"` | Rename |
| Value format | `"valueColumn": "rev", "aggregation": "SUM"` (single) | `"aggregations": [{"column": "rev", "type": "sum"}]` (array) | Restructure |
| Max values | _(missing)_ | `"pivotColumnMaxValues": 100` | Add |
| Explicit values | _(missing)_ | `"explicitValues": []` | Add |

### 2.11 DISTINCT Recipe -- Missing Field

**File**: `py2dataiku/exporters/dss_exporter.py:508-521`

| Field | py2dataiku sends | DSS expects | Fix |
|---|---|---|---|
| Keep all columns | _(missing)_ | `"keepAllColumns": true` | Add boolean field |

### 2.12 PYTHON Recipe -- Payload Format Issue

**File**: `py2dataiku/exporters/dss_exporter.py:523-540`

| Field | py2dataiku sends | DSS expects | Fix |
|---|---|---|---|
| Payload format | JSON object with `params.code` | Plain text string (the script itself) | The recipe _definition_ can have params, but the _payload_ is just the code string |

---

## 3. Dataset Connection Gaps

| Connection Type | In Enum | Config Implemented | DSS Supported | Notes |
|---|---|---|---|---|
| FILESYSTEM | Yes | Generic only | Yes | Missing `path_in_connection` config |
| SQL_POSTGRESQL | Yes | No | Yes | Missing `table`, `schema`, `catalog` |
| SQL_MYSQL | Yes | No | Yes | Missing `table`, `schema` |
| SQL_BIGQUERY | Yes | No | Yes | Missing `table`, `schema` |
| SQL_SNOWFLAKE | Yes | No | Yes | Missing `table`, `schema`, `warehouse` |
| SQL_REDSHIFT | Yes | No | Yes | Missing `table`, `schema` |
| S3 | Yes | No | Yes | Missing `bucket`, `path_in_connection` |
| GCS | Yes | No | Yes | Missing `bucket`, `path_in_connection` |
| AZURE_BLOB | Yes -- **wrong value** (`"AzureBlob"` vs DSS `"Azure"`) | No | Yes | Wrong type string + missing `container`, `path_in_connection` |
| HDFS | Yes | No | Yes | Missing HDFS-specific path format |
| MANAGED_FOLDER | Yes -- **not a dataset type** | N/A | N/A | ManagedFolder is a separate DSS object type, not a DatasetConnectionType |
| MONGODB | Yes | No | Yes | Missing collection config |
| ELASTICSEARCH | Yes | No | Yes | Missing index config |
| UploadedFiles | **Missing** | No | Yes | Manually uploaded files |
| JDBC | **Missing** | No | Yes | Generic JDBC connection |
| Vertica | **Missing** | No | Yes | Vertica database |
| Teradata | **Missing** | No | Yes | Teradata database |
| Oracle | **Missing** | No | Yes | Oracle database |
| SQLServer | **Missing** | No | Yes | SQL Server database |
| SAPHana | **Missing** | No | Yes | SAP HANA |
| Synapse | **Missing** | No | Yes | Azure Synapse |
| Databricks | **Missing** | No | Yes | Databricks |
| DatabricksLakehouse | **Missing** | No | Yes | Databricks Lakehouse |
| Athena | **Missing** | No | Yes | AWS Athena |
| FTP / SCP / SFTP | **Missing** | No | Yes | File transfer protocols |
| HTTP | **Missing** | No | Yes | HTTP download |
| Cassandra | **Missing** | No | Yes | Apache Cassandra |

**Additional dataset issues**:

- **GAP-3.4a** (`dss_exporter.py:210`): Non-INPUT datasets get type `"Managed"`, which is not a valid DSS dataset type string. DSS uses the connection type string (e.g., `"Filesystem"`) and distinguishes managed vs unmanaged via the `"managed": true/false` flag.
- **GAP-7.2a** (`dataiku_dataset.py:91`): `to_json()` uses literal string `"${PROJECT_KEY}"` as projectKey placeholder instead of an actual value.

---

## 4. Processor Type Gaps

### 4.1 Processor Type Strings That Don't Match DSS

These ProcessorType values will produce type strings that DSS will reject.

| py2dataiku ProcessorType | py2dataiku .value | DSS Actual String | File |
|---|---|---|---|
| SPLIT_COLUMN | `"SplitColumn"` | `"ColumnsSplitter"` | `prepare_step.py` |
| CONCAT_COLUMNS | `"ConcatColumns"` | `"ColumnsConcat"` | `prepare_step.py` |
| COLUMNS_CONCATENATOR | `"ColumnsConcatenator"` | `"ColumnsConcat"` | `prepare_step.py` |
| FILL_EMPTY_WITH_PREVIOUS_NEXT | `"FillEmptyWithPreviousNext"` | `"UpDownFill"` | `prepare_step.py` |
| TEXT_SIMPLIFIER | `"TextSimplifier"` | `"SimplifyText"` | `prepare_step.py` |
| REGEXP_EXTRACTOR | `"RegexpExtractor"` | `"PatternExtract"` | `prepare_step.py` |
| CLIP_COLUMN | `"ClipColumn"` | `"NumberClipping"` | `prepare_step.py` |
| ROUND_COLUMN | `"RoundColumn"` | `"Round"` | `prepare_step.py` |
| NORMALIZER | `"Normalizer"` | `"MeasureNormalize"` | `prepare_step.py` |
| COLUMN_DELETER | `"ColumnDeleter"` | `"ColumnsSelector"` (with `keep=false`) | `prepare_step.py` |
| MERGE_LONG_TAIL_VALUES | `"MergeLongTailValues"` | `"LongTailGrouper"` | `prepare_step.py` |
| DATE_COMPONENTS_EXTRACTOR | `"DateComponentsExtractor"` | `"DateComponentExtractor"` (singular) | `prepare_step.py` |
| DATE_DIFF_CALCULATOR | `"DateDiffCalculator"` | `"DateDifference"` | `prepare_step.py` |
| DATETIME_FORMATTER | `"DatetimeFormatter"` | `"DateFormatter"` | `prepare_step.py` |

### 4.2 ProcessorType Values with No DSS Equivalent (19 invalid)

These exist in py2dataiku but are NOT actual DSS Prepare processor types. If used, DSS will reject them.

| ProcessorType | .value | What DSS has instead |
|---|---|---|
| ABS_COLUMN | `"AbsColumn"` | Use `CreateColumnWithGREL` with `abs()` expression |
| DISCRETIZER | `"Discretizer"` | Use `Binner` |
| QUANTILE_TRANSFORMER | `"QuantileTransformer"` | No DSS equivalent (scikit-learn concept) |
| ROBUST_SCALER | `"RobustScaler"` | No DSS equivalent (scikit-learn concept) |
| MIN_MAX_SCALER | `"MinMaxScaler"` | Use `MeasureNormalize` with `MIN_MAX` method |
| STANDARD_SCALER | `"StandardScaler"` | Use `MeasureNormalize` with `ZSCORE` method |
| LOG_TRANSFORMER | `"LogTransformer"` | Use `CreateColumnWithGREL` with `log()` expression |
| POWER_TRANSFORMER | `"PowerTransformer"` | No DSS equivalent (scikit-learn concept) |
| BOX_COX_TRANSFORMER | `"BoxCoxTransformer"` | No DSS equivalent (scikit-learn concept) |
| ONE_HOT_ENCODER | `"OneHotEncoder"` | ML preprocessing only, not a Prepare processor |
| LABEL_ENCODER | `"LabelEncoder"` | ML preprocessing only |
| ORDINAL_ENCODER | `"OrdinalEncoder"` | ML preprocessing only |
| TARGET_ENCODER | `"TargetEncoder"` | ML preprocessing only |
| LEAVE_ONE_OUT_ENCODER | `"LeaveOneOutEncoder"` | ML preprocessing only |
| WOE_ENCODER | `"WOEEncoder"` | ML preprocessing only |
| FEATURE_HASHER | `"FeatureHasher"` | ML preprocessing only |
| BOOLEAN_CONVERTER | `"BooleanConverter"` | Use `TypeSetter` with `type: "boolean"` |
| NUMBER_TO_STRING | `"NumberToString"` | Use `TypeSetter` with `type: "string"` |
| STRING_TO_NUMBER | `"StringToNumber"` | Use `TypeSetter` with `type: "double"` or `"int"` |

### 4.3 DSS Processors Not in py2dataiku (Top 20 by Utility)

| DSS Processor Type String | Description | Utility |
|---|---|---|
| `"MemoryEquiJoiner"` | In-memory equi join (lookup) | High -- common enrichment pattern |
| `"ObjectUnnestJSON"` | Unnest JSON object to columns | High -- JSON data handling |
| `"GeoPointCreator"` | Create geopoint from lat/lon | High -- geospatial workflows |
| `"GeoPointExtractor"` | Extract lat/lon from geopoint | High -- geospatial workflows |
| `"FuzzyJoiner"` | Fuzzy join in Prepare recipe | Medium -- data matching |
| `"DateRoundDown"` | Truncate date to unit | Medium -- time series |
| `"FilterOnDate"` | Filter rows by date range | Medium -- time filtering |
| `"FilterOnMeaning"` | Filter by data meaning | Medium -- data quality |
| `"InvalidSplit"` | Split valid/invalid rows | Medium -- data quality |
| `"MeaningTranslate"` | Translate via data meaning | Medium -- standardization |
| `"UnixTimestampParser"` | Convert Unix timestamps | Medium -- data ingestion |
| `"CurrencyConverter"` | Currency conversion | Medium -- financial data |
| `"NumericHashing"` | Hash numeric values | Low -- ML feature engineering |
| `"NumericalCombinations"` | Numeric feature combinations | Low -- ML feature engineering |
| `"Mean"` | Compute average of columns | Low -- basic math |
| `"GeoInfoExtractor"` | Extract city/country from geopoint | Low -- enrichment |
| `"GeoDistance"` | Compute geographic distance | Low -- geospatial |
| `"ArrayExtract"` | Extract element from array | Low -- array handling |
| `"ArraysConcat"` | Concatenate arrays | Low -- array handling |
| `"ZipArrays"` | Zip arrays together | Low -- array handling |

### 4.4 Processor Parameter Schema Issues

ProcessorCatalog entries have `required_params` and `optional_params` but no runtime validation occurs when creating PrepareStep instances. Factory methods also do not enforce required parameters. This means invalid processor configurations can be generated silently.

---

## 5. pandas-to-Dataiku Mapping Gaps

### Operations Incorrectly Falling Back to PYTHON Recipe

| pandas Operation | Current Mapping | Better DSS Recipe/Processor | Impact |
|---|---|---|---|
| `df.query("condition")` | Python recipe (via `requires_python_recipe()`) | FilterOnFormula processor or Split recipe | High -- very common operation |
| `df.stack()` | Python recipe | FoldMultipleColumns processor | Medium |
| `df.unstack()` | Python recipe | Pivot recipe (unpivot) | Medium |
| `pd.json_normalize()` | Python recipe | JSONFlattener / ObjectUnnestJSON processor | Medium |
| `df.pct_change()` | Python recipe | Window recipe with LAG + percentage calculation | Low |
| `df.eval("expression")` | Python recipe | CreateColumnWithGREL for simple cases | Low |
| `df.assign(new_col=...)` | Python recipe | CreateColumnWithGREL for simple cases | Low |
| `df.resample()` | Python recipe | Window recipe with date-based grouping | Low |

### Common pandas Operations with NO Mapping at All

| pandas Operation | Recommended DSS Equivalent | Impact |
|---|---|---|
| `df["col"].str.slice(start, end)` | GREL `substring()` expression | Medium |
| `df["col"].str.cat()` | ColumnsConcat processor | Medium |
| `df.between(low, high)` | FilterOnRange processor | Medium |
| `df.isin([vals])` | FilterOnValue with multiple values | Medium |
| `df.where(cond)` / `df.mask(cond)` | IfThenElse processor | Medium |
| `df.replace({mapping})` | TranslateValues or FindReplace | Medium |
| `df.value_counts()` | Grouping recipe with COUNT | Medium |
| `pd.crosstab()` | Pivot recipe | Low |
| `df.rolling(window).agg()` | Window recipe | Low |
| `df.expanding().agg()` | Window recipe | Low |
| `df["col"].dt.year/month/day` | DateComponentExtractor processor | Low |
| `df["col"].dt.strftime()` | DateFormatter processor | Low |
| `pd.to_numeric()` | TypeSetter processor | Low |
| `df["col"].str.pad()` | StringTransformer PAD_LEFT/PAD_RIGHT | Low |
| `df["col"].str.zfill()` | StringTransformer PAD_LEFT | Low |

### Aggregation Mapping Structural Issue

The `AGG_MAPPINGS` system (`pandas_mappings.py:74-88`) assumes aggregations are represented as single `"function"` strings (e.g., `"SUM"`, `"AVG"`). DSS Grouping recipes use boolean flags per aggregation type (`"sum": true, "avg": false, ...`). This is a structural mismatch that affects all grouping operations.

---

## 6. Deployment Gaps (DSSFlowDeployer)

**File**: `py2dataiku/integrations/dss_client.py`

### What It Cannot Do

| Capability | Status | dataikuapi Support |
|---|---|---|
| Flow zone assignment | Not implemented | `flow.create_zone()`, `zone.add_item()` |
| Dataset partitioning | Not implemented | `builder.with_copy_partitioning_from()`, partition dimensions |
| Format type specification | Not implemented | `create_dataset(formatType="csv", formatParams={...})` |
| Existing dataset reuse | Not implemented | `project.get_dataset()` + check existence |
| Append mode outputs | Not implemented | `creator.with_existing_output(append=True)` |
| Input/output roles | Not implemented | `creator.with_input(name, role="main"/"secondary")` |
| Schema propagation | Not implemented | `flow.run_schema_propagation()` |
| Error recovery / rollback | Not implemented | Manual cleanup needed |
| Multiple output roles (Split) | Not implemented | Split recipe needs multiple named output references |
| Cross-project references | Not implemented | `"FOREIGN_PROJECT.dataset_name"` format |
| Recipe-specific creators | Not used | `GroupingRecipeCreator`, `JoinRecipeCreator`, etc. |

### Specific Bugs

**GAP-6.3b** (`dss_client.py:246`): `builder.with_store_into(connection_type)` passes the connection type VALUE (e.g., `"Filesystem"`) as the connection name. The `with_store_into()` method expects a **connection name** (e.g., `"filesystem_managed"`, `"S3_my_bucket"`), not a connection type string. This will fail at runtime.

**GAP-6.2b** (`dss_client.py:305-309`): Recipe settings applied via `recipe_def.get_json_payload().update(builder_args)`:
1. `.update()` is shallow -- won't correctly merge nested structures like `engineParams`
2. For code recipes, the payload is a string, not a dict -- calling `.update()` will raise an error

**GAP-6.2a** (`dss_client.py:294`): Uses `project.new_recipe(dss_type, recipe.name)` but dataikuapi's `new_recipe()` signature varies. Should use explicit keyword: `project.new_recipe(type=dss_type, name=recipe.name)`.

**GAP-6.3a** (`dss_client.py:242`): Uses `new_managed_dataset()` for ALL datasets, including INPUT type. Input datasets should use `create_dataset()` or connection-specific methods (`create_filesystem_dataset()`, `create_s3_dataset()`, etc.).

---

## 7. Metadata & Schema Gaps

### Missing Fields DSS Expects

**On Recipe API dict** (`dataiku_recipe.py:388-418`):

| Field | DSS Expected | py2dataiku Status |
|---|---|---|
| `projectKey` | Required for cross-project | Missing entirely |
| `tags` | `[]` (array) | Missing |
| `versionTag` | `{"versionNumber": 0}` for new objects | Missing from `to_api_dict()` |
| `appendMode` on output items | `false` (boolean) | Missing -- sends `deps: []` instead |
| `deps` on output items | Not expected on outputs | Present but wrong |

**On Dataset JSON** (`dataiku_dataset.py:87-99`):

| Field | DSS Expected | py2dataiku Status |
|---|---|---|
| `projectKey` | Actual project key string | Uses literal `"${PROJECT_KEY}"` placeholder |
| `versionTag` | Present | Missing from `to_json()` |
| `partitioning.filePathPattern` | `null` for non-partitioned | Missing (only `dimensions: []`) |
| `managed` | `true/false` boolean | Missing |
| `formatType` | `"csv"`, `"parquet"`, etc. | Missing |
| `formatParams` | `{"separator": ",", ...}` | Missing |

### Wrong Formats

| Issue | Location | Details |
|---|---|---|
| Output item format | `dataiku_recipe.py:409` | Sends `{"ref": "name", "deps": []}` but DSS expects `{"ref": "name", "appendMode": false}` |
| Dataset type for managed | `dss_exporter.py:210` | Uses `"Managed"` as type string; should use connection type + `"managed": true` flag |
| Flow zone items | `dss_exporter.py:542-556` | Exports empty zones with `"items": []`; should list all recipes and datasets |
| Zone item format | `dss_exporter.py` | Should use `{"objectId": "name", "objectType": "DATASET", "projectKey": "KEY"}` |

---

## 8. Prioritised Fix List

### Critical Priority (DSS import/API will fail)

| # | Gap | File | Effort | Impact |
|---|---|---|---|---|
| 1 | Join conditions structure completely wrong (`on` array vs `conditions` with typed columns) | `dss_exporter.py:452-458` | 2-3 hrs | Join recipes are unusable |
| 2 | Grouping aggregation format wrong (single `function` string vs boolean flags) | `dss_exporter.py:478-480` | 2-3 hrs | Grouping recipes produce wrong aggregations |
| 3 | Window recipe payload structure completely wrong | `recipe_settings.py:238-249` | 3-4 hrs | Window recipes are unusable |
| 4 | 14 processor type strings don't match DSS | `prepare_step.py` (multiple values) | 1-2 hrs | Prepare steps rejected by DSS |
| 5 | 5 wrong RecipeType DSS type strings (`fuzzy_join`, `geo_join`, `sql_query`, `sparksql`, `evaluation`) | `dataiku_recipe.py:25-67` | 30 min | These recipe types silently produce wrong output |
| 6 | `with_store_into()` receives type instead of connection name | `dss_client.py:246` | 30 min | All dataset creation fails at runtime |
| 7 | Output items have `deps` instead of `appendMode` | `dataiku_recipe.py:409` | 15 min | Recipe output binding incorrect |

### High Priority (Invalid or incomplete output)

| # | Gap | File | Effort | Impact |
|---|---|---|---|---|
| 8 | Sort uses `desc` key instead of `ascending` (inverted) | `dss_exporter.py:498-501` | 15 min | Sort direction reversed |
| 9 | Stack uses `"UNION"` instead of `"UNION_ALL"` + missing virtualInputs | `recipe_settings.py:392-395` | 1 hr | Stack recipes produce wrong mode |
| 10 | Split payload completely different structure | `recipe_settings.py:296-299` | 2-3 hrs | Split recipes are unusable |
| 11 | Sampling method values and key names wrong | `recipe_settings.py:270-276`, `dataiku_recipe.py:208-217` | 1-2 hrs | Sampling recipes fail |
| 12 | TopN key names wrong (`topN`/`rankingColumn` vs `limit`/`orderBy`) | `recipe_settings.py:347-351` | 1 hr | TopN recipes produce wrong output |
| 13 | Pivot key names wrong (`rowColumns`/`columnColumn` vs `keyColumns`/`pivotColumn`) | `recipe_settings.py:443-449` | 1 hr | Pivot recipes produce wrong output |
| 14 | AZURE_BLOB value is `"AzureBlob"`, DSS uses `"Azure"` | `dataiku_dataset.py:29` | 10 min | Azure datasets get wrong type |
| 15 | `"Managed"` is not a valid DSS dataset type string | `dss_exporter.py:210` | 30 min | Exported datasets have invalid type |
| 16 | DSSExporter falls back to `"python"` for 7 code recipe types | `dss_exporter.py:356` | 30 min | R, Hive, Spark recipes exported as Python |
| 17 | 19 ProcessorType values have no DSS equivalent (scikit-learn concepts) | `prepare_step.py` | 2-3 hrs | Need to map to real DSS alternatives or remove |

### Medium Priority (Missing functionality)

| # | Gap | File | Effort | Impact |
|---|---|---|---|---|
| 18 | 4 separate recipe type maps, no single source of truth | Multiple files | 2-3 hrs | Maintenance burden, sync issues |
| 19 | Missing 17+ DSS connection types | `dataiku_dataset.py:16-32` | 2-3 hrs | Can't represent many database types |
| 20 | No connection-specific config handlers | `dss_exporter.py:204-264` | 4-6 hrs | Generic dataset configs only |
| 21 | 5+ pandas operations could use visual recipes instead of Python fallback | `pandas_mappings.py:281-297` | 3-4 hrs | Suboptimal flow generation |
| 22 | DSSFlowDeployer missing zones, partitioning, format, schema propagation | `dss_client.py` | 6-8 hrs | Limited deployment capabilities |
| 23 | Not using recipe-specific creator classes from dataikuapi | `dss_client.py:294` | 4-6 hrs | Missing helper methods |
| 24 | Literal `"${PROJECT_KEY}"` placeholder string | `dataiku_dataset.py:91` | 15 min | Invalid projectKey in exports |
| 25 | Flow zones exported empty (no items) | `dss_exporter.py:542-556` | 1-2 hrs | Zones don't contain expected objects |

### Low Priority (Missing optional fields/features)

| # | Gap | File | Effort | Impact |
|---|---|---|---|---|
| 26 | Prepare steps missing `preview`, `alwaysShowComment`, `comment` fields | `dss_exporter.py:394-399` | 15 min | DSS may add defaults, but export is incomplete |
| 27 | Sort recipe missing `rowNumber`/`rank`/`denseRank` options | Sort recipe payload | 30 min | Can't generate rank columns |
| 28 | Distinct recipe missing `keepAllColumns` field | `dss_exporter.py:508-521` | 10 min | DSS may default, but export incomplete |
| 29 | Missing 27+ DSS processors from ProcessorType enum | `prepare_step.py` | 4-6 hrs | Can't represent some processor types |
| 30 | Missing 15+ pandas method mappings | `pandas_mappings.py` | 3-4 hrs | Some common operations not mapped |
| 31 | Missing `versionTag` on `to_api_dict()` and `to_json()` | `dataiku_recipe.py`, `dataiku_dataset.py` | 30 min | Missing optimistic locking field |
| 32 | Missing `projectKey` on recipe API dict | `dataiku_recipe.py:398-418` | 15 min | Cross-project references broken |

---

## 9. Quick Wins (< 30 min each)

### 1. Fix 5 wrong RecipeType DSS type strings (15 min)

**File**: `py2dataiku/models/dataiku_recipe.py`

| Line | Current | Change to |
|---|---|---|
| ~25 | `FUZZY_JOIN = "fuzzy_join"` | `FUZZY_JOIN = "fuzzyjoin"` |
| ~26 | `GEO_JOIN = "geo_join"` | `GEO_JOIN = "geojoin"` |
| ~51 | `SQL = "sql_query"` | `SQL = "sql_script"` |
| ~54 | `SPARKSQL = "sparksql"` | `SPARKSQL = "spark_sql_query"` |
| ~67 | `EVALUATION = "evaluation"` | `EVALUATION = "standalone_evaluation"` |

### 2. Fix output item format -- `deps` to `appendMode` (15 min)

**File**: `py2dataiku/models/dataiku_recipe.py:409`

Change output serialization from `{"ref": name, "deps": []}` to `{"ref": name, "appendMode": false}`.

### 3. Fix AZURE_BLOB connection type string (10 min)

**File**: `py2dataiku/models/dataiku_dataset.py:29`

Change `AZURE_BLOB = "AzureBlob"` to `AZURE_BLOB = "Azure"`.

### 4. Fix Sort recipe `desc` key (15 min)

**File**: `py2dataiku/exporters/dss_exporter.py:498-501`

Change `"desc": true/false` to `"ascending": false/true` (invert the boolean and rename the key).

### 5. Add `keepAllColumns` to Distinct payload (10 min)

**File**: `py2dataiku/exporters/dss_exporter.py:508-521`

Add `"keepAllColumns": true` to the distinct recipe payload dict.

### 6. Fix Prepare payload field name (10 min)

**File**: `py2dataiku/exporters/dss_exporter.py:432`

Change `"columnsSelection"` to `"colSelection"`.

### 7. Fix Prepare step missing fields (15 min)

**File**: `py2dataiku/exporters/dss_exporter.py:394-399`

Add `"preview": false, "alwaysShowComment": false, "comment": ""` to each step dict.

### 8. Fix `"${PROJECT_KEY}"` literal placeholder (15 min)

**File**: `py2dataiku/models/dataiku_dataset.py:91`

Accept a `project_key` parameter in `to_json()` instead of using a literal placeholder string.

### 9. Add `versionTag` to recipe and dataset serialization (20 min)

**Files**: `py2dataiku/models/dataiku_recipe.py:388-418`, `py2dataiku/models/dataiku_dataset.py:87-99`

Add `"versionTag": {"versionNumber": 0}` to both `to_api_dict()` and `to_json()` output.

### 10. Fix DSSExporter fallback for code recipes (15 min)

**File**: `py2dataiku/exporters/dss_exporter.py:337-356`

Add missing entries to `_get_dss_recipe_type()`: R, HIVE, IMPALA, SPARKSQL, PYSPARK, SPARK_SCALA, SPARKR, SHELL. Currently these fall back to `"python"`.

### 11. Fix `with_store_into()` parameter (15 min)

**File**: `py2dataiku/integrations/dss_client.py:246`

Change from passing connection type value to accepting/using a connection name. At minimum, add a `connection_name` parameter to `deploy_dataset()` or derive a reasonable connection name from the type.

### 12. Add `projectKey` to recipe API dict (15 min)

**File**: `py2dataiku/models/dataiku_recipe.py:398-418`

Accept a `project_key` parameter and include it in the output dict.

---

**End of Gap Analysis Report**
