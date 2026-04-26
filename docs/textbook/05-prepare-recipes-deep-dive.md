# Chapter 5 — Prepare Recipes Deep Dive

## What you'll learn

How a single PREPARE recipe composes many small transforms into one ordered pipeline of `PrepareStep` instances; why step ordering changes output schemas; how the optimizer flushes the prepare-step buffer when a structural recipe interrupts the chain. By the end, the V1 running example will read line-by-line as a sequence of processors with named parameters.

## The shape of a PREPARE recipe

A PREPARE recipe is a single node in the DSS flow that holds an ordered list of processor steps. Each step is a `PrepareStep` instance with a `ProcessorType` and a `params` dict. The recipe takes one input dataset and produces one output dataset. DSS executes the steps top-to-bottom in a streaming pass; step N reads the schema and rows produced by step N−1.

The class shape is plain data:

```python
from py2dataiku.models.prepare_step import PrepareStep, ProcessorType

step = PrepareStep.fill_empty(column="discount_pct", value=0.0)
print(step.processor_type)  # ProcessorType.FILL_EMPTY_WITH_VALUE
print(step.params)           # {'column': 'discount_pct', 'value': '0.0'}
print(step.to_dict())
# {'metaType': 'PROCESSOR', 'type': 'FillEmptyWithValue',
#  'disabled': False, 'params': {'column': 'discount_pct', 'value': '0.0'}}
```

The `metaType` and string-valued `type` come straight from the DSS wire format used by the official client (see [dataiku-api-client-python: `PrepareRecipe`](https://github.com/dataiku/dataiku-api-client-python/blob/master/dataikuapi/dss/recipe.py)). py-iku's job is to assemble these dictionaries; DSS executes them.

The 122 processor types are enumerated as `ProcessorType` values. A handful (`FillEmptyWithValue`, `ColumnRenamer`, `ColumnsSelector`, `Formula`, `FilterOnValue`, `FilterOnNumericRange`, `FilterOnFormula`, `RemoveDuplicates`, `RemoveRowsOnEmpty`, `StringTransformer`, `NumericalTransformer`, `TypeSetter`, `DateParser`) cover the bulk of pandas idioms; the rest handle specialized text, geography, JSON, and conditional-logic cases. The full list is documented at [Dataiku docs: Processors reference](https://doc.dataiku.com/dss/latest/preparation/processors/index.html).

## Why one PREPARE, not N

The first non-obvious property of the rule-based path: a chain of element-wise pandas operations collapses into a single PREPARE recipe with multiple steps. It does not become a chain of PREPARE recipes, even though each individual `df.fillna(...)` or `df.rename(...)` could be expressed that way.

Take a four-line snippet:

```python
import pandas as pd
from py2dataiku import convert

source = """
import pandas as pd
orders = pd.read_csv("orders.csv")
orders["discount_pct"] = orders["discount_pct"].fillna(0.0)
orders["revenue"] = orders["quantity"] * orders["unit_price"] * (1 - orders["discount_pct"])
orders_clean = orders.rename(columns={"order_date": "ordered_at"})
"""
flow = convert(source)
assert len(flow.recipes) == 1
assert flow.recipes[0].recipe_type.value == "prepare"
print(len(flow.recipes[0].steps))  # 3
```

One recipe, three steps. The rule that produces this shape: a step is element-wise (touches columns within a row, preserves row count and ordering) versus structural (groups, joins, sorts, splits, or reshapes the dataset). Element-wise transforms become processors inside an active PREPARE buffer; structural transforms flush the buffer and emit their own recipe nodes.

The economic reason for collapsing into one recipe: in DSS, every recipe is a unit of scheduling, partitioning, and cache invalidation. A flow with three sequential PREPARE recipes has three intermediate datasets, three partition spaces, and three places a downstream consumer might read from. Collapsing them produces a single intermediate dataset and a single execution unit. The DSS scheduler does not pay for the steps individually — it pays for the recipe.

## Step ordering and the schema invariant

PREPARE is a sequence, not a set. Step N runs against the schema produced by step N−1. Reordering changes meaning.

```python
from py2dataiku.models.prepare_step import PrepareStep

# Order A: rename first, then filter on the new name
order_a = [
    PrepareStep.rename_columns({"order_date": "ordered_at"}),
    PrepareStep.filter_on_value(column="ordered_at", values=["2024-01-01"]),
]

# Order B: filter first, then rename
order_b = [
    PrepareStep.filter_on_value(column="order_date", values=["2024-01-01"]),
    PrepareStep.rename_columns({"order_date": "ordered_at"}),
]
```

Order A's filter sees a column called `ordered_at`. Order B's filter sees `order_date`. If a PREPARE recipe is fed an Order-A configuration but a dataset where `ordered_at` does not yet exist, DSS fails the recipe at step 2; it does not reorder the steps to be helpful.

The library's optimizer reorders steps within a single PREPARE recipe under one specific rule, captured in `RecipeMerger.optimize_prepare_steps`. The rule:

1. Column deletions first — drop data early so later steps do less work.
2. Type setters next — establish the typed schema before transforms that depend on it.
3. Row filters and duplicate removals — reduce row count before per-row work.
4. Other element-wise steps in original order.
5. Column renames last — renames change the names later steps would have referenced, so they go at the end.

The reordering only happens within a single PREPARE recipe. The optimizer does not move a step across a recipe boundary, because that would change the schema visible to a downstream non-PREPARE recipe. The full source for the rule lives in `py2dataiku/optimizer/recipe_merger.py`.

## When the buffer flushes

The PREPARE buffer is the analyzer's running list of pending element-wise steps. While the analyzer walks the source code, every element-wise transform appends to the buffer. When a structural transform appears, the analyzer flushes the buffer into a PREPARE recipe and then emits the structural recipe as a separate node. After the structural recipe, a new buffer starts.

This shows up as a predictable pattern in the LLM generator's main loop: every non-PREPARE branch begins by checking `if prepare_steps_buffer: current_input = self._create_prepare_recipe(...)` before emitting the structural recipe. The pattern is identical in the rule-based generator. The result is that any sequence `[element, element, ..., structural, element, ..., structural]` produces alternating PREPARE and structural recipes in the flow.

A small example: a rename, then a groupby, then another rename:

```python
from py2dataiku import convert

source = """
import pandas as pd
df = pd.read_csv("orders.csv")
df = df.rename(columns={"order_date": "ordered_at"})
agg = df.groupby("customer_id")["revenue"].sum().reset_index()
agg = agg.rename(columns={"revenue": "total_revenue"})
"""
flow = convert(source)
types = [r.recipe_type.value for r in flow.recipes]
print(types)  # ['prepare', 'grouping', 'prepare']
```

Two PREPARE recipes, separated by a GROUPING. They cannot be merged into one PREPARE because the GROUPING changes the row dimensionality between them; the second PREPARE operates on a different dataset shape than the first.

## Walking V1 of the running example

The V1 block of the running example (`_running_example.md`) is the canonical case. The pandas:

```python
orders = pd.read_csv("orders.csv")
orders["discount_pct"] = orders["discount_pct"].fillna(0.0)
orders["revenue"] = orders["quantity"] * orders["unit_price"] * (1 - orders["discount_pct"])
orders = orders.rename(columns={"order_date": "ordered_at"})
orders_clean = orders
```

becomes one PREPARE recipe with three steps, in this order:

1. `FILL_EMPTY_WITH_VALUE` on `discount_pct` with value `0.0`. The `fillna(0.0)` translates directly. Params: `{"column": "discount_pct", "value": "0.0"}`.
2. A column-creation step for `revenue = quantity * unit_price * (1 - discount_pct)`. The expression is multiplicative across columns and is emitted as a formula step (typically `CREATE_COLUMN_WITH_GREL` or `FORMULA` depending on the analyzer's translation path). Params include the new column name and the GREL expression.
3. `COLUMN_RENAMER` mapping `order_date` to `ordered_at`. Params: `{"renamings": [{"from": "order_date", "to": "ordered_at"}]}`.

Run it end-to-end:

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
recipe = flow.recipes[0]
assert recipe.recipe_type.value == "prepare"
assert recipe.inputs == ["orders"]
assert recipe.outputs == ["orders_clean"]
processor_types = [s.processor_type.value for s in recipe.steps]
print(processor_types)
# ['FillEmptyWithValue', 'CreateColumnWithGREL' (or 'Formula'), 'ColumnRenamer']
```

The order in `processor_types` is the order DSS will execute them. If the optimizer reorders them, the rename moves to the end (where it already is), the fill stays before the formula (since the formula reads `discount_pct` after the fill), and nothing else changes.

## Inspecting the params dict

The `params` dict on each step is the part DSS actually reads. py-iku's factory methods pre-populate the canonical keys so the emitted JSON imports cleanly. For a `FilterOnValue` step:

```python
step = PrepareStep.filter_on_value(
    column="tier",
    values=["gold"],
    matching_mode="FULL_STRING",
    keep=True,
)
print(step.params)
# {'column': 'tier', 'values': ['gold'], 'matchingMode': 'FULL_STRING', 'keep': True}
```

The `matchingMode` key is the lever that controls what kind of match `FilterOnValue` performs — Chapter 8 covers it in detail. For a `ColumnsSelector` step used as a deleter, the params include both the legacy and current keys to round-trip cleanly through DSS:

```python
step = PrepareStep.delete_columns(["email"])
print(step.params)
# {'columns': ['email'], 'keep': False, 'mode': 'remove'}
```

Without `keep: False` the processor defaults to KEEP and silently inverts intent — a real footgun documented in the class docstring. py-iku's factory methods exist precisely so users do not have to remember these defaults.

## Discovering processors at runtime

The 122 processor types are enumerated in `ProcessorType`, but a richer catalog with metadata lives in `ProcessorCatalog`:

```python
from py2dataiku.mappings.processor_catalog import ProcessorCatalog

catalog = ProcessorCatalog()
all_processors = catalog.list_processors()
print(len(all_processors))  # 122

renamer = catalog.get_processor("COLUMN_RENAMER")
print(renamer)  # canonical entry: type, params schema, category
```

The catalog is instance-based, not a flat dict, and is the right place to look up which params a processor expects. The enum is the right place to look up which processors exist. Use both in tandem: enum for type-safe references in code, catalog for runtime introspection or auto-generation of documentation.

## A note on inter-recipe merging

A separate optimizer pass runs after the analyzer produces its initial flow. If that pass sees two adjacent PREPARE recipes on a single edge (output of recipe A is the only input of recipe B, no fan-out), it merges them into one PREPARE with the combined step list. Chapter 10 covers the merge rule in depth, including the fan-out guard that prevents a merge when a PREPARE feeds two downstream consumers. For now, two facts to carry forward:

- A single `convert()` call can produce a flow where a chain `df.fillna(...).pipe(some_structural).rename(...)` becomes `[PREPARE, structural, PREPARE]`. The two PREPAREs do not merge because a structural recipe sits between them.
- The same chain with no structural step in the middle becomes one PREPARE with the combined steps.

The merge is conservative on purpose. Merging across a fan-out can change semantics if the two downstream consumers expect different intermediate schemas. The optimizer refuses the merge in that case and leaves the recipes alone.

## Theory anchor: composition is a sequence

PREPARE is the first recipe type the textbook treats as a composite object. A recipe is the unit DSS schedules; a step is the unit DSS composes inside the recipe's runtime. Two consequences follow:

- The granularity of orchestration is the recipe, not the step. Adding a fourth fillna to a 3-step PREPARE does not introduce a new scheduling unit; adding a groupby does.
- The order of steps inside a PREPARE is part of the recipe's identity. Two PREPARE recipes with the same steps in different orders are not equal — they describe different transformations. Round-trip serialization preserves the order, and the optimizer is the only mechanism allowed to reorder steps, under the four-bucket rule above.

A reader who internalizes the buffer-and-flush model can predict the recipe count of any pandas script before running `convert()`: count the structural transformations, add one for each leading or trailing run of element-wise steps, and that is the recipe count of the post-optimization flow.

## Further reading

- [Recipes and processor models API reference](../api/models.md)
- [Notebook 02: intermediate transforms](https://github.com/m-deane/py-iku/blob/main/notebooks/02_intermediate.ipynb)
- [Dataiku docs: Prepare recipe processors](https://doc.dataiku.com/dss/latest/preparation/processors/index.html)
- [dataiku-api-client-python: recipe.py](https://github.com/dataiku/dataiku-api-client-python/blob/master/dataikuapi/dss/recipe.py)

## What's next

Chapter 6 leaves the PREPARE recipe behind and tours the eight non-PREPARE recipe types — GROUPING, JOIN, SORT, TOP_N, WINDOW, SPLIT, STACK, DISTINCT — that the running example walks through from V2 to V5.
