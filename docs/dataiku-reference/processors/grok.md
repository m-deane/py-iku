---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/grok.html
fetched_at: 2026-04-29
category: processors
---

# Extract with grok

This processor extracts parts from a column using grok patterns and/or a set of regular expressions. The chunks to extract are delimited using named captures.

## Overview

- The processor comes with a list of integrated grok patterns. See Supported grok patterns below.
- You can combine several grok patterns with regular expressions in the same processor.
- You can use the Grok Editor window to write & preview the results of your regular expressions.

## Syntax

Named captures copy the matches into new columns.

### With a grok pattern

Syntax: `%{Grok_Pattern_Name:named_capture}`

Example:
```
%{IP:clientIP}
```

Output:

| clientIP |
|----------|
| 83.149.9.216 |

### With a regular expression (regex)

Syntax: `(?<named_capture>custom_pattern)`

Example:
```
(?<firstWord>\w+)
```

Output:

| firstWord |
|-----------|
| 2021 |

> **Note**
>
> Named captures only works with a full name (i.e: no `"_"`, `"-"` or `" "` allowed).

## Found column

If you enable this option, a column named 'found' will contain a boolean to indicate whether the pattern matched.

## Some cases of application

### 1. Parsing DSS access logs

Here is a data sample from DSS access.log:

| Line |
|------|
| `127.0.0.1 - - [15/Oct/2020:07:31:29 +0200] "GET /bower_components/jquery/dist/jquery.min.js HTTP/1.1" 200 34847 "http://localhost:11200/home/" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.80 Safari/537.36"` |

Regular expression:
```
%{IP:ip} \- \- \[%{HTTPDATE:HTTPDate}\]
"%{WORD:method} %{URIPATH:resourceURI} %{WORD}/%{NUMBER}"
%{NUMBER:statusCode} %{NUMBER:noIdea} "http:%{URIPATH}"
"%{GREEDYDATA:userAgent}"
```

### 2. Parsing backend logs timestamp

Here is a data sample from DSS backend.log:

| Line |
|------|
| `[2021/09/15-15:12:09.776] [qtp1429351083-884] [DEBUG] [dku.tracing] - [ct: 2] Start call: /api/discussions/get-discussion-counts [GET] user=admin [projectKey=S3DSSVSELK objectType=PROJECT objectId=S3DSSVSELK]` |

Regular expression:
```
(?<Timestamp>%{YEAR}[/-]%{MONTHNUM}[/-]%{MONTHDAY}[/-]%{HOUR}:?%{MINUTE}?:%{SECOND})
```

## Supported grok patterns

(See source URL for the full table of supported grok patterns including USERNAME, USER, INT, BASE10NUM, NUMBER, BASE16NUM, BASE16FLOAT, POSINT, NONNEGINT, WORD, NOTSPACE, SPACE, DATA, GREEDYDATA, QUOTEDSTRING, UUID, networking patterns (MAC, CISCOMAC, WINDOWSMAC, COMMONMAC, IPV4, IP, HOSTNAME, HOST, IPORHOST, HOSTPORT), path patterns (PATH, UNIXPATH, TTY, WINPATH), URI patterns (URIPROTO, URIHOST, URIPATH, URIPARAM, URIPATHPARAM, URI), date/time patterns (MONTH, MONTHNUM, MONTHNUM2, MONTHDAY, DAY, YEAR, HOUR, MINUTE, SECOND, TIME, DATE_US, DATE_EU, ISO8601_TIMEZONE, ISO8601_SECOND, TIMESTAMP_ISO8601, DATE, DATESTAMP, TZ, DATESTAMP_RFC822, DATESTAMP_RFC2822, DATESTAMP_OTHER, DATESTAMP_EVENTLOG), syslog/log format patterns (SYSLOGTIMESTAMP, PROG, SYSLOGPROG, SYSLOGHOST, SYSLOGFACILITY, HTTPDATE, QS, SYSLOGBASE, MESSAGESLOG, COMMONAPACHELOG, COMBINEDAPACHELOG, COMMONAPACHELOG_DATATYPED), and LOGLEVEL.)
