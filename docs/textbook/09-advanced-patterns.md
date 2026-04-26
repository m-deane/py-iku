# Chapter 9 — Advanced Patterns

## What you'll learn

The two structural inferences py-iku makes from local AST patterns: complementary-filter detection (which collapses `df[cond]` and `df[~cond]` into a single SPLIT recipe), and GREL formula compilation (which turns compound predicates and column expressions into formula-driven steps). The chapter walks V5 of the running example and is explicit about the patterns the library does *not* yet detect.

## Two inferences, two antecedents

Most pandas-to-DSS translation is local: each statement maps to one processor or recipe based on its operator and operand types. A few translations are non-local — they depend on a relationship between two statements. py-iku currently makes two such inferences:

- **Complementary-filter detection.** When two boolean indexings on the same DataFrame use complementary conditions, the analyzer collapses them into one SPLIT recipe with two output datasets instead of two FILTER processors with separate output datasets.
- **Compound-predicate compilation.** When a predicate uses bitwise AND/OR or unary negation, the analyzer compiles the AST to a GREL formula and emits a `FilterOnFormula` step (or a SPLIT recipe with a GREL `split_condition`).

Both inferences have explicit antecedents — small theorems that the library can prove from the syntactic shape. Surfacing the antecedents is what makes the tool predictable: a reader who knows which patterns trigger which inference can predict the output flow without running it.

## V5 and complementary-filter detection

V5 of the running example is the canonical case. The pandas:

```python
high_value_customers = orders_ranked[orders_ranked["lifetime_revenue"] >= 1000]
remaining_customers = orders_ranked[orders_ranked["lifetime_revenue"] < 1000]
```

Two filters on `orders_ranked` with predicates `lifetime_revenue >= 1000` and `lifetime_revenue < 1000`. The two outputs together cover every row in the input. py-iku's job is to recognise the partition and emit one SPLIT recipe rather than two PREPARE-with-FILTER recipes.

Run the full V5 pipeline and check the SPLIT recipe specifically:

```python
import pandas as pd
from py2dataiku import convert

source = """
import pandas as pd
orders = pd.read_csv("orders.csv")
orders["discount_pct"] = orders["discount_pct"].fillna(0.0)
orders["revenue"] = orders["quantity"] * orders["unit_price"] * (1 - orders["discount_pct"])
orders_clean = orders.rename(columns={"order_date": "ordered_at"})

customers = pd.read_csv("customers.csv")
products = pd.read_csv("products.csv")
orders_enriched = orders_clean.merge(customers, on="customer_id", how="left")
orders_enriched = orders_enriched.merge(products, on="product_id", how="left")

orders_enriched = orders_enriched.sort_values(["customer_id", "ordered_at"])
orders_windowed = orders_enriched.copy()
orders_windowed["rolling_30d_revenue"] = (
    orders_windowed
    .groupby("customer_id")["revenue"]
    .rolling("30D", on="ordered_at")
    .sum()
    .reset_index(level=0, drop=True)
)

lifetime = orders_windowed.groupby("customer_id")["revenue"].sum().rename("lifetime_revenue")
orders_ranked = orders_windowed.merge(lifetime, on="customer_id", how="left")
orders_ranked = orders_ranked.sort_values("lifetime_revenue", ascending=False)

high_value_customers = orders_ranked[orders_ranked["lifetime_revenue"] >= 1000]
remaining_customers = orders_ranked[orders_ranked["lifetime_revenue"] < 1000]
"""
flow = convert(source)
splits = [r for r in flow.recipes if r.recipe_type.value == "split"]
```

Two assertions worth running on the result:

```python
assert len(splits) == 1, "expected exactly one SPLIT recipe"
split = splits[0]
assert split.inputs == ["orders_ranked"]
assert set(split.outputs) == {"high_value_customers", "remaining_customers"}
```

One SPLIT recipe, one input dataset, two output datasets — the canonical shape for a partitioned filter in DSS.

## The detector's antecedent

The detector — `_merge_complementary_filters` in the AST analyzer — runs as a post-pass over the list of transformations the visitor has produced. Its rule is deliberately narrow:

> Match two consecutive FILTER transformations where the conditions are explicit complements of each other (one wraps the other in a unary `~` or `not`). Replace the pair with a single FILTER carrying `parameters["complementary_outputs"] = [target_a, target_b]`. The flow generator turns that flag into a SPLIT recipe.

What "explicit complement" means in code: the detector compares condition strings after stripping whitespace. If one condition starts with `~` (or `~(`) and the inner expression equals the other condition, they are complements. If both are bare expressions, they are *not* complements — even if they happen to be mathematically opposite.

V5 uses bare comparisons (`>= 1000` and `< 1000`), not `~cond` and `cond`. In current py-iku, the V5 SPLIT detection works because the *condition strings* the analyzer records for the two filters are recognised as complementary by an extended check on the comparison operator pair (`>=` against `<` on the same column with the same boundary value). The textbook reads this as "the explicit-complement rule plus a small extension for mirror-image numeric comparisons on the same column and boundary".

For predicates the detector does not handle — for example, `df[df.x > 100]` and `df[df.x <= 99]`, which are complementary in integer arithmetic but not in float — the two filters stay separate. That conservatism is the whole point: a wrong SPLIT silently drops or duplicates rows; two correct FILTERs are merely verbose.

## Why a single SPLIT is the right shape

The two-FILTER form and the one-SPLIT form are not equivalent in DSS. They differ in three operationally relevant ways:

- **Reads of the input dataset.** Two FILTER recipes each scan `orders_ranked` independently. One SPLIT recipe scans it once and dispatches each row to the matching output. For a large input dataset that doesn't fit in memory, the SPLIT form halves the I/O cost.
- **Number of recipes in the flow.** The SPLIT form has one fewer flow node. A reader scanning the flow visually sees "split into high-value and remaining" rather than "filter for high-value, filter for remaining" — the structural intent is more legible.
- **Cache invalidation.** The two FILTER form has two cache slots, one per output. If `orders_ranked` changes upstream, both must be invalidated. The SPLIT form has one cache slot for the recipe, two for the outputs.

DSS's SPLIT recipe natively supports the partition pattern; the [recipe overview](https://doc.dataiku.com/dss/latest/other_recipes/index.html) lists it under partition-style recipes. The library follows DSS's lead: when the source code expresses a partition, the flow expresses a partition.

## GREL formula generation

The second non-local inference is GREL formula compilation. When a predicate or column expression cannot be expressed by a stock processor, py-iku translates the AST to a GREL string and emits a formula-driven step.

Two cases trigger the path:

- **Compound predicates.** AND/OR/negation combinations of comparisons on possibly different columns. None of `FilterOnValue`, `FilterOnNumericRange`, or `FilterOnMultipleValues` accept a multi-column boolean expression in their params. The fallback is `FilterOnFormula` with a GREL string.
- **Element-wise column expressions that lack a stock processor.** Things like string concatenation across columns, arithmetic with multiple operands, or a conditional value derivation that does not match `IF_THEN_ELSE` or `SWITCH_CASE`. The fallback is `CREATE_COLUMN_WITH_GREL` (or `FORMULA`) with a GREL expression.

### Example: compound predicate

```python
import pandas as pd
from py2dataiku import convert

source = """
import pandas as pd
orders = pd.read_csv("orders.csv")
target = orders[(orders["revenue"] > 100) & (orders["quantity"] < 50)]
"""
flow = convert(source)
recipe = flow.recipes[0]
step = recipe.steps[0]
print(step.processor_type.value)  # 'FilterOnFormula'
print(step.params["formula"])
# '(val("revenue") > 100) && (val("quantity") < 50)'
```

The translator handles the AST nodes that pandas predicates use:

- `ast.Compare` → GREL comparison (`==`, `!=`, `<`, `<=`, `>`, `>=`).
- `ast.BinOp` with `BitAnd` / `BitOr` (pandas's `&` / `|`) → `&&` / `||` with parenthesised operands.
- `ast.UnaryOp` with `Invert` / `Not` → `!(...)`.
- `ast.Call` for `.isin([...])` → expanded `(col == "a") || (col == "b") || ...`.
- `ast.Subscript` for `df["col"]` → `val("col")`.
- `ast.Constant` for literals — strings escape backslashes and quotes; booleans become `true`/`false`; `None` becomes `null`.

The translator returns `None` on any AST shape it does not recognise. Callers treat the `None` as a signal to leave the formula unset rather than emit a wrong one. That is the conservative-failure rule from Chapter 8.

### Example: column expression with multiple operands

```python
source = """
import pandas as pd
customers = pd.read_csv("customers.csv")
customers["full_name"] = customers["first_name"] + " " + customers["last_name"]
"""
flow = convert(source)
recipe = flow.recipes[0]
step = next(s for s in recipe.steps if "full_name" in str(s.params))
# typical params:
# {'column': 'full_name',
#  'expression': 'concat(val("first_name"), " ", val("last_name"))'}
```

A two-operand string concatenation is element-wise but does not have a stock DSS processor; `CONCAT_COLUMNS` exists, but its parameter shape is column-list-only — it cannot insert a literal separator between arbitrary positions. The fallback is a GREL `concat(...)` expression on a `CREATE_COLUMN_WITH_GREL` step. Out-of-running-example schema (`first_name`, `last_name`) is used here because the running-example `customers` table does not have first/last name columns; the principle is unaffected.

## Conditional logic in the source

Python `if` / `else` blocks at module scope are handled in two ways depending on what they assign:

- **Disjoint flow paths.** If each branch produces a different named DataFrame and downstream code references them, the analyzer treats the two branches as independent flow paths. This is rare in production scripts but appears in scripts that toggle a feature with a constant.
- **Formula-driven processors.** A pattern like `df["bucket"] = "high" if df["value"] > 100 else "low"` (which pandas does *not* support directly, but vectorised equivalents like `np.where` are common) becomes an `IF_THEN_ELSE` processor or a GREL formula depending on the operator complexity.

The library does not attempt to detect runtime branching — control flow that depends on data values rather than constant flags. That is properly the job of a Python recipe; py-iku falls back to PYTHON for any AST shape it cannot statically classify.

## Collapsing `df.assign(...)` chains

A pandas idiom that comes up in production code:

```python
df = (
    df
    .assign(revenue=lambda x: x["quantity"] * x["unit_price"])
    .assign(margin=lambda x: x["revenue"] - x["cost"])
    .assign(margin_pct=lambda x: x["margin"] / x["revenue"])
)
```

Three sequential `assign` calls, each adding a column derived from existing columns. The translator unfolds the chain into three column-creation steps inside a single PREPARE recipe — the buffer-and-flush rule from Chapter 5 keeps them together because none of them is structural.

```python
import pandas as pd
from py2dataiku import convert

source = """
import pandas as pd
orders = pd.read_csv("orders.csv")
orders = (
    orders
    .assign(revenue=lambda x: x["quantity"] * x["unit_price"])
    .assign(net_revenue=lambda x: x["revenue"] * (1 - x["discount_pct"]))
)
"""
flow = convert(source)
recipe = flow.recipes[0]
assert recipe.recipe_type.value == "prepare"
print(len(recipe.steps))  # 2
```

The lambda inside `assign` is not arbitrary Python — it is the row-wise expression that the translator parses as it would a column-creation expression. The output is a `CREATE_COLUMN_WITH_GREL` (or `FORMULA`) step per call. If a lambda contains a shape the translator cannot translate (for example, a method call on `x` that does not map cleanly to GREL), the analyzer falls back to a Python recipe for the chain rather than emit an incorrect prepare step.

## What py-iku does not currently detect

The textbook should not over-promise. Two patterns the library does not yet detect, both noted as open items in the project's review log:

- **Complementary filters that are mathematically but not syntactically opposite.** `df[df.x >= 1000]` and `df[df.x < 1000]` are complementary on the integer domain; py-iku's detector currently does not collapse them into a SPLIT (the V5 case works because of the extended numeric-mirror rule, but predicates with different boundary types or off-by-one shifts do not). Two PREPARE recipes are emitted instead. The output is correct, only verbose.
- **Branches with side-effecting code.** A control-flow branch whose body contains anything other than DataFrame assignments — print statements, file writes, environment lookups — defeats the static analysis. The library falls back to a Python recipe for the branch. This is a feature, not a bug: faking a visual recipe for code that has side effects would mislead a flow auditor.

Both gaps are tractable in principle; both are deferred until the detection logic can be tested against a wider corpus without producing false positives. Users who hit either case can write a custom analyzer plugin (Chapter 12) or fall back to the LLM path (Chapter 7), which often spots the partition by reading the intent of the code.

## Theory anchor: small theorems with explicit antecedents

The two inferences in this chapter are not heuristics in the loose sense; they are small theorems with explicit antecedents:

- *Antecedent for complementary-filter detection*: two FILTER transformations on the same source DataFrame, with conditions related by explicit unary negation (or the extended numeric-mirror form on the same column and boundary). *Consequent*: collapse to one SPLIT recipe with two output datasets.
- *Antecedent for GREL formula compilation*: an AST node whose class is one of the supported operators (Compare, BinOp/BitAnd, BinOp/BitOr, UnaryOp/Not, UnaryOp/Invert, Call/isin), and whose operands recursively translate. *Consequent*: emit the GREL string and route to `FilterOnFormula` (for predicates) or `CREATE_COLUMN_WITH_GREL` (for column expressions).

Each antecedent is checkable in code, and the library checks it before applying the inference. Patterns that fail the antecedent get the conservative fallback — two FILTER recipes, or a Python recipe — rather than a guess. That conservatism is the property that makes the library predictable in CI: the same input produces the same output, and the same input never produces a flow that drops or duplicates rows compared to the original pandas script.

## Further reading

- [Models API reference](../api/models.md)
- [Recipe settings API reference](../api/recipe-settings.md)
- [Notebook 05: master patterns](https://github.com/m-deane/py-iku/blob/main/notebooks/05_master.ipynb)
- [Dataiku docs: GREL formula language](https://doc.dataiku.com/dss/latest/formula/index.html)
- [pandas mappings source](https://github.com/m-deane/py-iku/blob/main/py2dataiku/mappings/pandas_mappings.py)

## What's next

Chapter 10 broadens the view from local AST patterns to DAG-aware optimization — when adjacent PREPARE recipes merge, when fan-out blocks the merge, and how the flow graph is walked once per `convert()` call.
