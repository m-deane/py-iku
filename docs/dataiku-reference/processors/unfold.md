---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/unfold.html
fetched_at: 2026-04-29
category: processors
---

# Unfold

This processor transforms the values of a column into several binary columns. Also called 'dummification', creation of 'dummy columns' or one-hot encoding.

You can prefix new columns by filling the "Prefix" option.

You can choose the maximum number of columns to create with the "Max nb. columns to create" option.

For example, with the following dataset:

| id | type |
|----|------|
| 0  | A    |
| 1  | A    |
| 2  | C    |
| 3  | B    |

Applying the "Unfold" processor on the "type" column will generate the following result:

| id | type_A | type_C | type_B |
|----|--------|--------|--------|
| 0  | 1      |        |        |
| 1  | 1      |        |        |
| 2  |        | 1      |        |
| 3  |        |        | 1      |

Each value of the unfolded column will create a new column. This new column:

- contain the value "1" if the original column contained this value
- remains empty else.

Unfolding is often used to find some correlations to a particular value, or for creating graphs.

## Warning

**Limitations**

The Unfold processor dynamically creates new columns based on the actual data within the cells.

Due to the way the schema is handled when you create a preparation recipe, only the values that were found at least once in the sample will create columns in the output dataset.

Unfolding a column with a large number of values will create a large number of columns. This can cause performance issues. It is highly recommended not to unfold columns with more than 100 values, or to limit the number of created columns with the "Max nb. columns to create" option.

For more details on reshaping, please see [Reshaping](../reshaping.html).
