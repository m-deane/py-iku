---
title: Roadmap
sidebar_position: 99
description: Planned milestones and future work for py-iku Studio.
---

# Roadmap

The full milestone tree and planning document is at [`.claude_plans/py-iku-studio.md`](https://github.com/m-deane/py-iku/blob/main/.claude_plans/py-iku-studio.md).

## Shipped milestones (M0–M9)

| Milestone | Deliverable |
|-----------|------------|
| M0 | pnpm monorepo, CI matrix |
| M1 | FastAPI wrapper, `/health`, `/convert`, `packages/types` codegen |
| M2 | Design tokens, 37 recipe glyphs, Storybook |
| M3 | `packages/flow-viz` — React Flow, ELK layout, zone overlays |
| M4 | `apps/web` — Monaco, Zustand, TanStack Query, routing shell |
| M5 | WebSocket streaming, inspector panel, diff view |
| M6 | Export bundle API, catalog browser |
| M7 | Score, share links, audit log, snippet gallery, validation panel |
| M8 | Playwright E2E, Vitest, Storybook visual regression, a11y |
| M9 | Docusaurus docs site, DSS write-back design doc, code review pass |

## Planned milestones

### M10 — DSS Write-back

Implement the `DSSApiSink` class, enabling Studio to write converted flows directly to a Dataiku DSS project via the `dataikuapi` Python client. Key features:

- Enable the `/settings/connections` page (currently disabled by flag).
- Implement `DSSApiSink.write()` with idempotency (content-hash check, upsert-or-skip).
- Per-node deployment status badges (live data, not always `not_deployed`).
- Dry-run diff modal showing what will change in DSS before committing.
- Rollback: snapshot DSS project state before write, reverse-diff restore.
- Telemetry: `dss.write` and `dss.dry_run` events in the audit log.

See [DSS Write-back Design](/future-dss-writeback) (in the library docs) for the detailed design.

### M11 — Authentication & multi-user

- Full bearer token auth with API key management UI.
- Per-user flow storage (user-scoped flows, not shared SQLite).
- OAuth2 integration (GitHub, Google).
- Per-token revocation for share links.
- Retention policies and audit log export to S3.

### M12 — Zone auto-assignment

- `py2dataiku` automatically assigns recipes to zones based on data lineage heuristics.
- Zone drag and drop in the canvas.
- Zone-level export (DSS "project export" format).

### M13 — Parallel execution simulation

- Execution sim respects DAG parallelism (independent branches execute simultaneously).
- Performance profiling view: estimated wall-clock time per recipe based on heuristic.

## Design doc: future DSS write-back

A detailed design document for M10 is in the library docs:
[`docs/future-dss-writeback.md`](https://github.com/m-deane/py-iku/blob/main/docs/future-dss-writeback.md) (visible at the [py2dataiku library docs site](https://m-deane.github.io/py-iku/)).
