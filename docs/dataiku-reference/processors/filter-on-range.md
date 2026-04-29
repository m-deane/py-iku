---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/filter-on-range.html
fetched_at: 2026-04-29
category: processors
---

# Filter rows/cells on numerical range

Filter rows from the dataset that contain numbers within a numerical range. Alternatively, this processor can clear content from matching cells instead of filtering entire rows.

The boundaries of the numerical range are inclusive. A value is considered out of range if it isn't a valid numerical value.

## Options

**Action**

Select the action to perform on matching (in range) rows or cells:

*   Keep matching rows only
*   Remove matching rows
*   Clear content of matching cells
*   Clear content of non-matching cells

**Column**

Apply the matching condition to the following:

*   A single column
*   An explicit list of columns
*   All columns matching a regex pattern
*   All columns

Note

When applying the match condition to several columns (multiple, pattern, all), select whether the row will be considered as matching if all columns match (ALL) or at least one column matches (OR).
