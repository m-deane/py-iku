---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/array-extract.html
fetched_at: 2026-04-29
category: processors
---

# Extract from array

Extract an element or a sub-array from an array written in JSON.

## Options

**Input column**

Column to extract element or array.

**Mode**

Choose from:

- **Extract an element:** Provide the element's index number. Use negative index to count from the end of the array: (-1 is the last value, -2 is second to last, etc).

- **Extract a sub-array:** Provide the starting and ending index numbers.

**Output column**

Create a separate output column or leave blank to perform extraction in-column.
