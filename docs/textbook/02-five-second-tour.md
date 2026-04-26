# Chapter 2 — The 5-Second Tour

## What you'll learn

This chapter takes V1 of the running example, runs it through `convert(...)`, and inspects the resulting `DataikuFlow` end-to-end. By the end of it, you will know how to call the entry point, how to count and identify recipes in the produced flow, how to round-trip the flow through JSON, and how to render a visualization.

## The input

Here is V1 of the running example, copied from the running-example contract verbatim. The file is named `running_example_v1.py`; subsequent chapters extend it to V2 through V5.

```python
# running_example_v1.py
import pandas as pd

orders = pd.read_csv("orders.csv")
orders["discount_pct"] = orders["discount_pct"].fillna(0.0)
orders["revenue"] = orders["quantity"] * orders["unit_price"] * (1 - orders["discount_pct"])
orders = orders.rename(columns={"order_date": "ordered_at"})
orders_clean = orders
```

The script does three things to the `orders` table: it fills missing values in `discount_pct` with `0.0`, it derives a `revenue` column from `quantity`, `unit_price`, and `discount_pct`, and it renames `order_date` to `ordered_at`. Two of those three operations — the fill and the rename — are recognised by the current rule-based analyzer and become [processors](appendix-a-glossary.md#processor) in a [PREPARE recipe](appendix-a-glossary.md#recipe); the arithmetic-derived `revenue` column is not yet emitted as a `CreateColumnWithGREL` step on the rule-based path and is handled by the LLM path in Chapter 7.

## One call

py-iku's public entry point for the rule-based analyzer is the `convert` function. It takes either a Python source string, a `pathlib.Path` to a `.py` file, or a path-like string ending in `.py`, and returns a `DataikuFlow` object (see the public API surface in [`py2dataiku/__init__.py`](https://github.com/dataiku/py-iku/blob/main/py2dataiku/__init__.py) — the exported `convert` symbol is the canonical entry point).

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
```

That is the entire conversion. There are no required arguments beyond the source. The `optimize=True` default runs the post-conversion [optimizer](appendix-a-glossary.md#optimizer) pass that merges adjacent PREPARE recipes; for V1 there is only one PREPARE so the optimizer has nothing to merge, but the same default applies in later chapters.

The function is deterministic. Running it ten times in a row on the same source produces ten structurally identical flow objects. That property is what makes the rule-based path fit for use inside a CI assertion — the test does not need to tolerate run-to-run variation, because there is none. Chapter 7 establishes the analogous property for the LLM path, with the additional condition that `temperature=0`.

## Inspecting the flow

`DataikuFlow` is a plain dataclass with a small public surface. The two attributes worth looking at first are `recipes` and `datasets`.

```python
print(len(flow.recipes))
# 1

print([r.recipe_type.value for r in flow.recipes])
# ['prepare']

print([d.name for d in flow.datasets])
# ['orders', 'orders_prepared_prepared']
```

The flow has exactly one recipe — a PREPARE — and two [datasets](appendix-a-glossary.md#dataset), one input (`orders`) and one auto-named produced dataset (`orders_prepared_prepared`; the doubled `_prepared` suffix is an artifact of the current naming pass and is not load-bearing). The script's final assignment `orders_clean = orders` is a plain Python rebinding the rule-based analyzer treats as a no-op, so the variable name does not propagate into a dataset name; the LLM path in Chapter 7 sometimes preserves the variable name. The structural V1 contract — one PREPARE, one input dataset, one produced dataset — holds either way.

The recipe itself is a `DataikuRecipe`. Its type is the `RecipeType.PREPARE` enum value, and because it is a PREPARE recipe it carries an ordered list of `PrepareStep` instances under `recipe.steps`.

```python
recipe = flow.recipes[0]
print(recipe.recipe_type.value)
# 'prepare'

print(len(recipe.steps))
# 2

print([s.processor_type.value for s in recipe.steps])
# ['FillEmptyWithValue', 'ColumnRenamer']
```

The exact `ProcessorType` values come from the `ProcessorType` enum defined in `py2dataiku.models.prepare_step`. The two values above correspond to two of the three operations the script performed, in source order:

1. `FillEmptyWithValue` for `orders["discount_pct"].fillna(0.0)`.
2. `ColumnRenamer` for the `rename(columns={"order_date": "ordered_at"})` call.

The `revenue` arithmetic does not produce a step on the rule-based path: the current AST analyzer does not recognise pandas arithmetic-on-columns as a `CreateColumnWithGREL` formula and skips it. The LLM path in Chapter 7 does emit a `CreateColumnWithGREL` step for that line, with the [GREL](appendix-a-glossary.md#grel) expression `numval(quantity) * numval(unit_price) * (1 - numval(discount_pct))` — GREL is DSS's row-level formula language; see Chapter 9 for the AST-to-GREL translator and [the glossary](appendix-a-glossary.md#grel) for a quick definition. The verifier at `tests/test_py2dataiku/test_textbook_examples.py` pins the rule-based shape (one PREPARE, two steps) against this chapter so any future change to the analyzer that closes the gap will fail the test and prompt a doc update.

## Input and output dataset views

`DataikuFlow` has three derived properties that filter the dataset list by role: `input_datasets`, `intermediate_datasets`, and `output_datasets`. They classify by `dataset_type`, which the analyzer infers from how each dataset is referenced in the source. A name produced by `pd.read_csv(...)` and never written back is an input. A name written by one operation and read by another is an intermediate. A name written by the final operation is an output.

```python
print([d.name for d in flow.input_datasets])
# ['orders']

print([d.name for d in flow.intermediate_datasets])
# ['orders_prepared_prepared']

print([d.name for d in flow.output_datasets])
# []
```

V1 produces one input dataset and one intermediate dataset; `output_datasets` is empty because the rule-based analyzer only marks a dataset as an output when the script explicitly writes it to a recognised sink (e.g. `to_csv`, `to_parquet`). The trailing `orders_clean = orders` rebinding does not register as a sink, so the produced dataset is classified as intermediate and named `orders_prepared_prepared`. V2 in the next chapter writes through a `to_csv` call and the dataset roles shift accordingly.

These properties are convenience views, not separate collections. Mutating `flow.datasets` is reflected in all three. They exist so that downstream code that wants to render only the inputs (a flow header) or only the outputs (a flow tail) does not have to filter the list by hand.

## Asserting the shape

Because the conversion is deterministic, you can assert against the produced flow directly. This is the assertion pattern Chapter 11 builds CI integration around; it is worth seeing the shape now.

```python
from py2dataiku import RecipeType

assert len(flow.recipes) == 1
assert flow.recipes[0].recipe_type == RecipeType.PREPARE
assert len(flow.recipes[0].steps) == 2

dataset_names = {d.name for d in flow.datasets}
assert dataset_names == {"orders", "orders_prepared_prepared"}
```

These four assertions encode the V1 contract as the rule-based analyzer currently produces it. The same code runs as a `pytest` test, as a script, or as a notebook cell. If a future change to the rule-based analyzer broke V1's expected shape — or closed the `CreateColumnWithGREL` gap and bumped the step count — every one of these assertions would fail in a way that pinpoints the breakage.

## Round-tripping the flow

A `DataikuFlow` is data, not a side effect. It can be serialised to a Python `dict` with `to_dict()` and reconstructed with `DataikuFlow.from_dict(...)`. The same is true for JSON and YAML.

```python
import json
from py2dataiku import DataikuFlow

# Serialize to dict, then to JSON
flow_dict = flow.to_dict()
flow_json = json.dumps(flow_dict, indent=2)

# Reload from JSON and assert structural equality
reloaded_dict = json.loads(flow_json)
reloaded = DataikuFlow.from_dict(reloaded_dict)

assert len(reloaded.recipes) == len(flow.recipes)
assert reloaded.recipes[0].recipe_type == flow.recipes[0].recipe_type
assert len(reloaded.recipes[0].steps) == len(flow.recipes[0].steps)
```

The convenience methods `flow.to_json()` and `DataikuFlow.from_json(...)` skip the intermediate `dict` step. The same pair exists for YAML. Round-trip equality is a property tested in the library's own test suite; the practical use of it is that a flow can be checked into git and reviewed as a text artifact.

The round-trip property is what makes the rule-based path operate as data engineering infrastructure rather than as a one-shot script. The `DataikuFlow` object is the source of truth for the produced flow shape, and any downstream tool — [DSS](appendix-a-glossary.md#dss) deployer, visualizer, diff tool — reads from that object rather than from the original Python script.

## Rendering a visualization

The `flow.visualize(format=...)` method produces a string in the requested format; `flow.save(path, format=...)` writes the string to disk and infers the format from the file extension if `format` is not given.

```python
from pathlib import Path

# Render to SVG, write to disk
svg = flow.visualize(format="svg")
Path("v1_flow.svg").write_text(svg, encoding="utf-8")

# Or, equivalently:
flow.save("v1_flow.svg")
```

For V1 the rendered SVG shows two dataset nodes connected by a single PREPARE recipe node: `orders → PREPARE → orders_prepared_prepared`. The visualizer dispatches to a format-specific class (`SVGVisualizer`, `HTMLVisualizer`, `ASCIIVisualizer`, `PlantUMLVisualizer`) depending on the `format` argument; the SVG path is the one that produces the pixel-accurate Dataiku styling.

The ASCII variant is useful in terminal contexts where loading an image viewer would be heavy:

```python
print(flow.visualize(format="ascii"))
```

The output is a small text-art DAG with the two dataset names and the single recipe between them. It is not a substitute for the SVG when the flow gets larger — Chapter 6 produces flows with seven nodes and the ASCII view does not stay legible — but for V1 it fits in a comment block.

## Determinism in practice

The rule-based path produces the same flow object every time for the same input. That property is what makes it fit for CI; it also has a more immediate consequence for development. Two team members running `convert(source)` on the same script on different machines and at different times produce flow objects whose `to_dict()` outputs compare equal. Diffing the JSON serialization of two converted flows is a meaningful diff: every difference between two outputs corresponds to a difference between the two inputs.

The library's own test suite asserts this property by running `convert(source)` against each example script and comparing against a checked-in expected flow shape. There is no need to tolerate run-to-run variation in those tests because there is none to tolerate. Chapter 11 walks the same pattern at the project level — a `pytest` test that loads a script, calls `convert(...)`, and asserts against the recipe types in [topological order](appendix-a-glossary.md#topological-order).

The LLM path establishes the same property under different conditions: temperature pinned to zero and a fixed system prompt. Chapter 7 covers that; for now, the takeaway is that both paths are usable as deterministic infrastructure rather than as one-shot tools.

## A note on dataset names

py-iku reads input dataset names from `pd.read_csv("orders.csv")` calls. In V1 the input is `orders` (the CSV name minus the extension); the produced dataset is auto-named `orders_prepared_prepared` because the script does not write to an explicit sink and the rule-based naming pass appends a `_prepared` suffix per PREPARE recipe (the doubled suffix here is the merged-prepare optimizer's contribution). Subsequent chapters add more inputs (`customers`, `products`) and more named intermediates (`orders_enriched`, `orders_windowed`, `orders_ranked`), all of which match the dataset names declared in the running-example contract once an explicit sink is introduced.

The library invents a name only when the script does not provide one through a recognised write call. Where the script does write — V2 onward, via `to_csv` — the produced dataset takes its name from the path argument. Either way, every name in the produced flow can be traced back to the source.

## What this leaves out

V1 exercises one recipe type (PREPARE) and two processors. That is enough to demonstrate the conversion shape but not enough to exercise the model: PREPARE alone does not show how the DAG is built, the optimizer pass has nothing structural to merge across, and there is no JOIN, GROUPING, WINDOW, SORT, or SPLIT to compare against.

Chapter 3 takes V1's flow object and walks every attribute on it, including the `flow.graph` accessor that becomes load-bearing for the rest of the book. Chapter 4 introduces V2, which adds two `merge(...)` calls and produces the first multi-recipe flow.

## Further reading

- [Quick Start tutorial](../getting-started/quickstart.md) — install the library and run the V1 conversion end-to-end.
- [Glossary](appendix-a-glossary.md) — for the recipe, processor, dataset, and GREL terms used here.
- [Core functions API reference](../api/core-functions.md) — `convert`, `convert_file`, and the LLM-mode counterparts.
- [Models API reference](../api/models.md) — `DataikuFlow`, `DataikuRecipe`, `PrepareStep`.
- [Notebook 01 — Beginner](https://github.com/m-deane/py-iku/blob/main/notebooks/01_beginner.ipynb) — runs through the V1 conversion interactively.

## What's next

Chapter 3 walks every attribute on V1's flow object — `flow.recipes`, `flow.datasets`, `flow.graph`, `recipe.settings`, `recipe.steps` — and explains the recipe-versus-processor distinction that the rest of the book relies on.
