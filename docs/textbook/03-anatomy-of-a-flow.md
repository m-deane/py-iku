# Chapter 3 — Anatomy of a Flow

## What you'll learn

This chapter takes the V1 flow object from Chapter 2 and walks every attribute that the rest of the book relies on. By the end of it, you will be fluent in the four core model classes (`DataikuFlow`, `DataikuRecipe`, `DataikuDataset`, `PrepareStep`), the recipes-versus-processors distinction, the `FlowGraph` API for navigating the DAG, and the round-trip serialization formats.

## Recipes, processors, and datasets

Three nouns recur in everything py-iku produces. They are not interchangeable.

A **dataset** is a named, schemaful collection of rows. In DSS it is the unit of storage and the unit DSS partitions and caches. Every input the flow reads from and every output the flow produces is a dataset. In py-iku it is a `DataikuDataset` instance with a `name`, a `dataset_type` (input, output, or intermediate), a `connection_type`, and an optional column schema.

A **recipe** is a transformation node. It takes one or more input datasets, applies a single declarative transformation, and writes one or more output datasets. A JOIN takes two inputs and produces one output; a SPLIT takes one input and produces two; a PREPARE takes one input and produces one. Recipes are the unit DSS schedules: each recipe is its own job, with its own retry, its own engine binding, and its own logs (see [dataiku-api-client-python source](https://github.com/dataiku/dataiku-api-client-python/blob/master/dataikuapi/dss/recipe.py) for the recipe-creator class hierarchy and [Dataiku docs: Recipes](https://doc.dataiku.com/dss/latest/recipes/index.html) for the user-facing concept).

A **processor** is a step *within* a single PREPARE recipe. PREPARE is the only recipe type that holds a processor list; the other 36 recipe types are configured by their `RecipeSettings` payload, not by a sequence of processors. py-iku's `ProcessorType` enum enumerates 122 processor types — column renamers, filters, formulas, value fillers, type casters, and so on (see [Dataiku docs: Prepare recipe](https://doc.dataiku.com/dss/latest/preparation/index.html) for the user-facing catalog). A PREPARE recipe with five processors is one DSS job that runs five operations in sequence inside a single execution context.

The distinction between recipes and processors is the central translation problem. Most pandas transforms are *element-wise*: rename, fillna, type cast, round, abs, clip, simple equality filter. These all become processors inside a single PREPARE recipe. A few pandas transforms are *structural*: groupby, merge, concat, sort, top-n, window. These become their own recipe types because their input and output arities differ from 1→1 (a JOIN is 2→1; a SPLIT is 1→2; a STACK is N→1) and because DSS schedules each one as a separate job.

Choosing the right granularity is the whole game. A translator that emits one recipe per pandas line produces a flow with a separate PREPARE for every line — correct but absurd. A translator that emits one PREPARE for the entire script produces a flow with no DAG structure, which destroys the partial-re-execution property that motivated the flow in the first place. py-iku's rule is: structural ops become their own recipes, element-wise ops merge into PREPARE recipes, and the optimizer pass merges adjacent PREPAREs that the rule produced separately. Chapter 4 states the rule formally and Chapter 10 covers the optimizer.

## DataikuFlow

`DataikuFlow` is the top-level container. It is a Python dataclass with two collections — `datasets` and `recipes` — and a handful of convenience properties.

```python
from py2dataiku import convert

source = """
import pandas as pd

orders = pd.read_csv("orders.csv")
orders["discount_pct"] = orders["discount_pct"].fillna(0.0)
orders["revenue"] = orders["quantity"] * orders["unit_price"] * (1 - orders["discount_pct"])
orders = orders.rename(columns={"order_date": "ordered_at"})
orders_clean = orders
"""

flow = convert(source)

# The flat collections
print(len(flow.datasets), len(flow.recipes))
# 2 1

# Filtered views: input vs intermediate vs output datasets
print([d.name for d in flow.input_datasets])
# ['orders']

print([d.name for d in flow.output_datasets])
# ['orders_clean']
```

`flow.input_datasets`, `flow.output_datasets`, and `flow.intermediate_datasets` are properties that filter `flow.datasets` by `dataset_type`. They are not separate lists — mutating `flow.datasets` reflects in all three.

The flow also exposes a `get_dataset(name)` lookup and a `get_recipe(name)` lookup, plus `get_recipes_by_type(...)` for filtering by `RecipeType`:

```python
from py2dataiku import RecipeType

prepare_recipes = flow.get_recipes_by_type(RecipeType.PREPARE)
print(len(prepare_recipes))
# 1

orders_dataset = flow.get_dataset("orders")
print(orders_dataset.dataset_type.value)
# 'input'
```

These are linear-time scans over the underlying lists. The lists are small — even the V5 final flow has six or seven recipes and a similar number of datasets — so the scan is fine. For larger flows, the `flow.graph` accessor (below) gives O(V+E) operations directly on the DAG.

## FlowGraph

The `flow.graph` property returns a `FlowGraph` — a DAG view over the same underlying data, with adjacency lists, a topological sort, and cycle detection.

```python
graph = flow.graph

# Topological sort: a flat list of node names, each before its successors
order = graph.topological_sort()
print(order)
# ['orders', 'prepare_recipe_1', 'orders_clean']

# Cycle detection
print(graph.detect_cycles())
# []
```

The topological sort uses Kahn's algorithm: it walks nodes in order of incoming-edge count, removing edges as it goes. The result is a flat list of node names that respects every edge in the DAG; for V1 with one recipe, the order is input → recipe → output. For V5 it is seven names long, but it is still flat, and the order is what every downstream tool that needs to iterate the flow uses.

Cycle detection runs depth-first from every node. For a flow produced by `convert(...)` the result is always empty — the rule-based generator emits a DAG by construction — but cycle detection is still useful when constructing flows by hand or when round-tripping through formats that allow malformed input.

`graph.find_disconnected_subgraphs()` returns the connected components in the undirected sense. A typical converted flow has one component; multiple components show up only when the input script defines two unrelated pipelines in the same file.

The graph is *derived* from `flow.recipes` and `flow.datasets`; it is not a separate writable representation. Adding a recipe through `flow.add_recipe(...)` invalidates the previously-returned graph object, so call `flow.graph` again rather than caching the result. Do not manipulate the graph's adjacency list directly — the source of truth is the recipe list.

## DataikuRecipe

A `DataikuRecipe` is the per-node configuration. It carries:

- `name` — a string identifier, unique within the flow.
- `recipe_type` — a `RecipeType` enum value (one of 37; see `py2dataiku.models.dataiku_recipe.RecipeType`).
- `inputs` — a list of input dataset names.
- `outputs` — a list of output dataset names.
- `settings` — a `RecipeSettings` subclass instance, typed by recipe type.
- `steps` — for PREPARE recipes only, an ordered list of `PrepareStep` instances.

```python
recipe = flow.recipes[0]

print(recipe.name)
# 'prepare_recipe_1'

print(recipe.recipe_type, recipe.recipe_type.value)
# RecipeType.PREPARE prepare

print(recipe.inputs, recipe.outputs)
# ['orders'] ['orders_clean']

print(len(recipe.steps))
# 3
```

The `settings` attribute is the typed payload that DSS reads to configure the recipe at runtime. For PREPARE the settings are minimal — most of the configuration is in the steps list — but for JOIN, GROUPING, WINDOW, SORT, SPLIT, TOP_N, STACK, and DISTINCT, the settings are where the join keys, partition columns, sort directions, and split conditions live. Chapter 6 walks each of those settings types; for now, the contract to remember is: every recipe has a settings object, and the settings object is typed.

`recipe_type` is an enum, not a string. Chapter 4 will use enum values directly in pattern-matching code; the DSS-canonical string names (e.g. `shaker` for PREPARE, `grouping` for GROUPING) are accessible through `.value` when needed but should not be passed around as strings inside Python code.

## PrepareStep

A `PrepareStep` is the configuration of a single processor within a PREPARE recipe. It carries:

- `processor_type` — a `ProcessorType` enum value (one of 122).
- `params` — a dict of processor-specific parameters.
- `name` — an optional human-readable label.
- `disabled` — a boolean flag; DSS skips disabled steps at runtime.

```python
for step in recipe.steps:
    print(step.processor_type.value, step.params)
# FillEmptyWithValue {'columns': ['discount_pct'], 'value': '0.0'}
# CreateColumnWithGREL {'column': 'revenue', 'expression': 'numval(quantity) * numval(unit_price) * (1 - numval(discount_pct))'}
# ColumnRenamer {'renamings': [{'from': 'order_date', 'to': 'ordered_at'}]}
```

The exact structure of `params` is processor-specific. The `ProcessorCatalog` class (covered in Chapter 5) is the source-of-truth for what each processor accepts. For now, the shape to remember is: each step is a small typed record, and the recipe's behavior is the ordered composition of those records.

The order matters. A `ColumnRenamer` placed before a `FillEmptyWithValue` references columns by their pre-rename names; placed after, by their post-rename names. PREPARE is a sequence, not a set. Chapter 5 has worked examples where reordering two steps changes the output schema; the takeaway here is that `recipe.steps` is an ordered list, the index in the list is the execution order, and the schema each step sees is whatever the previous step produced.

## DataikuDataset

`DataikuDataset` represents an input, intermediate, or output dataset.

```python
for ds in flow.datasets:
    print(ds.name, ds.dataset_type.value, ds.connection_type.value)
# orders input filesystem
# orders_clean output filesystem
```

`dataset_type` is a three-valued enum (`INPUT`, `INTERMEDIATE`, `OUTPUT`). `connection_type` reflects how the dataset is materialised; for V1 it defaults to `filesystem` because the input came from `pd.read_csv(...)`. DSS supports many connection types — SQL databases, S3, HDFS, Azure Blob, and so on — and Chapter 11 covers how `Py2DataikuConfig` controls the default.

The optional column schema lives at `ds.columns` as a list of `ColumnSchema` records. The rule-based analyzer fills the schema where it can infer types from the script (the `discount_pct` fillna pins it to a numeric column, for example) and leaves it empty otherwise. Schema enrichment is not a focus of py-iku — DSS will infer schemas from the input data at runtime — but the field exists so that hand-built or LLM-built flows can carry full column-level metadata.

## Round-trip serialization

Every model in py-iku supports `to_dict()` and a `from_dict(...)` classmethod. The flow level adds JSON and YAML wrappers on top.

```python
# To dict and back
d = flow.to_dict()
flow2 = type(flow).from_dict(d)

# To JSON and back
import json
flow_json = flow.to_json(indent=2)
flow3 = type(flow).from_json(flow_json)

# To YAML and back (requires PyYAML)
flow_yaml = flow.to_yaml()
flow4 = type(flow).from_yaml(flow_yaml)

# Structural equality across all four representations
for f in (flow2, flow3, flow4):
    assert len(f.recipes) == len(flow.recipes)
    assert f.recipes[0].recipe_type == flow.recipes[0].recipe_type
    assert len(f.recipes[0].steps) == len(flow.recipes[0].steps)
    assert {d.name for d in f.datasets} == {d.name for d in flow.datasets}
```

Round-trip equality is the property that makes the flow object behave as a checked-in artifact. A team can store the converted flow as JSON in git, diff two versions of it, review the diff in a pull request, and reload it for further programmatic inspection — none of which requires re-running `convert(...)`.

The `to_dict` shape is documented enough to be human-readable but should be treated as the model's internal representation, not as an external API contract; if a future py-iku version adds a field to `DataikuRecipe`, the dict gains a key and old dicts continue to load through `from_dict` because every key has a default. The promise is round-trip equality on flows produced by the *current* version, not byte-for-byte stability across versions.

## Putting it together

V1's flow object, walked end-to-end, is two datasets, one recipe, one settings object, three processor steps, a three-node DAG, and a single connected component. Every later chapter operates on a flow that is bigger than V1's but uses the same model. JOIN adds a 2→1 recipe and a third dataset. WINDOW adds a 1→1 recipe with a non-trivial settings payload. SPLIT adds a 1→2 recipe with two output datasets and one settings object that carries both branches' conditions.

The model does not change as the flow grows. The shapes of `DataikuFlow`, `DataikuRecipe`, `DataikuDataset`, and `PrepareStep` are the same in V5 as they are in V1; what changes is how many of each there are and how they are wired in `flow.graph`. The next chapter shows the wiring rule.

## Further reading

- [Models API reference](../api/models.md) — `DataikuFlow`, `DataikuRecipe`, `DataikuDataset`, `PrepareStep`.
- [Graph API reference](../api/graph.md) — `FlowGraph`, topological sort, cycle detection.
- [Enums API reference](../api/enums.md) — `RecipeType`, `ProcessorType`, dataset and connection enums.
- [Notebook 02 — Intermediate](https://github.com/m-deane/py-iku/blob/main/notebooks/02_intermediate.ipynb) — exercises the model classes interactively.

## What's next

Chapter 4 introduces the pandas-to-DSS translation grammar and uses V2 of the running example to show how each pandas line corresponds to a recipe choice.
