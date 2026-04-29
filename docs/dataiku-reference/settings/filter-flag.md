---
source_url: https://doc.dataiku.com/dss/latest/preparation/filter-flag.html
fetched_at: 2026-04-29
category: settings
---

# Filtering and flagging rows

Dataiku DSS provides 5 processors for filtering data. These processors can:

- Remove rows based on various conditions
- Clear the content of cells based on the same conditions
- Create "flag" columns indicating whether each row matches a condition

## Common filtering actions

The configuration for most of these processors can be divided into two sections:

- Defining match conditions that will be evaluated on a row
- Defining the action to perform on the rows matching the condition:
  - Remove matching rows
  - Keep matching rows only
  - Clear the content of a cell, only for matching rows
  - Clear the content of a cell, only for non-matching rows
  - Create an indicator (0 / 1) column indicating whether the row matches the condition

## Columns selection

Some of these processors can check their condition on multiple columns:

- A single column
- An explicit list of columns
- All columns matching a given pattern
- All columns

For processors that support column selection, you can select whether the column will be considered as matching if:

- All columns are matching
- Or, at least one column is matching

## Filter on value

The Filter rows/cells on value and Flag rows on value match rows based on whether certain columns contain specified values.

### Values

You can select multiple values. The filter matches if at least one of the values matches.

### Matching mode

By setting the match mode, you can specify how you want this processor to search:

- 'Complete value': match where the searched value is the complete cell value
- 'Substring': match when the cell contains the searched value
- 'Regular expression': match when the cell matches the searched pattern (note: the regular expression is not anchored)

### Normalization mode

By setting the normalization mode, you can specify how you want this processor to search:

- Using a case-sensitive search ('Exact' mode)
- Using a case-insensitive search ('Lowercase' mode)
- Using an accents-insensitive search ('Normalize' mode)

'Normalize' mode performs a unicode normalization.

## Filter on numerical range

The Filter rows/cells on numerical range and Flag rows on numerical range match rows for which the value is within a numerical range.

- The boundaries of the numerical range are inclusive.
- Both lower and upper boundaries are optional.
- If the column does not contain a valid numerical value for a row, this row is considered as being out of the range (and thus non-matching).

## Filter on date range

The Filter rows/cells on date and Flag rows/cells on date range match rows for which the date is within different types of ranges: a static range, a relative (moving) range, a range of date parts.

**Date Range**
- The boundaries are inclusive.
- Both lower and upper boundaries are optional
- If the column does not contain a valid date for a row, this row is considered as being out of the range.
- The provided time zone will be used to filter dates.

**Relative Range**
- The boundaries are inclusive
- The boundaries are dynamic and update relative to the time specified on the DSS server
- Date periods are calendar periods: 'last 3 months' will be a range that only includes the last 3 complete calendar months

**Date Part**
- Filter using date components like year, quarter, or weekday

Note: this processor works on columns with "Date" meaning, i.e. parsed dates.

## Filter on formula

The Filter rows/cells with formula and Flag rows with formula match rows based on the result of a Formula language expression.

The row matches if the result of the formula is considered as "truish", which includes:

- A true boolean
- A number (integer or decimal) which is not 0
- The string "true"

## Filter on bad meaning

The Filter invalid rows/cells and Flag invalid rows match rows based on whether they are considered as valid for the selected meaning.
