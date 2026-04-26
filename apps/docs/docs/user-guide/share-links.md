---
title: Share Links
sidebar_position: 8
description: Generate time-limited, read-only share links for your flows.
---

# Share Links

Share links let you send a read-only view of a flow to someone who does not have a Studio account. They are HMAC-signed, scoped to a single flow, and expire after a configurable TTL.

## Creating a share link

1. Save the flow first (click **Save** in the toolbar). Studio persists it via `POST /flows` and returns a `{id}`.
2. Click **Share** in the toolbar.
3. In the Share modal, choose a TTL (default 24 hours; max 7 days).
4. Click **Generate Link**. The API calls `POST /flows/{id}/share` and returns `{token, url, expires_at}`.
5. Copy the URL and share it.

## Recipient experience

The recipient visits the URL, which hits `GET /share/{token}`. If the token is valid and unexpired, they see:

- The full flow canvas (read-only; no edit controls).
- The Inspector panel (read-only).
- An Export button (they can download but not overwrite).
- A banner: "Shared view — read only. Expires [date]."

The share URL does not require login and does not count against any quota (but is rate-limited to 60 requests per minute per IP).

## Security model

Share tokens are HMAC-SHA256 signed with a server-side secret (`SHARE_SECRET_KEY` env var). The token payload contains:

```json
{
  "flow_id": "...",
  "expires_at": 1234567890,
  "scopes": ["read"]
}
```

The `apps/api/app/security/share_links.py` module handles signing and verification. Keys are never exposed to the browser. Tokens are opaque to the recipient.

## Revoking a share link

There is no revocation UI in M8. To revoke, restart the API server with a rotated `SHARE_SECRET_KEY`, which invalidates all existing tokens. Per-token revocation is planned for M10.

## Expiry

After the TTL expires, `GET /share/{token}` returns `401 Unauthorized` with a problem+json body:

```json
{
  "type": "https://py-iku.io/errors/share-expired",
  "title": "Share link has expired",
  "status": 401,
  "detail": "This link expired at 2025-01-15T12:00:00Z"
}
```
