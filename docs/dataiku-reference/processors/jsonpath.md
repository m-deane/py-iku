---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/jsonpath.html
fetched_at: 2026-04-29
category: processors
---

# Extract with JSONPath

Extract data from a column containing JSON using the JSONPath syntax, and create a new column containing the extracted data.

## Example

JSON object from input column: `{"person":"John","age":24}`

JSONPath expression: `$.age`

Extracted data: `24`

## Options

**Input column**

Column containing the JSON to extract.

**Output column**

Create a new column for output.

**JSONPath expression**

Expression following the syntax in the "[JSONPath documentation](http://goessner.net/articles/JsonPath/)".

**Single value**

Check if the path represents a single value and not an array.
