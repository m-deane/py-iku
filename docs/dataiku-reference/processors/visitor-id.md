---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/visitor-id.html
fetched_at: 2026-04-29
category: processors
---

# Generate a best-effort visitor id

This processor generates visitor identifiers for web logs that don't already have one.

When processing web logs, it is often required to have a unique identifier for each visitor.

When processing logs coming from a full-featured web tracker, like Dataiku's WT1, each log line already features a unique visitor id.

However, when processing more raw logs, like Apache Access logs, you generally don't have one. It is also possible to have no visitor id if the visitor disabled cookies.

This processor will try to assign a visitor-id to each line, using as much information to identify the visitor as possible. You need to specify a name for the output column, and to fill information about which columns are available. All input columns are optional.

This processor will try to use:

* The IP address
* The user-agent string
* The language of the user's browser
* The timezone offset of the user's browser

## Important note

Although these information will often lead to uniquely identifying each visitor (especially for home users), this represents a best-effort approach and some collisions (two distinct visitors being assigned the same identifier) will occur, particularly for visitors from large organizations.
