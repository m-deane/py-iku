---
title: Share
sidebar_position: 8
description: GET /share/\{token\} — public read-only flow viewer via share link.
---

:::note API stable as of M7
The API surface described in this section is stable as of M7. See [/audit](/user-guide/audit-log) for a change log of events. Breaking changes will be versioned.
:::

# Share

## GET /share/\{token\}

Retrieve a shared flow by its HMAC-signed token. This endpoint does not require authentication and is rate-limited to 60 requests per minute per IP.

### Path parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `token` | string | HMAC-signed token returned by `POST /flows/\{id\}/share`. |

### Response 200

Same shape as `GET /flows/\{id\}`, with an additional `expires_at` field:

```json
{
  "id": "flw_01HXXXXXX",
  "name": "Sales pipeline v2",
  "flow": { ...DataikuFlow.to_dict()... },
  "tags": ["sales"],
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z",
  "expires_at": "2025-01-16T10:30:00Z"
}
```

### Status codes

| Code | Meaning |
|------|---------|
| 200 | Token valid and flow returned |
| 401 | Token expired or invalid signature |
| 404 | Underlying flow not found (deleted after share was created) |
| 429 | Rate limit exceeded |

### Error response for expired token

```json
{
  "type": "https://py-iku.io/errors/share-expired",
  "title": "Share link has expired",
  "status": 401,
  "detail": "This link expired at 2025-01-16T10:30:00Z",
  "instance": "/share/eyJ..."
}
```

### Security notes

- Tokens are HMAC-SHA256 signed with `SHARE_SECRET_KEY` (server env var).
- Rotating `SHARE_SECRET_KEY` invalidates all existing tokens immediately.
- The token payload contains `{flow_id, expires_at, scopes}`.
- This endpoint logs a `share.viewed` event to the audit log (without recording the token value).
