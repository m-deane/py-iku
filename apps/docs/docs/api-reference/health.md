---
title: Health
sidebar_position: 10
description: GET /health — service liveness check.
---

:::note API stable as of M7
The API surface described in this section is stable as of M7. See [/audit](/user-guide/audit-log) for a change log of events. Breaking changes will be versioned.
:::

# Health

## GET /health

Service liveness check. Returns the API status, API version, and the underlying `py2dataiku` library version. No authentication required.

### Response 200

```json
{
  "status": "ok",
  "version": "0.0.0",
  "py_iku_version": "0.3.0"
}
```

| Field | Source |
|-------|--------|
| `status` | Always `"ok"` when the server is up. |
| `version` | API application version from `pyproject.toml`. |
| `py_iku_version` | `py2dataiku.__version__` (resolved via `importlib.metadata` at runtime; fallback `0.3.0`). |

### Usage in CI

The health endpoint is used by Docker Compose health checks:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 10s
  timeout: 5s
  retries: 3
```

It is also called by `apps/web` on startup to confirm the API is reachable before enabling the Convert button.

### Example

```bash
curl http://localhost:8000/health
# {"status":"ok","version":"0.0.0","py_iku_version":"0.3.0"}
```
