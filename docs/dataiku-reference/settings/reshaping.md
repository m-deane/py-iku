---
source_url: https://doc.dataiku.com/dss/latest/preparation/reshaping.html
fetched_at: 2026-04-29
category: settings
---

# Reshaping

Reshaping processors are used to change the "shape" (rows/columns) of the data.

DSS provides the following reshaping processors:

- Split and Fold
- Fold multiple columns
- Fold multiple columns by pattern
- Unfold
- Unfold an array
- Split and Unfold
- Triggered Unfold

## Split and Fold

The Split and fold processor creates new lines by splitting the values of a column.

For example, with the following dataset:

| customer_id | events | browser |
|---|---|---|
| 1 | login,product,buy | Mozilla |
| 2 | login,product,logout | Chrome |

Applying "Split and Fold" on the "events" column with "," as the separator will generate the following result:

| customer_id | events | browser |
|---|---|---|
| 1 | login | Mozilla |
| 1 | product | Mozilla |
| 1 | buy | Mozilla |
| 2 | login | Chrome |
| 2 | product | Chrome |
| 2 | logout | Chrome |

More details are available in the reference documentation.

## Fold multiple columns

The Fold multiple columns processor takes values from multiple columns and transforms them to one line per column.

For example, with the following dataset representing monthly scores:

| person | age | 01/2014 | 02/2014 | 03/2014 |
|---|---|---|---|---|
| John | 24 | 3 | 4 | 3 |
| Sidney | 31 | 6 | 9 |  |
| Bill | 33 | 1 | 4 |  |

Applying the processor with:

- 3 columns in the "columns list": 01/2014, 02/2014, 03/2014
- "month" as the "fold name column"
- "score" as the "fold value column"

will generate the following result:

| person | age | month | score |
|---|---|---|---|
| John | 24 | 01/2014 | 3 |
| John | 24 | 02/2014 | 4 |
| John | 24 | 03/2014 | 6 |
| Sidney | 31 | 01/2014 |  |
| Sidney | 31 | 02/2014 | 6 |
| Sidney | 31 | 03/2014 | 9 |
| Bill | 33 | 01/2014 | 1 |
| Bill | 33 | 02/2014 |  |
| Bill | 33 | 03/2014 | 4 |

More details are available in the reference documentation.

## Fold multiple columns by pattern

This processor is a variant of Fold multiple columns, where the columns to fold are specified by a pattern instead of a list. The processor only creates lines for non-empty columns.

For example, using "tag_(.*)" as column to fold pattern:

| name | n_connection | tag_1 | tag_2 | tag_3 |
|---|---|---|---|---|
| Florian | 16570 | bigdata | python | puns |

becomes

| name | n_connection | tag | rank |
|---|---|---|---|
| Florian | 16570 | bigdata | 1 |
| Florian | 16570 | python | 2 |
| Florian | 16570 | puns | 3 |

More details are available in the reference documentation.

## Unfold

This processor transforms cell values into binary columns.

For example, with the following dataset:

| id | type |
|---|---|
| 0 | A |
| 1 | A |
| 2 | C |
| 3 | B |

Applying the "Unfold" processor on the "type" column will generate the following result:

| id | type_A | type_C | type_B |
|---|---|---|---|
| 0 | 1 |  |  |
| 1 | 1 |  |  |
| 2 |  | 1 |  |
| 3 |  |  | 1 |

Each value of the unfolded column will create a new column. This new column:

- contain the value "1" if the original column contained this value
- remains empty else.

Unfolding is often used to find some correlations to a particular value, or for creating graphs.

### Limitations

The Unfold processor dynamically creates new columns based on the actual data within the cells. Due to the way the schema is handled when you create a preparation recipe, only the values that were found at least once in the sample will create columns in the output dataset.

Unfolding a column with a large number of values will create a large number of columns. This can cause performance issues. It is highly recommended not to unfold columns with more than 100 values, or to limit the number of created columns with the "Max nb. columns to create" option.

More details are available in the reference documentation.

## Unfold an array

This processor transforms array values into occurrence columns.

For example, with the following dataset:

| id | words |
|---|---|
| 0 | ['hello', 'hello', 'world'] |
| 1 | ['hello', 'world'] |
| 2 | ['hello'] |
| 3 | ['world', 'world'] |

Applying the "Unfold an array" processor on the "words" column will generate the following result:

| id | words | words_hello | words_world |
|---|---|---|---|
| 0 | ['hello', 'hello', 'world'] | 2 | 1 |
| 1 | ['hello', 'world'] | 1 | 1 |
| 2 | ['hello'] | 1 |  |
| 3 | ['world', 'world'] |  | 2 |

Each value of the unfolded column will create a new column. This new column:

- contains the number of occurrences of the value found in the original column,
- remains empty if the original column does not contain this value.

### Limitations

The limitations that apply to the Unfold processor also apply to the Unfold an array processor.

More details are available in the reference documentation.

## Split and Unfold

This processor splits multiple values in a cell and transforms them into columns.

For example, with the following dataset:

| customer_id | events |
|---|---|
| 1 | login, product, buy |
| 2 | login, product, logout |

We get:

| customer_id | events_login | events_product | events_buy | events_logout |
|---|---|---|---|---|
| 1 | 1 | 1 | 1 |  |
| 2 | 1 | 1 |  | 1 |

The unfolded column is deleted.

### Limitations

The limitations that apply to the Unfold processor also apply to the Split and Unfold processor.

More details are available in the reference documentation.

## Triggered Unfold

This processor is used to reassemble several rows when a specific value is encountered. It is useful for analysis of "interaction sessions" (a series of events with a specific event marking the beginning of a new interaction session). For example, while analyzing the logs of a web game, the "start game" event would be the beginning event.

More details are available in the reference documentation.
