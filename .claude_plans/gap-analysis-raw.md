# Gap Analysis: py2dataiku vs Dataiku DSS API

**Date**: 2026-03-14
**Purpose**: Identify all gaps between py2dataiku's output and what Dataiku DSS actually expects
**Sources**: Direct source code reading + API reference + capability map

---

## 1. Recipe Type Coverage Gaps

### 1.1 _DSS_TYPE_MAP Correctness

py2dataiku maintains THREE separate recipe type maps that must stay in sync:

| Location | File | Line | Count |
|----------|------|------|-------|
| `DataikuRecipe._DSS_TYPE_MAP` | `py2dataiku/models/dataiku_recipe.py` | 383-386 | 2 entries |
| `DSSExporter._get_dss_recipe_type()` | `py2dataiku/exporters/dss_exporter.py` | 337-356 | 15 entries |
| `_DSS_RECIPE_TYPE_MAP` | `py2dataiku/integrations/dss_client.py` | 39-63 | 22 entries |
| `_MCP_RECIPE_TYPE_MAP` | `py2dataiku/integrations/mcp_tools.py` | 25-48 | 22 entries |

**GAP-1.1a**: `DataikuRecipe._DSS_TYPE_MAP` (line 383) only has 2 entries (`prepare->shaker`, `stack->vstack`). All other types fall through to `recipe_type.value`. This works for most types but is fragile -- any RecipeType whose `.value` doesn't match DSS's expected string will silently produce wrong output.

**GAP-1.1b**: `DSSExporter._get_dss_recipe_type()` (line 337) has 15 entries but is missing 7 types present in `dss_client.py`: PYSPARK, R, HIVE, IMPALA, SPARKSQL, SPARK_SCALA, SPARKR, SHELL. Unknown types fall back to `"python"` (line 356), so any of these 7 recipe types would be incorrectly exported as Python recipes.

**GAP-1.1c**: Three maps exist with different sizes (2, 15, 22, 22). No single source of truth. If a new recipe type is added, it must be updated in 4 places.

### 1.2 Incorrect DSS Type Strings

| RecipeType | py2dataiku .value | DSS Expected | Status |
|-----------|-------------------|--------------|--------|
| PREPARE | `"prepare"` | `"shaker"` or `"prepare"` | OK (mapped) |
| STACK | `"stack"` | `"vstack"` | OK (mapped) |
| FUZZY_JOIN | `"fuzzy_join"` | `"fuzzyjoin"` | **WRONG**: DSS uses `"fuzzyjoin"` (no underscore) |
| GEO_JOIN | `"geo_join"` | `"geojoin"` | **WRONG**: DSS uses `"geojoin"` (no underscore) |
| SQL | `"sql_query"` | `"sql_script"` | **WRONG**: DSS uses `"sql_script"`, not `"sql_query"` |
| SPARKSQL | `"sparksql"` | `"spark_sql_query"` | **WRONG**: DSS uses `"spark_sql_query"` |
| EVALUATION | `"evaluation"` | `"standalone_evaluation"` | **WRONG**: DSS uses `"standalone_evaluation"` |
| HIVE | `"hive"` | `"hive"` | Verify: may be `"hiveserver2"` for newer DSS |
| IMPALA | `"impala"` | `"impala"` | OK |

**Files affected**:
- `py2dataiku/models/dataiku_recipe.py:25` (FUZZY_JOIN value)
- `py2dataiku/models/dataiku_recipe.py:26` (GEO_JOIN value)
- `py2dataiku/models/dataiku_recipe.py:51` (SQL value)
- `py2dataiku/models/dataiku_recipe.py:54` (SPARKSQL value)
- `py2dataiku/models/dataiku_recipe.py:67` (EVALUATION value)

### 1.3 Recipe Types Missing from py2dataiku

DSS supports these recipe types that have NO RecipeType enum value:

| DSS Type | Description | Impact |
|----------|-------------|--------|
| `"csync"` | Continuous Sync | Medium -- streaming use case |
| `"export"` | Export recipe | Medium -- data pipeline output |
| `"embed_documents"` | Embed Documents (LLM) | Low -- newer AI feature |
| `"extract_content"` | Extract Content | Low -- document processing |
| `"nlp_llm_rag_embedding"` | RAG Embedding | Low -- newer AI feature |

### 1.4 RecipeType Values with No Implementation

These exist in the RecipeType enum but have NO Settings class, NO payload builder, and NO MCP mapping:

| RecipeType | Has Settings | Has Payload | Has MCP | Has Handler |
|-----------|-------------|-------------|---------|------------|
| GENERATE_FEATURES | No | No | No | No |
| GENERATE_STATISTICS | No | No | No | No |
| PUSH_TO_EDITABLE | No | No | No | No |
| LIST_FOLDER_CONTENTS | No | No | No | No |
| DYNAMIC_REPEAT | No | No | No | No |
| EXTRACT_FAILED_ROWS | No | No | No | No |
| UPSERT | No | No | No | No |
| LIST_ACCESS | No | No | No | No |
| PREDICTION_SCORING | No | No | No | No |
| CLUSTERING_SCORING | No | No | No | No |
| EVALUATION | No | No | No | No |
| AI_ASSISTANT_GENERATE | No | No | No | No |
| FUZZY_JOIN | No | No | No | Yes (handler only) |
| GEO_JOIN | No | No | No | Yes (handler only) |

---

## 2. Recipe Payload Accuracy

### 2.1 PREPARE Recipe Payload

**py2dataiku** (`dss_exporter.py:390-436`):
```json
{
  "mode": "BATCH",
  "steps": [...],
  "maxJobsPerCategory": {...},
  "engineParams": {...},
  "columnsSelection": {"mode": "ALL"},
  "virtualInputs": [],
  "filterExpression": {}
}
```

**DSS expects** (API reference section 3.2):
```json
{
  "steps": [...],
  "samplingMethod": "HEAD_SEQUENTIAL",
  "maxRecords": 10000,
  "targetRatio": 0.02,
  "selection": {"samplingMethod": "HEAD_SEQUENTIAL", "maxRecords": 10000},
  "colSelection": {"mode": "ALL"},
  "explorationFilters": [],
  "contextProjectKey": "PROJECT_KEY"
}
```

**Gaps**:
- **GAP-2.1a**: py2dataiku uses `"mode": "BATCH"` -- DSS payload has no top-level `mode` field; this is not in the DSS expected format
- **GAP-2.1b**: Missing `samplingMethod`, `maxRecords`, `targetRatio` -- DSS expects these for the shaker sampling configuration
- **GAP-2.1c**: Missing `selection` object -- DSS uses this for data sampling in the Prepare UI
- **GAP-2.1d**: py2dataiku uses `"columnsSelection"` (line 432) -- DSS uses `"colSelection"` (different key name)
- **GAP-2.1e**: Missing `contextProjectKey` -- DSS expects project key reference
- **GAP-2.1f**: Missing `explorationFilters` -- DSS expects this array
- **GAP-2.1g**: Step objects missing `preview`, `alwaysShowComment`, `comment` fields that DSS includes

**Prepare step structure** (`dss_exporter.py:394-399`):
```json
{"metaType": "PROCESSOR", "type": "...", "disabled": false, "params": {...}}
```
DSS expects:
```json
{"metaType": "PROCESSOR", "type": "...", "disabled": false, "params": {...}, "preview": false, "alwaysShowComment": false, "comment": ""}
```

### 2.2 GROUPING Recipe Payload

**py2dataiku** (`dss_exporter.py:468-486`):
```json
{
  "engineParams": {...},
  "keys": [{"column": "k", "type": "string"}],
  "values": [{"column": "c", "type": "string", "$idx": 0, "function": "SUM"}],
  "globalCount": false,
  "preFilter": {},
  "postFilter": {},
  "computedColumns": []
}
```

**DSS expects** (API reference section 3.3):
```json
{
  "keys": [{"column": "group_col"}],
  "values": [{
    "column": "value_col", "type": "COLUMN",
    "count": true, "min": false, "max": false, "sum": false, "avg": false,
    "stddev": false, "countDistinct": false, "concat": false, "first": false, "last": false
  }],
  "globalCount": false,
  "computeMode": "GLOBAL"
}
```

**Gaps**:
- **GAP-2.2a**: py2dataiku uses `"function": "SUM"` as a single field; DSS uses **boolean flags** per aggregation (`"sum": true`, `"avg": false`, etc.). This is a fundamentally different data structure.
- **GAP-2.2b**: py2dataiku includes `"$idx"` field which is not part of the DSS spec
- **GAP-2.2c**: py2dataiku sets `"type": "string"` on values; DSS uses `"type": "COLUMN"`
- **GAP-2.2d**: Missing `"computeMode"` field (DSS expects `"GLOBAL"` or `"PER_KEY"`)
- **GAP-2.2e**: py2dataiku keys include `"type": "string"` -- DSS keys are simpler `{"column": "name"}`

### 2.3 JOIN Recipe Payload

**py2dataiku** (`dss_exporter.py:438-466`):
```json
{
  "mode": "LEFT",
  "engineParams": {...},
  "virtualInputs": [{"index": 0, "computedColumns": [], "originLabel": "input_0"}, ...],
  "joins": [{
    "table1": 0, "table2": 1, "conditionsMode": "AND",
    "type": "LEFT",
    "on": [{"left": {"column": "..."}, "right": {"column": "..."}, "matchType": "EXACT"}],
    "outerJoinOnTheLeft": true
  }],
  "preFilter": {},
  "postFilter": {},
  "enableAutoCastInJoinConditions": false,
  "computedColumns": [],
  "selectedColumns": [],
  "outputColumnsSelectionMode": "MANUAL"
}
```

**DSS expects** (API reference section 3.4):
```json
{
  "virtualInputs": [{"index": 0, "preFilter": {}, "computedColumns": []}, ...],
  "joins": [{
    "table1": 0, "table2": 1, "joinType": "LEFT",
    "outerJoinOnTheLeft": true, "conditionsMode": "AND",
    "conditions": [{
      "type": "EQ",
      "column1": {"name": "id", "table": 0},
      "column2": {"name": "id", "table": 1}
    }]
  }],
  "selectedColumns": [],
  "computedColumns": [],
  "postFilter": {},
  "limitOutputColumns": false
}
```

**Gaps**:
- **GAP-2.3a**: Top-level `"mode": "LEFT"` -- DSS does not have a top-level `mode` on the join payload
- **GAP-2.3b**: Join conditions use `"on": [{"left": {...}, "right": {...}}]` format -- DSS uses `"conditions": [{"type": "EQ", "column1": {"name": "...", "table": 0}, "column2": {"name": "...", "table": 1}}]`. **Completely different structure.**
- **GAP-2.3c**: py2dataiku uses `"type": "LEFT"` in join object -- DSS uses `"joinType": "LEFT"` (different key name)
- **GAP-2.3d**: py2dataiku virtualInputs include `"originLabel"` -- DSS includes `"preFilter"` instead
- **GAP-2.3e**: py2dataiku uses `"outputColumnsSelectionMode"` -- DSS uses `"limitOutputColumns"` (boolean)
- **GAP-2.3f**: py2dataiku has `"preFilter"` at top level -- DSS puts preFilter inside each virtualInput

### 2.4 SORT Recipe Payload

**py2dataiku** (`dss_exporter.py:488-506`):
```json
{
  "engineParams": {...},
  "orders": [{"column": "date_col", "desc": true}],
  "preFilter": {},
  "computedColumns": []
}
```

**DSS expects** (API reference section 3.7):
```json
{
  "orders": [{"column": "date_col", "ascending": false}],
  "rowNumber": {"enabled": true, "name": "row_number"},
  "rank": {"enabled": false, "name": "rank"},
  "denseRank": {"enabled": false, "name": "dense_rank"}
}
```

**Gaps**:
- **GAP-2.4a**: py2dataiku uses `"desc": true` -- DSS uses `"ascending": false` (inverted boolean, different key name)
- **GAP-2.4b**: Missing `rowNumber`, `rank`, `denseRank` computed column options

### 2.5 DISTINCT Recipe Payload

**py2dataiku** (`dss_exporter.py:508-521`):
```json
{
  "engineParams": {...},
  "columns": [],
  "preFilter": {},
  "computedColumns": [],
  "postFilter": {}
}
```

**DSS expects** (API reference section 3.9):
```json
{
  "columns": [],
  "keepAllColumns": true
}
```

**Gaps**:
- **GAP-2.5a**: Missing `"keepAllColumns"` field -- DSS expects this boolean

### 2.6 PYTHON Recipe Payload

**py2dataiku** (`dss_exporter.py:523-540`):
Stores code in `params.code` as JSON.

**DSS expects** (API reference section 3.14):
Python recipe payload is stored as **raw script text**, not JSON. Access via `settings.get_code()` / `settings.set_code()`.

**Gaps**:
- **GAP-2.6a**: py2dataiku puts code in a JSON `params` object. DSS stores the code recipe payload as a **plain text string**, not a JSON object. The `params` key with `code`, `envSelection`, `pythonParams` may be correct for the recipe _definition_ but the _payload_ itself is just the code string.

### 2.7 WINDOW Recipe Payload (No DSSExporter Support)

**py2dataiku** (`recipe_settings.py:238-249` via `to_dss_builder_args()`):
```json
{
  "partitionColumns": [{"column": "user_id"}],
  "orderColumns": [{"column": "event_date"}],
  "aggregations": [...]
}
```

**DSS expects** (API reference section 3.11):
```json
{
  "windowDefinitions": [{
    "partitionBy": [{"column": "user_id"}],
    "orderBy": [{"column": "event_date", "ascending": true}],
    "frameType": "ROWS",
    "frameStart": {"mode": "UNBOUNDED_PRECEDING"},
    "frameEnd": {"mode": "CURRENT_ROW"}
  }],
  "values": [{
    "column": "revenue", "windowAggregation": "SUM",
    "outputColumn": "running_total", "windowDefinitionIndex": 0
  }]
}
```

**Gaps**:
- **GAP-2.7a**: py2dataiku uses `"partitionColumns"` -- DSS uses `"windowDefinitions"` with `"partitionBy"` inside
- **GAP-2.7b**: py2dataiku uses `"orderColumns"` -- DSS uses `"orderBy"` inside windowDefinitions
- **GAP-2.7c**: Missing `frameType`, `frameStart`, `frameEnd` -- DSS requires window frame specification
- **GAP-2.7d**: py2dataiku uses `"aggregations"` -- DSS uses `"values"` with `"windowAggregation"`, `"outputColumn"`, `"windowDefinitionIndex"`
- **GAP-2.7e**: Completely different structure -- py2dataiku's flat layout vs DSS's nested windowDefinitions + values

### 2.8 STACK Recipe Payload (No DSSExporter Support)

**py2dataiku** (`recipe_settings.py:392-395` via `to_dss_builder_args()`):
```json
{"mode": "UNION"}
```

**DSS expects** (API reference section 3.5):
```json
{
  "virtualInputs": [{"index": 0}, {"index": 1}],
  "mode": "UNION_ALL",
  "selectedColumns": [],
  "originColumn": {"name": "__dku_input_origin", "enabled": false}
}
```

**Gaps**:
- **GAP-2.8a**: py2dataiku uses `"UNION"` -- DSS uses `"UNION_ALL"` (wrong value)
- **GAP-2.8b**: Missing `virtualInputs` -- DSS requires indexed input references
- **GAP-2.8c**: Missing `selectedColumns` and `originColumn`

### 2.9 SPLIT Recipe Payload (No DSSExporter Support)

**py2dataiku** (`recipe_settings.py:296-299` via `to_dss_builder_args()`):
```json
{"splitMode": "FILTER", "condition": ""}
```

**DSS expects** (API reference section 3.6):
```json
{
  "mode": "VALUES",
  "column": "status",
  "splits": [{
    "filter": {"conditions": [{"col": "status", "type": "EQ", "val": "active"}], "enabled": true},
    "output": {"mode": "dataset", "value": "output_index_0"}
  }],
  "defaultOutputIndex": -1
}
```

**Gaps**:
- **GAP-2.9a**: py2dataiku uses `"splitMode"` -- DSS uses `"mode"` (different key)
- **GAP-2.9b**: py2dataiku uses a single `"condition"` string -- DSS uses structured `"splits"` array with `"filter"` objects
- **GAP-2.9c**: Missing `"column"`, `"splits"`, `"defaultOutputIndex"` -- completely different structure

### 2.10 SAMPLING Recipe Payload (No DSSExporter Support)

**py2dataiku** (`recipe_settings.py:270-276` via `to_dss_builder_args()`):
```json
{"samplingMethod": "RANDOM", "sampleSize": 1000}
```

**DSS expects** (API reference section 3.12):
```json
{
  "samplingMethod": "RANDOM_FIXED_NB",
  "maxRecords": 10000,
  "targetRatio": 0.1,
  "column": null,
  "partitionByColumn": null,
  "seed": null,
  "ascendingOrder": true
}
```

**Gaps**:
- **GAP-2.10a**: py2dataiku uses `"RANDOM"` -- DSS uses `"RANDOM_FIXED_NB"` or `"RANDOM_FIXED_RATIO"` (wrong enum value)
- **GAP-2.10b**: py2dataiku uses `"sampleSize"` -- DSS uses `"maxRecords"` (different key name)
- **GAP-2.10c**: Missing `targetRatio`, `column`, `partitionByColumn`, `seed`, `ascendingOrder`
- **GAP-2.10d**: SamplingMethod enum values (`py2dataiku/models/dataiku_recipe.py:208-217`) don't match DSS values: `RANDOM` vs `RANDOM_FIXED_NB`, `RANDOM_FIXED` vs `RANDOM_FIXED_RATIO`, `FIRST_ROWS` vs `HEAD_SEQUENTIAL`, `LAST_ROWS` vs `TAIL_SEQUENTIAL`

### 2.11 TOP_N Recipe Payload (No DSSExporter Support)

**py2dataiku** (`recipe_settings.py:347-351` via `to_dss_builder_args()`):
```json
{"topN": 10, "rankingColumn": "col"}
```

**DSS expects** (API reference section 3.8):
```json
{
  "orderBy": [{"column": "revenue", "ascending": false}],
  "limit": 100,
  "groupBy": []
}
```

**Gaps**:
- **GAP-2.11a**: py2dataiku uses `"topN"` -- DSS uses `"limit"` (different key name)
- **GAP-2.11b**: py2dataiku uses `"rankingColumn"` (single string) -- DSS uses `"orderBy"` (array of objects with `column` and `ascending`)
- **GAP-2.11c**: Missing `"groupBy"` -- DSS supports top N within groups

### 2.12 PIVOT Recipe Payload (No DSSExporter Support)

**py2dataiku** (`recipe_settings.py:443-449` via `to_dss_builder_args()`):
```json
{
  "rowColumns": ["region"],
  "columnColumn": "category",
  "valueColumn": "revenue",
  "aggregation": "SUM"
}
```

**DSS expects** (API reference section 3.10):
```json
{
  "keyColumns": ["region"],
  "pivotColumn": "category",
  "pivotColumnMaxValues": 100,
  "aggregations": [{"column": "revenue", "type": "sum"}],
  "explicitValues": []
}
```

**Gaps**:
- **GAP-2.12a**: py2dataiku uses `"rowColumns"` -- DSS uses `"keyColumns"` (different key name)
- **GAP-2.12b**: py2dataiku uses `"columnColumn"` -- DSS uses `"pivotColumn"` (different key name)
- **GAP-2.12c**: py2dataiku uses `"valueColumn"` + `"aggregation"` (single) -- DSS uses `"aggregations"` array with `"column"` + `"type"` per entry (supports multiple aggregations)
- **GAP-2.12d**: Missing `"pivotColumnMaxValues"` and `"explicitValues"`

---

## 3. Dataset Connection Gaps

### 3.1 py2dataiku ConnectionType vs DSS Type Strings

| py2dataiku ConnectionType | .value | DSS Expected | Match? |
|---------------------------|--------|--------------|--------|
| FILESYSTEM | `"Filesystem"` | `"Filesystem"` | OK |
| SQL_POSTGRESQL | `"PostgreSQL"` | `"PostgreSQL"` | OK |
| SQL_MYSQL | `"MySQL"` | `"MySQL"` | OK |
| SQL_BIGQUERY | `"BigQuery"` | `"BigQuery"` | OK |
| SQL_SNOWFLAKE | `"Snowflake"` | `"Snowflake"` | OK |
| SQL_REDSHIFT | `"Redshift"` | `"Redshift"` | OK |
| S3 | `"S3"` | `"S3"` | OK |
| GCS | `"GCS"` | `"GCS"` | OK |
| AZURE_BLOB | `"AzureBlob"` | `"Azure"` | **WRONG**: DSS uses `"Azure"`, not `"AzureBlob"` |
| HDFS | `"HDFS"` | `"HDFS"` | OK |
| MANAGED_FOLDER | `"ManagedFolder"` | N/A | **Not a dataset type** -- ManagedFolder is a separate DSS object type, not a dataset connection type |
| MONGODB | `"MongoDB"` | `"MongoDB"` | OK |
| ELASTICSEARCH | `"Elasticsearch"` | `"Elasticsearch"` | OK |

**File**: `py2dataiku/models/dataiku_dataset.py:29`

### 3.2 DSS Connection Types Missing from py2dataiku

| DSS Type | Description |
|----------|-------------|
| `"UploadedFiles"` | Manually uploaded files |
| `"JDBC"` | Generic JDBC connection |
| `"Vertica"` | Vertica database |
| `"Teradata"` | Teradata database |
| `"Oracle"` | Oracle database |
| `"SQLServer"` | SQL Server database |
| `"SAPHana"` | SAP HANA |
| `"Netezza"` | IBM Netezza |
| `"Greenplum"` | Greenplum |
| `"Hiveserver2"` | Hive via HiveServer2 |
| `"Synapse"` | Azure Synapse |
| `"Databricks"` | Databricks |
| `"DatabricksLakehouse"` | Databricks Lakehouse |
| `"Athena"` | AWS Athena |
| `"FTP"` | FTP transfer |
| `"SCP"` / `"SFTP"` | Secure file transfer |
| `"HTTP"` | HTTP download |
| `"Cassandra"` | Apache Cassandra |

**13 connection types in py2dataiku vs 30+ in DSS** -- missing 17+ connection types.

### 3.3 Connection-Specific Configuration

**GAP-3.3a**: No connection has specific config handlers. `DSSExporter._build_dataset_config()` (line 204-264) uses generic `params` with just `"connection"` and `"path"`. Missing:

- **SQL datasets**: `table`, `schema`, `catalog` parameters
- **S3 datasets**: `bucket`, `path_in_connection` parameters
- **GCS datasets**: `bucket`, `path_in_connection` parameters
- **Azure datasets**: `container`, `path_in_connection` parameters
- **HDFS datasets**: `path` with HDFS-specific format

### 3.4 Dataset Type String Issue

**GAP-3.4a**: `DSSExporter._build_dataset_config()` (line 210) maps `DatasetType.INPUT` to `"Filesystem"` and non-INPUT to `"Managed"`. But `"Managed"` is not a valid DSS dataset type string. DSS uses the connection type (e.g., `"Filesystem"`, `"S3"`) as the `type` field, and distinguishes managed vs unmanaged via the `"managed": true/false` flag.

---

## 4. Processor Type Gaps

### 4.1 Processor Type String Mismatches

py2dataiku uses PascalCase strings that mostly match DSS, but several have mismatches:

| py2dataiku ProcessorType | .value | DSS Expected | Match? |
|--------------------------|--------|--------------|--------|
| SPLIT_COLUMN | `"SplitColumn"` | `"ColumnsSplitter"` | **WRONG** |
| CONCAT_COLUMNS | `"ConcatColumns"` | `"ColumnsConcat"` | **WRONG** |
| FILL_EMPTY_WITH_PREVIOUS_NEXT | `"FillEmptyWithPreviousNext"` | `"UpDownFill"` | **WRONG** |
| TEXT_SIMPLIFIER | `"TextSimplifier"` | `"SimplifyText"` | **WRONG** |
| REGEXP_EXTRACTOR | `"RegexpExtractor"` | `"PatternExtract"` | **WRONG** |
| CLIP_COLUMN | `"ClipColumn"` | `"NumberClipping"` | **WRONG** |
| ROUND_COLUMN | `"RoundColumn"` | `"Round"` | **WRONG** |
| ABS_COLUMN | `"AbsColumn"` | Not a native DSS processor | **WRONG** -- no DSS equivalent |
| NORMALIZER | `"Normalizer"` | `"MeasureNormalize"` | **WRONG** |
| COLUMNS_CONCATENATOR | `"ColumnsConcatenator"` | `"ColumnsConcat"` | **WRONG** |
| COLUMN_DELETER | `"ColumnDeleter"` | `"ColumnsSelector"` (with `keep=false`) | **WRONG** -- DSS has no "ColumnDeleter"; uses ColumnsSelector |
| MERGE_LONG_TAIL_VALUES | `"MergeLongTailValues"` | `"LongTailGrouper"` | **WRONG** |
| CATEGORICAL_ENCODER | `"CategoricalEncoder"` | Not a single DSS processor | **CHECK** -- DSS has specific encoder types |
| DATE_COMPONENTS_EXTRACTOR | `"DateComponentsExtractor"` | `"DateComponentExtractor"` | **WRONG** (plural vs singular) |
| DATE_DIFF_CALCULATOR | `"DateDiffCalculator"` | `"DateDifference"` | **WRONG** |
| BOOLEAN_CONVERTER | `"BooleanConverter"` | Not a native DSS processor | **CHECK** |
| NUMBER_TO_STRING | `"NumberToString"` | Not a native DSS processor | **CHECK** -- use TypeSetter |
| STRING_TO_NUMBER | `"StringToNumber"` | Not a native DSS processor | **CHECK** -- use TypeSetter |
| DATETIME_FORMATTER | `"DatetimeFormatter"` | `"DateFormatter"` | **WRONG** (already have DATE_FORMATTER) |

**Files affected**: `py2dataiku/models/prepare_step.py:36-37, 27, 41, 34, 59, 57, 22, 80-81, 121`

### 4.2 Processors Missing from py2dataiku

DSS has these processors that py2dataiku doesn't enumerate:

| DSS Processor | Description |
|--------------|-------------|
| `"ObjectNest"` | Nest columns into JSON object |
| `"ObjectUnnestJSON"` | Unnest JSON object |
| `"UnixTimestampParser"` | Convert Unix timestamp |
| `"CurrencyConverter"` | Convert currency |
| `"NumericHashing"` | Hash numeric values |
| `"NumericalCombinations"` | Numeric combinations |
| `"Mean"` | Compute average |
| `"InvalidSplit"` | Split valid/invalid |
| `"FilterOnMeaning"` | Filter by data meaning |
| `"MeaningTranslate"` | Translate via meaning |
| `"DateRoundDown"` | Truncate date |
| `"FilterOnDate"` | Filter by date |
| `"MemoryEquiJoiner"` | In-memory equi join |
| `"FuzzyJoiner"` | Fuzzy join in Prepare |
| `"ArrayExtract"` | Extract from array |
| `"ArraysConcat"` | Concatenate arrays |
| `"UnfoldArray"` | Unfold array to columns |
| `"ZipArrays"` | Zip arrays |
| `"JSONPathExtractor"` | Extract via JSONPath |
| `"GeoPointCreator"` | Create geopoint |
| `"GeoPointExtractor"` | Extract lat/lon |
| `"GeoInfoExtractor"` | Extract geo info |
| `"GeoDistance"` | Compute distance |
| `"GeoIPResolver"` | Resolve GeoIP |
| `"SplitFold"` | Split and fold |
| `"SplitUnfold"` | Split and unfold |
| `"Folder"` (MultiColumnFold) | Fold wide to key-value |

### 4.3 py2dataiku Processors Not in DSS

These exist in py2dataiku's ProcessorType enum but are NOT actual DSS processor type strings:

| ProcessorType | .value | Status |
|--------------|--------|--------|
| ABS_COLUMN | `"AbsColumn"` | Not a DSS processor -- use NumericalTransformer or Formula |
| DISCRETIZER | `"Discretizer"` | Not a DSS processor -- use Binner |
| QUANTILE_TRANSFORMER | `"QuantileTransformer"` | Not a DSS processor -- scikit-learn concept |
| ROBUST_SCALER | `"RobustScaler"` | Not a DSS processor -- scikit-learn concept |
| MIN_MAX_SCALER | `"MinMaxScaler"` | Not a DSS processor -- use MeasureNormalize |
| STANDARD_SCALER | `"StandardScaler"` | Not a DSS processor -- use MeasureNormalize |
| LOG_TRANSFORMER | `"LogTransformer"` | Not a DSS processor -- use NumericalTransformer |
| POWER_TRANSFORMER | `"PowerTransformer"` | Not a DSS processor -- scikit-learn concept |
| BOX_COX_TRANSFORMER | `"BoxCoxTransformer"` | Not a DSS processor -- scikit-learn concept |
| ONE_HOT_ENCODER | `"OneHotEncoder"` | **CHECK** -- DSS may use this name in ML preprocessing but not as a Prepare processor |
| LABEL_ENCODER | `"LabelEncoder"` | Not a DSS Prepare processor -- scikit-learn concept |
| ORDINAL_ENCODER | `"OrdinalEncoder"` | Not a DSS Prepare processor |
| TARGET_ENCODER | `"TargetEncoder"` | Not a DSS Prepare processor |
| LEAVE_ONE_OUT_ENCODER | `"LeaveOneOutEncoder"` | Not a DSS Prepare processor |
| WOE_ENCODER | `"WOEEncoder"` | Not a DSS Prepare processor |
| FEATURE_HASHER | `"FeatureHasher"` | Not a DSS Prepare processor |
| BOOLEAN_CONVERTER | `"BooleanConverter"` | Not a DSS processor |
| NUMBER_TO_STRING | `"NumberToString"` | Not a DSS processor |
| STRING_TO_NUMBER | `"StringToNumber"` | Not a DSS processor |

These 19 processor types would produce **invalid type strings** if sent to DSS.

---

## 5. pandas-to-Dataiku Mapping Gaps

### 5.1 Operations Falling Back to PYTHON Recipe

The `requires_python_recipe()` method (`pandas_mappings.py:281-297`) lists these as Python-only:

| pandas Method | Could Use Visual Recipe? | Recommended DSS Equivalent |
|---------------|--------------------------|---------------------------|
| `apply` | Sometimes | GREL expression for simple cases; PythonUDF processor for row-level |
| `applymap` | Sometimes | GREL expression for simple cases |
| `transform` | Sometimes | Window recipe for group transforms |
| `pipe` | No | Genuinely requires Python |
| `eval` | Sometimes | GREL expression |
| `query` | Yes | FILTER processor or Split recipe |
| `assign` | Sometimes | GREL CreateColumnWithGREL |
| `stack` | Yes | FOLD_MULTIPLE_COLUMNS processor |
| `unstack` | Yes | PIVOT recipe |
| `json_normalize` | Yes | JSONFlattener/JSONPathExtractor processor |
| `resample` | Sometimes | Window recipe with date-based grouping |
| `pct_change` | Yes | Window recipe with LAG_DIFF |

**GAP-5.1a**: `query()` should map to FilterOnFormula processor, not Python recipe
**GAP-5.1b**: `stack()` should map to FoldMultipleColumns processor
**GAP-5.1c**: `unstack()` should map to Pivot recipe
**GAP-5.1d**: `json_normalize()` should map to JSONFlattener processor
**GAP-5.1e**: `pct_change()` should map to Window recipe with percentage calculation

### 5.2 Missing pandas Method Mappings

These common pandas operations have NO mapping (not even to PYTHON):

| pandas Method | Recommended DSS Equivalent |
|--------------|---------------------------|
| `str.pad()` | StringTransformer PAD_LEFT/PAD_RIGHT |
| `str.zfill()` | StringTransformer PAD_LEFT |
| `str.repeat()` | GREL expression |
| `str.wrap()` | GREL expression |
| `str.slice()` | GREL substring |
| `str.cat()` | ColumnsConcat processor |
| `between()` | FilterOnNumericRange processor |
| `isin()` | FilterOnValue with multiple values |
| `where()` | IfThenElse processor (listed in suggestions but not in mappings) |
| `mask()` | IfThenElse processor |
| `replace()` | TranslateValues or FindReplace processor |
| `value_counts()` | Grouping recipe with COUNT |
| `crosstab()` | Pivot recipe |
| `rolling()` (with window) | Window recipe |
| `expanding()` | Window recipe |
| `ewm()` | Window recipe (exponential moving) |
| `dt.year/month/day/...` | DateComponentExtractor processor |
| `dt.strftime()` | DateFormatter processor |
| `to_numeric()` | TypeSetter processor |

### 5.3 Aggregation Mapping Issues

`AGG_MAPPINGS` (`pandas_mappings.py:74-88`):

| pandas | py2dataiku | DSS Expected | Match? |
|--------|-----------|--------------|--------|
| `"std"` | `"STDDEV"` | `"stddev"` (as boolean flag on values) | N/A -- structure differs |
| `"nunique"` | `"COUNTDISTINCT"` | `"countDistinct": true` (boolean flag) | N/A -- structure differs |

The entire AGG_MAPPINGS system assumes a `"function"` string field, but DSS grouping uses boolean flags per aggregation type. See GAP-2.2a.

---

## 6. Deployment Gaps

### 6.1 DSSFlowDeployer Limitations

**Location**: `py2dataiku/integrations/dss_client.py`

| dataikuapi Capability | DSSFlowDeployer Support | Gap |
|----------------------|------------------------|-----|
| Schema definition on datasets | Partial (line 251-260) | Schema set after creation; no validation of DSS column type strings |
| Connection-specific config | No | `builder.with_store_into()` called with raw connection type value (line 246) |
| Flow zone assignment | No | Recipes/datasets not assigned to flow zones |
| Partitioning | No | No `with_copy_partitioning_from()` or partition dimension setup |
| Format type specification | No | No `formatType` or `formatParams` configuration |
| Existing dataset reuse | No | Always creates new managed datasets; no check for existing |
| Append mode | No | No `with_existing_output(append=True)` support |
| Input/output roles | No | All inputs use flat `builder.with_input()` -- no role specification |
| Recipe payload application | Partial (line 305-309) | Uses `get_definition().get_json_payload().update()` which may not handle nested structures correctly |
| Schema propagation | No | No `flow.run_schema_propagation()` after deployment |
| Error recovery / rollback | No | If recipe 5 of 10 fails, first 4 remain orphaned |
| Multiple output roles | No | Split recipe needs multiple named output roles |
| Cross-project references | No | No support for `"FOREIGN_PROJECT.dataset_name"` format |

### 6.2 deploy_recipe Issues

**GAP-6.2a** (`dss_client.py:294`): Uses `project.new_recipe(dss_type, recipe.name)` but `dataikuapi` signature is `project.new_recipe(type, name=None)`. The name parameter may not work as positional arg in all versions.

**GAP-6.2b** (`dss_client.py:305-309`): Recipe settings applied via `recipe_def.get_json_payload().update(builder_args)`. This is problematic because:
1. `get_json_payload()` returns a Python dict that may already have DSS defaults
2. `.update()` is shallow -- won't merge nested structures like `engineParams`
3. For code recipes, the payload is a string, not a dict

**GAP-6.2c**: No recipe-type-specific creator classes used. dataikuapi provides `GroupingRecipeCreator`, `JoinRecipeCreator`, etc. with helper methods like `with_group_key()`, `add_condition_to_join()`. These are bypassed in favor of raw payload manipulation.

### 6.3 deploy_dataset Issues

**GAP-6.3a** (`dss_client.py:242`): Uses `new_managed_dataset()` for all datasets, including INPUT type. Input datasets should use `create_dataset()` or `create_filesystem_dataset()` etc.

**GAP-6.3b** (`dss_client.py:246`): `builder.with_store_into(connection_type)` passes the connection type VALUE (e.g., `"Filesystem"`) as the connection name. This is wrong -- `with_store_into()` expects a **connection name** (e.g., `"filesystem_managed"`), not a connection type.

---

## 7. Metadata/Schema Gaps

### 7.1 versionTag

**GAP-7.1a**: `DSSExporter` includes `versionTag` in recipe configs (line 314-318) and dataset configs (line 223-227). This is correct for export bundles.

**GAP-7.1b**: `DataikuRecipe.to_api_dict()` (line 388-418) does NOT include `versionTag`. This means recipes created via this method lack the optimistic locking field.

**GAP-7.1c**: `DataikuDataset.to_json()` (line 87-99) does NOT include `versionTag`.

### 7.2 projectKey

**GAP-7.2a**: `DataikuDataset.to_json()` (line 91) uses `"${PROJECT_KEY}"` as a literal string placeholder. This is not valid -- it should be set to the actual project key or omitted.

**GAP-7.2b**: `DataikuRecipe.to_api_dict()` does not include `projectKey` at all.

### 7.3 Missing Recipe Fields

`DataikuRecipe.to_api_dict()` output is missing:

| Field | DSS Expected | py2dataiku Status |
|-------|-------------|-------------------|
| `projectKey` | Required | Missing |
| `tags` | Optional (array) | Missing |
| `versionTag` | Expected | Missing |
| `customMeta` | Optional | Missing |
| `deps` on output items | `[]` expected | Missing on outputs (only on inputs) |
| `appendMode` on outputs | `false` default | Missing |

**File**: `py2dataiku/models/dataiku_recipe.py:388-418`

Correct DSS output item format:
```json
{"ref": "OUTPUT_DATASET", "appendMode": false}
```
py2dataiku outputs:
```json
{"ref": "OUTPUT_DATASET", "deps": []}
```

**GAP-7.3a**: Output items have `deps` (wrong) instead of `appendMode` (correct).

### 7.4 Missing Dataset Fields

`DSSExporter._build_dataset_config()` is missing:

| Field | DSS Expected | Status |
|-------|-------------|--------|
| `schema.userModified` | Present | OK |
| `partitioning.filePathPattern` | `null` for non-partitioned | Missing (only has `dimensions: []`) |
| `customFields` | Optional | Missing |
| `checklists` | Optional | Missing |

### 7.5 Flow Zone Configuration

**GAP-7.5a**: `DSSExporter._export_flow_zones()` (line 542-556) creates an empty default zone with no items. All recipes and datasets should be listed in the zone's `items` array.

**GAP-7.5b**: Zone items must use this format:
```json
{"objectId": "name", "objectType": "DATASET", "projectKey": "KEY"}
```
but `_export_flow_zones()` writes `"items": []`.

**GAP-7.5c**: `DataikuFlow.zones` (FlowZone dataclass) is not used by the exporter at all.

---

## Summary: Gap Severity Matrix

### Critical (Would Cause DSS Import/API Failure)

| # | Gap | Location | Issue |
|---|-----|----------|-------|
| 1 | GAP-2.3b | `dss_exporter.py:452-458` | Join conditions structure completely wrong |
| 2 | GAP-2.2a | `dss_exporter.py:478-480` | Grouping aggregation format wrong (function string vs boolean flags) |
| 3 | GAP-2.7a-e | `recipe_settings.py:238-249` | Window recipe payload structure completely wrong |
| 4 | GAP-4.1 | `prepare_step.py` (multiple) | 10+ processor type strings wrong -- DSS will reject |
| 5 | GAP-1.2 | `dataiku_recipe.py:25-67` | 5 wrong DSS type strings (fuzzy_join, geo_join, sql_query, sparksql, evaluation) |
| 6 | GAP-6.3b | `dss_client.py:246` | with_store_into() receives type instead of connection name |
| 7 | GAP-7.3a | `dataiku_recipe.py:409` | Output items have wrong field (deps vs appendMode) |

### High (Produces Invalid/Incomplete Output)

| # | Gap | Location | Issue |
|---|-----|----------|-------|
| 8 | GAP-2.4a | `dss_exporter.py:498-501` | Sort uses desc/ascending inversion |
| 9 | GAP-2.8a | `recipe_settings.py:382` | Stack uses UNION vs UNION_ALL |
| 10 | GAP-2.9a-c | `recipe_settings.py:296-299` | Split payload completely different structure |
| 11 | GAP-2.10a-d | `recipe_settings.py:270-276` | Sampling method values and key names wrong |
| 12 | GAP-2.11a-c | `recipe_settings.py:347-351` | TopN key names wrong |
| 13 | GAP-2.12a-d | `recipe_settings.py:443-449` | Pivot key names wrong |
| 14 | GAP-3.1 | `dataiku_dataset.py:29` | AZURE_BLOB wrong string |
| 15 | GAP-3.4a | `dss_exporter.py:210` | "Managed" not a valid DSS dataset type |
| 16 | GAP-1.1b | `dss_exporter.py:356` | DSSExporter falls back to "python" for 7 recipe types |
| 17 | GAP-4.3 | `prepare_step.py` (multiple) | 19 processor types produce invalid DSS strings |

### Medium (Missing Functionality)

| # | Gap | Location | Issue |
|---|-----|----------|-------|
| 18 | GAP-1.1c | Multiple files | 4 separate recipe type maps, no single source of truth |
| 19 | GAP-3.2 | `dataiku_dataset.py:16-32` | Missing 17+ DSS connection types |
| 20 | GAP-3.3a | `dss_exporter.py:204-264` | No connection-specific config handlers |
| 21 | GAP-5.1 | `pandas_mappings.py:281-297` | 5+ operations could use visual recipes instead of Python |
| 22 | GAP-6.1 | `dss_client.py` | Missing: zones, partitioning, format, schema propagation |
| 23 | GAP-6.2c | `dss_client.py:294` | Not using recipe-specific creator classes |
| 24 | GAP-7.2a | `dataiku_dataset.py:91` | Literal "${PROJECT_KEY}" placeholder string |
| 25 | GAP-7.5 | `dss_exporter.py:542-556` | Flow zones exported empty |

### Low (Missing Optional Fields / Features)

| # | Gap | Location | Issue |
|---|-----|----------|-------|
| 26 | GAP-2.1g | `dss_exporter.py:394-399` | Step missing preview/comment fields |
| 27 | GAP-2.4b | Sort recipe | Missing rowNumber/rank/denseRank options |
| 28 | GAP-2.5a | Distinct recipe | Missing keepAllColumns field |
| 29 | GAP-4.2 | `prepare_step.py` | Missing 27+ DSS processors |
| 30 | GAP-5.2 | `pandas_mappings.py` | Missing 19+ pandas method mappings |
| 31 | GAP-7.1b-c | Multiple | Missing versionTag on to_api_dict/to_json |
| 32 | GAP-7.2b | `dataiku_recipe.py:398-418` | Missing projectKey on recipe API dict |

---

## Appendix: File Reference Index

| File | Key Lines | Contents |
|------|-----------|----------|
| `py2dataiku/models/dataiku_recipe.py` | 10-71, 383-386, 388-501 | RecipeType enum, _DSS_TYPE_MAP, to_api_dict(), _build_settings() |
| `py2dataiku/models/dataiku_dataset.py` | 16-32, 87-99, 204-264 | DatasetConnectionType, to_json() |
| `py2dataiku/models/prepare_step.py` | 8-177, 333-787 | ProcessorType enum (122 values), PrepareStep class |
| `py2dataiku/models/recipe_settings.py` | 63-449 | 12 RecipeSettings subclasses |
| `py2dataiku/exporters/dss_exporter.py` | 337-540 | _get_dss_recipe_type(), all _build_*_payload() methods |
| `py2dataiku/integrations/dss_client.py` | 39-63, 264-329 | _DSS_RECIPE_TYPE_MAP, deploy_recipe(), _get_recipe_builder_args() |
| `py2dataiku/integrations/mcp_tools.py` | 25-48 | _MCP_RECIPE_TYPE_MAP |
| `py2dataiku/mappings/pandas_mappings.py` | 18-98, 281-297 | RECIPE_MAPPINGS, PROCESSOR_MAPPINGS, requires_python_recipe() |

---

**End of Gap Analysis**
