---
title: Audit Log
sidebar_position: 9
description: The append-only audit log — what events are recorded and how to query them.
---

# Audit Log

Route: `/audit`

The Audit Log is an append-only record of all conversion, export, share, and flow-persistence events. It is accessible via the `/audit` UI page and the `GET /audit` API endpoint.

## What is recorded

| Event type | Trigger |
|-----------|---------|
| `convert.rule` | `POST /convert` with `mode=rule` |
| `convert.llm` | `POST /convert` with `mode=llm` |
| `convert.stream.start` | WebSocket `/convert/stream` connection opened |
| `convert.stream.complete` | WebSocket `/convert/stream` closed with `completed` event |
| `export` | `POST /export/{format}` |
| `flow.created` | `POST /flows` |
| `flow.updated` | `PATCH /flows/{id}` |
| `flow.shared` | `POST /flows/{id}/share` |
| `share.viewed` | `GET /share/{token}` (successful) |

DSS write-back events (`dss.write`, `dss.dry_run`) will be added in M10.

## Event schema

Each audit event has:

```json
{
  "id": "evt_01HXXXXXX",
  "event_type": "convert.rule",
  "actor": "anonymous",
  "ts": "2025-01-15T10:30:00Z",
  "payload": {
    "code_size_bytes": 1243,
    "recipe_count": 4,
    "dataset_count": 5,
    "warnings": 0
  }
}
```

LLM API keys and share link secrets are **never** included in audit payloads.

## Querying the log

From the UI:

- Filter by event type using the dropdown.
- Filter by date range using the date pickers.
- Search by actor (when authentication is enabled in future milestones).

From the API:

```bash
# Last 50 events
GET /audit?limit=50

# Events since a timestamp
GET /audit?since=2025-01-15T00:00:00Z

# Paginate using cursor
GET /audit?since=2025-01-15T00:00:00Z&limit=20
# Response includes next_cursor if more events exist
GET /audit?cursor=<next_cursor>
```

## Retention

Events are stored in a SQLite database (`apps/api/app/store/audit_repo.py`). There is no automatic pruning in M8. Retention policies and export-to-S3 are planned for M10.

## Exporting the log

Click **Export CSV** on the `/audit` page to download all visible events as a CSV file. This calls the API with the current filter parameters and streams the response.
