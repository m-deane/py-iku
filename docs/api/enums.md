# Enums

All enumeration types used throughout the library.

---

## RecipeType

Dataiku recipe types. Visual recipes appear as colored circles in the flow.

```python
from py2dataiku import RecipeType
```

### Visual Recipes - Data Preparation

| Value | API String | Description |
|-------|-----------|-------------|
| `PREPARE` | `"prepare"` | Data preparation with processors |
| `SYNC` | `"sync"` | Dataset synchronization |
| `GROUPING` | `"grouping"` | Group-by with aggregations |
| `WINDOW` | `"window"` | Window functions |
| `JOIN` | `"join"` | Standard join |
| `FUZZY_JOIN` | `"fuzzy_join"` | Fuzzy matching join |
| `GEO_JOIN` | `"geo_join"` | Geographic join |
| `STACK` | `"stack"` | Vertical concatenation |
| `SPLIT` | `"split"` | Split into multiple outputs |
| `SORT` | `"sort"` | Sort rows |
| `DISTINCT` | `"distinct"` | Remove duplicates |
| `TOP_N` | `"topn"` | Top N rows |
| `PIVOT` | `"pivot"` | Pivot table |
| `SAMPLING` | `"sampling"` | Sample rows |
| `DOWNLOAD` | `"download"` | Download data |

### Visual Recipes - Additional

| Value | API String | Description |
|-------|-----------|-------------|
| `GENERATE_FEATURES` | `"generate_features"` | Auto feature generation |
| `GENERATE_STATISTICS` | `"generate_statistics"` | Statistical analysis |
| `PUSH_TO_EDITABLE` | `"push_to_editable"` | Push to editable dataset |
| `LIST_FOLDER_CONTENTS` | `"list_folder_contents"` | List managed folder |
| `DYNAMIC_REPEAT` | `"dynamic_repeat"` | Dynamic loop |
| `EXTRACT_FAILED_ROWS` | `"extract_failed_rows"` | Extract failed rows |
| `UPSERT` | `"upsert"` | Upsert operation |
| `LIST_ACCESS` | `"list_access"` | List dataset access |

### Code Recipes

| Value | API String | Description |
|-------|-----------|-------------|
| `PYTHON` | `"python"` | Python code recipe |
| `R` | `"r"` | R code recipe |
| `SQL` | `"sql_query"` | SQL query |
| `HIVE` | `"hive"` | Hive query |
| `IMPALA` | `"impala"` | Impala query |
| `SPARKSQL` | `"sparksql"` | Spark SQL |
| `PYSPARK` | `"pyspark"` | PySpark code |
| `SPARK_SCALA` | `"spark_scala"` | Spark Scala |
| `SPARKR` | `"sparkr"` | SparkR code |
| `SHELL` | `"shell"` | Shell script |

### ML Recipes

| Value | API String | Description |
|-------|-----------|-------------|
| `PREDICTION_SCORING` | `"prediction_scoring"` | Score with prediction model |
| `CLUSTERING_SCORING` | `"clustering_scoring"` | Score with clustering model |
| `EVALUATION` | `"evaluation"` | Model evaluation |

### AI-Assisted

| Value | API String | Description |
|-------|-----------|-------------|
| `AI_ASSISTANT_GENERATE` | `"ai_assistant_generate"` | AI assistant recipe |

---

## ProcessorType

Dataiku Prepare recipe processor types. 122 types total.

```python
from py2dataiku import ProcessorType
```

### Column Manipulation

| Value | Description |
|-------|-------------|
| `COLUMN_RENAMER` | Rename columns |
| `COLUMN_COPIER` | Copy column |
| `COLUMN_DELETER` | Delete columns |
| `COLUMNS_SELECTOR` | Select columns |
| `COLUMN_REORDER` | Reorder columns |
| `COLUMNS_CONCATENATOR` | Concatenate column values |

### Missing Value Handling

| Value | Description |
|-------|-------------|
| `FILL_EMPTY_WITH_VALUE` | Fill with constant value |
| `REMOVE_ROWS_ON_EMPTY` | Remove rows with empty values |
| `FILL_EMPTY_WITH_PREVIOUS_NEXT` | Fill with adjacent values |
| `FILL_EMPTY_WITH_COMPUTED_VALUE` | Fill with computed value |
| `IMPUTE_WITH_ML` | ML-based imputation |

### String Transformations

| Value | Description |
|-------|-------------|
| `STRING_TRANSFORMER` | General string transform (see `StringTransformerMode`) |
| `TOKENIZER` | Split text into tokens |
| `REGEXP_EXTRACTOR` | Extract with regex |
| `FIND_REPLACE` | Find and replace |
| `SPLIT_COLUMN` | Split column by delimiter |
| `CONCAT_COLUMNS` | Concatenate columns |
| `HTML_STRIPPER` | Strip HTML tags |
| `MULTI_COLUMN_FIND_REPLACE` | Multi-column find/replace |
| `NGRAMMER` | Generate n-grams |
| `TEXT_SIMPLIFIER` | Simplify text |
| `STEM_TEXT` | Stem words |
| `LEMMATIZE_TEXT` | Lemmatize words |
| `LANGUAGE_DETECTOR` | Detect language |
| `SENTIMENT_ANALYZER` | Analyze sentiment |
| `TEXT_HASHER` | Hash text |
| `UNICODE_NORMALIZER` | Normalize Unicode |
| `URL_PARSER` | Parse URL components |
| `IP_ADDRESS_PARSER` | Parse IP addresses |
| `EMAIL_DOMAIN_EXTRACTOR` | Extract email domain |
| `PHONE_FORMATTER` | Format phone numbers |
| `COUNTRY_NORMALIZER` | Normalize country names |
| `USER_AGENT_PARSER` | Parse user agent strings |

### Numeric Transformations

| Value | Description |
|-------|-------------|
| `NUMERICAL_TRANSFORMER` | General numeric transform (see `NumericalTransformerMode`) |
| `ROUND_COLUMN` | Round values |
| `ABS_COLUMN` | Absolute value |
| `CLIP_COLUMN` | Clip to range |
| `BINNER` | Bin into buckets |
| `NORMALIZER` | Normalize values |
| `DISCRETIZER` | Discretize continuous values |
| `QUANTILE_TRANSFORMER` | Quantile transform |
| `ROBUST_SCALER` | Robust scaling |
| `MIN_MAX_SCALER` | Min-max scaling |
| `STANDARD_SCALER` | Standard scaling (z-score) |
| `LOG_TRANSFORMER` | Log transform |
| `POWER_TRANSFORMER` | Power transform |
| `BOX_COX_TRANSFORMER` | Box-Cox transform |

### Type Conversion

| Value | Description |
|-------|-------------|
| `TYPE_SETTER` | Set column type |
| `DATE_PARSER` | Parse date strings |
| `DATE_FORMATTER` | Format dates |
| `BOOLEAN_CONVERTER` | Convert to boolean |
| `NUMBER_TO_STRING` | Number to string |
| `STRING_TO_NUMBER` | String to number |

### Date/Time Operations

| Value | Description |
|-------|-------------|
| `DATE_COMPONENTS_EXTRACTOR` | Extract year, month, day, etc. |
| `DATE_DIFF_CALCULATOR` | Calculate date differences |
| `HOLIDAYS_COMPUTER` | Compute holiday flags |
| `TIMEZONE_CONVERTER` | Convert timezones |
| `DATE_RANGE_CLASSIFIER` | Classify into date ranges |
| `DATETIME_FORMATTER` | Format datetime values |
| `TIMESTAMP_EXTRACTOR` | Extract timestamps |

### Filtering

| Value | Description |
|-------|-------------|
| `FILTER_ON_VALUE` | Filter by value match |
| `FILTER_ON_BAD_TYPE` | Filter invalid types |
| `FILTER_ON_FORMULA` | Filter by formula |
| `FILTER_ON_DATE_RANGE` | Filter by date range |
| `FILTER_ON_NUMERIC_RANGE` | Filter by numeric range |
| `FILTER_ON_MULTIPLE_VALUES` | Filter by multiple values |
| `FILTER_ON_NULL_NUMERIC` | Filter null numerics |
| `FILTER_ON_GEO_ZONE` | Filter by geographic zone |
| `FILTER_ON_CUSTOM_CONDITION` | Custom filter condition |

### Flagging

| Value | Description |
|-------|-------------|
| `FLAG_ON_VALUE` | Flag by value match |
| `FLAG_ON_FORMULA` | Flag by formula |
| `FLAG_ON_BAD_TYPE` | Flag invalid types |
| `FLAG_ON_DATE_RANGE` | Flag by date range |
| `FLAG_ON_NUMERIC_RANGE` | Flag by numeric range |

### Row Operations

| Value | Description |
|-------|-------------|
| `REMOVE_DUPLICATES` | Remove duplicate rows |
| `SORT_ROWS` | Sort rows |
| `SAMPLE_ROWS` | Sample rows |
| `SHUFFLE_ROWS` | Shuffle rows |

### Computed Columns

| Value | Description |
|-------|-------------|
| `CREATE_COLUMN_WITH_GREL` | Create column with GREL expression |
| `FORMULA` | Formula-based column |
| `MULTI_COLUMN_FORMULA` | Multi-column formula |
| `COLUMN_PSEUDO_ANONYMIZER` | Pseudonymize values |
| `HASH_COMPUTER` | Compute hash |
| `UUID_GENERATOR` | Generate UUIDs |

### Categorical Encoding

| Value | Description |
|-------|-------------|
| `MERGE_LONG_TAIL_VALUES` | Merge rare categories |
| `CATEGORICAL_ENCODER` | General encoding |
| `ONE_HOT_ENCODER` | One-hot encoding |
| `LABEL_ENCODER` | Label encoding |
| `ORDINAL_ENCODER` | Ordinal encoding |
| `TARGET_ENCODER` | Target encoding |
| `LEAVE_ONE_OUT_ENCODER` | Leave-one-out encoding |
| `WOE_ENCODER` | Weight of evidence encoding |
| `FEATURE_HASHER` | Feature hashing |

### Geographic

| Value | Description |
|-------|-------------|
| `GEO_POINT_CREATOR` | Create geo points |
| `GEO_ENCODER` | Geocode addresses |
| `GEO_IP_RESOLVER` | Resolve IP to location |
| `GEO_DISTANCE_CALCULATOR` | Calculate distances |
| `GEO_POLYGON_MATCHER` | Match points to polygons |
| `ADDRESS_PARSER` | Parse addresses |
| `REVERSE_GEOCODER` | Reverse geocode |

### Conditional Logic

| Value | Description |
|-------|-------------|
| `IF_THEN_ELSE` | Conditional branching |
| `SWITCH_CASE` | Multi-case switch |

### Data Reshaping

| Value | Description |
|-------|-------------|
| `FOLD_MULTIPLE_COLUMNS` | Fold columns to rows |
| `TRANSPOSE_ROWS_TO_COLUMNS` | Transpose rows/columns |
| `UNFOLD` | Unfold column values |
| `TRANSLATE_VALUES` | Translate/map values |
| `COALESCE` | Coalesce multiple columns |
| `FILL_COLUMN` | Fill entire column |

### Array/JSON Operations

| Value | Description |
|-------|-------------|
| `ARRAY_SPLITTER` | Split arrays |
| `ARRAY_JOINER` | Join array elements |
| `ARRAY_SORTER` | Sort arrays |
| `ARRAY_UNFOLD` | Unfold array to rows |
| `ARRAY_FOLD` | Fold rows to array |
| `ARRAY_ELEMENT_EXTRACTOR` | Extract array element |
| `JSON_FLATTENER` | Flatten JSON |
| `JSON_EXTRACTOR` | Extract from JSON |
| `XML_EXTRACTOR` | Extract from XML |
| `EXTRACT_WITH_JSONPATH` | JSONPath extraction |
| `SPLIT_URL` | Split URL components |

### Other

| Value | Description |
|-------|-------------|
| `NESTED_PROCESSOR` | Nested processor |
| `PROCESSOR_GROUP` | Group of processors |
| `PYTHON_UDF` | Python user-defined function |

---

## DatasetType

```python
from py2dataiku import DatasetType
```

| Value | Description |
|-------|-------------|
| `INPUT` | Source dataset |
| `INTERMEDIATE` | Intermediate dataset |
| `OUTPUT` | Final output dataset |

---

## DatasetConnectionType

```python
from py2dataiku import DatasetConnectionType
```

| Value | Description |
|-------|-------------|
| `FILESYSTEM` | Local/network filesystem |
| `SQL_POSTGRESQL` | PostgreSQL |
| `SQL_MYSQL` | MySQL |
| `SQL_BIGQUERY` | Google BigQuery |
| `SQL_SNOWFLAKE` | Snowflake |
| `SQL_REDSHIFT` | Amazon Redshift |
| `S3` | Amazon S3 |
| `GCS` | Google Cloud Storage |
| `AZURE_BLOB` | Azure Blob Storage |
| `HDFS` | Hadoop HDFS |
| `MANAGED_FOLDER` | DSS managed folder |
| `MONGODB` | MongoDB |
| `ELASTICSEARCH` | Elasticsearch |

---

## JoinType

```python
from py2dataiku import JoinType
```

| Value | Description |
|-------|-------------|
| `INNER` | Inner join |
| `LEFT` | Left outer join |
| `RIGHT` | Right outer join |
| `OUTER` | Full outer join |
| `CROSS` | Cross join |
| `LEFT_ANTI` | Left anti join |
| `RIGHT_ANTI` | Right anti join |
| `ADVANCED` | Advanced join conditions |

---

## AggregationFunction

```python
from py2dataiku import AggregationFunction
```

**Basic:** `SUM`, `AVG`, `MEAN`, `COUNT`, `COUNTD`, `MIN`, `MAX`, `FIRST`, `LAST`

**Statistical:** `STD`, `STDDEV`, `VAR`, `VARIANCE`, `MEDIAN`, `MODE`, `NUNIQUE`

**Percentiles:** `PERCENTILE_25`, `PERCENTILE_50`, `PERCENTILE_75`, `PERCENTILE_90`, `PERCENTILE_95`, `PERCENTILE_99`

**Collections:** `CONCAT`, `COLLECT_LIST`, `COLLECT_SET`

---

## WindowFunctionType

```python
from py2dataiku import WindowFunctionType
```

**Ranking:** `ROW_NUMBER`, `RANK`, `DENSE_RANK`, `NTILE`, `PERCENT_RANK`, `CUME_DIST`

**Offset:** `LAG`, `LEAD`, `LAG_DIFF`, `LEAD_DIFF`, `FIRST_VALUE`, `LAST_VALUE`, `NTH_VALUE`

**Running:** `RUNNING_SUM`, `RUNNING_AVG`, `RUNNING_MIN`, `RUNNING_MAX`, `RUNNING_COUNT`

**Moving:** `MOVING_AVG`, `MOVING_SUM`, `MOVING_MIN`, `MOVING_MAX`, `MOVING_STDDEV`

---

## SplitMode

```python
from py2dataiku import SplitMode
```

| Value | Description |
|-------|-------------|
| `FILTER` | Filter-based split |
| `RANDOM` | Random split |
| `COLUMN_VALUE` | Split by column value |
| `PERCENTILE` | Percentile-based split |

---

## SamplingMethod

```python
from py2dataiku import SamplingMethod
```

| Value | Description |
|-------|-------------|
| `RANDOM` | Random sampling |
| `RANDOM_FIXED` | Random with fixed seed |
| `FIRST_ROWS` | First N rows |
| `LAST_ROWS` | Last N rows |
| `STRATIFIED` | Stratified sampling |
| `CLASS_REBALANCE` | Class rebalancing |
| `RESERVOIR` | Reservoir sampling |

---

## StringTransformerMode

```python
from py2dataiku import StringTransformerMode
```

**Case:** `UPPERCASE`, `LOWERCASE`, `TITLECASE`, `CAPITALIZE`, `SWAPCASE`

**Whitespace:** `TRIM`, `TRIM_LEFT`, `TRIM_RIGHT`, `NORMALIZE_WHITESPACE`, `REMOVE_WHITESPACE`, `COLLAPSE_WHITESPACE`

**Character removal:** `REMOVE_ACCENTS`, `ASCII_TRANSLITERATE`, `REMOVE_NON_ALPHANUMERIC`, `REMOVE_NON_PRINTABLE`, `REMOVE_PUNCTUATION`, `REMOVE_DIGITS`, `KEEP_ONLY_DIGITS`, `KEEP_ONLY_ALPHA`

**Padding:** `PAD_LEFT`, `PAD_RIGHT`, `PAD_CENTER`

**Other:** `REVERSE`, `QUOTE`, `UNQUOTE`

---

## NumericalTransformerMode

```python
from py2dataiku import NumericalTransformerMode
```

**Arithmetic:** `MULTIPLY`, `DIVIDE`, `ADD`, `SUBTRACT`, `POWER`, `SQRT`, `LOG`, `LOG10`, `LOG2`, `EXP`, `ABS`, `NEGATE`, `INVERSE`, `MODULO`

**Rounding:** `ROUND`, `FLOOR`, `CEIL`, `TRUNCATE`, `ROUND_TO_SIGNIFICANT`

**Trigonometric:** `SIN`, `COS`, `TAN`, `ASIN`, `ACOS`, `ATAN`

**Conversion:** `DEGREES_TO_RADIANS`, `RADIANS_TO_DEGREES`

---

## FilterMatchMode

```python
from py2dataiku import FilterMatchMode
```

`EQUALS`, `NOT_EQUALS`, `CONTAINS`, `NOT_CONTAINS`, `STARTS_WITH`, `ENDS_WITH`, `REGEX`, `NOT_REGEX`, `IS_EMPTY`, `IS_NOT_EMPTY`, `IS_NULL`, `IS_NOT_NULL`, `IN_LIST`, `NOT_IN_LIST`
