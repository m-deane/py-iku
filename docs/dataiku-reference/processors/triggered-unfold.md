---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/triggered-unfold.html
fetched_at: 2026-04-29
category: processors
---

# Triggered unfold

This processor is used to reassemble several rows when a specific value is encountered.

It is useful for analysis of "interaction sessions" (a series of events with a specific event marking the beginning of a new interaction session). For example, while analyzing the logs of a web game, the "start game" event would be the beginning event.

## Warning

**Limitations**

Triggered unfold offers a basic session analysis that is very simple to use, but it comes with many limitations.

Triggered unfold assumes that the input data is sorted by time. It only works on "unsplitted" datasets (for example, a single file or a SQL table)

Non-terminated sessions are kept in memory. It is recommended that you do not use Triggered Unfold if you have more than a few thousands sessions

For more advanced sessions analysis, if you have splitted data or a large number of sessions, you should use specific recipes (for example, using SQL)

## Example

For example, let's imagine this dataset:

| user_id | event_type | timestamp |
|---------|-----------|-----------|
| user_id1 | login_event | t1 |
| user_id2 | login_event | t2 |
| user_id1 | event_type2 | t3 |
| user_id2 | event_type2 | t4 |
| user_id1 | login_Event | t5 |
| user_id2 | event_type3 | t6 |
| user_id2 | login_event | t7 |

We know that "login_event" marks the beginning of a new session / new interaction, and we want to track the timestamps of other event types in each session.

We apply a "Triggered unfold" with the following parameters:

* Column acting as event key: user_id
* Fold column: event_type
* Trigger value: login_event
* Column with data: timestamp

We generate the following result:

| user_id | login_event | event_type2 | event_type3 | login_event_prev |
|---------|-----------|-----------|-----------|-----------|
| user_id1 | t1 | t3 | | |
| user_id2 | t2 | t4 | t6 | |
| user_id1 | t5 | | | t1 |
| user_id2 | t7 | | | t2 |

We get:

* One column for each type of event
* One line for each occurence of "login_event" in the stream
* The user_id associated to each login_event is kept, and the timestamps of events are restored
* The "_prev" column tracks the data associated to the previous occurence of "login_event" for each user_id.

For more details on reshaping, please see [Reshaping](../reshaping.html).
