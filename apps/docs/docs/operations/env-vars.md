---
title: Environment Variables
sidebar_position: 3
description: Complete reference for all environment variables used by the Studio stack.
---

# Environment Variables

## API (`apps/api`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | No | — | Anthropic API key. Required for `mode=llm` with provider `anthropic`. |
| `OPENAI_API_KEY` | No | — | OpenAI API key. Required for `mode=llm` with provider `openai`. |
| `SHARE_SECRET_KEY` | Production: Yes | `dev-insecure-key` | HMAC-SHA256 secret for signing share link tokens. Rotate to invalidate all existing tokens. |
| `API_AUTH_ENABLED` | No | `false` | Set `true` to require `Authorization: Bearer <token>` on all endpoints. |
| `API_AUTH_TOKEN` | If auth enabled | — | The bearer token value. In production, use a secrets manager instead of env var. |
| `MAX_CODE_SIZE_BYTES` | No | `262144` | Maximum allowed Python code payload in bytes. 413 returned if exceeded. |
| `DB_PATH` | No | `./data/studio.db` | Path to the SQLite database file. Mount as a Docker volume in production. |
| `LOG_LEVEL` | No | `INFO` | Python logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`. |
| `CORS_ORIGINS` | No | `["http://localhost:5173"]` | Comma-separated allowed CORS origins. |
| `LLM_TIMEOUT_SECONDS` | No | `30` | Max wall-clock time for LLM conversion before 504 response. |

## Web (`apps/web`)

Vite env vars are embedded at build time (prefix `VITE_`).

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_BASE_URL` | No | `http://localhost:8000` | REST API base URL. |
| `VITE_WS_BASE_URL` | No | `ws://localhost:8000` | WebSocket base URL. |
| `VITE_SENTRY_DSN` | No | — | Sentry DSN for error tracking (planned M10). |

## Docker Compose

Pass env vars to Docker Compose via a `.env` file at the repo root:

```bash
# .env (do not commit this file)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
SHARE_SECRET_KEY=<openssl rand -hex 32>
```

Docker Compose interpolates from `.env` automatically.

## Security notes

- Never commit `.env` or any file containing API keys to git. The `.gitignore` excludes `.env` by default.
- `SHARE_SECRET_KEY` should be at least 32 random bytes. Generate with `openssl rand -hex 32`.
- In production, prefer injecting secrets via a secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.) rather than environment variables.
- LLM API keys are stored in the API's settings, not forwarded to the browser. The `apps/web` settings drawer POSTs them to the API; they are stored encrypted at rest using Fernet.
