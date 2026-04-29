---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/mean.html
fetched_at: 2026-04-29
category: processors
---

# Compute the average of numerical values

This processor computes the line by line arithmetical mean (average) of a set of numeric columns.

For a given line, empty columns will be ignored, the mean will be calculated only over the non-empty columns. If all columns are empty, the result will be either an empty cell or a default value defined in the processor options.

## Columns selection

This processor can compute the mean over multiple columns:

* An explicit list of columns
* All columns matching a given pattern

## Examples

* Mean of `[1, 2, 3]` will be `2`
* Mean of `[1, 2, ""]` will be `1.5` (the empty cell is ignored)
* Mean of `["", ""]` will be an empty cell or the default value, depending on the processor options.

Note that the processor doesn't support non-numeric values: Mean of `[1, 2, "some text"]` may yield an error when the recipe runs, depending on the execution environment.
