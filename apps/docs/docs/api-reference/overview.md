---
title: API Overview
sidebar_position: 1
description: Base URL, authentication, error model, and versioning for the py-iku Studio API.
---

:::note API stable as of M7
The API surface described in this section is stable as of M7. See [/audit](/user-guide/audit-log) for a change log of events. Breaking changes will be versioned.
:::

# API Reference Overview

The py-iku Studio API is a FastAPI application running at `http://localhost:8000` (default). All requests and responses are JSON unless the endpoint returns a binary stream.

## Base URL

```
http://localhost:8000
```

In production deployments, the base URL is configured via the `API_BASE_URL` environment variable consumed by `apps/web`.

## Authentication

M7 authentication is a bearer token stub. Pass the header:

```
Authorization: Bearer <token>
```

For local development, the token is not enforced unless `API_AUTH_ENABLED=true` is set. Full authentication (API key management, OAuth) is planned for M10.

## Content types

- Requests: `application/json`
- Responses: `application/json` for data endpoints; binary streams for export endpoints.
- WebSocket frames: JSON text frames.

## Error model (RFC 7807)

All error responses follow the Problem Details standard ([RFC 7807](https://www.rfc-editor.org/rfc/rfc7807)):

```json
{
  "type": "https://py-iku.io/errors/invalid-python",
  "title": "Invalid Python syntax",
  "status": 400,
  "detail": "SyntaxError at line 5: unexpected indent",
  "instance": "/convert"
}
```

### Error type mapping

The `Py2DataikuError` hierarchy maps to HTTP status codes as follows:

| Exception | HTTP status |
|-----------|------------|
| `InvalidPythonCodeError` | 400 |
| `ValidationError` | 422 |
| `LLMResponseParseError` | 502 |
| `ProviderError` | 502 |
| `ConfigurationError` | 500 |
| `ExportError` | 500 |
| `ConversionError` (generic) | 422 |

413 is returned when the code payload exceeds `max_code_size_bytes` (default 256 KB).

## Versioning

The API version is embedded in the `GET /health` response. The OpenAPI schema is available at:

- `GET /openapi.json` — raw schema
- `GET /docs` — Swagger UI
- `GET /redoc` — ReDoc UI

A snapshot of the OpenAPI schema as of M7 is committed at `packages/types/openapi.snapshot.json` and is used for TS type generation and drift checking in CI.

## Rate limiting

| Endpoint | Limit |
|---------|-------|
| `POST /convert` | 10 req/min per IP |
| `WS /convert/stream` | 5 concurrent connections per IP |
| `GET /share/{token}` | 60 req/min per IP |
| All other endpoints | No limit in M8 |

## OpenAPI snapshot drift check

The reference pages below are hand-authored — generic generators don't produce the curated examples and cross-links that make these pages useful. To prevent drift between the routes and the docs, `apps/docs/scripts/sync-api-reference.ts` cross-checks every documented path against `packages/types/openapi.snapshot.json` and exits non-zero on mismatch:

```bash
pnpm dlx tsx apps/docs/scripts/sync-api-reference.ts
```

CI runs this check on every push. If you add a new route, update the corresponding MDX page; if you remove one, delete its section.
