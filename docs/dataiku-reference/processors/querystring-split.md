---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/querystring-split.html
fetched_at: 2026-04-29
category: processors
---

# Split HTTP Query String

This processor splits the elements of an HTTP query string.

The query string is the part coming after the `?` in the string. For example: `product_id=234&step=3`

## Output

This processor outputs one column for each chunk of the query string. Columns are named with the prefix and the key of the HTTP Query string chunk.

## Example

For input:

| qs |
|---|
| productid=234&step=3 |
| customer_id=FDZ&action=cart&step=2 |

With prefix : 'qs_', result would be:

| qs | qs_product_id | qs_step | qs_customer_id | qs_action |
|---|---|---|---|---|
| productid=234&step=3 | 234 | 3 | | |
| customer_id=FDZ&action=cart&step=2 | | 2 | FDZ | cart |
