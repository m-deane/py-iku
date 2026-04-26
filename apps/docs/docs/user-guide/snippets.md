---
title: Snippets
sidebar_position: 7
description: The snippet gallery — pre-built pandas patterns for quick conversion testing.
---

# Snippets

Route: `/snippets`

The Snippet Gallery provides a library of pre-built pandas code patterns. Each snippet is a self-contained Python script that demonstrates one or more `py2dataiku` conversion patterns. Snippets are designed to be pasted into the Monaco editor for immediate conversion.

## Opening the gallery

- From the Convert page: click the **Snippets** button in the editor toolbar.
- Direct navigation: visit `/snippets`.

## Snippet categories

| Category | Examples |
|----------|---------|
| Aggregation | `groupby + agg`, `pivot_table`, `rolling mean`, `expanding sum` |
| Join | `pd.merge inner`, `pd.merge left`, `concat (stack)` |
| Transform | `dropna + fillna`, `rename + drop`, `astype + to_datetime` |
| Filter / Split | `boolean filter`, `query string`, `nlargest / nsmallest` |
| Encode | `get_dummies`, `pd.cut / pd.qcut`, `str.upper / str.lower` |
| Pipeline | multi-step real-world pipelines (sales analysis, customer segmentation) |

## Using a snippet

1. Click a snippet card in the gallery.
2. A preview panel shows the code and the expected flow diagram.
3. Click **Use in Editor** to copy the snippet to the Monaco editor on the Convert page.

If the Convert page is already open in another tab, the snippet is pushed to the editor via a Zustand store update.

## Snippet format

Snippets are plain Python strings stored in the web app. They follow the same conventions as `py2dataiku/examples/` — each snippet has a header comment indicating what Dataiku recipe types it exercises:

```python
# Demonstrates: GROUPING, JOIN, SORT
# Expected recipes: 3
# Expected datasets: 5 (2 input, 1 intermediate, 1 intermediate, 1 output)

import pandas as pd

df = pd.read_csv("orders.csv")
by_customer = df.groupby("customer_id").agg({"amount": ["sum", "count"]})
merged = pd.merge(df, by_customer, on="customer_id")
result = merged.sort_values("amount_sum", ascending=False)
```

## Adding new snippets

Snippets are defined in `apps/web/src/features/editor/snippets.ts`. To add one, append an entry to the `SNIPPETS` array following the existing shape. No backend changes are required — snippets are purely client-side.

After adding a snippet, write a conversion smoke-test in `apps/web/tests/unit/snippets.test.ts` to verify the expected recipe count.
