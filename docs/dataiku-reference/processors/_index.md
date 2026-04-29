---
category: processors
fetched_at: 2026-04-29
---

# Processors Index

| Slug | Category | URL | Summary |
|------|----------|-----|---------|
| [array-extract](array-extract.md) | Arrays / JSON | https://doc.dataiku.com/dss/latest/preparation/processors/array-extract.html | Extract an element or sub-array from a JSON array column. |
| [array-fold](array-fold.md) | Arrays / Reshaping | https://doc.dataiku.com/dss/latest/preparation/processors/array-fold.html | Fold a JSON array column into several rows, one value per row. |
| [array-sort](array-sort.md) | Arrays / JSON | https://doc.dataiku.com/dss/latest/preparation/processors/array-sort.html | Sort an array (written in JSON). |
| [arrays-concat](arrays-concat.md) | Arrays / JSON | https://doc.dataiku.com/dss/latest/preparation/processors/arrays-concat.html | Concatenate N JSON-array columns into a single JSON array. |
| [binner](binner.md) | Numerical | https://doc.dataiku.com/dss/latest/preparation/processors/binner.html | Discretize (bin) numerical values into fixed-width or custom intervals. |
| [change-crs](change-crs.md) | Geographic | https://doc.dataiku.com/dss/latest/preparation/processors/change-crs.html | Change the Coordinate Reference System of a geometry/geopoint column (project to WGS84/EPSG:4326). |
| [coalesce](coalesce.md) | Columns | https://doc.dataiku.com/dss/latest/preparation/processors/coalesce.html | Return the first non-null and non-empty value across several input columns. |
| [column-copy](column-copy.md) | Columns | https://doc.dataiku.com/dss/latest/preparation/processors/column-copy.html | Duplicate the content of one column into another. |
| [column-pseudonymization](column-pseudonymization.md) | Privacy | https://doc.dataiku.com/dss/latest/preparation/processors/column-pseudonymization.html | Pseudonymize column values via SHA-256/SHA-512/MD5 hashing with optional pepper and salt column. |
| [column-rename](column-rename.md) | Columns | https://doc.dataiku.com/dss/latest/preparation/processors/column-rename.html | Rename one or more columns; supports raw text bulk edit. |
| [columns-concat](columns-concat.md) | Columns | https://doc.dataiku.com/dss/latest/preparation/processors/columns-concat.html | Concatenate values across columns using a delimiter into a single output column. |
| [columns-select](columns-select.md) | Columns | https://doc.dataiku.com/dss/latest/preparation/processors/columns-select.html | Delete or keep columns by name (single, list, regex, or all). |
| [count-matches](count-matches.md) | Strings | https://doc.dataiku.com/dss/latest/preparation/processors/count-matches.html | Count occurrences of a pattern (complete value, substring, or regex) in a column. |
| [create-if-then-else](create-if-then-else.md) | Logic | https://doc.dataiku.com/dss/latest/preparation/processors/create-if-then-else.html | Compute a column from conditional if/then/else rules with simple, conjunction, or nested groups. |
| [currency-converter](currency-converter.md) | Numerical | https://doc.dataiku.com/dss/latest/preparation/processors/currency-converter.html | Convert monetary columns between currencies using historical reference rates. |
| [currency-splitter](currency-splitter.md) | Strings / Numerical | https://doc.dataiku.com/dss/latest/preparation/processors/currency-splitter.html | Split an amount-with-symbol column into amount + currency-code columns. |
| [date-components-extract](date-components-extract.md) | Dates | https://doc.dataiku.com/dss/latest/preparation/processors/date-components-extract.html | Extract date elements (year, month, day, hour, etc.) from an ISO-8601 column with timezone realignment. |
| [date-difference](date-difference.md) | Dates | https://doc.dataiku.com/dss/latest/preparation/processors/date-difference.html | Compute difference between dates with optional weekend/bank-holiday exclusion (per country calendar). |
| [date-formatter](date-formatter.md) | Dates | https://doc.dataiku.com/dss/latest/preparation/processors/date-formatter.html | Format an ISO-8601 date into a custom human-readable string using Java DateFormat patterns. |
| [date-parser](date-parser.md) | Dates | https://doc.dataiku.com/dss/latest/preparation/processors/date-parser.html | Parse strings to standard ISO-8601 with Smart Date assistance, locale, and timezone resolution. |
| [email-split](email-split.md) | Strings | https://doc.dataiku.com/dss/latest/preparation/processors/email-split.html | Split an email column into local part (before @) and domain (after @). |
| [enrich-french-departement](enrich-french-departement.md) | Enrichment | https://doc.dataiku.com/dss/latest/preparation/processors/enrich-french-departement.html | Add INSEE demographic, housing, fiscal, employment, and company data for French departments. |
| [enrich-french-postcode](enrich-french-postcode.md) | Enrichment | https://doc.dataiku.com/dss/latest/preparation/processors/enrich-french-postcode.html | Enrich a French postcode column with INSEE demographic and city data. |
| [enrich-with-build-context](enrich-with-build-context.md) | Enrichment | https://doc.dataiku.com/dss/latest/preparation/processors/enrich-with-build-context.html | Add columns with build-context info (build date, job ID); only populated at run-time. |
| [enrich-with-record-context](enrich-with-record-context.md) | Enrichment | https://doc.dataiku.com/dss/latest/preparation/processors/enrich-with-record-context.html | Add columns with record context (partition, file path/name, last modified) for partitioned/file-based datasets; DSS engine only. |
| [extract-ngrams](extract-ngrams.md) | Text / NLP | https://doc.dataiku.com/dss/latest/preparation/processors/extract-ngrams.html | Extract n-gram sequences from a text column with simplification and skip-gram options. |
| [extract-numbers](extract-numbers.md) | Strings / Numerical | https://doc.dataiku.com/dss/latest/preparation/processors/extract-numbers.html | Extract numerical values from a text column to columns or a JSON array. |
| [fill-column](fill-column.md) | Columns | https://doc.dataiku.com/dss/latest/preparation/processors/fill-column.html | Fill all values of a column with a fixed value. |
| [fill-empty](fill-empty.md) | Imputation | https://doc.dataiku.com/dss/latest/preparation/processors/fill-empty.html | Fill empty cells with a fixed value. |
| [fill-empty-with-computed-value](fill-empty-with-computed-value.md) | Imputation | https://doc.dataiku.com/dss/latest/preparation/processors/fill-empty-with-computed-value.html | Impute missing values with mean, median, or mode. |
| [filter-on-date](filter-on-date.md) | Filter / Dates | https://doc.dataiku.com/dss/latest/preparation/processors/filter-on-date.html | Filter or clear cells by static date range, relative date range, or date part. |
| [filter-on-formula](filter-on-formula.md) | Filter | https://doc.dataiku.com/dss/latest/preparation/processors/filter-on-formula.html | Filter or clear rows/cells based on a formula evaluating to truthy. |
| [filter-on-meaning](filter-on-meaning.md) | Filter / Meanings | https://doc.dataiku.com/dss/latest/preparation/processors/filter-on-meaning.html | Filter or clear rows/cells whose value is invalid for a selected meaning. |
| [filter-on-range](filter-on-range.md) | Filter / Numerical | https://doc.dataiku.com/dss/latest/preparation/processors/filter-on-range.html | Filter or clear rows/cells whose value is within a numerical range (inclusive). |
| [filter-on-value](filter-on-value.md) | Filter / Strings | https://doc.dataiku.com/dss/latest/preparation/processors/filter-on-value.html | Filter or clear rows/cells matching specific values (complete, substring, regex). |
| [find-replace](find-replace.md) | Strings | https://doc.dataiku.com/dss/latest/preparation/processors/find-replace.html | Find and replace strings in column(s) with sequential replacements, regex capture groups, and dataset-driven mappings. |
| [flag-on-date](flag-on-date.md) | Flag / Dates | https://doc.dataiku.com/dss/latest/preparation/processors/flag-on-date.html | Flag rows whose date matches a static range, relative range, or date part. |
| [flag-on-formula](flag-on-formula.md) | Flag | https://doc.dataiku.com/dss/latest/preparation/processors/flag-on-formula.html | Flag rows where a formula evaluates to truthy. |
| [flag-on-meaning](flag-on-meaning.md) | Flag / Meanings | https://doc.dataiku.com/dss/latest/preparation/processors/flag-on-meaning.html | Flag rows whose value is invalid for a selected meaning. |
| [flag-on-range](flag-on-range.md) | Flag / Numerical | https://doc.dataiku.com/dss/latest/preparation/processors/flag-on-range.html | Flag rows whose value is within a numerical range. |
| [flag-on-value](flag-on-value.md) | Flag / Strings | https://doc.dataiku.com/dss/latest/preparation/processors/flag-on-value.html | Flag rows whose value matches specified values. |
| [fold-columns-by-name](fold-columns-by-name.md) | Reshaping | https://doc.dataiku.com/dss/latest/preparation/processors/fold-columns-by-name.html | Fold a list of named columns into name+value rows (melt). |
| [fold-columns-by-pattern](fold-columns-by-pattern.md) | Reshaping | https://doc.dataiku.com/dss/latest/preparation/processors/fold-columns-by-pattern.html | Fold columns selected by regex pattern; supports capture group for fold-name extraction. |
| [fold-object](fold-object.md) | Reshaping / JSON | https://doc.dataiku.com/dss/latest/preparation/processors/fold-object.html | Split a JSON Object column into key/value rows. |
| [formula](formula.md) | Logic / Math | https://doc.dataiku.com/dss/latest/preparation/processors/formula.html | Compute new columns using formulas (math, string, date, conditional). |
| [fuzzy-join](fuzzy-join.md) | Join (deprecated) | https://doc.dataiku.com/dss/latest/preparation/processors/fuzzy-join.html | Memory-based fuzzy left join with another small dataset (deprecated; use fuzzy-join recipe). |
| [generate-big-data](generate-big-data.md) | Generation | https://doc.dataiku.com/dss/latest/preparation/processors/generate-big-data.html | Generate Big Data out of small data by replicating rows with synthesized values. |
| [geo-distance](geo-distance.md) | Geographic | https://doc.dataiku.com/dss/latest/preparation/processors/geo-distance.html | Compute geodesic distance between geospatial column and fixed geopoint/geometry/another column. |
| [geo-info-extractor](geo-info-extractor.md) | Geographic | https://doc.dataiku.com/dss/latest/preparation/processors/geo-info-extractor.html | Extract centroid point, length, and area from a geometry column. |
| [geo-join](geo-join.md) | Join (deprecated) | https://doc.dataiku.com/dss/latest/preparation/processors/geo-join.html | Memory-based geographic nearest-neighbour join (deprecated; use geo-join recipe). |
| [geoip](geoip.md) | Geographic | https://doc.dataiku.com/dss/latest/preparation/processors/geoip.html | Resolve an IP address to country, region, city, postal, lat/lon, GeoPoint, timezone via GeoLite City. |
| [geopoint-buffer](geopoint-buffer.md) | Geographic | https://doc.dataiku.com/dss/latest/preparation/processors/geopoint-buffer.html | Create a rectangular or circular buffer polygon around each geopoint. |
| [geopoint-create](geopoint-create.md) | Geographic | https://doc.dataiku.com/dss/latest/preparation/processors/geopoint-create.html | Create a GeoPoint column from latitude/longitude columns (WKT format). |
| [geopoint-extract](geopoint-extract.md) | Geographic | https://doc.dataiku.com/dss/latest/preparation/processors/geopoint-extract.html | Extract latitude and longitude columns from a GeoPoint column. |
| [grok](grok.md) | Strings / Logs | https://doc.dataiku.com/dss/latest/preparation/processors/grok.html | Extract chunks from a column using grok patterns and/or regular expressions with named captures. |
| [holidays-computer](holidays-computer.md) | Dates | https://doc.dataiku.com/dss/latest/preparation/processors/holidays-computer.html | Flag school holiday, bank holiday, or weekend for a date column with country-specific calendars. |
| [invalid-split](invalid-split.md) | Filter / Meanings | https://doc.dataiku.com/dss/latest/preparation/processors/invalid-split.html | Move column values invalid for a meaning into a separate column. |
| [join](join.md) | Join (deprecated) | https://doc.dataiku.com/dss/latest/preparation/processors/join.html | Memory-based left join with another small dataset (deprecated; use join recipe). |
| [jsonpath](jsonpath.md) | JSON | https://doc.dataiku.com/dss/latest/preparation/processors/jsonpath.html | Extract data from a JSON column using JSONPath syntax. |
| [long-tail](long-tail.md) | Strings | https://doc.dataiku.com/dss/latest/preparation/processors/long-tail.html | Group long-tail values into a generic 'Others' bucket using an allow-list. |
| [mean](mean.md) | Numerical | https://doc.dataiku.com/dss/latest/preparation/processors/mean.html | Line-by-line arithmetic mean over multiple numeric columns (ignores empties). |
| [meaning-translate](meaning-translate.md) | Meanings | https://doc.dataiku.com/dss/latest/preparation/processors/meaning-translate.html | Replace values according to a 'Value mapping' meaning. |
| [measure-normalize](measure-normalize.md) | Numerical | https://doc.dataiku.com/dss/latest/preparation/processors/measure-normalize.html | Normalize a measurement (mass, volume, surface). |
| [merge-long-tail-values](merge-long-tail-values.md) | Strings | https://doc.dataiku.com/dss/latest/preparation/processors/merge-long-tail-values.html | Merge values below a certain appearance threshold. |
| [move-columns](move-columns.md) | Columns | https://doc.dataiku.com/dss/latest/preparation/processors/move-columns.html | Move one or more columns relative to another column or to begin/end. |
| [negate](negate.md) | Logic | https://doc.dataiku.com/dss/latest/preparation/processors/negate.html | Transform a boolean value into its negation. |
| [number-clipping](number-clipping.md) | Numerical | https://doc.dataiku.com/dss/latest/preparation/processors/number-clipping.html | Clip or clear outliers above/below numeric bounds. |
| [numerical-combinations](numerical-combinations.md) | Numerical | https://doc.dataiku.com/dss/latest/preparation/processors/numerical-combinations.html | Generate every pair of numeric columns combined with +, -, x, /. |
| [numerical-format-convert](numerical-format-convert.md) | Numerical | https://doc.dataiku.com/dss/latest/preparation/processors/numerical-format-convert.html | Convert numbers between Raw / French / English / Italian / Swiss locale formats. |
| [object-nest](object-nest.md) | JSON | https://doc.dataiku.com/dss/latest/preparation/processors/object-nest.html | Combine N input columns into a single JSON object column. |
| [object-unnest-json](object-unnest-json.md) | JSON | https://doc.dataiku.com/dss/latest/preparation/processors/object-unnest-json.html | Unnest (flatten) a JSON object/array column to top-level columns with depth and array-flatten options. |
| [pattern-extract](pattern-extract.md) | Strings | https://doc.dataiku.com/dss/latest/preparation/processors/pattern-extract.html | Extract chunks from a column using a regular expression with named or numbered capture groups. |
| [pivot](pivot.md) | Reshaping | https://doc.dataiku.com/dss/latest/preparation/processors/pivot.html | Pivot processor: transpose rows into columns, widening the dataset using index/labels/values. |
| [python-custom](python-custom.md) | Custom code | https://doc.dataiku.com/dss/latest/preparation/processors/python-custom.html | Execute a custom Python function (Cell/Row/Rows mode, Jython or real Python with vectorized pandas). |
| [querystring-split](querystring-split.md) | Strings / Web | https://doc.dataiku.com/dss/latest/preparation/processors/querystring-split.html | Split an HTTP query string into one column per key=value chunk. |
| [remove-empty](remove-empty.md) | Filter | https://doc.dataiku.com/dss/latest/preparation/processors/remove-empty.html | Remove or keep rows for which selected cells are empty. |
| [round](round.md) | Numerical | https://doc.dataiku.com/dss/latest/preparation/processors/round.html | Round decimals (round/floor/ceil) by significant digits or decimal places. |
| [simplify-text](simplify-text.md) | Text / NLP | https://doc.dataiku.com/dss/latest/preparation/processors/simplify-text.html | Normalize, stem, clear stop words, alphabetic-sort words in a text column. |
| [split](split.md) | Reshaping / Strings | https://doc.dataiku.com/dss/latest/preparation/processors/split.html | Split a column on each delimiter occurrence into prefixed numbered columns or array. |
| [split-fold](split-fold.md) | Reshaping | https://doc.dataiku.com/dss/latest/preparation/processors/split-fold.html | Split a column on a separator and fold values into multiple rows. |
| [split-into-chunks](split-into-chunks.md) | Text / RAG | https://doc.dataiku.com/dss/latest/preparation/processors/split-into-chunks.html | Recursively split text into chunks (with overlap and separator list) for embedding/RAG. |
| [split-unfold](split-unfold.md) | Reshaping | https://doc.dataiku.com/dss/latest/preparation/processors/split-unfold.html | Split a column on a separator into multiple binary (dummified) columns. |
| [string-transform](string-transform.md) | Strings | https://doc.dataiku.com/dss/latest/preparation/processors/string-transform.html | Encode/decode/transform strings: case, URL/XML/Unicode (un)escape, trim, capitalize, normalize, truncate. |
| [switch-case](switch-case.md) | Logic | https://doc.dataiku.com/dss/latest/preparation/processors/switch-case.html | Replace input values according to key-value rules with default and normalization modes. |
| [tokenizer](tokenizer.md) | Text / NLP | https://doc.dataiku.com/dss/latest/preparation/processors/tokenizer.html | Tokenize a text column into array, one token per row, or one token per column with simplification options. |
| [transpose](transpose.md) | Reshaping | https://doc.dataiku.com/dss/latest/preparation/processors/transpose.html | Turn rows into columns (limited to 100 rows). |
| [triggered-unfold](triggered-unfold.md) | Reshaping / Sessions | https://doc.dataiku.com/dss/latest/preparation/processors/triggered-unfold.html | Reassemble rows when a specific trigger value is encountered (session reconstruction). |
| [unfold](unfold.md) | Reshaping | https://doc.dataiku.com/dss/latest/preparation/processors/unfold.html | Transform values of a column into binary columns (one-hot / dummification). |
| [unfold-array](unfold-array.md) | Reshaping / JSON | https://doc.dataiku.com/dss/latest/preparation/processors/unfold-array.html | Transform a JSON array column into per-value occurrence count columns. |
| [unixtimestamp-parser](unixtimestamp-parser.md) | Dates | https://doc.dataiku.com/dss/latest/preparation/processors/unixtimestamp-parser.html | Convert UNIX timestamps (seconds or milliseconds) to ISO-8601 dates. |
| [up-down-fill](up-down-fill.md) | Imputation | https://doc.dataiku.com/dss/latest/preparation/processors/up-down-fill.html | Fill empty cells with previous (or next) non-empty value. |
| [url-split](url-split.md) | Strings / Web | https://doc.dataiku.com/dss/latest/preparation/processors/url-split.html | Split a URL into protocol, host, port, path, querystring, anchor columns. |
| [user-agent](user-agent.md) | Web | https://doc.dataiku.com/dss/latest/preparation/processors/user-agent.html | Classify a User-Agent string into type, brand, category, version, os, osversion, osflavor. |
| [visitor-id](visitor-id.md) | Web | https://doc.dataiku.com/dss/latest/preparation/processors/visitor-id.html | Generate a best-effort visitor id from IP, user-agent, language, timezone. |
| [zip-arrays](zip-arrays.md) | JSON | https://doc.dataiku.com/dss/latest/preparation/processors/zip-arrays.html | Zip N JSON-array columns into a JSON array of objects. |
