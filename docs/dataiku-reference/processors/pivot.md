---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/pivot.html
fetched_at: 2026-04-29
category: processors
---

# Pivot

Transpose multiple rows into columns, widening the dataset.

> Before running a Pivot processor:
> - Sort the values of the index column so that identical values are adjacent
> - Ensure the data source is not parallel (i.e. single-threaded, e.g. a single file)

## Example

**Input:**

| Company | Type | Value |
|---------|------|-------|
| Comp.A | Revenue | 42M |
| Comp.A | Raw Margin | 9M |
| Comp.B | Revenue | 137M |
| Comp.B | Raw Margin | 3M |
| Comp.B | Net income | -11M |

Pivot with:
- Index column: Company
- Labels column: Type
- Values column: Value

**Result:**

| Company | Revenue | Raw Margin | Net income |
|---------|---------|-----------|-----------|
| Comp.A | 42M | 9M | |
| Comp.B | 137M | 3M | -11M |

## Options

**Index column**

Generate a new row for each change of value in the index column.

**Labels column**

Create a column for each value in the label column.

**Values column**

Populate cells with the values of the values column. When several rows share the same index and label, the pivot retains only the value from the last matching row.

**Other columns**

Select how to populate the cells in the other columns:

- Clear the cells
- Keep only the first value
- Retain the value if only one distinct value exists
- Enclose all values in an array

Example of acceptable input:

| idx1 | label1 | v1 |
| idx1 | label2 | v2 |
| idx2 | label1 | v3 |

Example of problematic input:

| idx1 | label1 | v1 |
| idx2 | label1 | v3 |
| idx1 | label2 | v2 |

## Related Resources

To build pivot tables with more control over the rows, columns and aggregations, use the "Pivot recipe" feature within Dataiku.
