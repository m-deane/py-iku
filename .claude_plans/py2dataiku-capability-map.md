# py2dataiku Capability Map vs Dataiku API

**Date**: 2026-03-14
**Purpose**: Complete mapping of py2dataiku capabilities against Dataiku DSS API

---

## Executive Summary

- **37 RecipeType values**: All mapped and partially implemented
- **122 ProcessorType values**: All enumerated, partially mapped in PandasMapper
- **13 DatasetConnectionType values**: All enumerated
- **12 RecipeSettings subclasses**: Fully implemented with to_dss_builder_args()
- **Exporters**: DSSExporter handles recipe payload building with 6 specific _build_*_payload methods
- **Integrations**: DSSFlowDeployer + MCP tools (19 recipe types mapped)
- **LLM Support**: LLMFlowGenerator with recipe handlers

---

## 1. RecipeType Enumeration (37 Types)

### Summary Table

| RecipeType | DSS Type String | Settings Class | to_dss_builder_args() | _build_*_payload | MCP Map | Handler |
|-----------|-----------------|-----------------|----------------------|------------------|---------|---------|
| PREPARE | shaker | ✓ PrepareSettings | ✓ | ✓ _build_prepare_payload | ✓ | ✓ |
| SYNC | sync | ✗ | ✗ | ✗ | ✓ | ✓ |
| GROUPING | grouping | ✓ GroupingSettings | ✓ | ✓ _build_grouping_payload | ✓ | ✓ |
| WINDOW | window | ✓ WindowSettings | ✓ | ✗ | ✓ | ✓ |
| JOIN | join | ✓ JoinSettings | ✓ | ✓ _build_join_payload | ✓ | ✓ |
| FUZZY_JOIN | fuzzy_join | ✗ | ✗ | ✗ | ✗ | ✓ |
| GEO_JOIN | geo_join | ✗ | ✗ | ✗ | ✗ | ✓ |
| STACK | vstack | ✓ StackSettings | ✓ | ✗ | ✓ | ✓ |
| SPLIT | split | ✓ SplitSettings | ✓ | ✗ | ✓ | ✓ |
| SORT | sort | ✓ SortSettings | ✓ | ✓ _build_sort_payload | ✓ | ✓ |
| DISTINCT | distinct | ✓ DistinctSettings | ✓ | ✓ _build_distinct_payload | ✓ | ✓ |
| TOP_N | topn | ✓ TopNSettings | ✓ | ✗ | ✓ | ✓ |
| PIVOT | pivot | ✓ PivotSettings | ✓ | ✗ | ✓ | ✓ |
| SAMPLING | sampling | ✓ SamplingSettings | ✓ | ✗ | ✓ | ✓ |
| DOWNLOAD | download | ✗ | ✗ | ✗ | ✓ | ✗ |
| GENERATE_FEATURES | generate_features | ✗ | ✗ | ✗ | ✗ | ✗ |
| GENERATE_STATISTICS | generate_statistics | ✗ | ✗ | ✗ | ✗ | ✗ |
| PUSH_TO_EDITABLE | push_to_editable | ✗ | ✗ | ✗ | ✗ | ✗ |
| LIST_FOLDER_CONTENTS | list_folder_contents | ✗ | ✗ | ✗ | ✗ | ✗ |
| DYNAMIC_REPEAT | dynamic_repeat | ✗ | ✗ | ✗ | ✗ | ✗ |
| EXTRACT_FAILED_ROWS | extract_failed_rows | ✗ | ✗ | ✗ | ✗ | ✗ |
| UPSERT | upsert | ✗ | ✗ | ✗ | ✗ | ✗ |
| LIST_ACCESS | list_access | ✗ | ✗ | ✗ | ✗ | ✗ |
| PYTHON | python | ✓ PythonSettings | ✓ | ✓ _build_python_payload | ✓ | ✓ |
| R | r | ✗ | ✗ | ✗ | ✓ | ✓ |
| SQL | sql_query | ✗ | ✗ | ✗ | ✓ | ✓ |
| HIVE | hive | ✗ | ✗ | ✗ | ✓ | ✓ |
| IMPALA | impala | ✗ | ✗ | ✗ | ✓ | ✓ |
| SPARKSQL | sparksql | ✗ | ✗ | ✗ | ✓ | ✓ |
| PYSPARK | pyspark | ✗ | ✗ | ✗ | ✓ | ✓ |
| SPARK_SCALA | spark_scala | ✗ | ✗ | ✗ | ✓ | ✓ |
| SPARKR | sparkr | ✗ | ✗ | ✗ | ✓ | ✓ |
| SHELL | shell | ✗ | ✗ | ✗ | ✓ | ✓ |
| PREDICTION_SCORING | prediction_scoring | ✗ | ✗ | ✗ | ✗ | ✗ |
| CLUSTERING_SCORING | clustering_scoring | ✗ | ✗ | ✗ | ✗ | ✗ |
| EVALUATION | evaluation | ✗ | ✗ | ✗ | ✗ | ✗ |
| AI_ASSISTANT_GENERATE | ai_assistant_generate | ✗ | ✗ | ✗ | ✗ | ✗ |

### Legend
- **DSS Type String**: Mapping from RecipeType.value to DSS API type (in _DSS_TYPE_MAP / _MCP_RECIPE_TYPE_MAP)
- **Settings Class**: RecipeSettings subclass implemented in `py2dataiku/models/recipe_settings.py`
- **to_dss_builder_args()**: Method to convert settings for DSS recipe builder API
- **_build_*_payload**: Dedicated method in DSSExporter to build recipe payload
- **MCP Map**: Mapped in `py2dataiku/integrations/mcp_tools.py` _MCP_RECIPE_TYPE_MAP
- **Handler**: Recipe creation handler exists (appears to be in flow generators)

### Key Findings

**Fully Implemented (11):**
- PREPARE, GROUPING, JOIN, SORT, DISTINCT, PYTHON
- WINDOW, STACK, SPLIT, SAMPLING, TOP_N, PIVOT (12 total when counted with settings)

**Partial Implementation (19):**
- Code recipes (R, SQL, HIVE, IMPALA, SPARKSQL, PYSPARK, SPARK_SCALA, SPARKR, SHELL)
- Additional types (SYNC, DOWNLOAD)
- Fuzzy/Geo operations (FUZZY_JOIN, GEO_JOIN)

**Not Yet Implemented (6):**
- ML recipes: PREDICTION_SCORING, CLUSTERING_SCORING, EVALUATION
- Advanced: GENERATE_FEATURES, GENERATE_STATISTICS
- Data management: PUSH_TO_EDITABLE, LIST_FOLDER_CONTENTS, DYNAMIC_REPEAT, EXTRACT_FAILED_ROWS, UPSERT, LIST_ACCESS, AI_ASSISTANT_GENERATE

---

## 2. DatasetConnectionType Enumeration (13 Types)

All 13 connection types enumerated and accessible via DatasetConnectionType enum:

```
FILESYSTEM, SQL_POSTGRESQL, SQL_MYSQL, SQL_BIGQUERY, SQL_SNOWFLAKE, SQL_REDSHIFT
S3, GCS, AZURE_BLOB, HDFS, MANAGED_FOLDER, MONGODB, ELASTICSEARCH
```

**Implementation Status:**
- ✓ Enumerated in `py2dataiku/models/dataiku_dataset.py`
- ✓ Used in dataset configurations (DSSExporter._build_dataset_config)
- ✓ Serialized in DataikuDataset.to_json()
- ✗ No dedicated handlers for connection-specific parameters in py2dataiku

---

## 3. ProcessorType Enumeration (122 Types)

**All 122 processor types enumerated** in `py2dataiku/models/prepare_step.py`

### Categories (with count)

| Category | Count | Processors |
|----------|-------|-----------|
| Column Manipulation | 6 | COLUMN_RENAMER, COLUMN_COPIER, COLUMN_DELETER, COLUMNS_SELECTOR, COLUMN_REORDER, COLUMNS_CONCATENATOR |
| Missing Value Handling | 5 | FILL_EMPTY_WITH_VALUE, REMOVE_ROWS_ON_EMPTY, FILL_EMPTY_WITH_PREVIOUS_NEXT, FILL_EMPTY_WITH_COMPUTED_VALUE, IMPUTE_WITH_ML |
| String Transformations | 21 | STRING_TRANSFORMER, TOKENIZER, REGEXP_EXTRACTOR, FIND_REPLACE, SPLIT_COLUMN, CONCAT_COLUMNS, HTML_STRIPPER, MULTI_COLUMN_FIND_REPLACE, NGRAMMER, TEXT_SIMPLIFIER, STEM_TEXT, LEMMATIZE_TEXT, LANGUAGE_DETECTOR, SENTIMENT_ANALYZER, TEXT_HASHER, UNICODE_NORMALIZER, URL_PARSER, IP_ADDRESS_PARSER, EMAIL_DOMAIN_EXTRACTOR, PHONE_FORMATTER, COUNTRY_NORMALIZER, USER_AGENT_PARSER |
| Numeric Transformations | 14 | NUMERICAL_TRANSFORMER, ROUND_COLUMN, ABS_COLUMN, CLIP_COLUMN, BINNER, NORMALIZER, DISCRETIZER, QUANTILE_TRANSFORMER, ROBUST_SCALER, MIN_MAX_SCALER, STANDARD_SCALER, LOG_TRANSFORMER, POWER_TRANSFORMER, BOX_COX_TRANSFORMER |
| Type Conversion | 6 | TYPE_SETTER, DATE_PARSER, DATE_FORMATTER, BOOLEAN_CONVERTER, NUMBER_TO_STRING, STRING_TO_NUMBER |
| Date/Time Operations | 7 | DATE_COMPONENTS_EXTRACTOR, DATE_DIFF_CALCULATOR, HOLIDAYS_COMPUTER, TIMEZONE_CONVERTER, DATE_RANGE_CLASSIFIER, DATETIME_FORMATTER, TIMESTAMP_EXTRACTOR |
| Filtering | 9 | FILTER_ON_VALUE, FILTER_ON_BAD_TYPE, FILTER_ON_FORMULA, FILTER_ON_DATE_RANGE, FILTER_ON_NUMERIC_RANGE, FILTER_ON_MULTIPLE_VALUES, FILTER_ON_NULL_NUMERIC, FILTER_ON_GEO_ZONE, FILTER_ON_CUSTOM_CONDITION |
| Flagging | 5 | FLAG_ON_VALUE, FLAG_ON_FORMULA, FLAG_ON_BAD_TYPE, FLAG_ON_DATE_RANGE, FLAG_ON_NUMERIC_RANGE |
| Row Operations | 4 | REMOVE_DUPLICATES, SORT_ROWS, SAMPLE_ROWS, SHUFFLE_ROWS |
| Computed Columns | 5 | CREATE_COLUMN_WITH_GREL, FORMULA, MULTI_COLUMN_FORMULA, COLUMN_PSEUDO_ANONYMIZER, HASH_COMPUTER, UUID_GENERATOR |
| Categorical | 8 | MERGE_LONG_TAIL_VALUES, CATEGORICAL_ENCODER, ONE_HOT_ENCODER, LABEL_ENCODER, ORDINAL_ENCODER, TARGET_ENCODER, LEAVE_ONE_OUT_ENCODER, WOE_ENCODER, FEATURE_HASHER |
| Geographic | 7 | GEO_POINT_CREATOR, GEO_ENCODER, GEO_IP_RESOLVER, GEO_DISTANCE_CALCULATOR, GEO_POLYGON_MATCHER, ADDRESS_PARSER, REVERSE_GEOCODER |
| Conditional Logic | 2 | IF_THEN_ELSE, SWITCH_CASE |
| Value Translation | 1 | TRANSLATE_VALUES |
| Data Extraction | 2 | EXTRACT_WITH_JSONPATH, SPLIT_URL |
| Reshaping | 3 | FOLD_MULTIPLE_COLUMNS, TRANSPOSE_ROWS_TO_COLUMNS, UNFOLD |
| Value Manipulation | 2 | COALESCE, FILL_COLUMN |
| Array/JSON Operations | 9 | ARRAY_SPLITTER, ARRAY_JOINER, ARRAY_SORTER, ARRAY_UNFOLD, ARRAY_FOLD, ARRAY_ELEMENT_EXTRACTOR, JSON_FLATTENER, JSON_EXTRACTOR, XML_EXTRACTOR |
| Nested/Group | 2 | NESTED_PROCESSOR, PROCESSOR_GROUP |
| Python UDF | 1 | PYTHON_UDF |

### Implementation Status

**ProcessorCatalog (122 entries):**
- ✓ All 122 processors have ProcessorInfo entries in `ProcessorCatalog.PROCESSORS`
- ✓ Each includes: name, category, description, required_params, optional_params, example_params
- ✓ Accessible via `ProcessorCatalog()` instance methods

**PandasMapper Coverage:**
- ✓ 16 PROCESSOR_MAPPINGS entries (fillna, dropna, rename, drop, astype, etc.)
- ✓ STRING_MAPPINGS for StringTransformerMode conversions
- ✓ Factory methods for common processors: fill_empty, rename_columns, delete_columns, string_transform, set_type, parse_date, filter_on_value, remove_rows_on_empty, remove_duplicates, create_column_grel, regexp_extract, python_udf, if_then_else, switch_case, translate_values, extract_with_jsonpath, split_url, fold_multiple_columns, unfold, coalesce, fill_column (25+ PrepareStep factory methods)

---

## 4. RecipeSettings Implementation (12 Classes)

All subclasses of `RecipeSettings` base class in `py2dataiku/models/recipe_settings.py`:

| Settings Class | Implements to_dict() | Implements to_display_dict() | Implements to_dss_builder_args() | Recipes |
|---|---|---|---|---|
| PrepareSettings | ✓ | ✓ | ✓ (complex) | PREPARE |
| GroupingSettings | ✓ | ✓ | ✓ | GROUPING |
| JoinSettings | ✓ | ✓ | ✓ | JOIN, FUZZY_JOIN |
| WindowSettings | ✓ | ✓ | ✓ | WINDOW |
| SamplingSettings | ✓ | ✓ | ✓ | SAMPLING |
| SplitSettings | ✓ | ✓ | ✓ | SPLIT |
| SortSettings | ✓ | ✓ | ✓ | SORT |
| TopNSettings | ✓ | ✓ | ✓ | TOP_N |
| DistinctSettings | ✓ | ✓ | ✓ | DISTINCT |
| StackSettings | ✓ | ✓ | ✓ | STACK |
| PythonSettings | ✓ | ✓ | ✓ | PYTHON |
| PivotSettings | ✓ | ✓ | ✓ | PIVOT |

**All 12 fully implement the three required abstract methods** from RecipeSettings ABC:
1. `to_dict()` - Dataiku API-compatible dictionary
2. `to_display_dict()` - Human-readable representation
3. `to_dss_builder_args()` - DSS recipe builder API format

---

## 5. DSSExporter Payload Building

**Location:** `py2dataiku/exporters/dss_exporter.py`

### _get_dss_recipe_type Mapping (in _DSS_TYPE_MAP)

```python
_DSS_TYPE_MAP = {
    "prepare": "shaker",
    "stack": "vstack",
    # All other recipe types use their RecipeType.value directly
}
```

### _build_*_payload Methods

| Method | Recipe Types | Implementation |
|--------|--------------|---|
| _build_recipe_payload() | Router method | Routes to specific builders based on recipe type |
| _build_prepare_payload() | PREPARE | ✓ Implemented |
| _build_join_payload() | JOIN | ✓ Implemented |
| _build_grouping_payload() | GROUPING | ✓ Implemented |
| _build_sort_payload() | SORT | ✓ Implemented |
| _build_distinct_payload() | DISTINCT | ✓ Implemented |
| _build_python_payload() | PYTHON | ✓ Implemented |

### Dataset & Project Export

| Method | Purpose |
|--------|---------|
| _export_dataset() | Exports individual dataset configurations |
| _build_dataset_config() | Builds DSS dataset config (with connection, schema, etc.) |
| _export_recipe() | Exports individual recipe configurations |
| _export_project_json() | Exports project.json metadata |
| _export_params_json() | Exports params.json for project variables |
| _export_flow_zones() | Exports flow zone configuration |

---

## 6. DSSFlowDeployer Integration

**Location:** `py2dataiku/integrations/dss_client.py`

### Capabilities

| Feature | Status | Notes |
|---------|--------|-------|
| Recipe Creation | ✓ | Via dataikuapi builder API |
| Dataset Creation | ✓ | Via dataikuapi API |
| Settings Configuration | ✓ | Uses to_dss_builder_args() |
| Dry-Run Mode | ✓ | Works without dataikuapi dependency |
| Error Handling | ✓ | DeploymentResult with errors/warnings |
| Flow Deployment | ✓ | Topological order via flow.graph |

### _DSS_RECIPE_TYPE_MAP (19 Recipe Types)

Maps 19 recipe types to DSS type strings:
- PREPARE→shaker, JOIN→join, STACK→vstack, SPLIT→split
- GROUPING→grouping, WINDOW→window, PIVOT→pivot, SORT→sort
- DISTINCT→distinct, TOP_N→topn, SAMPLING→sampling
- PYTHON→python, SQL→sql_query, SYNC→sync, DOWNLOAD→download
- PYSPARK→pyspark, R→r, HIVE→hive, IMPALA→impala
- SPARKSQL→sparksql, SPARK_SCALA→spark_scala, SPARKR→sparkr, SHELL→shell

### Flow Deployment Logic

```
1. Topological sort of recipes via flow.graph
2. For each dataset: create via dataikuapi
3. For each recipe: build config + create via dataikuapi
4. Track results in DeploymentResult
```

---

## 7. MCP Tools Integration

**Location:** `py2dataiku/integrations/mcp_tools.py`

### _MCP_RECIPE_TYPE_MAP (19 Recipe Types)

Same 19 recipe types mapped (identical to DSSFlowDeployer):

```python
_MCP_RECIPE_TYPE_MAP = {
    RecipeType.PREPARE: "shaker",
    RecipeType.JOIN: "join",
    RecipeType.STACK: "vstack",
    # ... 16 more mappings
}
```

### Tool Generation

| Function | Purpose |
|----------|---------|
| generate_mcp_tool_calls() | Converts DataikuFlow to MCP tool calls sequence |
| format_mcp_script() | Formats tool calls as executable MCP script |
| _dataset_to_mcp_args() | Builds MCP create_dataset arguments |
| _recipe_to_mcp_args() | Builds MCP create_recipe arguments |
| _get_recipe_settings() | Extracts settings via to_dict() or _build_settings() |

### MCP Tools Supported

Target server: `dataiku_factory` MCP server
- create_dataset
- create_recipe
- run_recipe
- get_project_flow

---

## 8. LLM Flow Generator

**Location:** `py2dataiku/generators/llm_flow_generator.py`

### LLMFlowGenerator Class

Extends BaseFlowGenerator and implements:

| Capability | Status |
|-----------|--------|
| Analysis result to flow conversion | ✓ |
| Dataset registration from LLM | ✓ |
| Step grouping by recipe type | ✓ |
| Recipe generation from LLM steps | ✓ |
| Optimization | ✓ |

### Supported Operations (OperationType)

Maps LLM analysis to recipe generation:
- READ_DATA → Dataset creation
- TRANSFORM → Processor/step handling
- GROUPBY → GROUPING recipe
- JOIN → JOIN recipe
- CONCAT → STACK recipe
- PIVOT → PIVOT recipe
- AGGREGATE → GROUPING recipe

---

## 9. Pandas → Dataiku Mappings

**Location:** `py2dataiku/mappings/pandas_mappings.py`

### RECIPE_MAPPINGS (21 methods)

```
merge/join → JOIN
concat → STACK
groupby → GROUPING
pivot/pivot_table → PIVOT
melt → PIVOT (unpivot)
sort_values → SORT
drop_duplicates → DISTINCT
head/nlargest/nsmallest → TOP_N
sample → SAMPLING
cumsum/cumprod/cummin/cummax/diff/shift/rank → WINDOW
nunique → GROUPING
```

### PROCESSOR_MAPPINGS (16 methods)

```
fillna → FILL_EMPTY_WITH_VALUE
dropna → REMOVE_ROWS_ON_EMPTY
rename → COLUMN_RENAMER
drop → COLUMN_DELETER
astype → TYPE_SETTER
to_datetime → DATE_PARSER
round → ROUND_COLUMN
abs → ABS_COLUMN
clip → CLIP_COLUMN
map → TRANSLATE_VALUES
explode → UNFOLD
combine_first → COALESCE
interpolate → FILL_EMPTY_WITH_PREVIOUS_NEXT
get_dummies → ONE_HOT_ENCODER
cut/qcut → BINNER
```

### AGG_MAPPINGS (aggregation functions)

```
sum→SUM, mean/avg→AVG, count→COUNT, min→MIN, max→MAX
std→STD, var→VAR, median→MEDIAN, first→FIRST, last→LAST
```

### STRING_MAPPINGS (7 string methods)

```
upper→UPPERCASE, lower→LOWERCASE, title/capitalize→TITLECASE
strip→TRIM, lstrip→TRIM_LEFT, rstrip→TRIM_RIGHT
```

---

## 10. Flow Graph & Optimization

**Location:** `py2dataiku/models/flow_graph.py`, `py2dataiku/generators/base_generator.py`

### FlowGraph Features

| Feature | Status |
|---------|--------|
| DAG topological sort | ✓ |
| Cycle detection | ✓ |
| Disconnected subgraph discovery | ✓ |
| Column lineage tracking | ✓ |
| Node/edge iteration | ✓ |

### Optimization

| Optimization | Status |
|---|---|
| Merge consecutive Prepare recipes | ✓ |
| Remove orphan datasets | ✓ |
| Sanitize names | ✓ |
| Remove unused steps | ✓ |

---

## 11. Advanced Features (Partial/Not Implemented)

### Scenario Support
**Location:** `py2dataiku/models/dataiku_scenario.py`
- ✗ Not integrated into flow deployment
- ✗ No DSS exporter support for scenarios

### Metrics & Data Quality
**Location:** `py2dataiku/models/dataiku_metrics.py`
- ✗ Not integrated into flow deployment
- ✗ No DSS exporter support for metrics

### ML Operations
**Location:** `py2dataiku/models/dataiku_mlops.py`
- ✗ APIEndpoint not integrated
- ✗ ModelVersion not integrated
- ✗ DriftConfig not integrated

---

## 12. Capability Gaps

### High-Impact Gaps

1. **ML Recipe Types** (3 recipes)
   - PREDICTION_SCORING, CLUSTERING_SCORING, EVALUATION
   - No Settings classes, no DSSExporter payloads

2. **Advanced Data Operations** (7 recipes)
   - GENERATE_FEATURES, GENERATE_STATISTICS
   - PUSH_TO_EDITABLE, LIST_FOLDER_CONTENTS, DYNAMIC_REPEAT
   - EXTRACT_FAILED_ROWS, UPSERT, LIST_ACCESS, AI_ASSISTANT_GENERATE

3. **Scenario Integration**
   - DataikuScenario model exists but not deployable
   - No DSSExporter._export_scenarios() method

4. **Data Quality & Metrics**
   - DataikuMetric & DataikuCheck models exist
   - No DSS export support

5. **Advanced Join Types**
   - FUZZY_JOIN, GEO_JOIN have RecipeType values
   - No Settings classes, no dedicated _build_*_payload methods
   - Minimal GEO support (GEO_DISTANCE_CALCULATOR processor exists but not integrated)

6. **Connection-Specific Configuration**
   - 13 DatasetConnectionType values enumerated
   - No dedicated handlers for connection parameters (e.g., database credentials, S3 bucket paths)
   - DSSExporter uses generic defaults

### Medium-Impact Gaps

1. **Code Recipe Customization**
   - SQL, R, Hive, Impala, Spark variants exist as RecipeType values
   - Only PYTHON has a Settings class (PythonSettings)
   - No SQL-specific, R-specific payload builders

2. **LLM Coverage**
   - LLMFlowGenerator handles basic operations
   - No support for FUZZY_JOIN, GEO_JOIN, advanced geo operations
   - Limited processor complexity handling

3. **Processor Parameter Validation**
   - ProcessorCatalog has parameter specifications
   - No runtime validation in PrepareStep creation
   - Factory methods don't enforce required params

### Low-Impact Gaps

1. **Plugin System**
   - PluginRegistry exists but not heavily used
   - No out-of-box extension points for new recipes

2. **Flow Zone Support**
   - FlowZone dataclass exists
   - Minimal integration in DSSExporter (basic empty zones.json)

3. **Visualization Detail**
   - Multiple visualizers (SVG, HTML, ASCII, Mermaid, PlantUML)
   - No dynamic icon/styling for advanced recipe types

---

## 13. Implementation Readiness Index

### Ready for Production (11/37 recipes)
- PREPARE, GROUPING, JOIN, WINDOW, STACK, SPLIT, SORT, DISTINCT, TOP_N, SAMPLING, PIVOT, PYTHON

### Ready for Beta (8/37 recipes)
- SYNC, DOWNLOAD, R, SQL, HIVE, IMPALA, SPARKSQL, PYSPARK, SPARK_SCALA, SPARKR, SHELL
  (Code recipes have MCP/DSSFlowDeployer support but limited Settings/payload builders)

### Prototype/Experimental (18/37 recipes)
- FUZZY_JOIN, GEO_JOIN, GENERATE_FEATURES, GENERATE_STATISTICS
- PUSH_TO_EDITABLE, LIST_FOLDER_CONTENTS, DYNAMIC_REPEAT, EXTRACT_FAILED_ROWS
- UPSERT, LIST_ACCESS, PREDICTION_SCORING, CLUSTERING_SCORING, EVALUATION
- AI_ASSISTANT_GENERATE

---

## 14. Processor Implementation Detail

### Fully Integrated (25+ processors with factory methods)

These have PrepareStep factory methods and are production-ready:

- FILL_EMPTY_WITH_VALUE (fill_empty)
- COLUMN_RENAMER (rename_columns)
- COLUMN_DELETER (delete_columns)
- STRING_TRANSFORMER (string_transform)
- TYPE_SETTER (set_type)
- DATE_PARSER (parse_date)
- FILTER_ON_VALUE (filter_on_value)
- REMOVE_ROWS_ON_EMPTY (remove_rows_on_empty)
- REMOVE_DUPLICATES (remove_duplicates)
- CREATE_COLUMN_WITH_GREL (create_column_grel)
- REGEXP_EXTRACTOR (regexp_extract)
- PYTHON_UDF (python_udf)
- IF_THEN_ELSE (if_then_else)
- SWITCH_CASE (switch_case)
- TRANSLATE_VALUES (translate_values)
- EXTRACT_WITH_JSONPATH (extract_with_jsonpath)
- SPLIT_URL (split_url)
- FOLD_MULTIPLE_COLUMNS (fold_multiple_columns)
- TRANSPOSE_ROWS_TO_COLUMNS (transpose_rows_to_columns)
- UNFOLD (unfold)
- COALESCE (coalesce)
- FILL_COLUMN (fill_column)

### Enumerated in Catalog (122 processors)

All 122 processors have ProcessorInfo entries with:
- Name, category, description
- Required and optional parameters
- Example parameter configurations

### Mapped in PandasMapper (16 processors)

Direct pandas→processor mappings available for common operations.

---

## Summary Statistics

| Metric | Count | Status |
|--------|-------|--------|
| RecipeType values | 37 | ✓ Enumerated |
| Fully-implemented recipes | 11 | ✓ Production-ready |
| Recipe Settings classes | 12 | ✓ All implement 3 methods |
| _build_*_payload methods | 6 | ✓ For core recipes |
| DSSExporter support | 11 | ✓ Full export capability |
| MCP-mapped recipes | 19 | ✓ Tool generation |
| ProcessorType values | 122 | ✓ Enumerated |
| Processors with factory methods | 22+ | ✓ Prod-ready |
| PROCESSOR_MAPPINGS | 16 | ✓ Pandas integration |
| DatasetConnectionType values | 13 | ✓ Enumerated |
| Connection-specific handlers | 0 | ✗ Generic only |

---

## Recommendations for Closure

1. **Immediate Priority**: Implement ML recipe types (PREDICTION_SCORING, CLUSTERING_SCORING, EVALUATION)
2. **Near-term**: Add Settings classes for code recipes (SQL, R variants)
3. **Medium-term**: Implement FUZZY_JOIN, GEO_JOIN with dedicated builders
4. **Roadmap**: Scenario, Metrics, MLOps integration for full DSS API coverage

---

**End of Capability Map**
