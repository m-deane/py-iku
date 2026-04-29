---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/flag-on-formula.html
fetched_at: 2026-04-29
category: processors
---

# Flag rows with formula

Flag rows from the dataset based on the result of a formula by creating a column containing '1' for all matching (in-range) rows. Unmatched rows are left empty.

## Options

**Expression**

Write a formula by which to evaluate each row for a match. The row matches if the result of the formula is considered as "truish," which includes:

*   A true boolean

*   A number (integer or decimal) that is not 0

*   The string "true"

**Flag column**

Name the column that will contain the match flags 1-true, empty-false

## Related resources

For more information on the formula language, please see the [formula language reference](https://doc.dataiku.com/dss/latest/formula/index.html) in Dataiku's documentation.
