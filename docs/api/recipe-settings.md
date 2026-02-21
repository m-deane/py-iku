# Recipe Settings

Typed settings classes for recipe configuration using the composition pattern. Each recipe type has a dedicated settings class that provides type-safe configuration.

---

## RecipeSettings (ABC)

Abstract base class for all recipe settings.

```python
from py2dataiku.models.recipe_settings import RecipeSettings
```

### Abstract Methods

```python
def to_dict(self) -> Dict[str, Any]         # Dataiku API-compatible dict
def to_display_dict(self) -> Dict[str, Any]  # Human-readable dict
```

---

## Usage with DataikuRecipe

Settings are composed into recipes via the `settings` field:

```python
from py2dataiku import DataikuRecipe, RecipeType
from py2dataiku.models.recipe_settings import GroupingSettings

recipe = DataikuRecipe(
    name="aggregate_sales",
    recipe_type=RecipeType.GROUPING,
    inputs=["cleaned_data"],
    outputs=["summary"],
    settings=GroupingSettings(
        keys=["region", "category"],
        aggregations=[{"column": "amount", "function": "SUM"}],
    ),
)
```

When `settings` is present, it takes precedence over the recipe's direct fields (`group_keys`, `aggregations`, etc.).

---

## PrepareSettings

Settings for PREPARE recipes.

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `steps` | `List[Dict[str, Any]]` | `[]` | Processor steps |

---

## GroupingSettings

Settings for GROUPING recipes (group-by + aggregate).

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `keys` | `List[str]` | `[]` | Group-by columns |
| `aggregations` | `List[Dict[str, Any]]` | `[]` | Aggregation definitions |
| `pre_filter` | `Optional[str]` | `None` | Pre-aggregation filter |

---

## JoinSettings

Settings for JOIN recipes.

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `join_type` | `str` | `"LEFT"` | Join type |
| `join_keys` | `List[Dict[str, str]]` | `[]` | Join key pairs |
| `selected_columns` | `Dict[str, List[str]]` | `{}` | Columns to select per input |
| `post_filter` | `Optional[str]` | `None` | Post-join filter |

---

## WindowSettings

Settings for WINDOW recipes (window functions).

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `partition_columns` | `List[str]` | `[]` | Partition-by columns |
| `order_columns` | `List[Dict[str, str]]` | `[]` | Order-by columns |
| `aggregations` | `List[Dict[str, Any]]` | `[]` | Window function definitions |

---

## PivotSettings

Settings for PIVOT recipes.

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `row_keys` | `List[str]` | `[]` | Row identifier columns |
| `column_key` | `Optional[str]` | `None` | Column to pivot on |
| `aggregations` | `List[Dict[str, Any]]` | `[]` | Value aggregations |

---

## SplitSettings

Settings for SPLIT recipes.

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `split_mode` | `str` | `"FILTER"` | Split mode |
| `condition` | `Optional[str]` | `None` | Split condition/formula |
| `column` | `Optional[str]` | `None` | Column for value-based split |
| `ratio` | `Optional[float]` | `None` | Split ratio for random |

---

## SortSettings

Settings for SORT recipes.

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `columns` | `List[Dict[str, str]]` | `[]` | Sort columns with direction |

**Column format:** `{"column": "name", "order": "ASC"}` or `{"column": "name", "order": "DESC"}`

---

## StackSettings

Settings for STACK recipes (vertical concatenation).

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `mode` | `str` | `"UNION"` | Stack mode: `"UNION"` or `"INTERSECT"` |
| `add_origin_column` | `bool` | `False` | Add column indicating source |
| `origin_column_name` | `str` | `"origin"` | Name of origin column |

---

## SamplingSettings

Settings for SAMPLING recipes.

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `method` | `str` | `"RANDOM"` | Sampling method |
| `sample_size` | `Optional[int]` | `None` | Number of rows |
| `ratio` | `Optional[float]` | `None` | Sampling ratio |
| `seed` | `Optional[int]` | `None` | Random seed |
| `stratify_column` | `Optional[str]` | `None` | Stratification column |

---

## TopNSettings

Settings for TOP_N recipes.

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `n` | `int` | `10` | Number of rows |
| `ranking_column` | `Optional[str]` | `None` | Column to rank by |
| `ascending` | `bool` | `False` | Sort direction |
| `partition_columns` | `List[str]` | `[]` | Top-N per group |

---

## DistinctSettings

Settings for DISTINCT recipes.

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `columns` | `List[str]` | `[]` | Columns to consider for dedup |
| `keep` | `str` | `"FIRST"` | Which duplicate to keep: `"FIRST"`, `"LAST"` |

---

## PythonSettings

Settings for PYTHON code recipes.

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `code` | `str` | `""` | Python code |
| `env_name` | `Optional[str]` | `None` | Code environment name |
| `container` | `Optional[str]` | `None` | Container configuration |
