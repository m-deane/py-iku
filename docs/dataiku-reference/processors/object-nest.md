---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/object-nest.html
fetched_at: 2026-04-29
category: processors
---

# Nest columns

Combine N input columns into a single JSON object column.

## Example

**Input:**

| a | b |
|---|---|
| 1 | 2 |

**Output:**

```json
{"a": 1, "b": 2}
```

## Options

**Column**

Apply the nest processor to the following:

- A single column
- An explicit list of columns
- All columns matching a regex pattern
- All columns

**Output column**

Name the created output column. Cannot be left blank.
