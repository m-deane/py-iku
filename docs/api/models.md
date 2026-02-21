# Core Models

Data models representing Dataiku DSS flows, recipes, datasets, and processor steps.

---

## DataikuFlow

The main output class representing a complete Dataiku pipeline.

```python
from py2dataiku import DataikuFlow
```

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | `"converted_flow"` | Flow name |
| `source_file` | `Optional[str]` | `None` | Source Python file path |
| `generation_timestamp` | `Optional[str]` | `None` | When the flow was generated |
| `datasets` | `List[DataikuDataset]` | `[]` | All datasets in the flow |
| `recipes` | `List[DataikuRecipe]` | `[]` | All recipes in the flow |
| `zones` | `List[FlowZone]` | `[]` | Logical grouping zones |
| `recommendations` | `List[FlowRecommendation]` | `[]` | Optimization recommendations |
| `optimization_notes` | `List[str]` | `[]` | Notes from optimizer |
| `warnings` | `List[str]` | `[]` | Conversion warnings |

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `graph` | [`FlowGraph`](graph.md#flowgraph) | DAG representation of the flow |
| `input_datasets` | `List[DataikuDataset]` | Datasets with type INPUT |
| `output_datasets` | `List[DataikuDataset]` | Datasets with type OUTPUT |
| `intermediate_datasets` | `List[DataikuDataset]` | Datasets with type INTERMEDIATE |

### Dataset Operations

```python
flow.add_dataset(dataset)          # Add a dataset
flow.get_dataset("name")           # Get dataset by name -> Optional[DataikuDataset]
```

### Recipe Operations

```python
flow.add_recipe(recipe)                    # Add a recipe
flow.get_recipe("name")                    # Get recipe by name -> Optional[DataikuRecipe]
flow.get_recipes_by_type(RecipeType.JOIN)   # Get all JOIN recipes -> List[DataikuRecipe]
```

### Analysis

```python
flow.validate()                    # Validate structure -> Dict[str, Any]
flow.get_summary()                 # Text summary -> str
flow.get_column_lineage("col")     # Trace column lineage -> ColumnLineage
flow.get_recommendations()         # Get recommendations -> List[FlowRecommendation]
```

### Visualization

```python
flow.visualize(format="svg")       # SVG (pixel-accurate Dataiku styling)
flow.visualize(format="html")      # Interactive canvas
flow.visualize(format="ascii")     # Terminal-friendly
flow.visualize(format="plantuml")  # Documentation-ready
flow.visualize(format="mermaid")   # GitHub/Notion compatible

flow.to_svg("output.svg")         # Save SVG to file
flow.to_html("output.html")       # Save HTML to file
flow.to_ascii()                    # Return ASCII string
flow.to_png("output.png")         # Requires cairosvg
flow.to_pdf("output.pdf")         # Requires cairosvg
```

### Serialization

```python
# Export
flow.to_dict()                     # -> Dict[str, Any]
flow.to_json(indent=2)             # -> str (JSON)
flow.to_yaml()                     # -> str (YAML)
flow.to_recipe_configs()           # -> List[Dict] (Dataiku API-compatible)
flow.export_all("output_dir/")     # Export all artifacts to directory

# Import (classmethods)
DataikuFlow.from_dict(data)        # -> DataikuFlow
DataikuFlow.from_json(json_str)    # -> DataikuFlow
DataikuFlow.from_yaml(yaml_str)    # -> DataikuFlow
```

### Special Methods

```python
len(flow)                          # Number of recipes
for recipe in flow:                # Iterate over recipes
    print(recipe.name)
flow._repr_svg_()                  # Jupyter notebook inline display
```

### Zone Operations

```python
flow.add_zone(FlowZone(name="ETL", color="#4b96e6"))
flow.get_zone("ETL")              # -> Optional[FlowZone]
```

---

## FlowZone

Logical grouping for flow elements.

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | *required* | Zone name |
| `color` | `str` | `"#4b96e6"` | Display color |
| `datasets` | `List[str]` | `[]` | Dataset names in this zone |
| `recipes` | `List[str]` | `[]` | Recipe names in this zone |

### Methods

```python
zone.add_dataset("dataset_name")
zone.add_recipe("recipe_name")
zone.to_dict()
FlowZone.from_dict(data)
```

---

## DataikuRecipe

A recipe node in the flow (transformation step).

```python
from py2dataiku import DataikuRecipe, RecipeType
```

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | *required* | Recipe name |
| `recipe_type` | [`RecipeType`](enums.md#recipetype) | *required* | Recipe type |
| `inputs` | `List[str]` | `[]` | Input dataset names |
| `outputs` | `List[str]` | `[]` | Output dataset names |
| `steps` | `List[PrepareStep]` | `[]` | Processor steps (PREPARE recipes) |
| `group_keys` | `List[str]` | `[]` | Group-by columns (GROUPING) |
| `aggregations` | `List[Aggregation]` | `[]` | Aggregation configs (GROUPING) |
| `join_type` | `JoinType` | `JoinType.LEFT` | Join type (JOIN) |
| `join_keys` | `List[JoinKey]` | `[]` | Join key pairs (JOIN) |
| `selected_columns` | `Optional[Dict[str, List[str]]]` | `None` | Column selection (JOIN) |
| `partition_columns` | `List[str]` | `[]` | Partition columns (WINDOW) |
| `order_columns` | `List[str]` | `[]` | Order columns (WINDOW) |
| `window_aggregations` | `List[Dict[str, Any]]` | `[]` | Window functions (WINDOW) |
| `sampling_method` | `SamplingMethod` | `SamplingMethod.RANDOM` | Sampling method |
| `sample_size` | `Optional[int]` | `None` | Sample size |
| `split_condition` | `Optional[str]` | `None` | Split condition (SPLIT) |
| `sort_columns` | `List[Dict[str, str]]` | `[]` | Sort columns (SORT) |
| `top_n` | `Optional[int]` | `None` | Number of rows (TOP_N) |
| `ranking_column` | `Optional[str]` | `None` | Ranking column (TOP_N) |
| `code` | `Optional[str]` | `None` | Python code (PYTHON recipe) |
| `settings` | `Optional[RecipeSettings]` | `None` | Composed settings (takes precedence) |
| `source_lines` | `List[int]` | `[]` | Source code line numbers |
| `notes` | `List[str]` | `[]` | Notes |

### Factory Methods

```python
# Create a PREPARE recipe
recipe = DataikuRecipe.create_prepare(
    name="prepare_data",
    input_dataset="raw_data",
    output_dataset="cleaned_data",
    steps=[step1, step2]
)

# Create a GROUPING recipe
recipe = DataikuRecipe.create_grouping(
    name="aggregate_sales",
    input_dataset="cleaned_data",
    output_dataset="summary",
    keys=["region", "category"],
    aggregations=[Aggregation("amount", "SUM")]
)

# Create a JOIN recipe
recipe = DataikuRecipe.create_join(
    name="join_tables",
    left_dataset="customers",
    right_dataset="orders",
    output_dataset="joined",
    join_keys=[JoinKey("customer_id", "cust_id")],
    join_type=JoinType.LEFT
)

# Create a PYTHON recipe
recipe = DataikuRecipe.create_python(
    name="custom_transform",
    inputs=["input_data"],
    outputs=["output_data"],
    code="import pandas as pd\n..."
)
```

### Instance Methods

```python
recipe.add_step(step)                                    # Add processor step (PREPARE)
recipe.add_aggregation("amount", "SUM", "total_amount")  # Add aggregation (GROUPING)
recipe.add_join_key("left_col", "right_col")             # Add join key (JOIN)
recipe.add_note("Note text")
recipe.get_step_summary()                                # -> List[str] (PREPARE)
recipe.to_dict()                                         # -> Dict[str, Any]
recipe.to_api_dict()                                     # Dataiku API-compatible dict
recipe.to_json()                                         # Alias for to_api_dict()
DataikuRecipe.from_dict(data)                            # Classmethod
```

---

## DataikuDataset

A dataset node in the flow.

```python
from py2dataiku import DataikuDataset, DatasetType, DatasetConnectionType
```

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | *required* | Dataset name |
| `dataset_type` | [`DatasetType`](enums.md#datasettype) | `DatasetType.INTERMEDIATE` | INPUT, OUTPUT, or INTERMEDIATE |
| `connection_type` | [`DatasetConnectionType`](enums.md#datasetconnectiontype) | `DatasetConnectionType.FILESYSTEM` | Connection type |
| `schema` | `List[ColumnSchema]` | `[]` | Column schema |
| `source_variable` | `Optional[str]` | `None` | Original Python variable name |
| `source_line` | `Optional[int]` | `None` | Line number in source |
| `notes` | `List[str]` | `[]` | Notes |

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `is_input` | `bool` | Whether this is an INPUT dataset |
| `is_output` | `bool` | Whether this is an OUTPUT dataset |

### Methods

```python
dataset.add_column("name", "string", nullable=True)
dataset.add_note("Note text")
dataset.to_dict()
dataset.to_json()                # Dataiku API-compatible
DataikuDataset.from_dict(data)   # Classmethod
```

---

## ColumnSchema

Column definition within a dataset.

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | *required* | Column name |
| `type` | `str` | *required* | Type: `"string"`, `"int"`, `"float"`, `"date"`, `"boolean"` |
| `nullable` | `bool` | `True` | Whether column allows nulls |
| `default` | `Optional[Any]` | `None` | Default value |
| `format` | `Optional[str]` | `None` | Format string (for dates) |

---

## PrepareStep

A processor step within a PREPARE recipe.

```python
from py2dataiku import PrepareStep, ProcessorType
```

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `processor_type` | [`ProcessorType`](enums.md#processortype) | *required* | Processor type |
| `params` | `Dict[str, Any]` | `{}` | Processor parameters |
| `disabled` | `bool` | `False` | Whether step is disabled |
| `name` | `Optional[str]` | `None` | Step label |
| `meta_type` | `str` | `"PROCESSOR"` | PROCESSOR or GROUP |
| `source_line` | `Optional[int]` | `None` | Source code line |
| `source_code` | `Optional[str]` | `None` | Source code snippet |

### Factory Methods

```python
# Fill missing values
step = PrepareStep.fill_empty("amount", 0)

# Rename columns
step = PrepareStep.rename_columns({"old_name": "new_name"})

# Delete columns
step = PrepareStep.delete_columns(["temp_col", "debug_col"])

# String transformation
step = PrepareStep.string_transform("name", StringTransformerMode.UPPERCASE)

# Set column type
step = PrepareStep.set_type("age", "int")

# Parse date
step = PrepareStep.parse_date("date_col", formats=["yyyy-MM-dd"])

# Filter on value
step = PrepareStep.filter_on_value("status", ["active", "pending"])

# Remove empty rows
step = PrepareStep.remove_rows_on_empty(["required_col"])
```

### Instance Methods

```python
step.to_dict()                    # -> Dict[str, Any]
step.to_json()                    # Dataiku API-compatible
PrepareStep.from_dict(data)       # Classmethod
```

---

## Aggregation

Aggregation configuration for GROUPING recipes.

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `column` | `str` | *required* | Column to aggregate |
| `function` | `str` | *required* | `"SUM"`, `"AVG"`, `"COUNT"`, `"MIN"`, `"MAX"`, etc. |
| `output_column` | `Optional[str]` | `None` | Output column name |

---

## JoinKey

Join key pair for JOIN recipes.

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `left_column` | `str` | *required* | Column from left dataset |
| `right_column` | `str` | *required* | Column from right dataset |
| `match_type` | `str` | `"EXACT"` | `"EXACT"` or `"FUZZY"` |
