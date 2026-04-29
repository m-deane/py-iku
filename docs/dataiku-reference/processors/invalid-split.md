---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/invalid-split.html
fetched_at: 2026-04-29
category: processors
---

# Split invalid cells into another column

This processor takes all values of a column that are invalid for a specific meaning and moves them to another column.

## Example

With the following data:

| icol |
|------|
| 42   |
| Baad |

With parameters:

- Column: icol
- Column for invalid data: bad_icol
- Meaning to check: Number

The result will be:

| icol | bad_icol |
|------|----------|
| 42   |          |
|      | Baad     |
