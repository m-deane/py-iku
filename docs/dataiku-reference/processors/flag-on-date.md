---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/flag-on-date.html
fetched_at: 2026-04-29
category: processors
---

# Flag rows/cells on date range

This processor flags rows or cells based on the type of date flag applied: a date range, a relative range, or a date part.

This processor should only be used on columns with meaning 'Date', ie. parsed dates.

## Action

You can select the action to perform on matching (in range) rows:

* Remove matching rows
* Keep matching rows only
* Clear the content of the matching cells
* Clear the content of the non-matching cells

### Flag on Date Range

Flag rows in the dataset if the date values in a column fall within the boundaries specified by a static range; these boundaries are inclusive. If the lower bound (From) is left empty, all dates before the upper bound (To) are flagged, and vice-versa. If the column does not contain a valid date for a given row, that row is considered as being outside the specified range.

The provided timezone will be used to flag dates.

### Flag on Relative Range

Flag rows in the dataset if the date values in a column fall within the boundaries specified by a relative range; these boundaries are dynamic and will update relative to the time on the local server. The relative range is defined using different date periods (year, quarter, month, day) and times (for example: this year, last N years, next N years, year to date). Note: each period is a calendar period; the last 1 year will flag data for the last complete calendar year.

The dates in the dataset as interpreted using the UTC timezone when flagging on relative range.

### Flag on Date Part

Flag rows in the dataset if the date values in a column have the same date part(s) as the one(s) specified in the processor. Data can be flagged on a variety of date parts like year, month, week, weekday, day, specific date...

The dates in the dataset as interpreted using the UTC timezone when flagging on date part.
