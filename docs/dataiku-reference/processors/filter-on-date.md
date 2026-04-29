---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/filter-on-date.html
fetched_at: 2026-04-29
category: processors
---

# Filter rows/cells on date

Filter rows from the dataset using a date filter defined by a fixed date range, a relative date range, or a matching date part. Alternatively, clear content from matching cells rather than filter the rows.

## Options

**Action**

Select the action to perform on matching (in range) rows or cells:

*   Keep matching rows only
*   Remove matching rows
*   Clear content of matching cells
*   Clear content of non-matching cells

**Date column**

Column containing data in ISO-8601 format. Use a Prepare step to parse the data into this format if it isn't already. If the column doesn't not contain a valid date for a row, this row is considered out of range.

**Filter on**

Choose how to define the date filter:

*   **Date range:** Use a fixed date range. The lower/upper boundaries are inclusive. If the lower bound is empty, all dates before the upper bound will match, and vice versa.
*   **Relative range:** Use a relative date range and time window (last N, next N, current, until now). The range is calculated relative to the current date and the chosen date parts. It will update itself over time.
*   **Date part:** Filter on date part falling within values in a list.
