---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/enrich-with-record-context.html
fetched_at: 2026-04-29
category: processors
---

# Enrich with record context

Add columns containing information about the current record, when available. This processor is used on partitioned or file-based datasets.

## Options

Add a column name to create any of the following:

* **Output partition column:** Create new column with source partition (for partitioned input datasets)

* **Output partition chunks columns prefix:** Create new column with source partition dimension values (for partitioned input datasets)

* **Output file path column:** Create column with file path (for file-based datasets)

* **Output filename column:** Create column with file name (for file-based datasets)

* **Output file record column:** Create column with record id in file (for file-based datasets)

* **Output last modified column:** Create column with file last modification timestamp (for file-based datasets)

> Warning: This processor can only work in the "DSS" engine. It is not compatible with the Spark and SQL engines.

> Note: This processor will not output any valid data when designing the preparation. The data will only populate when the Prepare recipe runs.
