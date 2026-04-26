# Chapter 10 — Optimization and the DAG

## What you'll learn

This chapter explains how `FlowOptimizer` rewrites a freshly-generated flow to fold redundant [recipes](appendix-a-glossary.md#recipe) together, why those rewrites are graph operations rather than list operations, and which structural property of the flow — the fan-out count of an intermediate [dataset](appendix-a-glossary.md#dataset) — decides whether two recipes can merge. The chapter walks through the two merge passes (PREPARE and [WINDOW](appendix-a-glossary.md#window)) on the running example, including the case where the [optimizer](appendix-a-glossary.md#optimizer) correctly leaves recipes alone.

Plugins compose with the optimizer — see Chapter 12 for how custom recipe handlers participate (or don't) in merge passes.

## What the optimizer is for

`FlowGenerator` and `LLMFlowGenerator` produce flows by walking the source one statement at a time. Every statement that maps to a structural recipe yields a recipe; every statement that maps to a prepare step yields a prepare step inside its own one-step PREPARE recipe. The result is correct but verbose: a script with three consecutive `df = df.fillna(...)` / `df = df.rename(...)` / `df["x"] = df["y"] * 2` lines produces three PREPARE recipes feeding one another, when one PREPARE recipe with three steps would describe the same computation.

The optimizer's job is to recover the more compact shape without changing the flow's semantics. It runs once per `convert()` call (controlled by the `optimize=True` argument), it operates over the post-generation `DataikuFlow`, and it mutates the flow in place. The output is the same flow object with fewer recipes, fewer intermediate datasets, and a populated `flow.optimization_notes` log. The implementation lives in [`py2dataiku/optimizer/flow_optimizer.py`](https://github.com/m-deane/py-iku/blob/main/py2dataiku/optimizer/flow_optimizer.py); the merge predicates are factored out into [`py2dataiku/optimizer/recipe_merger.py`](https://github.com/m-deane/py-iku/blob/main/py2dataiku/optimizer/recipe_merger.py).

The pass is deliberately conservative. It does not push filters earlier (Chapter 8 covers why filter ordering is observable, not merely an optimization hint), it does not reorder recipes across structural boundaries, and it does not touch the contents of any recipe except to concatenate prepare-step lists when merging. Anything more aggressive would risk changing the output [schema](appendix-a-glossary.md#schema) of an intermediate dataset in a way a downstream consumer can observe.

## The optimizer is a graph rewrite, not a list scan

The earliest version of the merge logic was a list scan: walk `flow.recipes` and merge `recipes[i]` with `recipes[i+1]` if both were PREPARE and the output of `i` matched the input of `i+1`. That works for linear scripts, but it fails the moment two PREPARE recipes are mergeable yet not adjacent in the recipe list — for example, if the LLM analyzer happens to emit them in a different order than the rule-based generator does, or if a topologically-unrelated recipe sits between them in `flow.recipes`.

The current implementation is graph-aware. `_find_merge_pair` builds a map from each dataset name to the list of recipe indices that consume it, then iterates candidate `recipe1` recipes and asks: which downstream recipe — by dataset edge, regardless of list position — is also a merge candidate? The lookup is O(V+E) over the flow graph and runs once per optimization pass.

The shape of the lookup is what makes the rest of the chapter's rules expressible:

```python
consumers: dict[str, list[int]] = {}
for idx, r in enumerate(flow.recipes):
    for inp in r.inputs:
        consumers.setdefault(inp, []).append(idx)

for i, recipe1 in enumerate(flow.recipes):
    output_name = recipe1.outputs[0]
    downstream_indices = consumers.get(output_name, [])
    if len(downstream_indices) != 1:
        continue  # fan-out — see below
    j = downstream_indices[0]
    # ... check recipe2 for mergeability
```

The `len(downstream_indices) != 1` check is the fan-out guard. It is what makes the rule-rewrite safe regardless of where in the recipe list the candidate sits.

## The fan-out guard

Two PREPARE recipes on a linear path are equivalent to one combined PREPARE: every prepare step is pure with respect to the dataset (it does not read external state), the merged recipe sees the same inputs and produces the same outputs, and any dataset between them is intermediate.

The same is not true across a fan-out. Suppose `recipe1` is a PREPARE that produces `cleaned_orders`, and two downstream recipes — `recipe2` (a [JOIN](appendix-a-glossary.md#join)) and `recipe3` (a [SPLIT](appendix-a-glossary.md#split)) — both consume `cleaned_orders`. Merging `recipe1` into `recipe2` would absorb the prepare steps into the JOIN's input pipeline, but `recipe3` still expects to read `cleaned_orders` as its own input.

The merge would either change `recipe3`'s input to a name that no longer exists, or it would leave `cleaned_orders` orphaned with the prepare steps no longer running before `recipe3` consumes it. Either way, the flow is no longer equivalent to the input.

The guard is one line: `if len(downstream_indices) != 1: continue`. It refuses to merge whenever the intermediate dataset has more than one consumer. The library would rather leave a redundant recipe in place than emit an unsound flow.

A worked example. Consider a small extension to V1 of the running example where `orders_clean` feeds two structural recipes — a JOIN with `customers` and a row-filter SPLIT — so the intermediate dataset has two consumers:

```python
import pandas as pd
from py2dataiku import convert

source = """
import pandas as pd
orders = pd.read_csv('orders.csv')
customers = pd.read_csv('customers.csv')
orders['discount_pct'] = orders['discount_pct'].fillna(0.0)
orders['revenue'] = orders['quantity'] * orders['unit_price'] * (1 - orders['discount_pct'])
orders_clean = orders

# Two downstream consumers of orders_clean — fan-out via structural recipes:
enriched = orders_clean.merge(customers, on='customer_id', how='left')
high_value = orders_clean[orders_clean.revenue > 1000]
"""

flow = convert(source)
recipe_types = [r.recipe_type.value for r in flow.recipes]
# The PREPARE that produces orders_clean cannot fold into either downstream
# recipe because orders_clean fans out to two consumers. The flow keeps three
# distinct recipes: PREPARE, JOIN, SPLIT.
assert recipe_types == ["prepare", "join", "split"]
```

Without fan-out, the chained PREPARE steps would collapse into one. With it, the PREPARE recipe survives because it has more than one downstream consumer — the JOIN and the SPLIT each read `orders_clean` directly. The recipe-type sequence is the diagnostic.

## Merging PREPARE recipes

`_apply_merge_prepare_recipes` walks the flow and applies one merge at a time, restarting the scan after each merge so that newly-formed PREPARE recipes can themselves participate in further merges. The eligibility check is `RecipeMerger.can_merge_prepare`: both recipes must be PREPARE, `recipe1.outputs[0]` must equal `recipe2.inputs[0]`, and (from the optimizer side) `recipe2.inputs` must be exactly `[recipe1.outputs[0]]` so that absorbing the input does not change `recipe2`'s input set.

The merge itself is a list concatenation. `RecipeMerger.merge_prepare_recipes` builds a new PREPARE recipe whose `steps` is the concatenation of the input recipes' steps, whose `inputs` is `recipes[0].inputs`, and whose `outputs` is `recipes[-1].outputs`. The intermediate dataset between them is dropped from `flow.datasets` if no other recipe still references it.

V1 of the running example exercises this directly. The three element-wise lines (`fillna`, `assign revenue`, `rename`) generate three PREPARE recipes pre-optimization; the optimizer folds them into one:

```python
from py2dataiku import convert

# V1 of the running example (see _running_example.md).
v1 = """
import pandas as pd
orders = pd.read_csv('orders.csv')
orders['discount_pct'] = orders['discount_pct'].fillna(0.0)
orders['revenue'] = orders['quantity'] * orders['unit_price'] * (1 - orders['discount_pct'])
orders = orders.rename(columns={'order_date': 'ordered_at'})
orders_clean = orders
"""

# Convert without optimization to see the pre-optimization shape.
flow_raw = convert(v1, optimize=False)
assert sum(1 for r in flow_raw.recipes if r.recipe_type.value == "prepare") >= 1

# Convert with optimization (default) to see the merged shape.
flow_opt = convert(v1)
prepare_recipes = [r for r in flow_opt.recipes if r.recipe_type.value == "prepare"]
assert len(prepare_recipes) == 1
assert len(prepare_recipes[0].steps) >= 3
```

`flow.optimization_notes` records each merge as a one-line entry: `"Merged 'prepare_1' + 'prepare_2' -> 'prepare_merged_prepare_1'"` followed by `"Removed intermediate dataset 'orders_step_2'"`.

## Step ordering inside the merged PREPARE

Step order within a PREPARE recipe is observable. `COLUMN_RENAMER` after `FILL_EMPTY_WITH_VALUE` references the pre-rename column name; the same two steps in the opposite order reference the post-rename name. The optimizer does not reorder prepare steps as part of the merge — it concatenates them in source order — but `RecipeMerger.optimize_prepare_steps` is available as a separate, opt-in pass that applies a deterministic ordering rule to a list of steps:

```python
# From RecipeMerger.optimize_prepare_steps:
return deletions + type_setters + row_filters + other + renames
```

The five-bucket ordering is:

1. **Column deletions first.** `COLUMN_DELETER` reduces the schema before any later step can refer to the deleted columns.
2. **Type setters next.** `TYPE_SETTER` ensures downstream numeric or date operations see the right type.
3. **Row filters.** `FILTER_ON_VALUE`, `REMOVE_ROWS_ON_EMPTY`, `REMOVE_DUPLICATES` reduce row count before any per-row computation.
4. **Other steps.** Everything else — `FILL_EMPTY_WITH_VALUE`, `NUMERIC_TRANSFORM`, `STRING_TRANSFORMER`, formula steps — runs in the middle.
5. **Renames last.** `COLUMN_RENAMER` is deferred so that earlier steps reference the original column names.

The rule is not applied automatically. A caller can opt into it after a merge, but the default `_apply_merge_prepare_recipes` preserves source order because the rule is correct only when each step refers to columns rather than to the schema as a whole. A formula step that references the renamed column name will not be re-ordered correctly by this rule; it is the caller's responsibility to know whether their steps are commutable.

## Merging WINDOW recipes

WINDOW merging is the second pass and the more interesting one structurally. Two WINDOW recipes are mergeable when they share the same input dataset, the same `partition_columns`, and the same `order_columns` — in other words, when they describe the same window frame and differ only in the [aggregations](appendix-a-glossary.md#aggregation) they compute. The merged recipe carries the union of both recipes' `window_aggregations`.

The function recognizes two cases:

- **Chained.** `recipe1.outputs[0] == recipe2.inputs[0]` — the second window reads the first's output. Subject to the same fan-out guard as the PREPARE case.
- **Sibling.** Both recipes read from the same input dataset but are not chained. The fan-out guard does not apply here because the shared input keeps its identity after merge; what matters is that no downstream recipe is reading the absorbed `recipe1` output before the merge.

V3 of the running example contains exactly one WINDOW recipe — the rolling 30-day revenue sum [partitioned](appendix-a-glossary.md#partition) by `customer_id` and ordered by `ordered_at`. If a script computed two such windows over the same partitioning and ordering — say a 30-day sum and a 30-day mean — the WINDOW merger would fold them into a single recipe with both aggregations:

```python
from py2dataiku import convert

source = """
import pandas as pd
orders = pd.read_csv('orders.csv')
orders = orders.rename(columns={'order_date': 'ordered_at'})
orders = orders.sort_values(['customer_id', 'ordered_at'])
orders['rolling_30d_sum'] = (
    orders.groupby('customer_id')['revenue']
          .rolling('30D', on='ordered_at').sum()
          .reset_index(level=0, drop=True)
)
orders['rolling_30d_mean'] = (
    orders.groupby('customer_id')['revenue']
          .rolling('30D', on='ordered_at').mean()
          .reset_index(level=0, drop=True)
)
"""

flow = convert(source)
windows = [r for r in flow.recipes if r.recipe_type.value == "window"]
# Two compatible WINDOW expressions over identical partitioning/ordering merge.
assert len(windows) == 1
assert len(windows[0].window_aggregations) == 2
```

If the second window had a different partition (`groupby('country')`) or a different order column, the merge would not fire and the flow would carry two WINDOW recipes.

## Inspecting an optimization pass

`flow.optimization_notes` is the cheapest way to see what the optimizer did. It is a list of strings appended in pass order:

```python
from py2dataiku import convert

flow = convert(v1)
for note in flow.optimization_notes:
    print(note)
# Merged 'prepare_1' + 'prepare_2' -> 'prepare_merged_prepare_1'
# Removed intermediate dataset 'orders_step_2'
# Merged 'prepare_merged_prepare_1' + 'prepare_3' -> 'prepare_merged_prepare_merged_prepare_1'
# Removed intermediate dataset 'orders_step_3'
```

The merge log is informational. The optimizer does not raise on a no-op pass; if no merges fire, the log is empty and `len(flow.recipes)` is unchanged. A test that expects a specific recipe count after `convert()` is asserting against the post-optimization flow by default; passing `optimize=False` to `convert()` returns the pre-optimization shape.

## Cost and termination

The optimization pass is O(V+E) over the flow graph for the consumer-map build, plus one pass per merge. Each merge is constant-time (the per-recipe field copies are O(steps)), and the loop terminates when no further merge candidate exists. For the running example V1 through V5, the optimizer fires between zero (V2 — the JOIN cannot merge with anything) and three times (V1's three PREPARE recipes folding into one).

There is no `_identify_parallel_branches` work to be aware of — that method is a no-op stub in the current code, kept only so callers that imported it don't break. The earlier implementation was an O(R^2 * D) hot path that did no useful work and dominated conversion time on large flows; removing it cut conversion time to negligible on a 100-recipe flow.

## What the optimizer does not do

For clarity:

- It does not push filters earlier in the flow. `_push_filters_early` only emits a recommendation in `flow.recommendations`; it does not rewrite the flow.
- It does not eliminate dead recipes whose outputs no consumer reads. Orphan dataset removal is in scope (`_apply_remove_orphan_datasets`); orphan recipe removal is not.
- It does not coalesce non-WINDOW non-PREPARE recipes. Two consecutive [SORT](appendix-a-glossary.md#sort) recipes, for example, will not merge — the optimizer has no rule for that case, and the right rewrite is conditional on whether the second SORT's keys are a prefix of the first's, which is a non-trivial check.

The point of leaving these out is that the optimizer is the most-trusted component of the pipeline: every flow that comes out of `convert()` has been through it.

A cautious set of rewrites is more useful than an aggressive one, because the production reader cares more about "this flow does what the source does" than about "this flow has the minimum possible recipe count."

## Further reading

- [Glossary](appendix-a-glossary.md)
- [Cheatsheet: determinism knobs](appendix-c-cheatsheet.md)
- [Graph and FlowGraph API reference](../api/graph.md)
- [Recipe settings API reference](../api/recipe-settings.md)
- [Notebook 04: expert patterns](https://github.com/m-deane/py-iku/blob/main/notebooks/04_expert.ipynb)

## What's next

Chapter 11 turns to wiring `convert()` into a real pipeline — CI assertions, cost monitoring, and the credentials-safe runner pattern.
