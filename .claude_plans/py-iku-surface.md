# py-iku Public Python Surface Map

**Version:** 0.3.0 | **Status:** Complete | **For:** FastAPI wrapper + TypeScript client

---

## 1. TOP-LEVEL ENTRY POINTS

### Convenience Functions (py2dataiku/__init__.py:263–461)

| Function | Signature | Notes |
|----------|-----------|-------|
| `convert()` | `convert(code, optimize: bool = True) -> DataikuFlow` | Rule-based (AST) conversion. Accepts string, Path, or .py filepath. |
| `convert_with_llm()` | `convert_with_llm(code, provider="anthropic", api_key=None, model=None, optimize=True, flow_name="converted_flow", on_progress=None, temperature=0.0) -> DataikuFlow` | LLM-based conversion with progress callback. Phases: "start", "analyzing", "analyzed", "generating", "optimizing", "done". |
| `convert_file()` | `convert_file(path: str, optimize: bool = True) -> DataikuFlow` | Rule-based file conversion. |
| `convert_file_with_llm()` | `convert_file_with_llm(path, provider="anthropic", api_key=None, model=None, optimize=True, flow_name=None, on_progress=None, temperature=0.0) -> DataikuFlow` | LLM file conversion. Defaults flow_name to filename. |

### Main Converter Class (py2dataiku/__init__.py:463–633)

```python
class Py2Dataiku:
    def __init__(self, provider="anthropic", api_key=None, model=None, use_llm=True)
    def convert(code: str, flow_name="converted_flow", optimize=True) -> DataikuFlow
    def analyze(code: str) -> AnalysisResult  # LLM mode only
    def generate_diagram(flow: DataikuFlow, format="mermaid") -> str
    def visualize(flow: DataikuFlow, format="svg", **kwargs) -> str
    def save_visualization(flow, output_path, format=None) -> None
```

### CLI Commands (py2dataiku/cli.py)

| Command | Signature | Formats |
|---------|-----------|---------|
| `convert` | `py2dataiku convert <input> -o <output> -f {json,yaml,dict,summary}` | Rule-based or `--llm` mode |
| `visualize` / `viz` | `py2dataiku visualize <input> -o <output> -f {svg,html,ascii,plantuml,mermaid}` | --theme {light,dark} |
| `analyze` | `py2dataiku analyze <input> -f {text,json,yaml} [--llm]` | Show detected operations |
| `export` | `py2dataiku export <input> -o <dir> --project-key KEY [--zip]` | DSS project export |

**Entry point:** `py2dataiku.cli:main(argv=None) -> int`

---

## 2. CORE MODELS

### DataikuFlow (`py2dataiku/models/dataiku_flow.py:96–720`)

**Constructor:**
```python
DataikuFlow(
    name: str = "converted_flow",
    source_file: Optional[str] = None,
    generation_timestamp: Optional[str] = None,
    datasets: list[DataikuDataset] = [],
    recipes: list[DataikuRecipe] = [],
    zones: list[FlowZone] = [],
    recommendations: list[FlowRecommendation] = [],
    optimization_notes: list[str] = [],
    warnings: list[str] = [],
)
```

**Public Methods:**

| Method | Returns | Purpose |
|--------|---------|---------|
| `graph` (property) | `FlowGraph` | DAG representation (topological sort, cycle detection, path finding) |
| `add_dataset(ds)` | `None` | Add dataset; auto-creates if missing |
| `get_dataset(name)` | `Optional[DataikuDataset]` | Lookup by name |
| `add_recipe(recipe)` | `None` | Add recipe; auto-creates missing input/output datasets |
| `get_recipe(name)` | `Optional[DataikuRecipe]` | Lookup by name |
| `get_recipes_by_type(recipe_type)` | `list[DataikuRecipe]` | Filter by RecipeType |
| `input_datasets`, `output_datasets`, `intermediate_datasets` (properties) | `list[DataikuDataset]` | Dataset access by type |
| `get_recommendations()` | `list[FlowRecommendation]` | Optimization suggestions |
| `add_recommendation(type, priority, message, impact, action)` | `None` | Add recommendation |
| `get_column_lineage(column, dataset=None)` | `ColumnLineage` | Trace column back through recipes |
| `validate()` | `dict[str, Any]` | DAG validation: cycles, orphans, missing datasets, disconnects |
| `add_zone(zone)` | `None` | Add FlowZone |
| `get_zone(name)` | `Optional[FlowZone]` | Lookup zone |
| `to_dict(include_timestamp=True)` | `dict[str, Any]` | Round-trip serialization |
| `from_dict(data)` (classmethod) | `DataikuFlow` | Deserialize from dict |
| `to_json(indent=2)` | `str` | JSON serialization |
| `from_json(json_str)` (classmethod) | `DataikuFlow` | Deserialize from JSON |
| `to_yaml()` | `str` | YAML serialization |
| `from_yaml(yaml_str)` (classmethod) | `DataikuFlow` | Deserialize from YAML |
| `to_recipe_configs()` | `list[dict]` | DSS API-compatible recipe list |
| `get_summary()` | `str` | Text summary (counts, types, notes) |
| `save(path, format=None)` | `None` | Save to file; auto-detect format (.json, .yaml, .svg, .html, .png, .pdf, .puml, .txt, .md) |
| `export_all(directory)` | `None` | Export flow + recipes to directory |
| `visualize(format="svg", **kwargs)` | `str` or `bytes` | Render visualization; mermaid, svg, html, ascii, plantuml, png, matplotlib |
| `to_svg(output_path=None)` | `str` | SVG render + optional save |
| `to_html(output_path=None)` | `str` | HTML render + optional save |
| `to_ascii()` | `str` | ASCII render |
| `to_plantuml(output_path=None)` | `str` | PlantUML render + optional save |
| `to_png(output_path, scale=2.0)` | `None` | PNG render (requires matplotlib) |
| `to_pdf(output_path)` | `None` | PDF render |
| `_repr_svg_()` | `str` | Jupyter Classic renderer |
| `_repr_mimebundle_()` | `dict` | Jupyter Lab/VS Code renderer |

---

### DataikuRecipe (`py2dataiku/models/dataiku_recipe.py:312–650`)

**Constructor:**
```python
DataikuRecipe(
    name: str,
    recipe_type: RecipeType,
    inputs: list[str] = [],
    outputs: list[str] = [],
    steps: list[PrepareStep] = [],  # PREPARE-specific
    group_keys: list[str] = [],     # GROUPING-specific
    aggregations: list[Aggregation] = [],
    join_type: JoinType = JoinType.LEFT,  # JOIN-specific
    join_keys: list[JoinKey] = [],
    selected_columns: Optional[dict] = None,
    partition_columns: list[str] = [],  # WINDOW-specific
    order_columns: list[str] = [],
    window_aggregations: list[dict] = [],
    sampling_method: SamplingMethod = SamplingMethod.RANDOM,  # SAMPLING-specific
    sample_size: Optional[int] = None,
    split_condition: Optional[str] = None,  # SPLIT-specific
    sort_columns: list[dict] = [],  # SORT-specific
    top_n: Optional[int] = None,    # TOP_N-specific
    ranking_column: Optional[str] = None,
    code: Optional[str] = None,     # PYTHON-specific
    settings: Optional[RecipeSettings] = None,  # Composed settings (takes precedence)
    source_lines: list[int] = [],
    notes: list[str] = [],
)
```

**Public Methods:**

| Method | Returns | Purpose |
|--------|---------|---------|
| `to_dict()` | `dict[str, Any]` | Display dict (human-readable) |
| `from_dict(data)` (classmethod) | `DataikuRecipe` | Deserialize |
| `to_api_dict(project_key="")` | `dict[str, Any]` | DSS API format (type→"shaker", inputs→{main:{items}}, params) |
| `to_json(project_key="")` | `dict[str, Any]` | Alias for to_api_dict |
| `_build_settings()` | `dict[str, Any]` | Recipe-specific DSS settings payload |

**RecipeType Enum (37 members, py2dataiku/models/dataiku_recipe.py:11–71)**

Visual recipes: PREPARE, SYNC, GROUPING, WINDOW, JOIN, FUZZY_JOIN, GEO_JOIN, STACK, SPLIT, SORT, DISTINCT, TOP_N, PIVOT, SAMPLING, DOWNLOAD, GENERATE_FEATURES, GENERATE_STATISTICS, PUSH_TO_EDITABLE, LIST_FOLDER_CONTENTS, DYNAMIC_REPEAT, EXTRACT_FAILED_ROWS, UPSERT, LIST_ACCESS

Code recipes: PYTHON, R, SQL, HIVE, IMPALA, SPARKSQL, PYSPARK, SPARK_SCALA, SPARKR, SHELL

ML recipes: PREDICTION_SCORING, CLUSTERING_SCORING, EVALUATION, AI_ASSISTANT_GENERATE

---

### DataikuDataset (`py2dataiku/models/dataiku_dataset.py:59–161`)

**Constructor:**
```python
DataikuDataset(
    name: str,
    dataset_type: DatasetType = DatasetType.INTERMEDIATE,
    connection_type: DatasetConnectionType = DatasetConnectionType.FILESYSTEM,
    schema: list[ColumnSchema] = [],
    source_variable: Optional[str] = None,  # Original Python var
    source_line: Optional[int] = None,
    notes: list[str] = [],
)
```

**Public Methods:**

| Method | Returns | Purpose |
|--------|---------|---------|
| `to_dict()` | `dict[str, Any]` | Round-trip dict |
| `from_dict(data)` (classmethod) | `DataikuDataset` | Deserialize |
| `to_json(project_key="")` | `dict[str, Any]` | DSS API format |
| `add_column(name, col_type, nullable=True, default=None)` | `None` | Add to schema |
| `add_note(note)` | `None` | Add note |
| `is_input`, `is_output` (properties) | `bool` | Type check |

**Enums:**

```python
DatasetType: INPUT, INTERMEDIATE, OUTPUT
DatasetConnectionType: FILESYSTEM, SQL_POSTGRESQL, SQL_MYSQL, SQL_BIGQUERY, SQL_SNOWFLAKE,
                       SQL_REDSHIFT, S3, GCS, AZURE_BLOB, HDFS, MANAGED_FOLDER, MONGODB, ELASTICSEARCH
```

---

### PrepareStep (`py2dataiku/models/prepare_step.py:1–195`)

**Constructor:**
```python
PrepareStep(
    processor_type: ProcessorType,
    params: dict[str, Any] = {},
    meta_type: str = "SingleColumnProcessor",
    disabled: bool = False,
)
```

**Public Methods:**

| Method | Returns | Purpose |
|--------|---------|---------|
| `to_dict()` | `dict[str, Any]` | Display dict |
| `to_json()` | `dict[str, Any]` | DSS wire format |
| `from_dict(data)` (classmethod) | `PrepareStep` | Deserialize |

---

### RecipeSettings Classes (12 types, py2dataiku/models/recipe_settings.py:32–496)

**Base ABC:**
```python
class RecipeSettings(ABC):
    def to_dict() -> dict[str, Any]
    def to_display_dict() -> dict[str, Any]
    def to_dss_builder_args() -> dict[str, Any]
```

**Subclasses (1 per recipe type):**

| Class | Constructor Fields | Key Methods |
|-------|-------------------|-------------|
| `PrepareSettings` | `steps: list[PrepareStep]`, `mode: str` | to_dict, to_dss_builder_args |
| `GroupingSettings` | `keys: list[str]`, `aggregations: list[Any]`, `global_count: bool` | to_dict, to_dss_builder_args |
| `JoinSettings` | `join_type: str`, `join_keys: list[Any]`, `selected_columns: Optional[dict]` | to_dict, to_dss_builder_args |
| `WindowSettings` | `partition_columns: list[str]`, `order_columns: list[str]`, `aggregations: list[dict]` | to_dict, to_dss_builder_args |
| `SamplingSettings` | `sampling_method: str`, `sample_size: Optional[int]` | to_dict, to_dss_builder_args |
| `SplitSettings` | `split_mode: str`, `condition: str` | to_dict, to_dss_builder_args |
| `SortSettings` | `sort_columns: list[dict[str, str]]` | to_dict, to_dss_builder_args |
| `TopNSettings` | `top_n: int`, `ranking_column: Optional[str]` | to_dict, to_dss_builder_args |
| `DistinctSettings` | `compute_count: bool` | to_dict, to_dss_builder_args |
| `StackSettings` | `mode: str` | to_dict, to_dss_builder_args |
| `PythonSettings` | `code: str` | to_dict, to_dss_builder_args |
| `PivotSettings` | `row_columns: list[str]`, `column_column: str`, `value_column: str`, `aggregation: str` | to_dict, to_dss_builder_args |

---

### FlowGraph (`py2dataiku/models/flow_graph.py:33–300`)

**Constructor:** `FlowGraph()`

**Public Methods:**

| Method | Returns | Purpose |
|--------|---------|---------|
| `add_node(name, node_type, metadata=None)` | `FlowNode` | Add dataset or recipe node |
| `add_edge(source, target)` | `None` | Add directed edge (validates nodes exist) |
| `get_node(name)` | `Optional[FlowNode]` | Lookup node |
| `nodes`, `dataset_nodes`, `recipe_nodes` (properties) | `list[FlowNode]` | Accessors |
| `edges` (property) | `list[tuple[str, str]]` | All (source, target) pairs |
| `get_successors(name)` | `list[str]` | Direct outgoing neighbors |
| `get_predecessors(name)` | `list[str]` | Direct incoming neighbors |
| `topological_sort()` | `list[str]` | Kahn's algorithm; raises ValueError if cycle |
| `detect_cycles()` | `list[list[str]]` | DFS cycle detection |
| `find_disconnected_subgraphs()` | `list[set[str]]` | Connected components (undirected sense) |
| `get_path(source, target)` | `Optional[list[str]]` | BFS shortest path |
| `get_roots()`, `get_leaves()` | `list[str]` | Source/sink nodes |
| `from_flow(flow)` (classmethod) | `FlowGraph` | Build DAG from DataikuFlow |

---

## 3. ENUMS

### ProcessorType (122 members, py2dataiku/models/prepare_step.py:8–195)

Grouped by category:

- **Column manipulation:** COLUMN_RENAMER, COLUMN_COPIER, COLUMNS_SELECTOR (alias COLUMN_DELETER), COLUMN_REORDER, COLUMNS_CONCATENATOR
- **Missing values:** FILL_EMPTY_WITH_VALUE, REMOVE_ROWS_ON_EMPTY, FILL_EMPTY_WITH_PREVIOUS_NEXT, FILL_EMPTY_WITH_COMPUTED_VALUE, IMPUTE_WITH_ML
- **String:** STRING_TRANSFORMER, TOKENIZER, REGEXP_EXTRACTOR, FIND_REPLACE, SPLIT_COLUMN, HTML_STRIPPER, MULTI_COLUMN_FIND_REPLACE, NGRAMMER, TEXT_SIMPLIFIER, STEM_TEXT, LEMMATIZE_TEXT, LANGUAGE_DETECTOR, SENTIMENT_ANALYZER, TEXT_HASHER, UNICODE_NORMALIZER, URL_PARSER, IP_ADDRESS_PARSER, EMAIL_DOMAIN_EXTRACTOR, PHONE_FORMATTER, COUNTRY_NORMALIZER, USER_AGENT_PARSER
- **Numeric:** NUMERICAL_TRANSFORMER, ROUND_COLUMN, CLIP_COLUMN, BINNER, NORMALIZER, [aliases: DISCRETIZER, QUANTILE_TRANSFORMER, ROBUST_SCALER, MIN_MAX_SCALER, STANDARD_SCALER, LOG_TRANSFORMER, POWER_TRANSFORMER, BOX_COX_TRANSFORMER]
- **Type conversion:** TYPE_SETTER, DATE_PARSER, DATE_FORMATTER, [aliases: BOOLEAN_CONVERTER, NUMBER_TO_STRING, STRING_TO_NUMBER]
- **Date/time:** DATE_COMPONENTS_EXTRACTOR, DATE_DIFF_CALCULATOR, HOLIDAYS_COMPUTER, TIMEZONE_CONVERTER, DATE_RANGE_CLASSIFIER, DATETIME_FORMATTER, TIMESTAMP_EXTRACTOR
- **Filtering:** FILTER_ON_VALUE, FILTER_ON_BAD_TYPE, FILTER_ON_FORMULA, FILTER_ON_DATE_RANGE, FILTER_ON_NUMERIC_RANGE, FILTER_ON_MULTIPLE_VALUES, FILTER_ON_NULL_NUMERIC, FILTER_ON_GEO_ZONE, FILTER_ON_CUSTOM_CONDITION
- **Flagging:** FLAG_ON_VALUE, FLAG_ON_FORMULA, FLAG_ON_BAD_TYPE, FLAG_ON_DATE_RANGE, FLAG_ON_NUMERIC_RANGE
- **Row ops:** REMOVE_DUPLICATES, SORT_ROWS, SAMPLE_ROWS, SHUFFLE_ROWS
- **Computed columns:** CREATE_COLUMN_WITH_GREL, [alias ABS_COLUMN], FORMULA, MULTI_COLUMN_FORMULA, COLUMN_PSEUDO_ANONYMIZER, HASH_COMPUTER, UUID_GENERATOR
- **Categorical:** MERGE_LONG_TAIL_VALUES, CATEGORICAL_ENCODER, [aliases: ONE_HOT_ENCODER, LABEL_ENCODER, ORDINAL_ENCODER, TARGET_ENCODER, LEAVE_ONE_OUT_ENCODER, WOE_ENCODER, FEATURE_HASHER]
- **Geographic:** GEO_POINT_CREATOR, GEO_ENCODER, GEO_IP_RESOLVER, GEO_DISTANCE_CALCULATOR, GEO_POLYGON_MATCHER, ADDRESS_PARSER, REVERSE_GEOCODER
- **Conditional:** IF_THEN_ELSE, SWITCH_CASE
- **Value translation:** TRANSLATE_VALUES
- **Data extraction:** EXTRACT_WITH_JSONPATH, SPLIT_URL
- **Reshaping:** FOLD_MULTIPLE_COLUMNS, TRANSPOSE_ROWS_TO_COLUMNS, UNFOLD
- **Value ops:** COALESCE, FILL_COLUMN
- **Array/JSON:** ARRAY_SPLITTER, ARRAY_JOINER, ARRAY_SORTER, ARRAY_UNFOLD, ARRAY_FOLD, ARRAY_ELEMENT_EXTRACTOR, JSON_FLATTENER, JSON_EXTRACTOR, XML_EXTRACTOR
- **Group:** NESTED_PROCESSOR, PROCESSOR_GROUP
- **Fallback:** PYTHON_UDF

**Mode Enums:**
```python
StringTransformerMode: UPPERCASE, LOWERCASE, TRIM, ...
NumericalTransformerMode: (various scales and transforms)
FilterMatchMode: FULL_STRING, PREFIX, SUFFIX, CONTAINS, REGEX
```

### Other Enums

```python
AggregationFunction (32 members): SUM, AVG/MEAN, COUNT, COUNTD/NUNIQUE, MIN, MAX, FIRST, LAST,
                                   STDDEV/STD, VAR/VARIANCE, MEDIAN, MODE, PERCENTILE_25/50/75/90/95/99,
                                   CONCAT, COLLECT_LIST, COLLECT_SET

WindowFunctionType (21 members): ROW_NUMBER, RANK, DENSE_RANK, NTILE, PERCENT_RANK, CUME_DIST,
                                 LAG, LEAD, LAG_DIFF, LEAD_DIFF, FIRST_VALUE, LAST_VALUE, NTH_VALUE,
                                 RUNNING_SUM/AVG/MIN/MAX/COUNT, MOVING_AVG/SUM/MIN/MAX/STDDEV

JoinType: INNER, LEFT, RIGHT, OUTER, CROSS, LEFT_ANTI, RIGHT_ANTI, ADVANCED

SplitMode: FILTER, RANDOM, COLUMN_VALUE, PERCENTILE

SamplingMethod: RANDOM, RANDOM_FIXED, FIRST_ROWS, LAST_ROWS, STRATIFIED, CLASS_REBALANCE, RESERVOIR

ColumnSchema, ColumnLineage: Support column-level lineage tracing
```

---

## 4. MAPPINGS & CATALOGS

### ProcessorCatalog (`py2dataiku/mappings/processor_catalog.py:19–1034`)

**Instance-based class (not flat dict).**

```python
ProcessorCatalog()(classmethod):
    @classmethod
    def get_processor(name: str) -> Optional[ProcessorInfo]
    @classmethod
    def list_processors(category: Optional[str] = None) -> list[str]
    @classmethod
    def list_categories() -> list[str]
    @classmethod
    def get_required_params(name: str) -> list[str]
    @classmethod
    def get_example(name: str) -> dict[str, Any]
    PROCESSORS: dict[str, ProcessorInfo]  # 122 entries + aliases
```

**ProcessorInfo dataclass:**
```python
@dataclass
class ProcessorInfo:
    name: str                           # Canonical name
    category: str                       # e.g., "Column Manipulation"
    description: str                    # 1-line
    required_params: list[str] = []     # Params that must be set
    optional_params: list[str] = []     # Optional params
    examples: dict[str, Any] = {}       # Sample use cases
```

---

### PandasMapper (`py2dataiku/mappings/pandas_mappings.py`)

Maps pandas operations → Dataiku recipes/processors (non-obvious cases documented in CLAUDE.md):

- `df.melt()` → PREPARE + FoldMultipleColumns (NOT pivot)
- `df.rolling()`, `df.cumsum()`, `df.shift()` → WINDOW
- `df.nlargest()`, `df.nsmallest()` → TOP_N
- `pd.concat(axis=0)` → STACK
- `df.groupby().agg()` → GROUPING
- `df.merge()` → JOIN
- `df[condition]` → PREPARE (FILTER) or SPLIT
- `df.drop_duplicates()` → DISTINCT
- `df.pivot_table()` → PIVOT

---

## 5. PLUGIN REGISTRY

### PluginRegistry (`py2dataiku/plugins/registry.py:15–200`)

**Constructor:** `PluginRegistry()`

**Instance Methods:**

| Method | Purpose |
|--------|---------|
| `add_recipe_mapping(pandas_method, recipe_type, override=False)` | Register pandas → recipe |
| `add_processor_mapping(pandas_method, processor_type, override=False)` | Register pandas → processor |
| `add_method_handler(method_name, handler, override=False)` | Register custom handler |
| `add_recipe_handler(recipe_type, handler, override=False)` | Register recipe builder |
| `add_processor_handler(processor_type, handler, override=False)` | Register processor builder |
| `add_plugin(name, version="1.0.0", description="", **kwargs)` | Register plugin metadata |
| `find_recipe_mapping(method)` | Lookup recipe mapping |
| `find_processor_mapping(method)` | Lookup processor mapping |
| `find_method_handler(method)` | Lookup method handler |
| `copy()` | Create independent copy |

**Global Convenience Functions (py2dataiku/plugins/__init__.py):**
```python
@default_registry
def register_recipe_handler(recipe_type, handler_fn)
@default_registry
def register_processor_handler(processor_type, handler_fn)
@default_registry
def register_pandas_mapping(pandas_method, recipe_type)
PluginRegistry._get_default() -> PluginRegistry  # Global instance
```

---

## 6. ANALYZERS & GENERATORS

### CodeAnalyzer (Rule-based, py2dataiku/parser/ast_analyzer.py:12–150+)

```python
class CodeAnalyzer:
    def analyze(code: str) -> list[Transformation]
```

Uses AST pattern matching. Maps 60+ pandas methods to Transformation objects.

### LLMCodeAnalyzer (py2dataiku/llm/analyzer.py:1–300+)

```python
class LLMCodeAnalyzer:
    def __init__(provider: LLMProvider)
    def analyze(code: str) -> AnalysisResult
```

Sends code + system prompt (with auto-generated ProcessorCatalog section) to LLM. Parses JSON response into AnalysisResult.

**System Prompt (py2dataiku/llm/analyzer.py:47–200):**
- RecipeType mappings
- ProcessorType catalog (grouped, deduplicated)
- Pandas mapping rules (melt, rolling, concat, etc.)
- Aggregation function naming (canonical DSS names: SUM, AVG, COUNTD, etc.)
- Examples: simple groupby, melt, multi-recipe ETL
- Output discipline: JSON-only, structured OperationType enum

---

### BaseFlowGenerator ABC (py2dataiku/generators/base_generator.py:12–111)

**Shared methods:**

| Method | Purpose |
|--------|---------|
| `_sanitize_name(name)` | Convert Python var names → alphanumeric + underscore; no leading digit |
| `_optimize_flow()` | Call FlowOptimizer + RecipeMerger + step reordering |
| `_optimize_prepare_steps()` | Remove redundant steps, reorder for efficiency |

### FlowGenerator (Rule-based, py2dataiku/generators/flow_generator.py:21–200+)

```python
class FlowGenerator(BaseFlowGenerator):
    def generate(transformations: list[Transformation], flow_name="converted_flow", optimize=True) -> DataikuFlow
```

Converts Transformation objects → recipes.

### LLMFlowGenerator (LLM-based, py2dataiku/generators/llm_flow_generator.py:28–300+)

```python
class LLMFlowGenerator(BaseFlowGenerator):
    def generate(analysis: AnalysisResult, flow_name="converted_flow", optimize=True) -> DataikuFlow
    OPERATION_TO_RECIPE: dict[OperationType, str]  # Fallback mappings
```

Converts AnalysisResult (DataStep list) → recipes. Uses fallback OperationType→recipe map when LLM doesn't provide suggested_recipe.

---

## 7. VISUALIZERS

### Base Class (py2dataiku/visualizers/base.py:11–47)

```python
class FlowVisualizer(ABC):
    def __init__(theme: Optional[DataikuTheme] = None)
    def render(flow) -> str  # Abstract
    def save(flow, output_path)
```

### Concrete Visualizers

| Class | File | Format | Supports Theme |
|-------|------|--------|-----------------|
| `SVGVisualizer` | svg_visualizer.py | SVG (pixel-accurate) | Yes |
| `HTMLVisualizer` | html_visualizer.py | HTML (interactive canvas) | Yes |
| `ASCIIVisualizer` | ascii_visualizer.py | Terminal text art | No |
| `PlantUMLVisualizer` | plantuml_visualizer.py | PlantUML (documentation) | No |
| `MermaidVisualizer` | mermaid_visualizer.py | Mermaid (GitHub/Notion) | No |
| `InteractiveVisualizer` | interactive_visualizer.py | Enhanced HTML (pan/zoom/search) | Yes |
| `MatplotlibVisualizer` | matplotlib_visualizer.py | PNG/PDF (matplotlib) | Yes |

### Entry Point (py2dataiku/visualizers/__init__.py)

```python
visualize_flow(flow, format="svg", theme=None, **kwargs) -> str | bytes
```

Dispatches to appropriate visualizer.

### Themes (py2dataiku/visualizers/themes.py:8–140)

**DataikuTheme dataclass fields:**

**Colors:**
- Input: `input_bg`, `input_border`, `input_text`
- Output: `output_bg`, `output_border`, `output_text`
- Intermediate: `intermediate_bg`, `intermediate_border`, `intermediate_text`
- Recipe colors by type (dict): prepare, join, stack, grouping, window, split, sort, distinct, filter, python, sync, sample, pivot, top_n, default (each: bg, border, text hex triplet)
- Connection: `connection_color`, `connection_hover`
- Zone: `zone_colors` (list[8]), `zone_border_colors` (list[8])

**Typography:**
- `font_family` (default: "Arial, Helvetica, sans-serif")
- `dataset_font_size`, `recipe_font_size`, `icon_font_size`

**Dimensions:**
- Dataset: `dataset_width`, `dataset_height`, `dataset_radius`
- Recipe: `recipe_size`, `recipe_radius`
- Layout: `layer_spacing`, `node_spacing`, `padding`
- Zone: `zone_label_size`, `zone_padding`

**Background & Grid:**
- `background_color`, `grid_color`, `show_grid`

**Presets:**
```python
DATAIKU_LIGHT  # Bright theme (white bg, blue/green accents)
DATAIKU_DARK   # Dark theme (dark bg, lighter accents)
```

### Icons (py2dataiku/visualizers/icons.py:7–99)

**RecipeIcons class (static methods):**

| Icon Type | Recipes Covered |
|-----------|-----------------|
| Unicode | prepare, join, stack, grouping, window, split, sort, distinct, filter, python, sync, sample, pivot, top_n, default |
| ASCII | [same as Unicode] |
| Labels | [same, human-readable] |
| SVG paths | prepare, join, grouping, split, default |

---

## 8. EXCEPTIONS

**Hierarchy (py2dataiku/exceptions.py:1–40):**

```
Py2DataikuError (base)
├── ConversionError
│   └── InvalidPythonCodeError
├── ProviderError
│   └── LLMResponseParseError
├── ValidationError
├── ExportError
└── ConfigurationError (multi-inherits ValueError for backward compat)
```

**Where raised:**

| Exception | Where |
|-----------|-------|
| `InvalidPythonCodeError` | CodeAnalyzer.analyze() on SyntaxError |
| `ConfigurationError` | AnthropicProvider.__init__, OpenAIProvider.__init, get_provider if no key/unknown provider |
| `LLMResponseParseError` | LLMCodeAnalyzer if JSON parse fails |
| `ValidationError` | DataikuFlow.validate() internal checks |
| `ExportError` | DSSExporter if project creation fails |

---

## 9. CONFIGURATION

### Py2DataikuConfig (py2dataiku/config.py:26–82)

**Dataclass fields:**

```python
# LLM settings
default_provider: str = "anthropic"
default_model: Optional[str] = None
api_key: Optional[str] = None

# Project settings
project_key: str = "MY_PROJECT"
flow_name: str = "converted_flow"

# Optimization
optimize: bool = True
optimization_level: int = 1  # 0=none, 1=basic, 2=aggressive

# Naming conventions
dataset_prefix: str = ""
dataset_suffix: str = ""
recipe_prefix: str = ""
recipe_suffix: str = ""

# Output
default_format: str = "svg"
default_connection: str = "Filesystem"

# Extra settings
extra: dict[str, Any] = {}
```

**Methods:**
```python
def to_dict() -> dict[str, Any]
@classmethod
def from_dict(data: dict) -> Py2DataikuConfig
```

**File formats (py2dataiku/config.py:18–23):**
- TOML: `py2dataiku.toml`, `.py2dataikurc`
- YAML: `.py2dataiku.yaml`, `.py2dataiku.yml`

**Environment overrides (py2dataiku/config.py:190–196):**
- `PY2DATAIKU_PROVIDER` → default_provider
- `PY2DATAIKU_PROJECT_KEY` → project_key

**Config discovery (py2dataiku/config.py:125–149):**
```python
find_config_file(start_dir=None) -> Optional[Path]  # Search: start_dir, cwd, home
load_config(config_path=None, auto_discover=True) -> Py2DataikuConfig
```

---

## 10. LLM INTEGRATION

### Providers (py2dataiku/llm/providers.py:1–300+)

**Base ABC:**
```python
class LLMProvider(ABC):
    def complete(prompt, system_prompt=None) -> LLMResponse
    def complete_json(prompt, system_prompt=None) -> dict[str, Any]
    @property
    def model_name() -> str
```

**AnthropicProvider (py2dataiku/llm/providers.py:60–177)**

```python
class AnthropicProvider(LLMProvider):
    def __init__(api_key=None, model="claude-sonnet-4-20250514", max_tokens=4096,
                 timeout=None, max_retries=2, temperature=0.0, disable_cache=False)
    def complete(prompt, system_prompt=None) -> LLMResponse
    def complete_json(prompt, system_prompt=None) -> dict[str, Any]
```

**Prompt Caching:** System prompt sent with `cache_control: ephemeral` (5-min cache). Env var support via ANTHROPIC_API_KEY.

**OpenAIProvider (py2dataiku/llm/providers.py:179–250)**

```python
class OpenAIProvider(LLMProvider):
    def __init__(api_key=None, model="gpt-4o", max_tokens=4096,
                 timeout=None, max_retries=2, temperature=0.0, seed=42)
```

Env var: OPENAI_API_KEY. No native cache support (seed for determinism).

**Factory (py2dataiku/llm/providers.py:300+):**
```python
def get_provider(provider_name, api_key=None, model=None, temperature=0.0) -> LLMProvider
```

**LLMResponse dataclass:**
```python
@dataclass
class LLMResponse:
    content: str
    model: str
    usage: Optional[dict[str, Optional[int]]]  # input_tokens, output_tokens, cache_*_input_tokens
    raw_response: Optional[Any]
```

### Schemas (py2dataiku/llm/schemas.py:1–200+)

**OperationType enum (26 members):**
```
READ_DATA, WRITE_DATA, FILTER, SELECT_COLUMNS, DROP_COLUMNS, RENAME_COLUMNS,
ADD_COLUMN, TRANSFORM_COLUMN, FILL_MISSING, DROP_MISSING, DROP_DUPLICATES,
GROUP_AGGREGATE, WINDOW_FUNCTION, JOIN, UNION, PIVOT, UNPIVOT, SORT, TOP_N,
SAMPLE, CAST_TYPE, PARSE_DATE, SPLIT_COLUMN, ENCODE_CATEGORICAL, NORMALIZE_SCALE,
GEO_OPERATION, STATISTICS, CUSTOM_FUNCTION, UNKNOWN
```

**DataStep dataclass (core LLM output):**
```python
@dataclass
class DataStep:
    step_number: int
    operation: OperationType
    description: str
    input_datasets: list[str] = []
    output_dataset: Optional[str] = None
    columns: list[str] = []
    filter_conditions: list[FilterCondition] = []
    aggregations: list[Aggregation] = []
    group_by_columns: list[str] = []
    join_conditions: list[JoinCondition] = []
    join_type: Optional[str] = None
    column_transforms: list[ColumnTransform] = []
    rename_mapping: dict[str, str] = {}
    sort_columns: list[dict[str, str]] = []
    fill_value: Optional[Any] = None
    source_lines: list[int] = []
    source_code: Optional[str] = None
    suggested_recipe: Optional[str] = None  # prepare, join, grouping, etc.
    suggested_processors: list[str] = []  # Canonical ProcessorType names
    requires_python_recipe: bool = False
    reasoning: Optional[str] = None  # LLM's explanation
    
    def to_dict() -> dict[str, Any]
```

**AnalysisResult dataclass:**
```python
@dataclass
class AnalysisResult:
    code_summary: str
    total_operations: int
    complexity_score: int
    datasets: list[DatasetInfo] = []  # {name, source, is_input, is_output}
    steps: list[DataStep] = []
    recommendations: list[str] = []
    warnings: list[str] = []
    summary: Optional[str] = None
    
    def to_dict() -> dict[str, Any]
```

### Prompt String (py2dataiku/llm/analyzer.py:47–200)

**System prompt sections (all lines significant for determinism):**

1. Task description (analyze code, identify operations, suggest recipes)
2. RecipeType mappings (37 types listed)
3. Auto-generated ProcessorCatalog section (_build_processor_catalog_section, 122 processors grouped by category, deterministically sorted)
4. Mapping Rules (pandas patterns → DSS recipes): melt→prepare/FoldMultipleColumns, rolling→window, concat→stack, pivot_table→pivot, merge→join, etc. (all file:line documented in CLAUDE.md)
5. Aggregation Function Naming (canonical names: SUM, AVG, COUNTD, STDDEV, VAR, MEDIAN)
6. Output Discipline (JSON-only, OperationType enum, suggested_processors must be canonical names, requires_python_recipe for unmapped operations)
7. Reasoning approach (identify operation, pick OperationType, apply Mapping Rules, pick processors)
8. Examples (simple groupby, melt, multi-recipe ETL — exact JSON shape)

---

## 11. QUICK REFERENCE: CONVERSION PIPELINE

### Rule-based Flow
```
Python code → CodeAnalyzer (AST) → Transformation[] → FlowGenerator → DataikuFlow
```

### LLM-based Flow
```
Python code → LLMCodeAnalyzer (→ LLM Provider) → AnalysisResult → LLMFlowGenerator → DataikuFlow
```

### DataikuFlow Round-trip
```
DataikuFlow ↔ to_dict()/from_dict() ↔ to_json()/from_json() ↔ to_yaml()/from_yaml()
            ↔ save(format) ↔ to_svg() ↔ to_html() ↔ to_png() ↔ to_pdf()
            ↔ visualize(format) ↔ validate() ↔ export_all()
```

### Jupyter Rendering
```
DataikuFlow._repr_svg_()        → Classic Jupyter
DataikuFlow._repr_mimebundle_() → JupyterLab / VS Code
```

---

## 12. CLI COMMAND REFERENCE

```bash
# Convert (rule-based, default)
py2dataiku convert script.py -o flow.json -f json
py2dataiku convert script.py --llm --provider anthropic -o flow.yaml -f yaml

# Visualize
py2dataiku visualize script.py -o flow.svg -f svg --theme dark
py2dataiku viz script.py -f html -o flow.html

# Analyze (show detected operations)
py2dataiku analyze script.py -f json

# Export (DSS project format)
py2dataiku export script.py -o dss_project/ --project-key MY_PROJ --zip

# Auto-shorthand (no subcommand needed)
py2dataiku script.py -o flow.json           # routes to convert
py2dataiku script.py --llm -f yaml          # LLM convert
```

---

**ENDPOINT SUMMARY FOR FASTAPI WRAPPER:**

1. **Conversion endpoints:** `POST /convert`, `POST /convert/llm`
2. **Analysis endpoint:** `POST /analyze` (LLM only)
3. **Visualization endpoints:** `POST /visualize`, `GET /visualize/{format}`
4. **Export endpoint:** `POST /export/dss`
5. **Config endpoint:** `GET/POST /config`
6. **Metadata endpoints:** `GET /processors`, `GET /recipes`, `GET /themes`

**CLIENT (TypeScript) CONCERNS:**

- Stream LLM progress via WebSocket (`on_progress` callback)
- Support all 7+ visualization formats with conditional rendering
- Serialize/deserialize DataikuFlow JSON round-trip
- Handle file upload + conversion (multipart form)
- Cache ProcessorCatalog + RecipeType enums client-side
- Mermaid/SVG viewer integration

---

**Report generated:** 2026-04-26 | **Scope:** 67 Python files, 200+ public APIs, 12 RecipeSettings, 122 ProcessorTypes, 37 RecipeTypes
