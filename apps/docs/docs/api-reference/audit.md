---
title: Audit
sidebar_position: 9
description: GET /audit — paginated append-only audit log.
---

:::note API stable as of M7
The API surface described in this section is stable as of M7. See [/audit](/user-guide/audit-log) for a change log of events. Breaking changes will be versioned.
:::

# Audit

## GET /audit

Retrieve paginated audit log events. Events are append-only and ordered by ascending timestamp.

### Query parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `since` | ISO 8601 datetime | Return events after this timestamp. |
| `actor` | string | Filter by actor (when auth is enabled). |
| `limit` | integer | Max events per page. Default 50, max 500. |
| `cursor` | string | Opaque cursor from previous response `next_cursor`. |

### Response 200

```json
{
  "items": [
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
  ],
  "next_cursor": "eyJ...",
  "total": 142
}
```

If `next_cursor` is `null`, there are no more events.

### Event types

| Event type | Trigger |
|-----------|---------|
| `convert.rule` | `POST /convert` with `mode=rule` |
| `convert.llm` | `POST /convert` with `mode=llm` |
| `convert.stream.start` | WebSocket connection opened |
| `convert.stream.complete` | WebSocket closed after `completed` |
| `export` | `POST /export/{format}` |
| `flow.created` | `POST /flows` |
| `flow.updated` | `PATCH /flows/{id}` |
| `flow.shared` | `POST /flows/{id}/share` |
| `share.viewed` | `GET /share/{token}` (success) |

### Status codes

| Code | Meaning |
|------|---------|
| 200 | Events returned (may be empty array) |
| 422 | Invalid `since` timestamp format |

### Example

```bash
# Last 20 events
curl "http://localhost:8000/audit?limit=20"

# Events since a date
curl "http://localhost:8000/audit?since=2025-01-15T00:00:00Z"

# Paginate
curl "http://localhost:8000/audit?cursor=eyJ..."
```
