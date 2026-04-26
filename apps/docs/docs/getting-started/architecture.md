---
title: Architecture Overview
sidebar_position: 3
description: How the four Studio components fit together — API, web, flow-viz, and types.
---

# Architecture Overview

Studio is a pnpm monorepo with four logical layers. The plan document at `.claude_plans/py-iku-studio.md` §1 and §3 contains the authoritative milestone tree and full directory layout; this page summarises the runtime architecture.

## Service topology

```
                 Browser (React)
                      |
               apps/web (Vite, port 5173)
               ├── Monaco editor
               ├── packages/flow-viz (React Flow canvas)
               └── TanStack Query / Zustand
                      |
               REST + WebSocket
                      |
               apps/api (FastAPI, port 8000)
               ├── POST /convert  ─────────────────────────────────┐
               ├── WS  /convert/stream                             │
               ├── GET /catalog/recipes, /catalog/processors       │
               ├── POST /export/{format}                           ▼
               ├── POST/GET /flows/{id}                     py2dataiku
               ├── POST /flows/{id}/share                   (Python library)
               ├── GET /share/{token}                             │
               ├── GET /audit                                     │
               ├── POST /score, /diff                             │
               └── GET /health                                    │
                                                                  │
                                                    DataikuFlow.to_dict() ◄──┘
```

## Component responsibilities

### `apps/api` — FastAPI server

The API server is a thin orchestration layer over `py2dataiku`. It:

- Accepts Python code from the browser (or any HTTP client).
- Calls `py2dataiku.convert()` or `py2dataiku.convert_with_llm()` depending on the `mode` field.
- Serialises the resulting `DataikuFlow` object via `.to_dict()`.
- Handles streaming via WebSocket, emitting structured event frames (`{event, seq, ts, payload}`).
- Provides catalog endpoints backed by `ProcessorCatalog()` (122 entries) and `RecipeType` enum (37 types).
- Manages flow persistence (SQLite), HMAC-signed share links, and an append-only audit log.
- Maps the `Py2DataikuError` hierarchy to RFC 7807 problem+json responses.

Source: `apps/api/app/`.

### `apps/web` — React SPA

The web application is a Vite + React 18 SPA that:

- Hosts a Monaco code editor with a snippet gallery.
- Renders flow graphs via `packages/flow-viz`.
- Manages state with Zustand (flow store, settings store).
- Fetches data with TanStack Query (caching, background refetch, optimistic updates).
- Routes: `/`, `/convert`, `/catalog`, `/diff`, `/audit`, `/snippets`, `/share/:token`, `/settings`.

Source: `apps/web/src/`.

### `packages/flow-viz` — React Flow canvas

The visualization library is consumed by `apps/web`. It:

- Renders all 37 `RecipeType` node types as custom React Flow nodes.
- Computes layout with ELK (Eclipse Layout Kernel) running in a Web Worker — target < 16ms per frame for 100-node graphs.
- Supports zone overlays (colour-coded `Zone`/`ZoneLayer` components), a minimap, and focus mode.
- Provides animated execution simulation (`useExecutionSim`).
- Exports to SVG, PNG, and PDF via `toSvg`, `toPng`, `toPdf`.

Source: `packages/flow-viz/src/`.

### `packages/types` — Shared TypeScript types

Generated TypeScript types and Zod validators, auto-derived from the FastAPI `/openapi.json` endpoint. Key exports:

- `DataikuFlow`, `DataikuRecipe`, `PrepareStep`, `FlowGraph` — mirrors of the Python models.
- `RecipeType`, `ProcessorType` — enum values.
- Zod guard functions in `guards.ts` for runtime validation.

Source: `packages/types/src/`. Codegen script: `packages/types/scripts/codegen.ts`.

## Data flow for a conversion request

1. User pastes code into Monaco and clicks **Convert**.
2. `apps/web` sends `POST /convert` with `{code, mode: "rule"}`.
3. `apps/api` validates the request (Pydantic v2 schema), enforces the 256 KB size limit, and calls `py2dataiku.convert(code)`.
4. `py2dataiku` runs `CodeAnalyzer` (AST) or `LLMCodeAnalyzer`, then `FlowGenerator` or `LLMFlowGenerator`, producing a `DataikuFlow`.
5. The API serialises `flow.to_dict()`, appends a `score` and `warnings[]`, and returns `ConvertResponse`.
6. `apps/web` writes the payload to Zustand's `flowStore`.
7. `packages/flow-viz`'s `FlowCanvas` reads the store and re-renders the graph.

For WebSocket streaming (`/convert/stream`), step 3–5 emit incremental events (`recipe_created`, `processor_added`, etc.) so the canvas animates as nodes appear.

## Security model

- LLM API keys are never sent to the browser. Users paste them into the Settings drawer, which POSTs to the API, which stores them encrypted at rest (Fernet). Keys are redacted in audit log entries.
- Share links are HMAC-signed JWTs with a configurable TTL and read-only scope. The `/share/{token}` endpoint is rate-limited and does not require authentication.
- The `/settings/connections` page (DSS write-back) is built but disabled behind a feature flag pending M10.

## Design token origin

Visual styling for recipe and dataset nodes derives from `docs/design/tokens.json`, which was extracted from `py2dataiku/visualizers/themes.py` during M2. Changes to themes should be made in `themes.py` first, then reflected in `tokens.json`.
