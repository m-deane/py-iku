---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/arrays-concat.html
fetched_at: 2026-04-29
category: processors
---

# Concatenate JSON arrays

This processor concatenates N input columns containing arrays (as JSON) into a single JSON array.

## Example

**Input:**

| a | b |
|---|---|
| [1,2] | ["x","y"] |

**Output:**

```
[1, 2, "x", "y"]
```
