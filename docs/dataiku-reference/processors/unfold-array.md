---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/unfold-array.html
fetched_at: 2026-04-29
category: processors
---

# Unfold an array

This processor takes a column containing JSON-formatted arrays and transforms it into several columns, containing the number of occurrences of each term of the array.

You can prefix new columns by filling the "Prefix" option.

You can choose the maximum number of columns to create with the "Max nb. columns to create" option.

You can transform the original column into binary columns by unchecking the "Count of Values" option.

For example, with the following dataset:

| id | words |
|---|---|
| 0 | ['hello', 'hello', 'world'] |
| 1 | ['hello', 'world'] |
| 2 | ['hello'] |
| 3 | ['world', 'world'] |

Applying the "Unfold an array" processor on the "words" column will generate the following result:

| id | words | words_hello | words_world |
|---|---|---|---|
| 0 | ['hello', 'hello', 'world'] | 2 | 1 |
| 1 | ['hello', 'world'] | 1 | 1 |
| 2 | ['hello'] | 1 |  |
| 3 | ['world', 'world'] |  | 2 |

Each value of the unfolded column will create a new column. This new column:

* contains the number of occurrences of the value found in the original column,
* remains empty if the original column does not contain this value.

## Warning

**Limitations**

The limitations that apply to the Unfold processor also apply to the Unfold an array processor.

For more details on reshaping, please see Reshaping.
