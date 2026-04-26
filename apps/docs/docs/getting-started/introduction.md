---
title: Introduction
sidebar_position: 1
description: Overview of py-iku Studio — what it is, how it fits with the py2dataiku library, and when to use it.
---

# py-iku Studio

py-iku Studio is a browser-based visual editor that wraps the [`py2dataiku`](https://m-deane.github.io/py-iku/) Python library and exposes it as an interactive web application. You paste Python data-processing code (pandas, numpy, scikit-learn), choose a conversion mode, and Studio renders a live Dataiku DSS flow graph that you can inspect, compare, export, and eventually write back to a DSS project.

## What Studio adds over the CLI

| Capability | `py2dataiku` CLI | Studio |
|------------|-----------------|--------|
| Convert Python to Dataiku flow | Yes | Yes |
| Visual node-by-node flow graph | SVG export only | Interactive, zoomable |
| Side-by-side rule vs LLM diff | No | Yes (diff view) |
| Per-node recipe inspector | No | Yes |
| Export zip / SVG / PNG / PDF | Via `flow.save()` | One-click download |
| Snippet gallery | No | Yes (Monaco editor integration) |
| Shareable links | No | Yes (HMAC-signed, TTL-bound) |
| Audit log | No | Yes (append-only, paginated) |
| 122-processor catalog browser | `ProcessorCatalog()` in Python | Searchable UI |

## Who it is for

- **Data engineers** who write pandas pipelines and want to migrate to Dataiku DSS without rewriting everything by hand.
- **Dataiku project owners** who want to review candidate flows before importing them into a DSS project.
- **Teams** evaluating rule-based vs LLM-based conversion quality.

## Relationship to the library

Studio is a thin orchestration layer. It never reimplements conversion logic — all conversion, export, and validation go through `py2dataiku` on the API server. The frontend only renders the `DataikuFlow.to_dict()` payload that the API returns.

```
Browser  →  apps/web  →  apps/api  →  py2dataiku
                              |
                         DataikuFlow.to_dict()
                              |
                     packages/flow-viz renders it
```

## Milestones shipped

Studio was built incrementally across M0–M8:

| Milestone | What shipped |
|-----------|-------------|
| M0 | pnpm monorepo, CI matrix |
| M1 | FastAPI wrapper, `/health`, `/convert`, Pydantic v2 schemas, `packages/types` codegen |
| M2 | Design tokens (`tokens.json`), 37 recipe glyphs, Storybook |
| M3 | `packages/flow-viz` — React Flow + ELK layout, zone overlays, focus mode, execution sim |
| M4 | `apps/web` shell — Monaco, Zustand, TanStack Query, routing |
| M5 | WebSocket streaming, inspector panel, diff view |
| M6 | Export bundle API, catalog browser |
| M7 | Score, share links, audit log, snippet gallery, validation panel |
| M8 | Playwright E2E, Vitest, Storybook visual regression, accessibility (axe) |
| M9 | This documentation site |

See [Roadmap](/roadmap) for planned milestones.
