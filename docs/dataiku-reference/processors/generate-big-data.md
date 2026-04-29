---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/generate-big-data.html
fetched_at: 2026-04-29
category: processors
---

# Generate Big Data

This processor generates Big Data out of small data.

The number of output rows will be exactly the number of input rows times the specified Expansion Factor.

The processor does not simply copy rows; instead, for numeric columns, it generates new values in the same range as the input values. For alphanumeric columns, it splits the column into words, and replaces each input word by a randomly selected one from the observed values.
