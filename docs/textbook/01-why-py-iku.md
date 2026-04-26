# Chapter 1 — Why py-iku

## What you'll learn

This chapter explains the gap between an analyst's pandas script and a Dataiku DSS visual flow, and why that gap is worth bridging with a tool rather than by hand. By the end of it, you will know what a flow gives you that a script does not, where py-iku sits in the conversion pipeline, and why the library ships with two analysis modes instead of one.

## A pandas script is not a flow

A pandas script is a sequence of statements. Each statement mutates a dataframe variable in memory, and the next statement runs against whatever the previous statement left behind. The call graph is implicit: it lives in the order of the lines and in the local variable names. Python's interpreter is the only thing that truly understands the graph.

A Dataiku DSS visual flow is a different object. It is a directed acyclic graph (DAG) in which the nodes are named *datasets* and *recipes*, and the edges are typed inputs and outputs. Each recipe is configured declaratively: a JOIN recipe lists its join columns and join type, a PREPARE recipe lists its ordered processor steps, a WINDOW recipe lists its partitioning and frame. The DSS server reads this configuration and runs the recipe on whatever execution engine the dataset is bound to — DSS-native, in-database SQL pushdown, Spark, or Python (see [Dataiku docs: The Flow](https://doc.dataiku.com/dss/latest/flow/index.html)).

Three differences fall out of that, and all three are why an enterprise will eventually push for a flow even if the analyst is happy with the script.

### Lineage

In a script, when a column appears in the final output you have to grep through the file (and, in practice, several files) to find where it was created, what it depended on, and whether the dependency was overwritten anywhere. In a flow, every column has an explicit recipe of origin and an explicit input dataset, and the DSS catalog can render the column-level lineage without re-running anything. Asking "where does `revenue` come from" stops being a code-archaeology task and becomes a click.

### Partial re-execution

A script reruns from the top by default. If a downstream step fails, you either rerun the whole pipeline or you carry around state in a Jupyter kernel and hope nothing is stale. A flow is partitioned into recipe nodes that DSS schedules independently. A failure in the WINDOW recipe does not invalidate the JOIN that fed it; the JOIN's output dataset is on disk, the WINDOW reruns against it, and execution time scales with what changed rather than with the length of the file (see [Dataiku docs: Recipes](https://doc.dataiku.com/dss/latest/recipes/index.html)).

### Execution-engine portability

The same script that runs on a 100-row CSV in a developer's notebook will not run on a 100-million-row Snowflake table without a rewrite. The same flow will: every recipe type has implementations against multiple engines, and DSS picks the engine based on where the input datasets live. The script's pandas call is the abstraction that breaks; the flow's recipe configuration is the abstraction that survives.

These three properties — lineage, partial re-execution, engine portability — are what make a flow auditable. An auditor cannot meaningfully audit a 400-line pandas script because there is no abstraction to audit; the only thing to inspect is the code itself. A flow has a fixed set of recipe types with fixed semantics, and that fixed surface is what compliance and platform teams actually want to look at.

## Why the gap is hard to close by hand

The natural question is: if a flow is so much better, why do data engineers keep writing scripts? The answer is that the script is where the work happens. Data engineers iterate on pandas because pandas is fast to type, fast to debug, and has a notebook surrounding it. Building the same logic by hand in DSS — clicking through forms, configuring recipe settings, naming intermediate datasets — is slower and less ergonomic for the *first pass*.

So scripts get written first, and then someone has to translate them. That translation is non-trivial in both directions, and the directions are not symmetric.

Going from pandas to a flow is lossy in the *sense* of execution semantics. Pandas allows arbitrary Python in the middle of a transform; a flow restricts you to a fixed catalog of recipes and processors. Anything that does not fit the catalog has to be either reshaped into something that does, or pushed into a `PYTHON` recipe, which is a flow node that wraps a script and gives back the script's opaqueness. A good translation is one that minimizes how much logic ends up inside `PYTHON` recipes, because everything inside a `PYTHON` recipe is invisible to the lineage and audit machinery that motivated the flow in the first place.

Going from a flow to pandas is lossy in the opposite *sense* of metadata. A flow knows the partitioning of each dataset, the schema of each intermediate, and the engine binding of each recipe. The equivalent pandas code throws all of that information away the moment it materialises everything in memory.

py-iku is concerned with the first direction. It takes a pandas script as input and emits a `DataikuFlow` object — a Python representation of the DSS flow configuration that can be serialised to DSS via the public API or rendered to SVG, HTML, PNG, PlantUML, Mermaid, or ASCII. The library does not execute the flow, and it does not stand in for DSS at runtime. The boundary is deliberate: py-iku produces DSS configuration, DSS executes it.

## The translation problem stated

Translating a pandas script to a flow is not a syntactic substitution. The two languages do not have a one-to-one mapping at the line level. Several pandas patterns map to the same flow shape, and several flow shapes can come from the same pandas pattern depending on context.

Three concrete examples make this concrete.

First, three sequential `df.assign(...)` calls and a single `df.assign(...)` with three keyword arguments produce different scripts and produce *the same* PREPARE recipe with three steps. The translator has to recognise that these are equivalent.

Second, a `df[df["x"] == "a"]` filter looks identical at the AST level to a `df[df["x"] > 100]` filter, but the first becomes a `FILTER_ON_VALUE` processor and the second becomes a `FILTER_ON_NUMERIC_RANGE`. DSS uses distinct processor types for distinct operator classes (see [Dataiku docs: Visual recipes](https://doc.dataiku.com/dss/latest/preparation/index.html)). The translator has to inspect the operator and the operand types, not only the syntactic shape.

Third, a script that filters one dataframe twice on complementary predicates (`df[col >= 1000]` and `df[col < 1000]`) is semantically a SPLIT — one input, two outputs — but the script itself looks like two independent filters. A direct line-by-line translation produces two FILTER recipes; the better translation recognises the complementarity and produces one SPLIT recipe with two output branches.

Each of these requires the translator to understand semantic equivalence, not only syntax. That is the central technical claim of this book: the translation problem is a small theory, and the rest of the book is about how py-iku's particular theory is built. Chapter 4 gives the grammar in full; chapters 5 through 9 work out the special cases.

## Where py-iku fits

py-iku sits between the pandas script and the DSS API. It does not replace either.

```
pandas script  →  py-iku  →  DataikuFlow  →  DSS API  →  running flow
                                          ↘  visualizers  →  SVG / HTML / PNG / ...
```

The library's job ends at `DataikuFlow`. From there, the produced object can be serialised through the official `dataiku-api-client-python` library to a real DSS instance (see [dataiku-api-client-python source](https://github.com/dataiku/dataiku-api-client-python/blob/master/dataikuapi/dss/recipe.py)), or it can be rendered to a diagram for review, or it can be round-tripped through JSON and YAML for storage and version control. None of those downstream paths need py-iku to run; they only need the flow object.

This narrow scope is intentional. Anything py-iku claims to do, it does on the configuration side. It does not benchmark execution, it does not compete with Spark or DSS engines, and it does not promise that a converted flow will run faster than the script — it promises that the converted flow has the properties that flows have (lineage, partial re-execution, engine portability) and that scripts do not.

## Why two analysis modes

py-iku ships with two ways to turn the input script into a `DataikuFlow`: a rule-based path and an LLM-based path. They share the output model — both produce `DataikuFlow` — but they reach it differently, and both exist for a reason.

The rule-based path is an AST walker. It parses the script with Python's `ast` module, classifies each statement against a fixed pattern table, and emits the corresponding recipes. It is deterministic by construction (the same input produces the same output, byte for byte), it is fast, and it has no external dependencies.

It is also limited: it can only recognise patterns it has been programmed to recognise. A `df.merge(...)` call is in the pattern table; an idiomatic but unusual `pd.concat([df.query("a==b"), other], axis=0).pipe(custom_fn)` may not be. When the rule-based path encounters something it cannot classify, it either falls back to a `PYTHON` recipe (which preserves correctness but loses lineage) or raises `InvalidPythonCodeError` (which preserves correctness more aggressively, at the cost of forcing the user to fix the input).

The LLM-based path uses an Anthropic or OpenAI model behind a single `LLMCodeAnalyzer` interface. The model's job is to read the script, identify each transformation, and emit a structured analysis result that the same flow generator turns into recipes. With temperature pinned to zero and a fixed system prompt, this path is also deterministic in the sense that matters for CI: the same script and the same prompt produce the same output across runs. It costs tokens, it requires an API key, and it will not always agree with the rule-based path on borderline cases — but it handles ambiguous code, conditional logic, and non-standard idioms that the rule-based path misclassifies. Chapter 7 covers the LLM path in detail.

The two paths are exposed as separate, explicit entry points: `convert(...)` always runs the rule-based AST analyzer, and `convert_with_llm(...)` always runs the LLM analyzer. There is no automatic mode-switching, no `llm=` keyword on `convert(...)`, and no environment-variable trigger that promotes one to the other. A reader who only ever wants the rule-based path can skip Chapter 7 entirely and call `convert(...)`; a reader who wants the LLM path calls `convert_with_llm(...)` and supplies an API key.

## A teaser

The smallest interesting input the rest of the book uses is V1 of the running example — a five-line pandas script that fills a missing column, derives a revenue column, and renames a date column. The output, on the rule-based path, is a single PREPARE recipe with two processor steps (the `revenue` arithmetic is currently handled only on the LLM path covered in Chapter 7). Here is the input:

```python
import pandas as pd

orders = pd.read_csv("orders.csv")
orders["discount_pct"] = orders["discount_pct"].fillna(0.0)
orders["revenue"] = orders["quantity"] * orders["unit_price"] * (1 - orders["discount_pct"])
orders = orders.rename(columns={"order_date": "ordered_at"})
orders_clean = orders
```

The full schema for `orders` is locked down in the running-example contract; for now, treat the column names as given. The next chapter runs this script through `convert(...)` and inspects the resulting flow. The rest of the book extends the same script through four more versions, each adding one new structural operation, until it ends up exercising every recipe type the textbook discusses.

## Further reading

- [Core functions API reference](../api/core-functions.md) — signatures for `convert` and `convert_with_llm`.
- [Models API reference](../api/models.md) — the `DataikuFlow`, `DataikuRecipe`, and `DataikuDataset` classes.
- [Notebook 01 — Beginner](https://github.com/m-deane/py-iku/blob/main/notebooks/01_beginner.ipynb) — the gentlest end-to-end walk-through.
- [Dataiku docs: The Flow](https://doc.dataiku.com/dss/latest/flow/index.html) — DSS's own description of the flow object.

## What's next

Chapter 2 runs the V1 script above through `convert(...)` and inspects the flow that comes out.
