# Chapter 6 — Recipe Types Tour

## What you'll learn

This chapter shows how the eight most common non-PREPARE recipe types behave as algebraic primitives over datasets — what each one's input and output arity is, what pandas idiom triggers it, and how the running example walks through GROUPING, JOIN, WINDOW, SORT, and SPLIT as it grows from V2 to V5. By the end, you can read a recipe type off a pandas snippet without running `convert()`.

## Recipes as primitives

Each non-PREPARE recipe type is a small algebra over datasets: it takes a fixed number of inputs, produces a fixed number of outputs, and applies one well-defined transformation. The DSS visual flow is a composition of these primitives — the visual recipe overview at [doc.dataiku.com](https://doc.dataiku.com/dss/latest/other_recipes/index.html) lists them with their input/output arities and configuration UIs.

Reading a flow becomes reading a sequence of arities:

| Recipe type | In  | Out | Effect on rows                    | Effect on columns                |
|-------------|-----|-----|-----------------------------------|----------------------------------|
| GROUPING    | 1   | 1   | reduces (group key cardinality)   | aggregations replace value cols  |
| JOIN        | 2..N| 1   | preserves or expands              | union of selected columns        |
| STACK       | 2..N| 1   | sums (concatenation)              | union (or intersection) of cols  |
| WINDOW      | 1   | 1   | preserves                         | adds derived per-row columns     |
| SORT        | 1   | 1   | permutes                          | unchanged                        |
| DISTINCT    | 1   | 1   | reduces (drops duplicates)        | unchanged                        |
| TOP_N       | 1   | 1   | reduces (keeps top K)             | unchanged                        |
| SPLIT       | 1   | 2..N| partitions                        | unchanged in each branch         |

The arity pinning is the entire reason these are recipes and not processors. A processor inside a PREPARE recipe is implicitly 1→1 over rows; if an operation changes cardinality structurally (groupby reduces, split partitions, stack sums), it cannot live inside PREPARE. The recipe layer is where cardinality changes happen.

The recipe-creator class hierarchy on the DSS side — `GroupingRecipeCreator`, `JoinRecipeCreator`, `WindowRecipeCreator`, and so on — encodes the same arity rules (see [dataiku-api-client-python: recipe.py](https://github.com/dataiku/dataiku-api-client-python/blob/master/dataikuapi/dss/recipe.py)). py-iku's `RecipeType` enum mirrors that hierarchy directly.

## V2: introducing JOIN

The V2 block of the running example adds two `merge` calls:

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
"""
flow = convert(source)
types = [r.recipe_type.value for r in flow.recipes]
print(types)  # ['prepare', 'join'] or ['prepare', 'join', 'join']
```

Two acceptable shapes per `_running_example.md`: a single multi-input JOIN with two join clauses, or a chain of two JOINs. Both are valid; this chapter assumes the chained form because it is what the rule-based path produces today.

The JOIN recipe takes 2→1: two input datasets, one output dataset, parameterised by a list of `JoinKey` instances and a `JoinType`. The pandas `how="left"` translates to `JoinType.LEFT`. The DSS-canonical wire format stores joins as a list of `{table1, table2, conditionsMode, joinType, conditions, outerJoinOnTheLeft}` blocks; the model class `DataikuRecipe._build_settings` builds that shape directly for export.

A small inspection on the V2 flow:

```python
join_recipes = [r for r in flow.recipes if r.recipe_type.value == "join"]
first_join = join_recipes[0]
print(first_join.inputs)              # ['', 'customers']  (rule-based: left input is the prior in-memory DataFrame)
print(first_join.outputs)             # ['orders_enriched']
print(first_join.join_type.value)     # 'LEFT'
print(first_join.join_keys[0].left_column)   # 'customer_id'
print(first_join.join_keys[0].right_column)  # 'customer_id'
```

The rule-based analyzer records the left input of a chained merge as the prior in-memory DataFrame and leaves the dataset name resolution to the optimizer. The LLM path resolves it to `orders_clean` directly. Both shapes are DSS-valid; the join keys, type, and right input are identical in either path.

## V3: introducing WINDOW

V3 adds a 30-day rolling sum per customer. In pandas:

```python
orders_enriched = orders_enriched.sort_values(["customer_id", "ordered_at"])
orders_windowed = orders_enriched.copy()
orders_windowed["rolling_30d_revenue"] = (
    orders_windowed
    .groupby("customer_id")["revenue"]
    .rolling("30D", on="ordered_at")
    .sum()
    .reset_index(level=0, drop=True)
)
```

The pandas idiom is `groupby(...).rolling(...)`. py-iku detects the rolling-with-groupby pattern and emits a single WINDOW recipe with:

- `partition_columns = ["customer_id"]` — the groupby key.
- `order_columns = ["ordered_at"]` — what the window orders by.
- A window aggregation entry of type `MOVING_SUM` over `revenue`, aliased to `rolling_30d_revenue`.

WINDOW is 1→1 in row count: the recipe preserves every input row and adds derived columns. A `df.cumsum()` or `df.expanding().mean()` produces the same recipe type with different aggregation specs (running rather than moving). The full window-function vocabulary lives in `WindowFunctionType` — `RANK`, `LAG`, `LEAD`, `RUNNING_*`, `MOVING_*` — and matches the operators DSS exposes in the Window recipe UI.

After convert, the rule-based path emits `[PREPARE, JOIN, JOIN, SORT, WINDOW]` for V3: the two `merge` calls stay as a chain of two JOIN recipes, and the standalone `sort_values` becomes its own SORT recipe upstream of the WINDOW (it is not folded into the WINDOW's `order_columns` by the rule-based analyzer today). The LLM path may collapse the chain into a single multi-input JOIN and consume the sort into the WINDOW; both shapes are DSS-valid.

## V4: introducing GROUPING and SORT

V4 computes a lifetime revenue per customer and sorts by it:

```python
lifetime = orders_windowed.groupby("customer_id")["revenue"].sum().rename("lifetime_revenue")
orders_ranked = orders_windowed.merge(lifetime, on="customer_id", how="left")
orders_ranked = orders_ranked.sort_values("lifetime_revenue", ascending=False)
```

Two new recipe types appear: GROUPING and SORT. The groupby-then-sum is structural (it reduces row dimensionality from one row per order to one row per customer), so it becomes a GROUPING recipe with:

- `group_keys = ["customer_id"]`
- `aggregations = [Aggregation(column="revenue", function="SUM")]`

The aggregation enum is `AggregationFunction`. `SUM`, `AVG` (also accessible as `MEAN`), `COUNT`, `COUNTD` (also `NUNIQUE`), `STDDEV` (also `STD`), `MEDIAN`, `MIN`, `MAX`, `FIRST`, `LAST`, plus collection variants (`COLLECT_LIST`, `COLLECT_SET`) and percentile entries (`PERCENTILE_25`, `PERCENTILE_50`, `PERCENTILE_75`). The pandas-style aliases share canonical wire values so emitted JSON imports cleanly into DSS.

The merge that follows feeds the lifetime column back onto each row — that is a JOIN, 2→1 again. The final `sort_values("lifetime_revenue", ascending=False)` is a SORT recipe with `sort_columns=[{"column": "lifetime_revenue", "ascending": False}]`. SORT is 1→1 in both row count and column set; only ordering changes.

V4 produces eight recipes in topological order: `[PREPARE, JOIN, JOIN, SORT, WINDOW, GROUPING, JOIN, SORT]`. One fewer if the analyzer or optimizer collapses the chained `merge` pair, or if the upstream sort is folded into the WINDOW's `order_columns`. The shape is verbose, but each recipe corresponds to one structural step of the original pandas script — that is the design intent.

## V5: introducing SPLIT

V5 partitions customers by lifetime revenue:

```python
high_value_customers = orders_ranked[orders_ranked["lifetime_revenue"] >= 1000]
remaining_customers = orders_ranked[orders_ranked["lifetime_revenue"] < 1000]
```

Two filters on the same column with complementary predicates. The rule-based path treats each boolean indexing line independently, so V5 as written above emits two single-output SPLIT recipes (one per assignment) — not one SPLIT with two outputs. The complementary-filter detector currently consolidates the pair *only* when the predicates are explicit syntactic complements (the `~cond` form: `cond = ...; high = df[cond]; low = df[~cond]`). Mathematically complementary value-comparisons such as `>= 1000` and `< 1000` are not collapsed today; Chapter 9 walks through the antecedent and what it would take to extend it.

SPLIT is the first 1→N recipe type in the tour. The output datasets are listed in the `outputs` field, in branch order — the first output corresponds to the positive condition. When the detector does not consolidate, the rule-based path emits one SPLIT per filter assignment, each carrying a single output, and downstream readers see a fanned-out shape rather than the canonical 1→2 SPLIT.

## STACK: appending rows

STACK does not appear in the running example; here is a small inline schema for it.

> Out-of-running-example: `events_jan` and `events_feb`, each with `event_id`, `user_id`, `timestamp`. Concatenating them yields `events_q1`.

```python
import pandas as pd
from py2dataiku import convert

source = """
import pandas as pd
events_jan = pd.read_csv("events_jan.csv")
events_feb = pd.read_csv("events_feb.csv")
events_q1 = pd.concat([events_jan, events_feb], ignore_index=True)
"""
flow = convert(source)
stack = flow.recipes[0]
assert stack.recipe_type.value == "stack"
assert stack.inputs == ["events_jan", "events_feb"]
assert stack.outputs == ["events_q1"]
```

STACK is N→1: variable input arity, one output. The mode is `UNION` by default, which corresponds to pandas `pd.concat`. DSS also supports an `INTERSECT` mode that is rarer in pandas pipelines.

## DISTINCT: deduplication as a recipe

DISTINCT is the canonical example of how the rule-based and LLM paths diverge on the same pandas idiom.

```python
import pandas as pd
from py2dataiku import convert

source = """
import pandas as pd
orders = pd.read_csv("orders.csv")
unique_orders = orders.drop_duplicates(subset=["customer_id"])
"""
flow = convert(source)
print(flow.recipes[0].recipe_type.value)  # 'prepare'
```

The rule-based path emits a PREPARE recipe with a single `REMOVE_DUPLICATES` processor. The LLM path emits a DISTINCT recipe — a 1→1 structural recipe. Both produce DSS-valid output; the choice has trade-offs.

- **PREPARE + REMOVE_DUPLICATES**: the dedup step lives inside a prepare buffer and merges with adjacent element-wise transforms. If a fillna runs immediately before, both end up in the same recipe with no intermediate dataset. The cost is one fewer flow node to inspect; the benefit is fewer scheduling units.
- **DISTINCT recipe**: dedup is its own visible flow node. A reader scanning the flow visually sees "DISTINCT" rather than "PREPARE with N steps". The cost is one more intermediate dataset; the benefit is auditability.

This split is documented as "explicitly accepted as not-bugs" in the project's review log: both shapes pass DSS validation, and the decision is left to the analyzer family the user selects. A team that wants minimal flow size picks the rule-based path; a team that wants every structural operation visible in the DAG picks the LLM path.

## TOP_N: ranked subset

`df.nlargest` and `df.nsmallest` map to TOP_N, a 1→1 recipe that keeps the top K rows by a ranking column.

```python
import pandas as pd
from py2dataiku import convert

source = """
import pandas as pd
orders = pd.read_csv("orders.csv")
top_orders = orders.nlargest(10, "revenue")
"""
flow = convert(source)
recipe = flow.recipes[0]
assert recipe.recipe_type.value == "topn"
assert recipe.top_n == 10
assert recipe.ranking_column == "revenue"
```

TOP_N is the row-reducing dual of SORT: SORT keeps every row but in order, TOP_N keeps the head and discards the tail. A pandas pipeline that does `sort_values(...).head(N)` should also become a TOP_N — the rule-based path collapses the two into one recipe when the head size is a literal integer.

## SAMPLING: a projection to a subset

`df.sample(n=...)` and `df.sample(frac=...)` map to SAMPLING. The mode determines which DSS sampling method is used: `RANDOM_FIXED_NB` for a literal row count, `RANDOM_FIXED_RATIO` for a fraction, `HEAD_SEQUENTIAL` and `TAIL_SEQUENTIAL` for `df.head` and `df.tail`, plus `STRATIFIED`, `CLASS_REBALANCE`, and `RESERVOIR` for cases the LLM path can detect from larger code patterns. SAMPLING is 1→1 with a row count strictly less than or equal to the input.

## PIVOT: reshaping rows to columns

`df.pivot_table(index=..., columns=..., values=..., aggfunc=...)` maps to PIVOT, a 1→1 recipe that takes one row-per-fact dataset and produces one row-per-index dataset with a column per pivot value. PIVOT differs from GROUPING in that the pivoted column space is data-dependent: the columns of the output depend on the values present in the `columns` argument's source.

The reverse — column-to-row reshaping (`pd.melt`) — does *not* get its own recipe type. It becomes a PREPARE recipe with a `FOLD_MULTIPLE_COLUMNS` processor. This is a documented non-obvious case, listed in `mappings/pandas_mappings.py` for reference. The asymmetry exists because PIVOT in DSS is a true reshape (potentially aggregating), whereas melt is a row-wise unfold that fits inside the prepare-step pipeline.

## The remaining recipe types

`RecipeType` lists 37 entries; this chapter has covered eight in detail. The other 29 fall into clusters:

- **Code recipes**: `PYTHON`, `R`, `SQL`, `HIVE`, `IMPALA`, `SPARKSQL`, `PYSPARK`, `SPARK_SCALA`, `SPARKR`, `SHELL`. These run user-authored code rather than visual configurations. py-iku falls back to PYTHON when no visual recipe matches an operation.
- **Data movement**: `SYNC`, `DOWNLOAD`, `UPSERT`, `PUSH_TO_EDITABLE`, `LIST_FOLDER_CONTENTS`, `DYNAMIC_REPEAT`, `EXTRACT_FAILED_ROWS`, `LIST_ACCESS`. These move bytes between locations rather than transform them; they rarely appear in pandas-translated flows.
- **Specialized joins**: `FUZZY_JOIN`, `GEO_JOIN`. Pandas has no first-class equivalent, but the LLM path can detect fuzzy-merge libraries and geo conditions.
- **Statistics and feature engineering**: `GENERATE_FEATURES`, `GENERATE_STATISTICS`. The latter is unusual in being a side-output recipe — it does not advance the working dataset, only profiles it.
- **ML scoring**: `PREDICTION_SCORING`, `CLUSTERING_SCORING`, `EVALUATION`. These appear in flows that consume DSS-trained models. Chapter 12 covers the ML extension points.
- **AI**: `AI_ASSISTANT_GENERATE`. Out of scope for this textbook.

The exhaustive enum lives at `py2dataiku/models/dataiku_recipe.py` for reference.

## Theory anchor: composition of typed primitives

Two ideas worth carrying away from the tour:

- **Arity is part of the recipe's identity.** A recipe type with output arity 2 (SPLIT) is structurally different from one with output arity 1 (FILTER inside PREPARE). A pandas script that produces two named DataFrames from one source can become either two recipes or one SPLIT — the choice depends on whether the two are complementary, and the SPLIT is always the more efficient option when it applies.
- **The flow is a composition of typed primitives.** A reader can predict the recipe shape of a pandas script from local syntactic patterns: `merge` becomes JOIN, `groupby + agg` becomes GROUPING, `groupby + rolling` becomes WINDOW, `sort_values` becomes SORT, `nlargest` becomes TOP_N, `sample` becomes SAMPLING, `pivot_table` becomes PIVOT, complementary boolean indexing becomes SPLIT, and everything element-wise lands in PREPARE.

The same rules apply to both the rule-based and LLM paths. The difference between them is what counts as "local syntactic pattern" — the rule-based analyzer reads the AST literally; the LLM analyzer reads the *intent* of the code. Chapter 7 covers the LLM path in depth.

## Further reading

- [Recipes API reference](../api/models.md)
- [Notebook 03: advanced recipes](https://github.com/m-deane/py-iku/blob/main/notebooks/03_advanced.ipynb)
- [Dataiku docs: Visual recipes overview](https://doc.dataiku.com/dss/latest/other_recipes/index.html)
- [dataiku-api-client-python: recipe.py](https://github.com/dataiku/dataiku-api-client-python/blob/master/dataikuapi/dss/recipe.py)

## What's next

Chapter 7 covers the LLM analyzer path — when to use it, the determinism contract, and the cost shape — before the textbook returns to predicate detection in Chapter 8.
