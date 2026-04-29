---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/long-tail.html
fetched_at: 2026-04-29
category: processors
---

# Group long-tail values

This processor merges together all values of a column that are not part of an allow-list of values that should not be merged.

## Use case

The main use case of this processor is to merge all values of a column except the most frequent ones. The merged values are replaced by a generic 'Others' value.
