---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/fold-columns-by-pattern.html
fetched_at: 2026-04-29
category: processors
---

# Fold multiple columns by pattern

Transforms values from multiple columns into one line per column. This processor selects the columns to fold using a pattern. It only creates lines for non-empty columns.

If the pattern has a capture group, this processor uses the captured portion of the column name instead of the full column name.

## Examples

Using `.*_score` as a column to fold pattern:

| person | age | Q1_score | Q2_score | Q3_score |
|--------|-----|----------|----------|----------|
| John   | 24  | 3        | 4        | 6        |
| Sidney | 31  | 6        | 9        |          |
| Bill   | 33  | 1        | 4        |          |

becomes:

| person | age | quarter  | score |
|--------|-----|----------|-------|
| John   | 24  | Q1_score | 3     |
| John   | 24  | Q2_score | 4     |
| John   | 24  | Q3_score | 6     |
| Sidney | 31  | Q2_score | 6     |
| Sidney | 31  | Q3_score | 9     |
| Bill   | 33  | Q1_score | 1     |
| Bill   | 33  | Q3_score | 4     |

Using a capture group, with the pattern `(.*)_score`, the example becomes:

| person | age | quarter | score |
|--------|-----|---------|-------|
| John   | 24  | Q1      | 3     |
| John   | 24  | Q2      | 4     |
| John   | 24  | Q3      | 6     |
| Sidney | 31  | Q2      | 6     |
| Sidney | 31  | Q3      | 9     |
| Bill   | 33  | Q1      | 1     |
| Bill   | 33  | Q3      | 4     |

## Options

**Columns to fold pattern**

Write a regular expression to find matching columns, or choose "Find with Smart Pattern" to get help writing a regular expression. In the Smart Pattern window, you can highlight the portion of the column name that you wish to use. To use a pattern in the processor, select it and choose OK.

**Column for fold name**

Give a name for the new column that will contain the fold name. ("Quarter" in the example.)

**Column for fold value**

Give a name for the new column that will contain the fold value. ("Score" in the example.)

**Remove folded columns**

Check the box to delete folded columns after running the recipe.

## Related resources

This processor is a variant of Fold multiple columns. Read more about that processor in the Dataiku documentation.
