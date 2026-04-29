---
source_url: https://doc.dataiku.com/dss/latest/preparation/engines.html
fetched_at: 2026-04-29
category: settings
---

# Execution engines

## Design of the preparation

The design of a data preparation is always done on an in-memory sample of the data. See [Sampling](sampling.html) for more information.

## Execution in analysis

When in an analysis, execution on the whole dataset happens when:

*   Exporting the prepared data.
*   Running a machine learning model.

In both cases, this uses a streaming engine: all data goes through the DSS server but does not need to be in memory.

## Execution of the recipe

For execution of the recipe, DSS provides three execution engines:

### DSS

All data goes through the DSS server but does not need to be in memory (as it is streamed).

### Spark

When Spark is installed (see: [DSS and Spark](../spark/index.html)), preparation recipe jobs can run on Spark.

We recommend that you only use this on the following dataset types that support fast read and write on Spark:

*   S3
*   Azure Blob Storage
*   Google Cloud Storage
*   Snowflake
*   HDFS

### In-database (SQL)

A subset of the preparation processors can be translated to SQL queries. When all processors in a preparation recipe can be translated, and both input and output are tables in the same SQL connection, the recipe runs fully in-database.

Please see the warnings and limitations below.

## Details on the in-database (SQL) engine

Only a subset of processors can be translated to SQL queries. They are documented in the processors reference. The SQL engine can only be selected if all processors are compatible with it.

If you add a non-supported processor while the in-database engine is selected, DSS will show which processor cannot be used with details.

**Note:** There are some edge cases of columns that change type where DSS may show the engine as supported, but upon running the recipe, you encounter a syntax error. If that happens, you will need to disable the SQL engine and fall back to the DSS engine.

Some of these edge cases relate to type conflicts, if for example you have a textual column and perform a find/replace operation that transforms it into a numerical column and immediately use it for numerical operations.

When using Snowflake with Java UDF, additional processors are supported thanks to unique extended push-down capabilities. Please see [Snowflake](../connecting/snowflake.html) for more details. Additional setup is required to benefit from extended push-down.

### Supported processors

These processors are available with SQL processing.

*   Keep/Delete columns
*   Reorder columns
*   Rename columns
*   Split columns
*   Filter by alphanumerical value
*   Filter by numerical range
*   Flag by alphanumerical value
*   Flag by numerical range
*   Remove rows with empty value
*   Fill empty cells with value
*   Concatenate columns
*   Copy columns
*   Unfold
*   Split and unfold
*   Create if, then, else statements

These processors are only available with Snowflake with Java UDF processing.

*   [Discretize (bin) numerical values](processors/binner.html)
*   [Convert currencies](processors/currency-converter.html)
*   [Split currencies in column](processors/currency-splitter.html)
*   [Split e-mail addresses](processors/email-split.html)
*   [Extract numbers](processors/extract-numbers.html)
*   [Resolve GeoIP](processors/geoip.html)
*   [Flag holidays](processors/holidays-computer.html)
*   [Normalize measure](processors/measure-normalize.html)
*   [Split HTTP Query String](processors/querystring-split.html)
*   [Simplify text](processors/simplify-text.html)
*   [Convert a UNIX timestamp to a date](processors/unixtimestamp-parser.html)
*   [Split URL (into protocol, host, port, ...)](processors/url-split.html)
*   [Classify User-Agent](processors/user-agent.html)
*   [Generate a best-effort visitor id](processors/visitor-id.html)

### Partially supported processors

In some variants of configuration of the processor, it will revert to a normal processing. Various issues may also appear and require you to switch back to DSS engine.

*   Formula (essentially same support as in other visual recipes)
*   Filter by formula (see above)
*   Flag by formula (see above)
*   Find / Replace (especially around regular expressions)
*   [Transform string](processors/string-transform.html) (depends on the transformation) - All are available with Snowflake
*   [Extract with regular expression](processors/pattern-extract.html) - More options are available with Snowflake
*   Date-handling processors (parse date, extract date components)
*   Geo processors (extract from geo column, change coordinate reference system (CRS), compute distances between geospatial objects)
*   [Filter invalid rows/cells](processors/filter-on-meaning.html) and [Flag invalid rows](processors/flag-on-meaning.html) (not supported for custom meanings) (Snowflake with Java UDF only)

## Details on the Spark engine

All processors are compatible with the Spark engine.
