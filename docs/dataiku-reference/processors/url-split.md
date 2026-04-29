---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/url-split.html
fetched_at: 2026-04-29
category: processors
---

# Split URL (into protocol, host, port, ...)

This processor splits the elements of a URL into multiple columns.

A valid URL follows this structure: `scheme://hostname[:port][/path][querystring][#anchor]`

The output values are produced in columns prefixed by the input column name.

If the input does not contain a valid URL, no output value is produced.

## Examples

* `http://www.google.com/search?q=query#results`
* `ftp://ftp.server.com/pub/downloads/myfile.tar.gz`
