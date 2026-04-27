---
title: py-iku Studio
slug: /
sidebar_position: 0
description: Convert pandas, numpy, and scikit-learn code to Dataiku DSS recipes and flows — interactive web UI on top of the py2dataiku library.
---

# py-iku Studio

A web UI on top of the [`py2dataiku`](https://m-deane.github.io/py-iku/) library. Paste Python code, get a Dataiku DSS flow you can inspect, diff, score, export, and share.

## What's here

- **[Getting Started](/getting-started/introduction)** — what Studio is, how to run it locally, and how the pieces fit together.
- **[User Guide](/user-guide/convert-page)** — the convert / catalog / diff / inspector / share / audit experience.
- **[API Reference](/api-reference/overview)** — every FastAPI route the Studio exposes (37 recipe types, 122 processors, streaming WS conversion, signed share links, audit log).
- **[flow-viz](/flow-viz/overview)** — the React Flow visualization library: nodes, layout, zones, focus mode, execution sim, SVG/PNG/PDF export.
- **[Types](/types/overview)** — the codegen pipeline that keeps TypeScript bindings + zod runtime validation in sync with the API.
- **[Operations](/operations/deployment)** — Docker compose, CI matrix, env vars, coverage gates.
- **[Contributing](/contributing/overview)** — adding new recipe types, commit conventions, milestone naming.
- **[Roadmap](/roadmap)** — what's shipped (M0–M9) and what's next (DSS write-back).

## Architecture at a glance

```
apps/web (React 18 + Vite + Monaco)
   │
   ▼  REST + WebSocket
apps/api (FastAPI)
   │
   ▼  in-process call
py2dataiku (the library — converts Python → DataikuFlow)
```

`packages/flow-viz` renders the resulting flow; `packages/types` keeps the wire format honest with zod-backed runtime validation generated from the OpenAPI snapshot.

## Quickstart

```bash
git clone https://github.com/m-deane/py-iku.git
cd py-iku
docker compose up -d            # api + web
open http://localhost:5173
```

Full setup is in **[Getting Started → Quickstart](/getting-started/quickstart)**.
