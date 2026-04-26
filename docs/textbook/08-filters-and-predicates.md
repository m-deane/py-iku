# Chapter 8 — Filters and Predicates

## What you'll learn

Why DSS provides three distinct processor types — `FilterOnValue`, `FilterOnNumericRange`, and `FilterOnFormula` — instead of one general-purpose filter, and how py-iku routes each pandas predicate to the correct one based on its operator class. The chapter unpacks the `matchingMode` field on `FilterOnValue` and the GREL escape hatch in `FilterOnFormula` that compound predicates compile to.

## The framing

DSS does not have a single filter processor with a generic operator parameter. It has a family of filter processors, each specialised for one operator class. The three that matter most for translating pandas:

- `FilterOnValue` — string-style match against a value or value list. The `matchingMode` field selects between full-string equality, substring containment, and regex pattern.
- `FilterOnNumericRange` — numeric comparison against a `min`, a `max`, or both. Bounds are inclusive.
- `FilterOnFormula` — a GREL expression that evaluates to a boolean per row. The escape hatch when neither of the above can express the predicate.

The first non-obvious lesson of this chapter: `FilterOnValue.matchingMode` is *not* an operator selector. It does not accept `GREATER_THAN`, `LESS_THAN`, or `EQUALS` in the comparison-operator sense. The canonical values are `FULL_STRING`, `SUBSTRING`, and `PATTERN` — all string-match modes (see [dataiku-api-client-python: recipe.py](https://github.com/dataiku/dataiku-api-client-python/blob/master/dataikuapi/dss/recipe.py) and the processor catalog at [doc.dataiku.com](https://doc.dataiku.com/dss/latest/preparation/processors/index.html)). A predicate like `df["amount"] > 100` cannot be expressed on `FilterOnValue` at all; it requires `FilterOnNumericRange`.

This single architectural fact — distinct processor types for distinct operator classes — drives every routing decision the analyzer makes. It is the load-bearing claim for the rest of the chapter.

## The dispatch

The predicate-to-processor routing lives in `pattern_matcher.match_filter`. The dispatch is by operator class:

- `==` and equality-style operators (`eq`, `equals`, default) → `FILTER_ON_VALUE` with `matchingMode="FULL_STRING"`, `keep=True`.
- `!=` (`ne`, `not_equals`) → `FILTER_ON_VALUE` with `matchingMode="FULL_STRING"`, `keep=False`.
- `in` / `isin` → `FILTER_ON_VALUE` with `matchingMode="FULL_STRING"`, `values` is the list, `keep=True`.
- `contains` / `substring` → `FILTER_ON_VALUE` with `matchingMode="SUBSTRING"`.
- `regex` / `matches` / `pattern` → `FILTER_ON_VALUE` with `matchingMode="PATTERN"`.
- `>`, `>=` (`gt`, `gte`) → `FILTER_ON_NUMERIC_RANGE` with `min` set.
- `<`, `<=` (`lt`, `lte`) → `FILTER_ON_NUMERIC_RANGE` with `max` set.
- `formula` / `expression` / `grel` → `FILTER_ON_FORMULA` with the GREL string.

The dispatch table is exhaustive over single-clause predicates. Compound predicates (AND, OR, negation of compounds) take the formula branch. The wave-7 audit established the mapping by checking each `matchingMode` value against the official client's source — earlier versions of the library had emitted `GREATER_THAN`, `LESS_THAN`, and `IN` strings on `FilterOnValue`, which DSS rejects on import.

## Four predicates, four processors

The cleanest way to internalise the dispatch is to walk four predicates side by side.

### Predicate 1: equality on a string column

```python
import pandas as pd
from py2dataiku import convert

source = """
import pandas as pd
customers = pd.read_csv("customers.csv")
gold_customers = customers[customers["tier"] == "gold"]
"""
flow = convert(source)
recipe = flow.recipes[0]
step = recipe.steps[0]
print(step.processor_type.value)       # 'FilterOnValue'
print(step.params["matchingMode"])     # 'FULL_STRING'
print(step.params["values"])           # ['gold']
print(step.params["keep"])             # True
```

The operator is `==`, the operand is a string literal. The processor is `FilterOnValue`, the matching mode is `FULL_STRING` — DSS performs whole-cell equality and keeps matching rows.

### Predicate 2: numeric comparison

```python
source = """
import pandas as pd
orders = pd.read_csv("orders.csv")
big_orders = orders[orders["revenue"] > 100]
"""
flow = convert(source)
recipe = flow.recipes[0]
step = recipe.steps[0]
print(step.processor_type.value)   # 'FilterOnNumericRange'
print(step.params.get("min"))      # 100
print(step.params.get("max"))      # None / not present
print(step.params["keep"])         # True
```

The operator is `>`. The processor is *not* `FilterOnValue` with some imagined `GREATER_THAN` mode — that would emit invalid DSS JSON. It is `FilterOnNumericRange` with `min=100`. The bound is inclusive at the DSS layer; the strict `>` versus non-strict `>=` distinction is collapsed at this level. The factory's docstring on `filter_on_numeric_range` is explicit: DSS does not natively distinguish strict vs. non-strict at the configuration layer, and a strict `>` is encoded by the same `min` bound that `>=` would use.

### Predicate 3: set membership

```python
source = """
import pandas as pd
customers = pd.read_csv("customers.csv")
ranked = customers[customers["tier"].isin(["gold", "silver"])]
"""
flow = convert(source)
recipe = flow.recipes[0]
step = recipe.steps[0]
print(step.processor_type.value)      # 'FilterOnValue'
print(step.params["values"])          # ['gold', 'silver']
print(step.params["matchingMode"])    # 'FULL_STRING'
```

`isin` becomes `FilterOnValue` with a list of values and `matchingMode="FULL_STRING"`. DSS treats the values as alternatives; a row matches if any element of `values` equals the cell. There is a separate `FILTER_ON_MULTIPLE_VALUES` processor type, but the conventional route for `isin` is the single-processor multi-value form, because it round-trips cleanly through the official client and nests inside a multi-clause filter without complication.

### Predicate 4: substring match

```python
source = """
import pandas as pd
customers = pd.read_csv("customers.csv")
gmail_customers = customers[customers["email"].str.contains("@gmail.com")]
"""
flow = convert(source)
recipe = flow.recipes[0]
step = recipe.steps[0]
print(step.processor_type.value)     # 'FilterOnValue'
print(step.params["matchingMode"])   # 'SUBSTRING'
print(step.params["values"])         # ['@gmail.com']
```

The operator is the `.str.contains` method on a string column. The processor stays at `FilterOnValue` but the matching mode changes to `SUBSTRING`. A regex-style `.str.match` would route the same way with `matchingMode="PATTERN"`. The matching mode is the entire mechanism that distinguishes the three string-match cases inside one processor type.

## Why the matching mode is not an operator

The `FilterOnValue.matchingMode` field is a string-match-style selector; it is not a comparison-operator selector. Calling out the difference:

- `FULL_STRING` says "treat each `values` entry as a whole-cell candidate". The cell either equals one of the candidates or it does not.
- `SUBSTRING` says "treat each `values` entry as a needle to find inside the cell". The cell either contains one of the needles or it does not.
- `PATTERN` says "treat each `values` entry as a regular expression". The cell either matches one of the patterns or it does not.

None of those have a numeric ordering. There is no place in `FilterOnValue` to say "the cell is greater than 100" — that would require an ordering relation, and `FilterOnValue` deliberately does not have one. The right processor for ordered comparison is `FilterOnNumericRange`. Treating `matchingMode` as an operator selector is a category error that produces JSON DSS rejects at import.

The wave-7 finding documented in the project's review log was exactly this: an earlier version of the library used `matchingMode` as if it were an operator selector. Verification against the official client source confirmed only the three string-match values are accepted, and the dispatch was rewritten to route numeric comparisons to `FilterOnNumericRange` instead.

## Multi-clause predicates: the formula branch

Pandas combines predicates with `&` (AND) and `|` (OR), with optional `~` for negation. None of these compose neatly inside a single `FilterOnValue` or `FilterOnNumericRange` step — the parameter shape supports either one column at a time or a single ordered range.

For compound predicates, py-iku translates the AST to GREL and emits a `FilterOnFormula` step.

```python
source = """
import pandas as pd
orders = pd.read_csv("orders.csv")
target = orders[(orders["revenue"] > 100) & (orders["quantity"] < 50)]
"""
flow = convert(source)
recipe = flow.recipes[0]
step = recipe.steps[0]
print(step.processor_type.value)   # 'FilterOnFormula'
print(step.params["formula"])      # something like '(val("revenue") > 100) && (val("quantity") < 50)'
print(step.params["keep"])         # True
```

The translator handles the cases that occur in practice:

- Comparisons: `==`, `!=`, `>`, `>=`, `<`, `<=` map to GREL `==`, `!=`, `>`, `>=`, `<`, `<=`.
- Bitwise AND/OR (pandas's `&` / `|`): map to GREL `&&` / `||` with parenthesised operands.
- Unary `~` and `not`: map to GREL `!(...)`.
- `.isin([...])`: expanded into a chain of `(col == "a") || (col == "b") || ...` clauses.
- Column references: `df["col"]` and `df.col` both translate to `val("col")`.
- String constants: escaped with backslashes and quoted.

The GREL grammar reference is at [doc.dataiku.com](https://doc.dataiku.com/dss/latest/formula/index.html). The translator returns `None` on AST shapes it does not recognise; the caller treats that as a signal to leave the formula unset rather than emit a wrong one. That conservative failure mode is intentional — a wrong filter is worse than a missing one, because it silently drops rows that should have been kept.

The same translator is reused by the SPLIT recipe's condition field, so a complementary filter pair like `df[cond]` / `df[~cond]` produces a SPLIT recipe whose `split_condition` is the GREL form of `cond`. Chapter 9 walks through that detection.

## Why three processors instead of one

A single general-purpose filter that took `(column, operator, value)` would, at first glance, be simpler. DSS chose three. Two practical consequences fall out of the choice and explain why py-iku honours it:

- **Configuration UI maps cleanly to processor type.** `FilterOnValue` opens a "value match" UI with a `matchingMode` toggle. `FilterOnNumericRange` opens a "range" UI with min and max fields. A human reading a flow inspector sees the right widget for the predicate. A unified filter would require a runtime branch on operator class to render the right widget, which is a more brittle UI design.
- **Round-tripping is type-safe at the configuration layer.** Each processor's params dict has a fixed shape with named keys. Validating a configuration is a per-processor schema check rather than a type-and-operator combinatoric check across one large schema. The official client classes mirror this — there is a class per processor type with typed setters.

This chapter does *not* claim that DSS uses different *runtime* implementations for the three processors (a hash-based filter for `FilterOnValue`, a range scan for `FilterOnNumericRange`, an expression interpreter for `FilterOnFormula`). That kind of execution-internals claim would require a primary source from the DSS engine documentation, and none has been verified by the project's review log. The argument here is at the configuration layer only.

## Filter as processor versus filter as recipe

A small detail that frequently confuses readers new to the library: a filter inside a PREPARE recipe (`FILTER_ON_VALUE`, `FILTER_ON_NUMERIC_RANGE`, `FILTER_ON_FORMULA`) is a *processor* — a step inside a 1→1 recipe. A SPLIT recipe is also rooted in filtering, but it is a *recipe* with arity 1→N. The two are not interchangeable.

- A single filter that drops rows and keeps one output dataset is a PREPARE-with-filter-step pattern. The output is a strict subset of the input.
- A pair of filters whose conditions partition the input and whose outputs are both downstream-relevant is a SPLIT pattern. The two outputs together cover the input.

The translator only emits SPLIT when the complementary-filter detector confirms the partition (Chapter 9 covers the antecedent in detail). Without that detection, two complementary filters become two PREPARE recipes — semantically correct but wasteful, since SPLIT does the same thing in one node.

## What py-iku does not do

The translator is conservative on purpose. Two cases it deliberately punts on:

- **Strict vs. non-strict at the DSS layer.** A predicate `df["x"] > 5` and `df["x"] >= 5` produce the same `FilterOnNumericRange` configuration with `min=5`. DSS's range bounds are inclusive, and emitting an "almost equal" bound on a float would be semantically suspect. The rule-based path accepts the boundary collapse; the LLM path can opt for a `FilterOnFormula` with explicit `> 5` to preserve strictness.
- **Inferred complementarity from value comparisons.** `df[df.x >= 1000]` and `df[df.x < 1000]` are mathematically complementary, but the detector currently only recognises the explicit `~cond` form. Inferring complementarity from value comparisons risks false positives when the two predicates differ in subtle ways (open versus closed bounds, integer versus float comparison). The conservative choice is to not collapse them — they end up as two PREPARE recipes rather than one SPLIT, which is correct if not optimal.

Both cases are documented in the project's review log under "outstanding items" and are candidates for a future revision. The textbook surfaces them so users do not over-promise the library to their teams.

## Theory anchor: distinct processor types for distinct operator classes

The framing repeated through the chapter:

- DSS exposes a family of filter processors, each specialised for one operator class.
- `FilterOnValue.matchingMode` is *not* an operator selector — its values (`FULL_STRING`, `SUBSTRING`, `PATTERN`) are all string-match modes.
- Numeric comparison is a separate processor (`FilterOnNumericRange`) with its own configuration shape.
- Compound predicates compile to a GREL formula on `FilterOnFormula`.
- Conflating the three at the configuration layer produces invalid DSS JSON.

The translator's job is to read the AST, classify the operator, and route to the right processor type. Once the routing is in place, every predicate the library handles falls out of the dispatch table without further special cases. The three-way split is the entire abstraction.

## Further reading

- [Models API reference](../api/models.md)
- [Notebook 04: expert filters and predicates](https://github.com/m-deane/py-iku/blob/main/notebooks/04_expert.ipynb)
- [Dataiku docs: GREL formula language](https://doc.dataiku.com/dss/latest/formula/index.html)
- [dataiku-api-client-python: recipe.py](https://github.com/dataiku/dataiku-api-client-python/blob/master/dataikuapi/dss/recipe.py)

## What's next

Chapter 9 picks up the SPLIT detection thread, walks through V5 of the running example, and covers the GREL formula generation that power compound-predicate flows.
