# Running Example — Retail Customer Revenue ETL

This file is the binding running-example contract. Phase 2 writer agents must use the schemas, names, and version progression below verbatim. Inventing new column names or dataset names is a contract violation.

The scenario: a retail business wants a per-customer revenue report, segmented by customer tier and time window. The pandas script joins three input tables, derives revenue figures, computes a rolling 30-day total per customer, sorts by lifetime revenue, and finally splits the customer base into a "high-value" cohort and a "remaining" cohort for downstream marketing flows.

This scenario was chosen over a web event log because event-log processing forces a sessionization step, which pollutes the visual recipe tour with patterns that do not generalize.

---

## Source Data Schema

These three input datasets are the only inputs the running example uses. Column names and types are fixed. Writers must not introduce new columns.

### `customers`

| Column          | Type     | Notes                                        |
|-----------------|----------|----------------------------------------------|
| `customer_id`   | string   | Primary key. Format: `C` + 7 digits.         |
| `signup_date`   | date     | ISO 8601, yyyy-mm-dd.                        |
| `country`       | string   | ISO 3166-1 alpha-2.                          |
| `tier`          | string   | One of `bronze`, `silver`, `gold`.           |
| `email`         | string   | May be null.                                 |

### `orders`

| Column          | Type     | Notes                                        |
|-----------------|----------|----------------------------------------------|
| `order_id`      | string   | Primary key. Format: `O` + 9 digits.         |
| `customer_id`   | string   | Foreign key to `customers.customer_id`.      |
| `product_id`    | string   | Foreign key to `products.product_id`.        |
| `order_date`    | datetime | ISO 8601 with time component.                |
| `quantity`      | int      | Always positive. May not be null.            |
| `unit_price`    | float    | Currency-naive; treated as a single currency.|
| `discount_pct`  | float    | Range [0.0, 1.0]. May be null (treat as 0).  |

### `products`

| Column          | Type     | Notes                                        |
|-----------------|----------|----------------------------------------------|
| `product_id`    | string   | Primary key. Format: `P` + 6 digits.         |
| `category`      | string   | E.g. `apparel`, `electronics`, `home`.       |
| `cost`          | float    | Per-unit cost. May not be null.              |

---

## Output Datasets (intermediate and final)

The version progression below introduces these output datasets in order:

| Dataset                  | Introduced in | Description                                                  |
|--------------------------|---------------|--------------------------------------------------------------|
| `orders_clean`           | V1            | `orders` after fillna and revenue computation.               |
| `orders_enriched`        | V2            | `orders_clean` joined with `customers` and `products`.       |
| `orders_windowed`        | V3            | `orders_enriched` with rolling 30-day per-customer revenue.  |
| `orders_ranked`          | V4            | `orders_windowed` sorted by lifetime revenue desc.           |
| `high_value_customers`   | V5            | Split output: lifetime revenue >= 1000.                      |
| `remaining_customers`    | V5            | Split output: lifetime revenue < 1000 (complementary).       |

---

## Final Pandas Script (V5)

This is the canonical full script. V1–V4 are strict prefixes (with the trailing operations omitted). Line numbers are stable across versions; writer agents should reference them when introducing each version.

```python
# running_example.py — retail customer revenue ETL, V5 (final)
import pandas as pd

# --- V1 begins ---
orders = pd.read_csv("orders.csv")
orders["discount_pct"] = orders["discount_pct"].fillna(0.0)
orders["revenue"] = orders["quantity"] * orders["unit_price"] * (1 - orders["discount_pct"])
orders = orders.rename(columns={"order_date": "ordered_at"})
orders_clean = orders
# --- V1 ends ---

# --- V2 adds JOIN ---
customers = pd.read_csv("customers.csv")
products = pd.read_csv("products.csv")
orders_enriched = orders_clean.merge(customers, on="customer_id", how="left")
orders_enriched = orders_enriched.merge(products, on="product_id", how="left")
# --- V2 ends ---

# --- V3 adds WINDOW ---
orders_enriched = orders_enriched.sort_values(["customer_id", "ordered_at"])
orders_windowed = orders_enriched.copy()
orders_windowed["rolling_30d_revenue"] = (
    orders_windowed
    .groupby("customer_id")["revenue"]
    .rolling("30D", on="ordered_at")
    .sum()
    .reset_index(level=0, drop=True)
)
# --- V3 ends ---

# --- V4 adds SORT ---
lifetime = orders_windowed.groupby("customer_id")["revenue"].sum().rename("lifetime_revenue")
orders_ranked = orders_windowed.merge(lifetime, on="customer_id", how="left")
orders_ranked = orders_ranked.sort_values("lifetime_revenue", ascending=False)
# --- V4 ends ---

# --- V5 adds SPLIT ---
high_value_customers = orders_ranked[orders_ranked["lifetime_revenue"] >= 1000]
remaining_customers = orders_ranked[orders_ranked["lifetime_revenue"] < 1000]
# --- V5 ends ---
```

---

## Version Progression and Expected Flow Shape

For each version, the table below states (a) which lines belong to that version, (b) the expected DSS recipe count after `convert()` and the rule-based optimizer pass, (c) the recipe types in topological order, and (d) the dataset names produced. Writer agents will assert against these values in code examples.

### V1 — Pure PREPARE

- **Lines**: 5–10 in the script above (the V1 block).
- **Used in**: Ch 2 (5-second tour), Ch 3 (Anatomy), Ch 5 (PREPARE deep dive).
- **Expected recipe count**: 1.
- **Expected recipe types (topological order)**: `[PREPARE]`.
- **Expected datasets**: `orders` (input) → `orders_clean` (output).
- **Expected processor types in the PREPARE recipe (in order)**:
  1. `FILL_EMPTY_WITH_VALUE` on `discount_pct` with value `0.0`.
  2. `CREATE_COLUMN_WITH_FORMULA` (or `FORMULA`) for `revenue = quantity * unit_price * (1 - discount_pct)`.
  3. `COLUMN_RENAMER` mapping `order_date` → `ordered_at`.

### V2 — V1 + JOIN

- **Lines**: V1 + the V2 block.
- **Used in**: Ch 4 (Grammar), Ch 6 (Recipe types tour), Ch 7 (LLM path comparison).
- **Expected recipe count**: 2 (after optimizer merge).
- **Expected recipe types (topological order)**: `[PREPARE, JOIN]`.
  - The two `merge` calls collapse into a single multi-input JOIN recipe configured with two join clauses (`customers` on `customer_id`, `products` on `product_id`). If the writer's chapter explicitly opts out of the merge, the alternative is `[PREPARE, JOIN, JOIN]` — both shapes are acceptable, but the chapter must state which one it expects and why.
- **Expected datasets**: `orders`, `customers`, `products` (inputs) → `orders_clean` (intermediate) → `orders_enriched` (output).

### V3 — V2 + WINDOW

- **Lines**: V1 + V2 + the V3 block.
- **Used in**: Ch 6 (Recipe types tour), Ch 9 (Advanced patterns), Ch 10 (Optimization).
- **Expected recipe count**: 3.
- **Expected recipe types (topological order)**: `[PREPARE, JOIN, WINDOW]`.
- **Expected datasets**: as V2, plus `orders_windowed` as the WINDOW output.
- **WINDOW configuration**: partition by `customer_id`, order by `ordered_at`, range frame of 30 days, aggregation `sum(revenue)` aliased to `rolling_30d_revenue`.

### V4 — V3 + SORT

- **Lines**: V1 + V2 + V3 + the V4 block.
- **Used in**: Ch 6 (Recipe types tour), Ch 10 (Optimization).
- **Expected recipe count**: 5.
- **Expected recipe types (topological order)**: `[PREPARE, JOIN, WINDOW, GROUPING, JOIN, SORT]` *or* `[PREPARE, JOIN, WINDOW, GROUPING, SORT]` if the inner self-join is detected as a window aggregation rather than a literal join.
  - Writer agents must pick one shape, declare the assumption ("the lifetime-revenue computation is detected as a GROUPING followed by a JOIN on `customer_id`"), and assert against that shape.
- **Expected datasets**: as V3, plus an intermediate aggregation dataset (writer's choice of name; suggest `lifetime_revenue`) and `orders_ranked` as the SORT output.

### V5 — V4 + SPLIT (final)

- **Lines**: the complete script above.
- **Used in**: Ch 6 (Recipe types tour), Ch 9 (Advanced patterns — complementary-filter detection), Appendix C.
- **Expected recipe count**: 6 (or 7 if the V4 inner JOIN is preserved).
- **Expected recipe types (topological order)**: `[PREPARE, JOIN, WINDOW, GROUPING, JOIN, SORT, SPLIT]` (or the V4-alternative shape with one fewer JOIN).
- **Expected datasets**: as V4, plus `high_value_customers` and `remaining_customers` as the two SPLIT outputs.
- **SPLIT detection**: the two assignment lines on `lifetime_revenue >= 1000` and `lifetime_revenue < 1000` are complementary on the same column. py-iku must emit a single SPLIT recipe with one branch per condition, not two FILTER recipes. Writers must assert this in Ch 9.

---

## Notes for writers

- The script is intentionally short. If a chapter needs to demonstrate something the running example does not exercise (e.g. STACK, DISTINCT, TOP_N), introduce a small inline schema in that section and label it "out of running example". Do not retroactively edit the running example.
- Column names with `_at` suffix (e.g. `ordered_at`) are deliberately introduced by V1's rename to give Ch 5 a real `COLUMN_RENAMER` to talk about. Do not skip the rename in V1.
- The V4 → V5 jump is the only place complementary filters are demonstrated. Preserve the exact predicates `>= 1000` and `< 1000`. Changing the boundary or the operator will defeat the SPLIT-detection test in Ch 9.
- All input CSVs are assumed to exist alongside the script; no chapter needs to demonstrate file I/O. The library treats `pd.read_csv("orders.csv")` as the input-dataset declaration for `orders`.
- When a chapter asserts `len(flow.recipes) == N`, the assertion runs against the *post-optimization* flow unless the chapter explicitly disables optimization. Default is post-optimization.
