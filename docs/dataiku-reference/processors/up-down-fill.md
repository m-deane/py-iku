---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/up-down-fill.html
fetched_at: 2026-04-29
category: processors
---

# Fill empty cells with previous/next value

Fill empty cells in column(s) with the previous or next non-empty value.

## Example

| Values | Fill with previous | Fill with next |
|--------|-------------------|----------------|
|        | A                 | A              |
| A      | A                 | A              |
|        | A                 | B              |
|        | A                 | B              |
| B      | B                 | B              |
|        | B                 |                |

## Options

When filling with previous value, you can specify multiple columns. When filling with next value, you can use only a single column.
