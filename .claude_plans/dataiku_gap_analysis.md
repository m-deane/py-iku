# Dataiku DSS Component Gap Analysis

## Research Summary

Based on deep research of [Dataiku DSS 14 official documentation](https://doc.dataiku.com/dss/latest/), this document identifies missing recipes, processors, and settings from the py2dataiku library.

---

## Part 1: Recipe Types Gap Analysis

### Currently Implemented in py2dataiku (18 types)

```python
class RecipeType(Enum):
    # Visual recipes (14)
    PREPARE = "prepare"
    SYNC = "sync"
    GROUPING = "grouping"
    WINDOW = "window"
    JOIN = "join"
    FUZZY_JOIN = "fuzzy_join"
    GEO_JOIN = "geo_join"
    STACK = "stack"
    SPLIT = "split"
    SORT = "sort"
    DISTINCT = "distinct"
    TOP_N = "topn"
    PIVOT = "pivot"
    SAMPLING = "sampling"
    DOWNLOAD = "download"

    # Code recipes (3)
    PYTHON = "python"
    SQL = "sql_query"
    R = "r"

    # ML recipes (3)
    PREDICTION_SCORING = "prediction_scoring"
    CLUSTERING_SCORING = "clustering_scoring"
    EVALUATION = "evaluation"
```

### Missing Recipe Types from Dataiku DSS 14

| Recipe Type | Dataiku Purpose | Priority |
|-------------|-----------------|----------|
| **HIVE** | Hive SQL queries | Medium |
| **IMPALA** | Impala SQL queries | Medium |
| **SPARK_SCALA** | Spark Scala code | Medium |
| **PYSPARK** | PySpark code recipes | High |
| **SPARKR** | Spark R code | Low |
| **SPARKSQL** | SparkSQL queries | Medium |
| **SHELL** | Shell script recipes | Medium |
| **GENERATE_FEATURES** | Auto feature generation | High |
| **GENERATE_STATISTICS** | Dataset statistics | High |
| **PUSH_TO_EDITABLE** | Push to editable dataset | Low |
| **LIST_FOLDER_CONTENTS** | List folder files | Low |
| **DYNAMIC_REPEAT** | Dynamic recipe repeat | Medium |
| **AI_ASSISTANT_GENERATE** | AI-generated recipes | Low |
| **EXTRACT_FAILED_ROWS** | Extract failed rows | Medium |
| **UPSERT** | Consolidate/upsert data | High |
| **LIST_ACCESS** | List access control | Low |

### Recommended Additions (High Priority)

1. **PYSPARK** - Common for big data processing
2. **GENERATE_FEATURES** - Important for ML pipelines
3. **GENERATE_STATISTICS** - Data profiling
4. **UPSERT** - Common data consolidation pattern

---

## Part 2: Processor Types Gap Analysis

### Currently Implemented in py2dataiku (31 types)

```python
class ProcessorType(Enum):
    # Column manipulation (4)
    COLUMN_RENAMER, COLUMN_COPIER, COLUMN_DELETER, COLUMNS_SELECTOR

    # Missing values (3)
    FILL_EMPTY_WITH_VALUE, REMOVE_ROWS_ON_EMPTY, FILL_EMPTY_WITH_PREVIOUS_NEXT

    # String (7)
    STRING_TRANSFORMER, TOKENIZER, REGEXP_EXTRACTOR, FIND_REPLACE,
    SPLIT_COLUMN, CONCAT_COLUMNS, HTML_STRIPPER

    # Numeric (6)
    NUMERICAL_TRANSFORMER, ROUND_COLUMN, ABS_COLUMN, CLIP_COLUMN, BINNER, NORMALIZER

    # Type (3)
    TYPE_SETTER, DATE_PARSER, DATE_FORMATTER

    # Filter (5)
    FILTER_ON_VALUE, FILTER_ON_BAD_TYPE, FILTER_ON_FORMULA,
    FILTER_ON_DATE_RANGE, FILTER_ON_NUMERIC_RANGE

    # Flag (3)
    FLAG_ON_VALUE, FLAG_ON_FORMULA, FLAG_ON_BAD_TYPE

    # Row (3)
    REMOVE_DUPLICATES, SORT_ROWS, SAMPLE_ROWS

    # Computed (2)
    CREATE_COLUMN_WITH_GREL, FORMULA

    # Categorical (2)
    MERGE_LONG_TAIL_VALUES, CATEGORICAL_ENCODER

    # Geographic (2)
    GEO_POINT_CREATOR, GEO_ENCODER

    # Fallback (1)
    PYTHON_UDF
```

### Missing Processor Types from Dataiku DSS 14

#### Array Operations (6 - ALL MISSING)

| Processor | Purpose | Priority |
|-----------|---------|----------|
| **EXTRACT_FROM_ARRAY** | Extract element from array | Medium |
| **FOLD_ARRAY** | Fold array into rows | Medium |
| **SORT_ARRAY** | Sort array elements | Low |
| **CONCAT_JSON_ARRAYS** | Concatenate JSON arrays | Low |
| **UNFOLD_ARRAY** | Unfold array column | Medium |
| **ZIP_JSON_ARRAYS** | Zip multiple arrays | Low |

#### Column Operations (4 - PARTIALLY MISSING)

| Processor | Purpose | Priority | Status |
|-----------|---------|----------|--------|
| **COLUMN_PSEUDONYMIZATION** | Anonymize column data | High | MISSING |
| **MOVE_COLUMNS** | Reorder columns | Low | MISSING |
| **NEST_COLUMNS** | Nest into JSON object | Medium | MISSING |
| **UNNEST_OBJECT** | Flatten JSON | High | MISSING |

#### Numerical Operations (3 - PARTIALLY MISSING)

| Processor | Purpose | Priority | Status |
|-----------|---------|----------|--------|
| **CONVERT_NUMBER_FORMATS** | Number format conversion | Medium | MISSING |
| **GENERATE_NUMERICAL_COMBINATIONS** | Create combinations | Low | MISSING |
| **COMPUTE_AVERAGE** | Compute row-wise average | Low | MISSING |

#### Date/Time Operations (3 - PARTIALLY MISSING)

| Processor | Purpose | Priority | Status |
|-----------|---------|----------|--------|
| **EXTRACT_DATE_ELEMENTS** | Extract year/month/day | High | MISSING |
| **COMPUTE_DATE_DIFFERENCE** | Diff between dates | High | MISSING |
| **CONVERT_UNIX_TIMESTAMP** | Unix to date conversion | Medium | MISSING |
| **FLAG_HOLIDAYS** | Flag holiday dates | Low | MISSING |

#### Text Operations (6 - PARTIALLY MISSING)

| Processor | Purpose | Priority | Status |
|-----------|---------|----------|--------|
| **EXTRACT_NGRAMS** | N-gram extraction | Medium | MISSING |
| **EXTRACT_NUMBERS** | Extract numbers from text | Medium | MISSING |
| **SIMPLIFY_TEXT** | Text normalization | High | MISSING |
| **SPLIT_INTO_CHUNKS** | Split text into chunks | Low | MISSING |
| **SPLIT_AND_FOLD** | Split and create rows | Medium | MISSING |
| **SPLIT_AND_UNFOLD** | Split and unfold | Medium | MISSING |
| **EXTRACT_WITH_GROK** | Grok pattern extraction | Low | MISSING |
| **EXTRACT_WITH_JSONPATH** | JSONPath extraction | High | MISSING |

#### Data Enrichment (12 - ALL MISSING)

| Processor | Purpose | Priority |
|-----------|---------|----------|
| **ENRICH_FROM_FRENCH_DEPARTMENT** | French geo enrichment | Low |
| **ENRICH_FROM_FRENCH_POSTCODE** | French postcode data | Low |
| **ENRICH_WITH_BUILD_CONTEXT** | Add build metadata | Low |
| **ENRICH_WITH_RECORD_CONTEXT** | Add record metadata | Low |
| **RESOLVE_GEOIP** | IP to location | High |
| **CURRENCY_CONVERTER** | Currency conversion | Medium |
| **SPLIT_CURRENCIES** | Parse currency values | Low |
| **SPLIT_EMAIL_ADDRESSES** | Parse email parts | Medium |
| **SPLIT_URL** | URL parsing | High |
| **SPLIT_HTTP_QUERY_STRING** | Query string parsing | Medium |
| **CLASSIFY_USER_AGENT** | User agent parsing | High |
| **GENERATE_VISITOR_ID** | Generate visitor ID | Low |

#### Geographic Operations (4 - PARTIALLY MISSING)

| Processor | Purpose | Priority | Status |
|-----------|---------|----------|--------|
| **CHANGE_COORDINATES_SYSTEM** | Coordinate transformation | Medium | MISSING |
| **COMPUTE_GEO_DISTANCE** | Distance calculation | High | MISSING |
| **EXTRACT_FROM_GEO** | Extract geo properties | Medium | MISSING |
| **CREATE_AREA_AROUND_GEOPOINT** | Buffer creation | Medium | MISSING |
| **EXTRACT_LAT_LON** | Extract lat/lon from geo | Medium | MISSING |

#### Join Processors (2 - MISSING)

| Processor | Purpose | Priority |
|-----------|---------|----------|
| **JOIN_WITH_DATASET** | In-prepare join | High |
| **FUZZY_JOIN_WITH_DATASET** | In-prepare fuzzy join | Medium |

#### Data Transformation (17 - MOSTLY MISSING)

| Processor | Purpose | Priority |
|-----------|---------|----------|
| **IF_THEN_ELSE** | Conditional logic | High |
| **FILL_COLUMN** | Fill entire column | Medium |
| **IMPUTE_WITH_COMPUTED_VALUE** | Mean/median/mode impute | High |
| **NEGATE_BOOLEAN** | Boolean negation | Low |
| **COUNT_OCCURRENCES** | Count value occurrences | Medium |
| **TRANSLATE_VALUES** | Value translation/mapping | High |
| **NORMALIZE_MEASURE** | Unit normalization | Medium |
| **GROUP_LONG_TAIL** | Group rare values | Medium |
| **FOLD_MULTIPLE_COLUMNS** | Fold columns to rows | High |
| **FOLD_MULTIPLE_BY_PATTERN** | Fold by pattern | Medium |
| **FOLD_OBJECT_KEYS** | Fold JSON keys | Medium |
| **PIVOT** | Pivot in prepare | High |
| **SPLIT_INVALID_CELLS** | Split invalid to column | Medium |
| **SWITCH_CASE** | Switch/case logic | High |
| **TRANSPOSE_ROWS_TO_COLUMNS** | Row/column transpose | High |
| **TRIGGERED_UNFOLD** | Conditional unfold | Low |
| **UNFOLD** | Unfold column | Medium |
| **GENERATE_BIG_DATA** | Data generation | Low |

### Recommended Processor Additions (High Priority)

1. **UNNEST_OBJECT** - JSON flattening is common
2. **EXTRACT_DATE_ELEMENTS** - Date part extraction
3. **COMPUTE_DATE_DIFFERENCE** - Date arithmetic
4. **SIMPLIFY_TEXT** - Text normalization for NLP
5. **EXTRACT_WITH_JSONPATH** - JSON data extraction
6. **RESOLVE_GEOIP** - IP geolocation
7. **SPLIT_URL** - URL parsing
8. **CLASSIFY_USER_AGENT** - Web analytics
9. **JOIN_WITH_DATASET** - In-prepare joins
10. **IF_THEN_ELSE** - Conditional logic
11. **IMPUTE_WITH_COMPUTED_VALUE** - Statistical imputation
12. **TRANSLATE_VALUES** - Value mapping
13. **FOLD_MULTIPLE_COLUMNS** - Column to row transformation
14. **PIVOT** - In-prepare pivoting
15. **SWITCH_CASE** - Multiple conditions
16. **TRANSPOSE_ROWS_TO_COLUMNS** - Data reshaping
17. **COLUMN_PSEUDONYMIZATION** - Data anonymization

---

## Part 3: Settings Gap Analysis

### Join Settings

#### Currently Implemented

```python
class JoinType(Enum):
    INNER = "INNER"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    OUTER = "OUTER"
    CROSS = "CROSS"
```

#### Missing Join Types

| Join Type | Purpose | Priority |
|-----------|---------|----------|
| **LEFT_ANTI** | Rows in left not in right | High |
| **RIGHT_ANTI** | Rows in right not in left | High |
| **ADVANCED** | Custom join conditions | Medium |

#### Missing Join Condition Types

| Condition | Purpose | Priority |
|-----------|---------|----------|
| **LTE** | Less than or equal | High |
| **LT** | Less than | High |
| **GTE** | Greater than or equal | High |
| **GT** | Greater than | High |
| **NE** | Not equal | Medium |
| **WITHIN_RANGE** | Range condition | High |
| **K_NEAREST** | K nearest neighbors | Medium |
| **K_NEAREST_INFERIOR** | K nearest (below) | Low |
| **CONTAINS** | String contains | High |
| **STARTS_WITH** | String starts with | High |

### Aggregation Functions

#### Currently Implemented

- SUM, AVG, COUNT, MIN, MAX, FIRST, LAST

#### Missing Aggregation Functions

| Function | Purpose | Priority |
|----------|---------|----------|
| **STD** | Standard deviation | High |
| **VAR** | Variance | High |
| **NUNIQUE** | Count unique | High |
| **MEDIAN** | Median (SQL only) | High |
| **PERCENTILE** | Percentile calculation | Medium |
| **MODE** | Most common value | Medium |
| **COUNTD** | Distinct count | Medium |
| **CONCAT** | Concatenate values | Medium |
| **COLLECT_LIST** | Collect to list | Low |
| **COLLECT_SET** | Collect unique to set | Low |

### String Transformer Modes

#### Currently Implemented

```python
class StringTransformerMode(Enum):
    UPPERCASE = "TO_UPPER"
    LOWERCASE = "TO_LOWER"
    TITLECASE = "TITLECASE"
    TRIM = "TRIM"
    TRIM_LEFT = "TRIM_LEFT"
    TRIM_RIGHT = "TRIM_RIGHT"
    NORMALIZE_WHITESPACE = "NORMALIZE_WHITESPACE"
    REMOVE_WHITESPACE = "REMOVE_WHITESPACE"
```

#### Missing String Transformer Modes

| Mode | Purpose | Priority |
|------|---------|----------|
| **CAPITALIZE** | Capitalize first char only | Medium |
| **NORMALIZE** | Lowercase + remove accents | High |
| **TRUNCATE** | Keep first N chars | Medium |
| **URL_ENCODE** | URL encoding | Medium |
| **URL_DECODE** | URL decoding | Medium |
| **XML_ESCAPE** | Escape XML entities | Low |
| **XML_UNESCAPE** | Unescape XML entities | Low |
| **UNICODE_ESCAPE** | Unicode to codepoint | Low |
| **UNICODE_UNESCAPE** | Codepoint to Unicode | Low |

### Numerical Transformer Modes

#### Currently Implemented

```python
class NumericalTransformerMode(Enum):
    MULTIPLY = "MULTIPLY"
    DIVIDE = "DIVIDE"
    ADD = "ADD"
    SUBTRACT = "SUBTRACT"
    POWER = "POWER"
    ROUND = "ROUND"
    FLOOR = "FLOOR"
    CEIL = "CEIL"
```

#### Missing Numerical Modes

| Mode | Purpose | Priority |
|------|---------|----------|
| **LOG** | Natural logarithm | Medium |
| **LOG10** | Base-10 logarithm | Medium |
| **EXP** | Exponential | Medium |
| **SQRT** | Square root | Medium |
| **MOD** | Modulo operation | Medium |

### Window Function Types

#### Currently NOT Explicitly Defined

Need to add WindowFunctionType enum:

| Function | Purpose | Priority |
|----------|---------|----------|
| **ROW_NUMBER** | Row numbering | High |
| **RANK** | Rank with gaps | High |
| **DENSE_RANK** | Rank without gaps | High |
| **NTILE** | Bucket assignment | Medium |
| **LAG** | Previous row value | High |
| **LEAD** | Next row value | High |
| **LAG_DIFF** | Difference from previous | High |
| **LEAD_DIFF** | Difference from next | High |
| **FIRST_VALUE** | First value in window | Medium |
| **LAST_VALUE** | Last value in window | Medium |
| **NTH_VALUE** | Nth value in window | Low |
| **RUNNING_SUM** | Cumulative sum | High |
| **RUNNING_AVG** | Cumulative average | High |
| **RUNNING_MIN** | Cumulative minimum | Medium |
| **RUNNING_MAX** | Cumulative maximum | Medium |
| **RUNNING_COUNT** | Cumulative count | Medium |

### Filter Match Modes

#### Currently NOT Explicitly Defined

Need to add FilterMatchMode enum:

| Mode | Purpose | Priority |
|------|---------|----------|
| **COMPLETE_VALUE** | Exact match | High |
| **SUBSTRING** | Contains match | High |
| **REGULAR_EXPRESSION** | Regex match | High |
| **STARTS_WITH** | Prefix match | High |
| **ENDS_WITH** | Suffix match | High |

### Geo Join Operators

#### Currently NOT Defined

Need to add GeoJoinOperator enum:

| Operator | Purpose | Priority |
|----------|---------|----------|
| **WITHIN_DISTANCE** | Points within distance | High |
| **BEYOND_DISTANCE** | Points beyond distance | Medium |
| **INTERSECTS** | Geometries intersect | High |
| **CONTAINS** | Geometry contains | High |
| **WITHIN** | Geometry is within | High |
| **TOUCHES** | Geometries touch | Medium |
| **OVERLAPS** | Geometries overlap | Medium |
| **CROSSES** | Geometries cross | Low |

### Distance Units

#### Currently NOT Defined

Need to add DistanceUnit enum:

| Unit | Priority |
|------|----------|
| **METER** | High |
| **KILOMETER** | High |
| **FOOT** | Medium |
| **YARD** | Low |
| **MILE** | High |
| **NAUTICAL_MILE** | Low |

### Imputation Methods

#### Currently NOT Explicitly Defined

Need to add ImputationMethod enum:

| Method | Purpose | Priority |
|--------|---------|----------|
| **MEAN** | Fill with mean | High |
| **MEDIAN** | Fill with median | High |
| **MODE** | Fill with mode | High |
| **CONSTANT** | Fill with constant | High |
| **PREVIOUS** | Forward fill | High |
| **NEXT** | Backward fill | High |
| **INTERPOLATE** | Linear interpolation | Medium |

---

## Part 4: Summary Statistics

### Current Implementation Status

| Category | Implemented | Missing | Coverage |
|----------|-------------|---------|----------|
| Recipe Types | 18 | 16 | 53% |
| Processor Types | 31 | ~45 | 41% |
| Join Types | 5 | 2+ | 71% |
| Join Conditions | 1 (EQ) | 10 | 9% |
| Aggregations | 7 | 5+ | 58% |
| String Modes | 8 | 9 | 47% |
| Numerical Modes | 8 | 5 | 62% |
| Window Functions | 0 | 16 | 0% |
| Filter Modes | 0 | 5 | 0% |
| Geo Operators | 0 | 8 | 0% |

### Priority Recommendations

#### Critical (Must Have)
1. Window function types enum
2. Anti-join types (LEFT_ANTI, RIGHT_ANTI)
3. Additional join conditions (LTE, GTE, CONTAINS, etc.)
4. Missing aggregation functions (STD, NUNIQUE, MEDIAN)
5. IMPUTE_WITH_COMPUTED_VALUE processor

#### High Priority
1. Date manipulation processors
2. JSON/nested data processors
3. URL and user agent parsing
4. Conditional logic processors (IF_THEN_ELSE, SWITCH_CASE)
5. Data reshaping processors (TRANSPOSE, FOLD, UNFOLD)

#### Medium Priority
1. Code recipe types (PySpark, Spark Scala)
2. Array operations
3. Geo operations
4. Advanced text processing

---

## Sources

- [Visual Recipes Documentation](https://doc.dataiku.com/dss/latest/other_recipes/index.html)
- [Processors Reference](https://doc.dataiku.com/dss/latest/preparation/processors/index.html)
- [Join Recipe Documentation](https://doc.dataiku.com/dss/latest/other_recipes/join.html)
- [Window Recipe Documentation](https://doc.dataiku.com/dss/latest/other_recipes/window.html)
- [Grouping Recipe Documentation](https://doc.dataiku.com/dss/latest/other_recipes/grouping.html)
- [Geo Join Documentation](https://doc.dataiku.com/dss/latest/other_recipes/geojoin.html)
- [Code Recipes Documentation](https://doc.dataiku.com/dss/latest/code_recipes/index.html)
- [Transform String Processor](https://doc.dataiku.com/dss/latest/preparation/processors/string-transform.html)
- [Impute with Computed Value](https://doc.dataiku.com/dss/latest/preparation/processors/fill-empty-with-computed-value.html)
