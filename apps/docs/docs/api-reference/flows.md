---
title: Flows
sidebar_position: 7
description: POST /flows and GET/PATCH /flows/\{id\} — flow persistence endpoints.
---

:::note API stable as of M7
The API surface described in this section is stable as of M7. See [/audit](/user-guide/audit-log) for a change log of events. Breaking changes will be versioned.
:::

# Flows

## POST /flows

Persist a flow and return its assigned id.

### Request

```json
{
  "flow": { ...DataikuFlow.to_dict()... },
  "name": "Sales pipeline v2",
  "tags": ["sales", "pandas", "m7-review"]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `flow` | object | Yes | `DataikuFlow.to_dict()` payload. |
| `name` | string | Yes | Human-readable name. Max 255 chars. |
| `tags` | string[] | No | Optional tags for filtering. |

### Response 201

```json
{
  "id": "flw_01HXXXXXX",
  "name": "Sales pipeline v2",
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

## GET /flows/\{id\}

Retrieve a saved flow by id.

### Response 200

```json
{
  "id": "flw_01HXXXXXX",
  "name": "Sales pipeline v2",
  "flow": { ...DataikuFlow.to_dict()... },
  "tags": ["sales"],
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T11:00:00Z"
}
```

The `flow` field round-trips through `DataikuFlow.from_dict()` before serialisation to ensure integrity.

### Status codes

| Code | Meaning |
|------|---------|
| 200 | Found |
| 404 | Flow not found |

---

## PATCH /flows/\{id\}

Update a saved flow's name, tags, or flow payload.

### Request

All fields are optional (partial update):

```json
{
  "name": "Sales pipeline v3",
  "tags": ["sales", "reviewed"],
  "flow": { ...updated DataikuFlow.to_dict()... }
}
```

### Response 200

Returns the full updated flow record (same shape as `GET /flows/\{id\}`).

---

## POST /flows/\{id\}/share

Generate a time-limited share link for a saved flow.

### Request

```json
{
  "ttl_seconds": 86400,
  "scopes": ["read"]
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `ttl_seconds` | integer | 86400 (24h) | Link TTL. Max 604800 (7 days). |
| `scopes` | string[] | `["read"]` | Currently only `read` is supported. |

### Response 200

```json
{
  "token": "eyJ...",
  "url": "http://localhost:5173/share/eyJ...",
  "expires_at": "2025-01-16T10:30:00Z"
}
```
