---
title: Deployment
sidebar_position: 1
description: Docker Compose deployment, service ports, and environment variables.
---

# Deployment

## Docker Compose (local / self-hosted)

The `docker-compose.yml` at the repo root starts all three services:

```bash
docker compose up          # start all services
docker compose up api web  # start only API + web (skip docs)
docker compose up --build  # rebuild images first
```

### Services

| Service | Port | Image |
|---------|------|-------|
| `api` | `8000` | Python 3.11 + FastAPI + py2dataiku |
| `web` | `5173` | Node 20 + Vite dev server |
| `docs` | `3000` | Node 20 + Docusaurus dev server |

### Health checks

The `api` service has a Docker health check:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 10s
  timeout: 5s
  retries: 3
```

`apps/web` waits for the API to be healthy before showing the Convert page UI.

## Environment variables

### API (`apps/api`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | No | — | Anthropic API key for LLM mode |
| `OPENAI_API_KEY` | No | — | OpenAI API key for LLM mode |
| `SHARE_SECRET_KEY` | Yes (prod) | dev-insecure-key | HMAC secret for share link signing |
| `API_AUTH_ENABLED` | No | `false` | Enable bearer token auth |
| `MAX_CODE_SIZE_BYTES` | No | `262144` (256 KB) | Max Python code payload size |
| `DB_PATH` | No | `./data/studio.db` | SQLite database path |
| `LOG_LEVEL` | No | `INFO` | Python logging level |

### Web (`apps/web`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_BASE_URL` | No | `http://localhost:8000` | API base URL |
| `VITE_WS_BASE_URL` | No | `ws://localhost:8000` | WebSocket base URL |

### Docs (`apps/docs`)

The docs site has no runtime environment variables. It is a static site after build.

## Production deployment

For production:

1. Set `SHARE_SECRET_KEY` to a strong random value (`openssl rand -hex 32`).
2. Set `API_AUTH_ENABLED=true` and configure auth tokens.
3. Mount a persistent volume for `DB_PATH`.
4. Put a reverse proxy (nginx, Caddy) in front of both `api` (8000) and `web` (5173).
5. Set `VITE_API_BASE_URL` to the public API URL before building the web app.

The web app must be built with the correct `VITE_API_BASE_URL` baked in (Vite embeds env vars at build time):

```bash
VITE_API_BASE_URL=https://api.example.com pnpm --filter apps-web build
```

## Studio Docs GitHub Pages

The Studio docs site is deployed to GitHub Pages at `https://m-deane.github.io/py-iku/studio/` when a git tag is pushed. See `.github/workflows/studio-docs.yml`. On non-tag pushes, only the build step runs (artifact uploaded but not deployed).
