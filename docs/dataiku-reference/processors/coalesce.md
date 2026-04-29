---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/coalesce.html
fetched_at: 2026-04-29
category: processors
---

# Coalesce

Return the first non-null (and non-empty) value across several input columns.

The _Coalesce_ processor evaluates a list of columns and, for each row, outputs the first value that is neither null nor an empty string. If all selected input columns are null or empty, the processor can return a user-provided default value or NULL.

This processor behaves similarly to the SQL `COALESCE` function (specifically ignoring empty strings), but operates directly on recipe rows within DSS.

Note

Columns are evaluated in the order listed in the configuration.

## Options

**Columns to apply to**

Select one or more columns that the processor will evaluate. You may choose:

*   A single column
*   Multiple explicit columns
*   A pattern-based rule (regular expression)
*   All columns

Columns are evaluated from left to right. The processor uses the first non-null and non-empty value.

**Use default value**

Enable this option to specify a fallback value if all input columns are null or empty.

*   If **unchecked**: The processor returns `NULL` when no valid value is found.
*   If **checked**: The processor returns the content of the "Default value" field.

**Default value**

The value to return if "Use default value" is enabled and all inputs are null/empty.

*   If you leave this field empty, the processor returns an empty string (`""`).
*   If you enter text (e.g. `"N/A"`, `"0"`), that text is returned.
*   If containing spaces (e.g. `"   "`), these spaces are preserved.

## Example

The following table illustrates the behavior of the processor given two input columns, `col1` and `col2`, in different scenarios.

| col1 | col2 | Result | Scenario / Configuration |
|------|------|--------|--------------------------|
| `""` | `"foo"` | `"foo"` | **Value found.** The empty string in `col1` is skipped; valid data in `col2` is returned. |
| `""` | `""` | `NULL` | **Fallback (Default disabled).** All inputs are empty. "Use default value" is **unchecked**. |
| `""` | `""` | `""` | **Fallback (Default empty).** All inputs are empty. "Use default value" is **checked**, but the field is left blank. |
| `""` | `""` | `"N/A"` | **Fallback (Default set).** All inputs are empty. "Use default value" is **checked** and set to `"N/A"`. |
