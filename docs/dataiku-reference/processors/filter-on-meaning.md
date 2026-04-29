---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/filter-on-meaning.html
fetched_at: 2026-04-29
category: processors
---

# Filter invalid rows/cells

Filter rows from the dataset with invalid values, i.e. those that are invalid for the selected meaning. Alternatively, this processor can clear content from invalid cells instead of filtering entire rows.

Meaning is semantic information about the data and is usually automatically detected from the content of the column: URL, IP Address, Country. As such, each cell can be valid or invalid for a given meaning.

## Options

**Action**

Select the action to perform on matching (in range) rows or cells:

* Keep matching rows only
* Remove matching rows
* Clear content of matching cells
* Clear content of non-matching cells

**Column**

Apply the matching condition to the following:

* A single column
* An explicit list of columns
* All columns matching a regex pattern
* All columns

Note

When applying the match condition to several columns (multiple, pattern, all), select whether the row will be considered as matching if all columns match (ALL) or at least one column matches (OR).

**Meaning to check**

Select which meaning to check cells in the column for: text, decimal, integer, boolean, date, object, array, natural lang., geo...

## Related resources

For more information on data types (storage vs. meaning) in DSS, please see the reference documentation. If you prefer a hands-on approach, check out the article on meanings in the Dataiku Knowledge Base or explore user-defined meanings.
