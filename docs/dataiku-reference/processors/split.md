---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/split.html
fetched_at: 2026-04-29
category: processors
---

# Split column

Split a column into several columns on each occurrence of the delimiter. The output columns are numbered: The first chunk will be in prefix\_0, the second in prefix\_1, and so on.

## Examples

*   Split `col=a/b/c` using `/` as the delimiter and `chunk` as the output column prefix

    > *   Output: `chunk_0=a`, `chunk_1=b`, `chunk_3=c`
    >

*   Split `col=a/b/c` using `/` as the delimiter, `chunk` as the output column prefix, and keep 2 columns from the beginning

    > *   Output: `chunk_0=a`, `chunk_1=b`
    >

## Options

**Delimiter**

Separates values from each input column within the output.

**Output columns prefix**

Add a prefix to identify the output columns.

**Output as**

Output the result(s) of the split as separate columns or as an array (`A-B` -> `["A","B"]`).

**Truncate**

Limit the number of output columns and keep only the first N columns or the N last columns.

**Keep empty chunks**

Preserve empty chunks between consecutive delimiters. (`App`, delimiter `p` -> `["A", "", ""]`)
