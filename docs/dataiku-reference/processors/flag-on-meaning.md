---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/flag-on-meaning.html
fetched_at: 2026-04-29
category: processors
---

# Flag invalid rows

This processor flags rows with invalid values, ie values not matching a selected meaning.

It creates a column which will contain '1' if the row matches (invalid), nothing else

## Columns selection

This processor can check its matching condition on multiple columns:

*   A single column

*   An explicit list of columns

*   All columns matching a given pattern

*   All columns

You can select whether the row will be considered as matching if:

*   All columns are matching

*   Or, at least one column is matching
