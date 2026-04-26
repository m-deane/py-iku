# Chapter 4 — pandas-to-DSS Grammar

## What you'll learn

This chapter states the translation grammar that py-iku uses to map pandas idioms to DSS recipes and processors. By the end of it, you will know the structural-versus-element-wise rule the rule-based analyzer applies, the reference table of common pandas idioms and their py-iku targets, and the special cases that later chapters cover in depth.

## The translation problem

pandas is an imperative DSL over a single in-memory dataframe. Each statement reads or writes columns of the dataframe and the next statement runs against whatever the previous statement left behind. The dataframe is a single mutable object; the call graph is implicit in the order of the lines and the local variable names.

DSS is a declarative DAG over named datasets. Each recipe declares its inputs, outputs, and configuration; the call graph is explicit in the dataset names. The DSS server reads the configuration and runs each recipe as its own scheduled job.

Translating one to the other is not a syntactic substitution. The two languages do not have a one-to-one mapping at the line level. A line of pandas can map to a step inside an existing recipe, a new recipe, or no recipe at all (if it is consumed by a later structural operation). The translator's job is to look at each line in the *context of its neighbours*, decide whether it is structural or element-wise, and route it to the right place.

The rule py-iku uses is the structural-versus-element-wise rule. It is not the only possible rule, but it is the rule the rest of this chapter — and the rest of the book — assumes.

## The rule

A pandas operation is **structural** if it changes the shape of the dataframe in a way that DSS encodes as a separate recipe type. Examples: `df.merge(other)`, `df.groupby(...).agg(...)`, `pd.concat([df1, df2])`, `df.sort_values(...)`, `df.nlargest(n, col)`, `df.rolling(...)`, `df[condition]` when the condition is also used to derive a complementary partition.

A pandas operation is **element-wise** if it transforms columns within a single dataframe shape without changing the input/output arity. Examples: `df.rename(...)`, `df.fillna(...)`, `df["col"] = expr`, `df.astype({...})`, `df["col"].str.lower()`, `df.round(...)`, `df["col"].clip(0, 1)`.

Structural operations become their own recipes — one recipe per structural operation, with the input and output arities the recipe type defines. Element-wise operations become processor steps inside a PREPARE recipe, with adjacent element-wise operations merged into a single PREPARE.

The rule has two corollaries that fall out for free:

1. A run of N consecutive element-wise operations on the same dataframe produces one PREPARE recipe with N processor steps, not N PREPARE recipes with one step each. The optimizer pass enforces this even when the analyzer emits separate PREPAREs (Chapter 10).
2. A structural operation never absorbs an element-wise operation that runs on a different dataframe. If line K is `df = df.merge(other)` and line K+1 is `other = other.fillna(0)`, the element-wise operation is on `other`, not on the merge output, and it routes to a separate PREPARE that feeds the merge.

The rule is not perfect. A few pandas idioms straddle the boundary, and the next section covers the non-obvious cases. But the rule is what to apply *first* when reading new code.

## V2 in the grammar

V2 of the running example is V1 plus two `merge(...)` calls. Here is the V2 source:

```python
# running_example_v2.py
import pandas as pd

orders = pd.read_csv("orders.csv")
orders["discount_pct"] = orders["discount_pct"].fillna(0.0)
orders["revenue"] = orders["quantity"] * orders["unit_price"] * (1 - orders["discount_pct"])
orders = orders.rename(columns={"order_date": "ordered_at"})
orders_clean = orders

customers = pd.read_csv("customers.csv")
products = pd.read_csv("products.csv")
orders_enriched = orders_clean.merge(customers, on="customer_id", how="left")
orders_enriched = orders_enriched.merge(products, on="product_id", how="left")
```

Apply the rule line by line. The first three operations on `orders` (`fillna`, derived column, `rename`) are element-wise; they merge into one PREPARE. The two `merge(...)` calls are structural — they take two dataframes and produce one — and they route to JOIN recipes.

The conversion produces this:

```python
from py2dataiku import convert, RecipeType

source = open("running_example_v2.py").read()
flow = convert(source)

print(len(flow.recipes))
# 3

print([r.recipe_type.value for r in flow.recipes])
# ['prepare', 'join', 'join']

print([d.name for d in flow.datasets])
# ['orders', 'orders_prepared_prepared', 'customers', 'products', '', 'orders_enriched']
```

V2 is three recipes — one PREPARE and two JOINs — even after the default optimizer pass. The current optimizer collapses adjacent PREPAREs but does not (yet) fuse the two JOINs into a single multi-clause JOIN; that is a planned optimization rather than the present behaviour. The running-example contract documents both shapes (two-recipe and three-recipe) as acceptable, and what `convert()` returns today is the three-recipe shape.

If you want the fully unoptimized shape — useful for debugging or for building a flow where each PREPARE/JOIN runs on a different engine — pass `optimize=False`:

```python
unoptimized = convert(source, optimize=False)
print(len(unoptimized.recipes))
# 4
print([r.recipe_type.value for r in unoptimized.recipes])
# ['prepare', 'prepare', 'join', 'join']
```

The unoptimized shape has four recipes: two PREPAREs (the analyzer initially emits one per element-wise run before merging) and two JOINs for the two merges. The optimizer pass collapses the two adjacent PREPAREs into one because they share the same single edge with no fan-out; that is the merging rule that lifts the count from four to three. Chapter 10 walks the optimizer's full set of merging rules.

## The reference table

The table below is the canonical mapping the rule-based analyzer applies. The source-of-truth for the table is [`mappings/pandas_mappings.py`](https://github.com/dataiku/py-iku/blob/main/py2dataiku/mappings/pandas_mappings.py); this is the human-readable summary.

### Structural pandas → recipe types

| pandas idiom                                | py-iku recipe type | Arity |
|---------------------------------------------|--------------------|-------|
| `df.merge(other, on=..., how=...)`          | `JOIN`             | 2 → 1 |
| `pd.merge(df, other, on=...)`               | `JOIN`             | 2 → 1 |
| `df.groupby(...).agg(...)`                  | `GROUPING`         | 1 → 1 |
| `df.groupby(...).sum()` / `.mean()` / etc.  | `GROUPING`         | 1 → 1 |
| `pd.concat([df1, df2, ...], axis=0)`        | `STACK`            | N → 1 |
| `df.sort_values(...)`                       | `SORT`             | 1 → 1 |
| `df.nlargest(n, col)` / `df.nsmallest(...)` | `TOP_N`            | 1 → 1 |
| `df.rolling(...).agg(...)`                  | `WINDOW`           | 1 → 1 |
| `df.cumsum()` / `df.cumprod()` / `.expanding()` | `WINDOW`       | 1 → 1 |
| `df.drop_duplicates(...)`                   | `DISTINCT`         | 1 → 1 |
| `df[cond1]` and `df[~cond1]` (complementary)| `SPLIT`            | 1 → 2 |
| `df[cond]` (standalone)                     | `FILTER` processor inside PREPARE | 1 → 1 |
| `df.melt(...)`                              | PREPARE with `FOLD_MULTIPLE_COLUMNS` | 1 → 1 |
| `df.pivot(...)` / `df.pivot_table(...)`     | `PIVOT`            | 1 → 1 |

### Element-wise pandas → processors inside PREPARE

| pandas idiom                                | py-iku processor type   |
|---------------------------------------------|-------------------------|
| `df.rename(columns={...})`                  | `ColumnRenamer`         |
| `df.fillna({...})` / `df["c"].fillna(v)`    | `FillEmptyWithValue`    |
| `df.dropna(subset=...)`                     | `RemoveRowsOnEmpty`     |
| `df.drop(columns=...)`                      | `ColumnsSelector` (use `keep=False`) |
| `df.astype({...})`                          | `TypeSetter`            |
| `df["c"] = expr` (arithmetic)               | `CreateColumnWithGREL`  |
| `df["c"].str.lower()` / `.upper()` / etc.   | `StringTransformer`     |
| `df["c"].str.strip()` / `.replace(...)`     | `StringTransformer`     |
| `df["c"].str.contains(...)`                 | `FilterOnRegex` (predicate) |
| `df["c"].round(n)` / `.abs()` / `.clip(...)`| `NumericalTransformer`  |
| `df["c"] == v` (equality predicate)         | `FilterOnValue`         |
| `df["c"] > v` / `< v` (numeric range)       | `FilterOnNumericRange`|
| `df["c"].isin([...])`                       | `FilterOnValue` (multi) |
| `pd.to_datetime(df["c"])`                   | `DateParser`            |
| `df["c"].dt.year` / `.dt.month`             | `DateComponentExtractor`|

### The non-obvious cases

These are the mappings most likely to surprise readers coming from pure pandas.

- `df.melt(...)` does **not** become its own recipe type. It becomes a PREPARE recipe with a `FOLD_MULTIPLE_COLUMNS` processor. This is consistent with DSS's own handling: melt-like reshaping is a column-level operation, not a structural one (see [Dataiku docs: Visual recipes](https://doc.dataiku.com/dss/latest/preparation/index.html)).
- `df[condition]` is **context-dependent**. A standalone filter (one branch only, used as the input to the next step) becomes a `FILTER` processor inside PREPARE. A pair of complementary filters on the same column (`df[col >= 1000]` and `df[col < 1000]`) becomes a single SPLIT recipe with two output branches. Detecting complementarity is the subject of Chapter 9.
- `df.rolling(...)`, `df.cumsum()`, `df.cumprod()`, and `df.expanding()` all become a WINDOW recipe with the corresponding aggregation. The frame specification on the WINDOW recipe is what differs between them.
- `df.nlargest(n, col)` and `df.nsmallest(n, col)` become a `TOP_N` recipe, not a SORT-then-LIMIT. DSS has a dedicated TOP_N type because it pushes the operation down to engines that have a native TOP-N (most SQL engines do); reshaping it as SORT+LIMIT would defeat that.
- `df.round(...)`, `df.abs()`, `df.clip(...)` are element-wise numeric transforms and become `NumericalTransformer` processors. They are not structural even though they look like aggregation on first read.
- A `df["c"] = df["a"] + df["b"]` assignment becomes one `CreateColumnWithGREL` step with the GREL expression `numval(a) + numval(b)`. Three such assignments in a row do not become three recipes; they become three steps inside one PREPARE.

The full list of mappings, including the long tail of less-frequent processors, is in `py2dataiku/mappings/pandas_mappings.py`. The rule-based analyzer reads the table at `import` time; adding a new mapping is the recipe documented in `CLAUDE.md` under "Adding New Recipe Types".

## Why some pandas patterns produce different flows

The same pandas operation can produce different flow shapes depending on what surrounds it. Two examples make the contextual rule concrete.

### Example 1: filter is sometimes a processor, sometimes a recipe

```python
# Standalone filter — element-wise, becomes a FILTER processor inside PREPARE
df_a = df[df["country"] == "US"]
df_a["normalized_country"] = "USA"
```

Out-of-running-example schema (`country`, `normalized_country`) is used here because the running-example `customers` table does not carry a country column; the principle is unaffected.

```python
# Complementary filter pair — structural, becomes a SPLIT recipe
high = df[df["lifetime_revenue"] >= 1000]
low = df[df["lifetime_revenue"] < 1000]
```

In the first script, `df[...]` is followed by another element-wise operation on the filter result. The translator emits a single PREPARE with a `FilterOnValue` step and a `CreateColumnWithGREL` step. In the second script, the same column is filtered twice on complementary predicates and both branches feed independent downstream nodes; the translator emits a single SPLIT recipe with two output datasets. The pandas syntax is similar in both cases, but the *context* — what surrounds the filter — drives the shape.

### Example 2: rename versus rename-inside-merge

```python
# Two operations: PREPARE with one ColumnRenamer, then JOIN
orders = orders.rename(columns={"order_date": "ordered_at"})
orders_enriched = orders.merge(customers, on="customer_id")
```

```python
# One operation: JOIN with a renamed-column suffix on the join output
orders_enriched = orders.merge(customers, on="customer_id", suffixes=("_o", "_c"))
```

Both scripts produce a JOIN recipe, but the first also produces a PREPARE recipe upstream of it. Whether to fold the rename into the JOIN's output schema or keep it as its own step is a translator choice; py-iku keeps it as its own step because that matches the script's structure and because the renamed column might be referenced by other downstream recipes that do not see the JOIN.

This is the general lesson. A grammar that maps pandas to DSS line-by-line is too local. The translator has to look at the immediate neighbours of each line, recognise the structural-versus-element-wise classification in context, and emit the recipe that reflects what the script *does* rather than what it *says*.

## What gets the LLM path

The rule-based analyzer is a fixed pattern table. Code that does not match a pattern in the table either falls back to a `PYTHON` recipe (a flow node that wraps the offending script) or raises `InvalidPythonCodeError`. Both outcomes preserve correctness — the flow either runs the original Python or refuses to convert — but both lose the lineage and audit properties that motivated the conversion in the first place.

The LLM-based analyzer is for the cases the rule-based path cannot classify. Code with conditional logic, code that uses `df.pipe(custom_fn)`, code that mixes pandas with non-pandas libraries, and code that uses a pandas idiom the rule table does not know about — all of these go to the LLM path more cleanly than to the rule-based path. The LLM reads the script, identifies each transformation in the same structural-versus-element-wise vocabulary, and emits the same kind of analysis result the rule-based path emits. Chapter 7 walks the LLM path in detail.

The grammar this chapter describes applies to *both* paths. The LLM is given the same mapping rules in its system prompt; both paths produce a `DataikuFlow` whose recipes follow the same structural-versus-element-wise convention. The LLM is not a different grammar — it is a more flexible *parser* against the same grammar.

## What this chapter leaves out

Three special cases get dedicated chapters because they are too involved to fit here.

- **Filter predicates** (Chapter 8). The line `df[df["c"] == "x"]` becomes one of `FilterOnValue`, `FilterOnNumericRange`, `FilterOnRegex`, `FilterOnEmpty`, or several others depending on the predicate's operator and operand types. The chapter walks the routing logic.
- **Complementary splits** (Chapter 9). The detection that turns two filters on `>= 1000` and `< 1000` into a single SPLIT recipe is a small theorem with a specific antecedent; the chapter states the theorem and its limits.
- **Optimizer merging** (Chapter 10). The pass that turns three sequential PREPAREs into one PREPARE-with-three-steps, and that turns two adjacent JOINs into one multi-clause JOIN, runs after the analyzer and is DAG-aware: it does not merge across fan-outs because doing so would change semantics.

Each of these cases shows up as a forward reference elsewhere in the book. The mapping tables above are correct as-is; the chapters listed deepen them with cases that need more than a table row to explain.

## Further reading

- [Models API reference](../api/models.md) — `RecipeType`, `ProcessorType`, recipe settings.
- [Core functions API reference](../api/core-functions.md) — `convert(source, optimize=...)`.
- [Notebook 02 — Intermediate](https://github.com/m-deane/py-iku/blob/main/notebooks/02_intermediate.ipynb) — runs through V2 and V3 of the running example.

## What's next

Chapter 5 takes a deeper look at PREPARE recipes — the sequence-of-processor-steps recipe type that every flow this book builds uses at least once.
