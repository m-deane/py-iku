---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/split-unfold.html
fetched_at: 2026-04-29
category: processors
---

# Split and unfold

This processor splits the values of a column based on a separator and transforms them into several binary columns. Also called 'dummification'.

You can prefix new columns by filling the "Prefix" option.

You can choose the maximum number of columns to create with the "Max nb. columns to create" option.

For example, with the following dataset:

| customer_id | events |
|---|---|
| 1 | login, product, buy |
| 2 | login, product, logout |

We get:

| customer_id | events_login | events_product | events_buy | events_logout |
|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 0 |
| 2 | 1 | 1 | 0 | 1 |

The unfolded column is deleted.

## Warning

**Limitations**

The limitations that apply to the Unfold processor also apply to the Split and Unfold processor.

For more details on reshaping, please see Reshaping.
