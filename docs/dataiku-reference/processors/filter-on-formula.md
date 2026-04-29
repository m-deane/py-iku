---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/filter-on-formula.html
fetched_at: 2026-04-29
category: processors
---

# Filter rows/cells with formula

Filter rows from the dataset based on the result of a formula. Alternatively, clear content from matching cells rather than filter the rows.

The row/cell matches if the result of the formula is considered as "truish," which includes:

- A true boolean
- A number (integer or decimal) that is not 0
- The string "true"

## Options

**Action**

Select the action to perform on matching (in range) rows or cells:

- Keep matching rows only
- Remove matching rows
- Clear content of matching cells
- Clear content of non-matching cells
