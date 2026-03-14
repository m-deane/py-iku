# Dataiku DSS API Reference

Researched: 2026-03-14
Sources: dataikuapi GitHub repo (v14.4.2), developer.dataiku.com, doc.dataiku.com/dss/latest, community forums

---

## 1. dataikuapi Package

**PyPI**: `dataiku-api-client` (current: 14.4.2, released 2026-03-06)
**Install**: `pip install dataiku-api-client`
**GitHub**: https://github.com/dataiku/dataiku-api-client-python
**Docs**: https://developer.dataiku.com/latest/api-reference/python/index.html

---

## 2. Recipe Type Strings (Internal DSS Identifiers)

These are the exact strings DSS uses internally as the `type` field for recipes.

### Visual Recipes

| DSS Type String | Python Settings Class | Human Name |
|---|---|---|
| `"shaker"` or `"prepare"` | `PrepareRecipeSettings` | Prepare / Shaker |
| `"grouping"` | `GroupingRecipeSettings` | Group |
| `"join"` | `JoinRecipeSettings` | Join |
| `"fuzzyjoin"` | _(no dedicated settings class)_ | Fuzzy Join |
| `"geojoin"` | _(no dedicated settings class)_ | Geo Join |
| `"vstack"` | `StackRecipeSettings` | Stack |
| `"sampling"` | `SamplingRecipeSettings` | Sample/Filter |
| `"split"` | `SplitRecipeSettings` | Split |
| `"sort"` | `SortRecipeSettings` | Sort |
| `"distinct"` | `DistinctRecipeSettings` | Distinct |
| `"topn"` | `TopNRecipeSettings` | Top N |
| `"pivot"` | `PivotRecipeSettings` | Pivot |
| `"window"` | `WindowRecipeSettings` | Window |
| `"sync"` | `SyncRecipeSettings` | Sync |
| `"csync"` | _(continuous sync)_ | Continuous Sync |
| `"download"` | `DownloadRecipeSettings` | Download |
| `"export"` | `ExportRecipeSettings` | Export |
| `"upsert"` | `UpsertRecipeSettings` | Upsert |
| `"generate_features"` | _(AutoML feature gen)_ | Feature Generation |
| `"embed_documents"` | `EmbedDocumentsRecipeSettings` | Embed Documents |
| `"extract_content"` | `ExtractContentRecipeSettings` | Extract Content |
| `"nlp_llm_rag_embedding"` | _(RAG/LLM)_ | RAG Embedding |
| `"extract_failed_rows"` | _(validation)_ | Extract Failed Rows |

### Code Recipes

| DSS Type String | Human Name |
|---|---|
| `"python"` | Python |
| `"r"` | R |
| `"sql_script"` | SQL Script |
| `"spark_sql_query"` | Spark SQL |
| `"pyspark"` | PySpark |
| `"sparkr"` | SparkR |
| `"spark_scala"` | Spark Scala |
| `"shell"` | Shell |

### ML / Scoring Recipes

| DSS Type String | Human Name |
|---|---|
| `"prediction_scoring"` | Prediction Scoring |
| `"clustering_scoring"` | Clustering Scoring |
| `"standalone_evaluation"` | Standalone Evaluation |

**NOTE for py2dataiku**: py2dataiku currently uses `"PREPARE"`, `"GROUPING"`, `"JOIN"` etc. (uppercase) in its `RecipeType` enum. The actual DSS wire format uses lowercase strings. When exporting DSS project zips or calling the REST API, the lowercase strings must be used.

---

## 3. Recipe JSON Payload Structures

### 3.1 Generic Recipe Definition Envelope

All recipes share this outer envelope (what the REST API PUT/GET returns):

```json
{
  "name": "recipe_name",
  "type": "recipe_type_string",
  "inputs": {
    "main": {
      "items": [
        { "ref": "DATASET_NAME", "deps": [] }
      ]
    }
  },
  "outputs": {
    "main": {
      "items": [
        { "ref": "OUTPUT_DATASET", "appendMode": false }
      ]
    }
  },
  "params": {},
  "tags": [],
  "versionTag": {
    "versionNumber": 0,
    "lastModifiedBy": { "login": "admin" },
    "lastModifiedOn": 1234567890000
  }
}
```

The `payload` (recipe-specific configuration) is stored separately and accessed via `get_json_payload()` / `set_json_payload()`.

### 3.2 Prepare / Shaker Recipe Payload

The shaker payload is a JSON object with a `steps` array. Each step has the following structure:

```json
{
  "steps": [
    {
      "type": "ProcessorTypeString",
      "params": { ... },
      "preview": false,
      "disabled": false,
      "metaType": "PROCESSOR",
      "alwaysShowComment": false,
      "comment": ""
    }
  ],
  "samplingMethod": "HEAD_SEQUENTIAL",
  "maxRecords": 10000,
  "targetRatio": 0.02,
  "selection": {
    "samplingMethod": "HEAD_SEQUENTIAL",
    "maxRecords": 10000
  },
  "colSelection": {
    "mode": "ALL"
  },
  "explorationFilters": [],
  "contextProjectKey": "PROJECT_KEY"
}
```

**Accessing via API:**
```python
settings = recipe.get_settings()   # returns PrepareRecipeSettings
settings.raw_steps                  # list of step dicts
settings.add_processor_step("ColumnRenamer", {"renamings": [{"from": "old", "to": "new"}]})
settings.save()
```

### 3.3 Grouping Recipe Payload

```json
{
  "keys": [
    { "column": "group_col" }
  ],
  "values": [
    {
      "column": "value_col",
      "type": "COLUMN",
      "count": true,
      "min": false,
      "max": false,
      "sum": false,
      "avg": false,
      "stddev": false,
      "countDistinct": false,
      "concat": false,
      "first": false,
      "last": false
    }
  ],
  "globalCount": false,
  "computeMode": "GLOBAL"
}
```

**API pattern:**
```python
settings = recipe.get_settings()  # returns GroupingRecipeSettings
settings.clear_grouping_keys()
settings.add_grouping_key("category")
settings.set_global_count_enabled(True)
col = settings.get_or_create_column_settings("revenue")
settings.set_column_aggregations("revenue", sum=True, avg=True, min=True, max=True)
settings.save()
```

### 3.4 Join Recipe Payload

The join recipe uses "virtual inputs" - indexed references to input datasets:

```json
{
  "virtualInputs": [
    { "index": 0, "preFilter": {}, "computedColumns": [] },
    { "index": 1, "preFilter": {}, "computedColumns": [] }
  ],
  "joins": [
    {
      "table1": 0,
      "table2": 1,
      "joinType": "LEFT",
      "outerJoinOnTheLeft": true,
      "conditionsMode": "AND",
      "conditions": [
        {
          "type": "EQ",
          "column1": { "name": "id", "table": 0 },
          "column2": { "name": "id", "table": 1 }
        }
      ]
    }
  ],
  "selectedColumns": [],
  "computedColumns": [],
  "postFilter": {},
  "limitOutputColumns": false
}
```

**joinType values**: `"LEFT"`, `"RIGHT"`, `"INNER"`, `"FULL"`, `"CROSS"`
**conditionsMode values**: `"AND"`, `"OR"`
**condition type values**: `"EQ"`, `"NE"`, `"LT"`, `"LTE"`, `"GT"`, `"GTE"`, `"K_NEAREST"`, `"WITHIN_RANGE"`

**API pattern:**
```python
settings = recipe.get_settings()  # returns JoinRecipeSettings
settings.add_virtual_input(0)
settings.add_virtual_input(1)
j = settings.add_join("LEFT", 0, 1)
JoinRecipeSettings.add_condition_to_join(j, "EQ", "left_col", "right_col")
settings.save()
```

### 3.5 Stack / VStack Recipe Payload

```json
{
  "virtualInputs": [
    { "index": 0 },
    { "index": 1 }
  ],
  "mode": "UNION_ALL",
  "selectedColumns": [],
  "originColumn": {
    "name": "__dku_input_origin",
    "enabled": false
  }
}
```

**mode values**: `"UNION_ALL"`, `"INTERSECT"`, `"MINUS"`

### 3.6 Split Recipe Payload

```json
{
  "mode": "VALUES",
  "column": "status",
  "splits": [
    {
      "filter": {
        "conditions": [
          { "col": "status", "type": "EQ", "val": "active" }
        ],
        "enabled": true
      },
      "output": { "mode": "dataset", "value": "output_index_0" }
    }
  ],
  "defaultOutputIndex": -1
}
```

**split mode values**: `"VALUES"`, `"RANGE"`, `"RANDOM"`, `"RANDOM_COLUMNS"`, `"FILTER"`, `"CENTILE"`

**API pattern:**
```python
settings = recipe.get_settings()  # returns SplitRecipeSettings
settings.set_split_on_single_column_values("status", splits=[...], default_output_index=0)
# or:
settings.set_split_on_random_ratio(splits=[{"ratio": 0.8}, {"ratio": 0.2}], seed=42)
settings.save()
```

### 3.7 Sort Recipe Payload

```json
{
  "orders": [
    { "column": "date_col", "ascending": false }
  ],
  "rowNumber": { "enabled": true, "name": "row_number" },
  "rank": { "enabled": false, "name": "rank" },
  "denseRank": { "enabled": false, "name": "dense_rank" }
}
```

**API pattern:**
```python
settings = recipe.get_settings()  # returns SortRecipeSettings
settings.clear_sorting_keys()
settings.add_sorting_key("date_col", ascending=False)
settings.row_number_column_enabled = True
settings.rank_column_enabled = False
settings.save()
```

### 3.8 Top N Recipe Payload

```json
{
  "orderBy": [
    { "column": "revenue", "ascending": false }
  ],
  "limit": 100,
  "groupBy": []
}
```

### 3.9 Distinct Recipe Payload

```json
{
  "columns": [],
  "keepAllColumns": true
}
```

### 3.10 Pivot Recipe Payload

```json
{
  "keyColumns": ["region"],
  "pivotColumn": "category",
  "pivotColumnMaxValues": 100,
  "aggregations": [
    {
      "column": "revenue",
      "type": "sum"
    }
  ],
  "explicitValues": []
}
```

### 3.11 Window Recipe Payload

```json
{
  "windowDefinitions": [
    {
      "partitionBy": [
        { "column": "user_id" }
      ],
      "orderBy": [
        { "column": "event_date", "ascending": true }
      ],
      "frameType": "ROWS",
      "frameStart": { "mode": "UNBOUNDED_PRECEDING" },
      "frameEnd": { "mode": "CURRENT_ROW" }
    }
  ],
  "values": [
    {
      "column": "revenue",
      "windowAggregation": "SUM",
      "outputColumn": "running_total",
      "windowDefinitionIndex": 0
    }
  ]
}
```

**windowAggregation values**: `"SUM"`, `"AVG"`, `"MIN"`, `"MAX"`, `"COUNT"`, `"RANK"`, `"DENSE_RANK"`, `"ROW_NUMBER"`, `"LAG"`, `"LEAD"`, `"FIRST_VALUE"`, `"LAST_VALUE"`, `"NTILE"`, `"PERCENT_RANK"`, `"CUME_DIST"`

### 3.12 Sampling Recipe Payload

```json
{
  "samplingMethod": "HEAD_SEQUENTIAL",
  "maxRecords": 10000,
  "targetRatio": 0.1,
  "column": null,
  "partitionByColumn": null,
  "seed": null,
  "ascendingOrder": true
}
```

**samplingMethod values**: `"HEAD_SEQUENTIAL"`, `"TAIL_SEQUENTIAL"`, `"RANDOM_FIXED_NB"`, `"RANDOM_FIXED_RATIO"`, `"COLUMN_BASED"`, `"STRATIFIED_TARGET_NB"`, `"STRATIFIED_TARGET_RATIO"`, `"CLASS_RESAMPLING_TARGET_NB"`, `"CLASS_RESAMPLING_TARGET_RATIO"`

### 3.13 Sync Recipe Payload

```json
{
  "engineType": "DSS",
  "partitionBySpec": null
}
```

**engineType values**: `"DSS"`, `"SQL"`, `"SPARK"`, `"HIVE"`, `"IMPALA"`

### 3.14 Code Recipe Payload

For Python/R/SQL code recipes, the payload is simply the script text as a string (not JSON):

```python
settings = recipe.get_settings()  # returns CodeRecipeSettings
settings.get_code()               # returns script as string
settings.set_code("import dataiku\n...")
settings.save()
```

---

## 4. Dataset Types and Connection Types

### 4.1 Dataset Type Strings (DSS Internal)

**Filesystem-based:**
- `"Filesystem"` - local/NFS filesystem
- `"UploadedFiles"` - manually uploaded files
- `"S3"` - Amazon S3
- `"GCS"` - Google Cloud Storage
- `"Azure"` - Azure Blob Storage
- `"HDFS"` - Hadoop HDFS
- `"FTP"`, `"SCP"`, `"SFTP"` - file transfer protocols
- `"HTTP"` - HTTP download

**SQL databases:**
- `"JDBC"` - generic JDBC
- `"PostgreSQL"`, `"MySQL"`, `"Vertica"`
- `"Snowflake"`, `"Redshift"`, `"BigQuery"`
- `"Teradata"`, `"Oracle"`, `"SQLServer"`
- `"SAPHana"`, `"Netezza"`, `"Greenplum"`
- `"Hiveserver2"`, `"Synapse"`, `"Databricks"`
- `"Athena"` - AWS Athena
- `"DatabricksLakehouse"`

**Other:**
- `"Elasticsearch"`
- `"MongoDB"`
- `"Cassandra"`

### 4.2 Dataset Creation via Python API

```python
# Generic dataset creation
project.create_dataset(
    dataset_name="my_dataset",
    type="Filesystem",           # DSS type string
    params={"connection": "filesystem_default", "path": "/data/my_dataset"},
    formatType="csv",
    formatParams={"separator": ",", "style": "excel", "compress": ""}
)

# Convenience methods
project.create_s3_dataset("name", connection="s3_conn", path_in_connection="/path", bucket="my-bucket")
project.create_gcs_dataset("name", connection="gcs_conn", path_in_connection="/path", bucket="my-bucket")
project.create_azure_blob_dataset("name", connection="azure_conn", path_in_connection="/path", container="container")
project.create_filesystem_dataset("name", connection="filesystem_conn", path_in_connection="/data/name")
project.create_sql_table_dataset("name", type="Snowflake", connection="snowflake_conn", table="TABLE", schema="PUBLIC")

# Managed dataset builder
builder = project.new_managed_dataset("output_dataset")
builder.with_store_into("hdfs_managed")
builder.with_copy_partitioning_from("input_dataset")
dataset = builder.create(overwrite=False)
```

### 4.3 Dataset JSON Structure

```json
{
  "name": "dataset_name",
  "projectKey": "MY_PROJECT",
  "type": "Filesystem",
  "params": {
    "connection": "filesystem_default",
    "path": "/data/my_dataset",
    "notReadyIfEmpty": false
  },
  "formatType": "csv",
  "formatParams": {
    "separator": ",",
    "style": "excel",
    "compress": "",
    "dateSerializationFormat": "ISO",
    "arrayMapFormat": "json",
    "hiveSeparators": ["\u0002", "\u0003", "\u0004"]
  },
  "schema": {
    "columns": [
      { "name": "col1", "type": "string", "comment": "" }
    ],
    "userModified": false
  },
  "versionTag": {
    "versionNumber": 1,
    "lastModifiedBy": { "login": "admin" },
    "lastModifiedOn": 1234567890000
  },
  "tags": [],
  "managed": true,
  "partitioning": {
    "filePathPattern": null,
    "dimensions": []
  }
}
```

---

## 5. Prepare Recipe Processor Type Strings

These are the actual `type` strings used inside shaker step objects.

### 5.1 Column Management

| Type String | Parameters | Description |
|---|---|---|
| `"ColumnRenamer"` | `{"renamings": [{"from": "old", "to": "new"}]}` | Rename columns |
| `"ColumnsSelector"` | `{"keep": false, "columns": ["col1", "col2"]}` | Select/drop columns |
| `"ColumnCopier"` | `{"inputColumn": "src", "outputColumn": "dst"}` | Copy column |
| `"ColumnReorder"` | `{"appliesTo": "SINGLE", "columns": [...], "referenceColumn": "col"}` | Reorder columns |
| `"ColumnsSplitter"` | `{"inCol": "col", "separator": ",", "limit": -1}` | Split one column to many |
| `"ColumnsConcat"` | `{"outputColumn": "result", "columns": [...], "separator": ""}` | Concatenate columns |
| `"ObjectNest"` | `{"outputColumn": "obj", "columns": [...]}` | Nest columns into JSON object |
| `"ObjectUnnestJSON"` | `{"column": "json_col", "inPlace": true}` | Unnest JSON object |

### 5.2 Type Setting / Conversion

| Type String | Parameters | Description |
|---|---|---|
| `"TypeSetter"` | `{"columns": [...], "type": "double"}` | Set column storage type |
| `"DateParser"` | `{"column": "date_col", "formats": ["MM/dd/yyyy"], "outDateColumn": ""}` | Parse to standard date |
| `"UnixTimestampParser"` | `{"column": "ts_col", "unit": "SECONDS"}` | Convert Unix timestamp |
| `"CurrencyConverter"` | `{"column": "price", "inputCurrencyColumn": "currency"}` | Convert currency |

**TypeSetter type values**: `"string"`, `"double"`, `"float"`, `"bigint"`, `"int"`, `"smallint"`, `"tinyint"`, `"boolean"`, `"date"`, `"array"`, `"object"`, `"map"`, `"geopoint"`

### 5.3 Missing Values

| Type String | Parameters | Description |
|---|---|---|
| `"FillEmptyWithValue"` | `{"column": "col", "value": "default"}` | Fill nulls with fixed value |
| `"FillEmptyWithComputedValue"` | `{"column": "col", "mode": "MEAN"}` | Fill nulls with computed value |
| `"RemoveRowsOnEmpty"` | `{"columns": ["col1"], "appliesTo": "SINGLE"}` | Drop rows with empty values |
| `"UpDownFill"` | `{"column": "col", "method": "FORWARD"}` | Forward/backward fill |

**FillEmptyWithComputedValue mode values**: `"MEAN"`, `"MEDIAN"`, `"MIN"`, `"MAX"`, `"PREVIOUS"`, `"NEXT"`

### 5.4 String Transformations

| Type String | Parameters | Description |
|---|---|---|
| `"StringTransformer"` | `{"column": "col", "appliesTo": "SINGLE", "mode": "TO_UPPER"}` | String transform |
| `"FindReplace"` | `{"column": "col", "matching": "FULL_STRING", "mapping": [...], "output": "INPLACE"}` | Find and replace |
| `"SimplifyText"` | `{"column": "col", "normalize": true, "removeAccents": true}` | Simplify/normalize text |
| `"Tokenizer"` | `{"column": "col", "outputColumn": "tokens"}` | Tokenize text |
| `"PatternExtract"` | `{"column": "col", "pattern": "regex", "extractGroups": true}` | Extract via regex |

**StringTransformer mode values**: `"TO_UPPER"`, `"TO_LOWER"`, `"CAPITALIZE"`, `"TRIM"`, `"TRIM_LEFT"`, `"TRIM_RIGHT"`, `"REMOVE_BLANKS"`, `"REMOVE_EMOJI"`, `"TRUNCATE"`, `"PAD_LEFT"`, `"PAD_RIGHT"`

### 5.5 Numeric Transformations

| Type String | Parameters | Description |
|---|---|---|
| `"NumericHashing"` | `{"column": "col", "outputColumn": "hash"}` | Hash numeric values |
| `"NumericalCombinations"` | `{"columns": ["a", "b"], "operations": ["PLUS", "TIMES"]}` | Numeric combinations |
| `"NumberClipping"` | `{"column": "col", "minValue": 0, "maxValue": 100}` | Clip/clamp numbers |
| `"Round"` | `{"column": "col", "precision": 2, "mode": "ROUND"}` | Round numbers |
| `"Mean"` | `{"columns": ["a", "b"], "outputColumn": "avg"}` | Compute average |
| `"Binner"` | `{"inCol": "col", "outCol": "bucket", "mode": "FIXED_NB", "nbBins": 10}` | Discretize to bins |
| `"MeasureNormalize"` | `{"column": "col", "method": "MIN_MAX"}` | Normalize values |

**Binner mode values**: `"FIXED_NB"`, `"CUSTOM_RANGES"`, `"QUANTILES"`

### 5.6 Filtering / Row Operations

| Type String | Parameters | Description |
|---|---|---|
| `"FilterOnValue"` | `{"appliesTo": "SINGLE", "columns": ["col"], "action": "REMOVE_ROW", "values": [...]}` | Filter by value |
| `"FilterOnFormula"` | `{"formula": "len(col) > 5", "action": "REMOVE_ROW"}` | Filter by formula |
| `"FilterOnRange"` | `{"column": "col", "min": 0, "max": 100, "action": "REMOVE_ROW"}` | Filter by range |
| `"FilterOnMeaning"` | `{"column": "col", "meaning": "Email", "action": "REMOVE_ROW"}` | Filter invalid meanings |
| `"InvalidSplit"` | `{"column": "col", "meaning": "Email"}` | Split valid/invalid |

**action values**: `"REMOVE_ROW"`, `"CLEAR_CELL"`, `"KEEP_ROW"`

### 5.7 Categorical / Encoding

| Type String | Parameters | Description |
|---|---|---|
| `"LongTailGrouper"` | `{"column": "col", "topN": 10, "replacementValue": "Other"}` | Group long-tail categories |
| `"SwitchCase"` | `{"column": "col", "outputColumn": "out", "cases": [...]}` | Switch/case transform |
| `"CreateIfThenElse"` | `{"outputColumn": "out", "conditions": [...]}` | If/then/else logic |
| `"MeaningTranslate"` | `{"column": "col", "meaning": "US State Name"}` | Translate via meaning |

### 5.8 Formula / Computed Columns

| Type String | Parameters | Description |
|---|---|---|
| `"CreateColumnWithGREL"` | `{"column": "new_col", "expression": "upper(input)"}` | Create column via GREL expression |
| `"PythonUDF"` | `{"column": "out_col", "mode": "CELL", "pythonSourceCode": "def process(value):\n    return value"}` | Python function |

### 5.9 Date Operations

| Type String | Parameters | Description |
|---|---|---|
| `"DateComponentExtractor"` | `{"column": "date", "outputComponents": ["YEAR", "MONTH", "DAY"]}` | Extract date parts |
| `"DateDifference"` | `{"input1": "date1", "input2": "date2", "outputColumn": "diff", "outputUnit": "DAYS"}` | Compute date diff |
| `"DateFormatter"` | `{"column": "date", "outputFormat": "yyyy-MM-dd", "outputColumn": ""}` | Format date |
| `"DateRoundDown"` | `{"column": "date", "unit": "MONTH"}` | Truncate date |
| `"FilterOnDate"` | `{"column": "date", "relativeMin": "-7d"}` | Filter by date |

### 5.10 Pivoting / Reshaping

| Type String | Parameters | Description |
|---|---|---|
| `"Unfolder"` | `{"column": "key_col", "valueColumn": "val_col"}` | Unfold key-value to wide format |
| `"Folder"` | `{"nameColumn": "col_name", "valueColumn": "col_val", "columns": [...]}` | Fold wide to key-value |
| `"MultiColumnFold"` | `{"columnPattern": "^prefix_", "foldedNameColumn": "name", "foldedValueColumn": "value"}` | Fold multiple columns with pattern |
| `"Transpose"` | `{}` | Transpose rows and columns |
| `"SplitFold"` | `{"column": "col", "separator": ",", "outputColumn": ""}` | Split and fold |
| `"SplitUnfold"` | `{"column": "col", "separator": ","}` | Split and unfold |

### 5.11 Geographic Processors

| Type String | Parameters | Description |
|---|---|---|
| `"GeoPointCreator"` | `{"latColumn": "lat", "lonColumn": "lon", "outputColumn": "geopoint"}` | Create geopoint |
| `"GeoPointExtractor"` | `{"column": "geopoint", "latColumn": "lat", "lonColumn": "lon"}` | Extract lat/lon |
| `"GeoInfoExtractor"` | `{"column": "geopoint", "extractCity": true, "extractCountry": true}` | Extract geo info |
| `"GeoDistance"` | `{"point1Column": "a", "point2Column": "b", "outputColumn": "dist"}` | Compute distance |
| `"GeoIPResolver"` | `{"column": "ip_col", "extractCity": true}` | Resolve GeoIP |
| `"GeoJoin"` | `{"leftColumn": "geopoint", "referenceDataset": "geo_ref"}` | Spatial join |

### 5.12 Join / Lookup Processors (in-Prepare)

| Type String | Parameters | Description |
|---|---|---|
| `"MemoryEquiJoiner"` | `{"leftCol": "id", "rightInput": "ref_dataset", "rightCol": "id", "copyColumns": ["name"]}` | In-memory equi join |
| `"FuzzyJoiner"` | `{"leftCol": "name", "rightInput": "ref", "rightCol": "name"}` | Fuzzy join |
| `"Coalesce"` | `{"outputColumn": "out", "columns": ["a", "b", "c"]}` | Return first non-null |

### 5.13 Array / JSON Processors

| Type String | Parameters | Description |
|---|---|---|
| `"ArrayExtract"` | `{"column": "arr", "index": 0, "outputColumn": "first"}` | Extract from array |
| `"ArrayFold"` | `{"column": "arr", "outputColumn": "element"}` | Fold array to rows |
| `"ArraySort"` | `{"column": "arr", "ascending": true}` | Sort array values |
| `"ArraysConcat"` | `{"columns": ["arr1", "arr2"], "outputColumn": "merged"}` | Concatenate arrays |
| `"UnfoldArray"` | `{"column": "arr", "prefix": "item_"}` | Unfold array to columns |
| `"ZipArrays"` | `{"columns": ["a", "b"], "outputColumn": "zipped"}` | Zip arrays |
| `"JSONPathExtractor"` | `{"column": "json_col", "expression": "$.field", "outputColumn": "out"}` | Extract via JSONPath |

---

## 6. Flow Zone API

### 6.1 Creating and Managing Zones

```python
flow = project.get_flow()

# Create zone
zone = flow.create_zone("Preparation Zone", color="#2ab1ac")

# Get zones
zone = flow.get_zone("zone_id")
default_zone = flow.get_default_zone()
all_zones = flow.list_zones()

# Find which zone an object is in
zone = flow.get_zone_of_object(dataset)
```

### 6.2 Zone Item Management

```python
# Add item (moves from existing zone)
zone.add_item(dataset)     # DSSDataset, DSSManagedFolder, or DSSSavedModel

# Add multiple items
zone.add_items([dataset1, recipe1, dataset2])

# Share an item into zone without unsharing from current zone
zone.add_shared(dataset)
zone.remove_shared(dataset)

# Get settings
zone_settings = zone.get_settings()

# Get zone-specific flow graph
zone_graph = zone.get_graph()

# Delete zone (moves all items to default zone)
zone.delete()
```

### 6.3 Zone JSON Structure

```json
{
  "id": "zone_id",
  "name": "Zone Name",
  "color": "#2ab1ac",
  "items": [
    {
      "objectId": "dataset_name",
      "objectType": "DATASET",
      "projectKey": "MY_PROJECT"
    },
    {
      "objectId": "recipe_name",
      "objectType": "RECIPE",
      "projectKey": "MY_PROJECT"
    }
  ],
  "shared": [
    {
      "objectId": "shared_dataset",
      "objectType": "DATASET"
    }
  ]
}
```

**Supported objectType values**: `"DATASET"`, `"RECIPE"`, `"MANAGED_FOLDER"`, `"SAVED_MODEL"`, `"STREAMING_ENDPOINT"`, `"LABELING_TASK"`, `"MODEL_EVALUATION_STORE"`, `"RETRIEVABLE_KNOWLEDGE"`

**Important**: Recipes and their outputs always live in the same zone. Moving a dataset will move its upstream recipe. Best practice: think in terms of moving recipes to zones, not datasets.

---

## 7. Builder Pattern for Creating Recipes

### 7.1 Core Pattern

```python
import dataikuapi

client = dataikuapi.DSSClient("http://localhost:11200", "your-api-key")
project = client.get_project("MY_PROJECT")

# Step 1: Get recipe creator
creator = project.new_recipe("grouping")    # type string, not enum

# OR use specific creator class:
from dataikuapi.dss.recipe import GroupingRecipeCreator
creator = GroupingRecipeCreator("recipe_name", project)
creator.with_input("input_dataset")
creator.with_new_output("output_dataset", "connection_id")
creator.with_group_key("region")

# Step 2: Build
recipe = creator.build()

# Step 3: Configure (after creation)
recipe_def = recipe.get_definition_and_payload()
payload = recipe_def.get_json_payload()
# modify payload...
recipe_def.set_json_payload(payload)
recipe.set_definition_and_payload(recipe_def)
```

### 7.2 Available Creator Classes

- `DSSRecipeCreator` (base)
- `CodeRecipeCreator`
- `PythonRecipeCreator`
- `SQLQueryRecipeCreator`
- `SingleOutputRecipeCreator`
- `GroupingRecipeCreator`
- `JoinRecipeCreator`
- `StackRecipeCreator`
- `SplitRecipeCreator`
- `SortRecipeCreator`
- `DistinctRecipeCreator`
- `TopNRecipeCreator`
- `PivotRecipeCreator`
- `WindowRecipeCreator`
- `SamplingRecipeCreator`
- `SyncRecipeCreator`
- `DownloadRecipeCreator`

### 7.3 Inputs/Outputs Role Format

Some recipes have multiple input roles:

```python
# Join recipe: first input is "main", others use role index or "secondary"
creator.with_input("left_dataset", role="main")
creator.with_input("right_dataset", role="secondary")

# Split: multiple outputs
creator.with_output("output_1")
creator.with_output("output_2")

# Existing output (append mode)
creator.with_existing_output("existing_dataset", append=True)
```

---

## 8. versionTag Format

The `versionTag` field appears in dataset, recipe, and other DSS object definitions. It is used for optimistic locking (concurrent modification detection):

```json
{
  "versionTag": {
    "versionNumber": 42,
    "lastModifiedBy": {
      "login": "user@company.com"
    },
    "lastModifiedOn": 1710000000000
  }
}
```

- `versionNumber`: integer, incremented on each save
- `lastModifiedBy`: object with `login` field
- `lastModifiedOn`: Unix epoch milliseconds

When creating a new object via API, `versionTag` can be omitted or set to `{"versionNumber": 0}`.

---

## 9. projectKey Requirements and Conventions

- `projectKey` is required in most REST API paths as a URI parameter: `/projects/{projectKey}/recipes/`
- Internal references within a project can omit the projectKey prefix on dataset names
- Cross-project references use: `"FOREIGN_PROJECT.dataset_name"` format in the `ref` field of inputs/outputs
- projectKey must match pattern: `[A-Z][A-Z0-9_]*` (uppercase letters, digits, underscores)

---

## 10. Schema / Column Type Strings

DSS column type strings used in dataset schemas and recipes:

| DSS Type | Description |
|---|---|
| `"string"` | text/varchar |
| `"bigint"` | 64-bit integer |
| `"int"` | 32-bit integer |
| `"smallint"` | 16-bit integer |
| `"tinyint"` | 8-bit integer |
| `"double"` | 64-bit float |
| `"float"` | 32-bit float |
| `"boolean"` | true/false |
| `"date"` | timestamp/date |
| `"array"` | JSON array |
| `"object"` | JSON object/map |
| `"map"` | key-value map |
| `"geopoint"` | geographic point |
| `"geometry"` | geographic geometry |

---

## 11. DSSProjectFlow API

```python
flow = project.get_flow()

# Flow graph
graph = flow.get_graph()
# or per-zone: zone.get_graph()

# Schema propagation
propagation = flow.run_schema_propagation()
propagation.wait_for_completion()

# List all items by type
datasets = project.list_datasets()
recipes = project.list_recipes()

# Get specific items
recipe = project.get_recipe("recipe_name")
dataset = project.get_dataset("dataset_name")

# Delete
recipe.delete()
dataset.delete()
```

---

## 12. Key Mismatches / py2dataiku Concerns

Based on the API research, these areas warrant attention when comparing py2dataiku output with actual DSS expectations:

### 12.1 Recipe Type String Case
- DSS uses **lowercase** type strings: `"grouping"`, `"join"`, `"vstack"`, `"shaker"` etc.
- py2dataiku's `RecipeType` enum uses SCREAMING_SNAKE_CASE internally but the export must map to DSS lowercase strings

### 12.2 Prepare Recipe Type
- DSS uses `"shaker"` (legacy name) or `"prepare"` for Prepare recipes
- Both appear valid; `"shaker"` is more commonly seen in older exports

### 12.3 Stack Recipe Type
- DSS type string is `"vstack"`, NOT `"stack"`
- py2dataiku likely uses `RecipeType.STACK` internally but must export as `"vstack"`

### 12.4 Join Recipe Virtual Inputs
- Join recipes require the concept of "virtual inputs" (indexed references)
- A simple `inputs: [dataset1, dataset2]` is not enough; the payload needs `virtualInputs` with indexes

### 12.5 versionTag
- py2dataiku-generated flows may not include `versionTag`; DSS may require it or will create it on import
- Safe to include `{"versionTag": {"versionNumber": 0}}` in new objects

### 12.6 Processor Type Strings
- DSS processor type strings use PascalCase: `"ColumnRenamer"`, `"FillEmptyWithValue"`, `"TypeSetter"` etc.
- NOT SCREAMING_SNAKE_CASE or hyphen-separated

### 12.7 Inputs/Outputs Structure
- The REST API uses `inputs: {"role_name": {"items": [{"ref": "dataset_name", "deps": []}]}}`
- NOT a flat array

### 12.8 Missing Recipe Types
- py2dataiku documents 37 recipe types; DSS supports additional types: `fuzzyjoin`, `geojoin`, `csync`, `upsert`, `export`, `embed_documents`, `extract_content`, `generate_features`, `nlp_llm_rag_embedding`
- These are absent from py2dataiku's `RecipeType` enum

---

## 13. Sources

- [dataikuapi PyPI](https://pypi.org/project/dataiku-api-client/)
- [GitHub: dataiku/dataiku-api-client-python](https://github.com/dataiku/dataiku-api-client-python)
- [Developer Guide: Recipes API](https://developer.dataiku.com/latest/api-reference/python/recipes.html)
- [Developer Guide: Flow API](https://developer.dataiku.com/latest/api-reference/python/flow.html)
- [DSS REST API Reference](https://doc.dataiku.com/dss/api/14/rest/)
- [DSS Processors Reference](https://doc.dataiku.com/dss/latest/preparation/processors/index.html)
- [DSS Python API (v11 legacy)](https://doc.dataiku.com/dss/11/python-api/recipes.html)
- [DSS Managing Recipes (v7)](https://doc.dataiku.com/dss/7.0/python-api/rest-api-client/recipes.html)
- [Community: Programmatically creating prepare recipe](https://community.dataiku.com/discussion/40302/programmatically-creating-prepare-recipe)
- [ETL-Dataiku-DSS real shaker examples](https://github.com/bigdata-icict/ETL-Dataiku-DSS)
