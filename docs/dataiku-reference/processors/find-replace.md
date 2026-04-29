---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/find-replace.html
fetched_at: 2026-04-29
category: processors
---

# Find and replace

Find and replace strings in one or more columns. The processor supports multiple sequential replacements within the same cell.

To apply only the first matching replacement and stop further processing, enable **Only perform the first matching replacement**.

## Options

**Column**

Select which columns to process:

- A single column
- An explicit list of columns
- All columns matching a regex pattern
- All columns

**Output column**

Specify whether to create a new output column or modify the original column in-place.

**Replacements**

Define the strings to match and their corresponding replacement values.

**Matching mode**

Choose how the processor identifies matches:

- **Complete value:** replaces the entire cell content
- **Substring:** replaces all occurrences within the cell
- **Regular expression:** replaces patterns matching a regex

For regular expressions, capture groups can be referenced using `$index` notation. For example, the pattern `val-([0-9]*)-.*` can be replaced with `V$1` to transform `val-17-x` into `V17`. To replace the literal `$` character, escape it as `\$`.

**Normalization mode**

Specify how matching is performed:

- **Exact (no transformation):** case-sensitive matching
- **Lowercase:** case-insensitive matching

Accent-insensitive normalization applies only to complete value matching.

**Read replacements from a dataset**

Select **Advanced: Read replacements from a dataset** to load find-and-replace pairs from a dataset. Specify the dataset and identify two columns--one containing search terms and another containing replacements. Any explicitly listed replacements in the recipe step are ignored when using this option.

## Related resources

The [extract with regular expression](https://doc.dataiku.com/dss/latest/preparation/processors/pattern-extract.html) processor helps extract multiple values from a cell using regex patterns.
