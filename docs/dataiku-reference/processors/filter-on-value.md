---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/filter-on-value.html
fetched_at: 2026-04-29
category: processors
---

# Filter rows/cells on value

Filter rows from the dataset that contain specific values. Alternatively, this processor can clear content from matching cells instead of filtering entire rows.

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

**has values**

Input the values for the match condition. A cell will match if it matches one or more values in the list.

**Match mode**

Determine the match type:

*   **Complete value:** the entire cell must match the searched value(s)
*   **Substring:** the cell contains the searched value(s)
*   **Regular expression:** the cell matches the regex

Note

The regex is not anchored.

**Normalization mode**

Specify how to find the match:

*   **Exact (no transformation):** use case-sensitive search
*   **Ignore case:** use case-insensitive search
*   **Normalize (ignore accents):** use accents-insensitive search

Note

Accent-insensitive normalization is only available for complete value matching.
