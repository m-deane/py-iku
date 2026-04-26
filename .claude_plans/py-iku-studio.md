# py-iku-studio — Planning Doc

Branch: `claude/react-dataiku-dashboard-CUFl4` | Top-level adds: `apps/`, `packages/`, `docs/`
Wraps existing `py2dataiku` library. No edits to `py2dataiku/` source from this initiative.

---

## 1. Milestone tree

| ID | Goal | Owner role | Prereqs | Exit criteria |
|----|------|------------|---------|---------------|
| M0 | Monorepo bootstrap (pnpm workspace, ruff/black config inherited, CI matrix py3.11/node20, pre-commit) | `python-pro` | — | `pnpm i && pnpm -r build` green; `pytest` still green; CI green on PR |
| M1 | FastAPI wrapper around `py2dataiku.api.convert` + Pydantic v2 schemas + TS codegen of `DataikuFlow`, `DataikuRecipe`, `RecipeType`, `ProcessorType`, `PrepareStep`, `FlowGraph` | `python-pro` | M0 | `/health` 200; `packages/types` emits `.d.ts` from JSON schema; round-trip test `flow.to_dict()` ↔ TS parse |
| M2 | Design system tokens + Dataiku-faithful node/zone specs (recipe glyphs, dataset shapes, connection-type colors), reuse `themes.py` palette via JSON export | `ui-ux-designer` | M0 | Figma + tokens.json shipped; Storybook MDX of 37 recipe glyphs + 8 dataset variants; light/dark parity screenshots |
| M3 | `packages/flow-viz` React Flow + D3 layered layout; zone overlays, minimap, focus mode, animated execution sim; Storybook stories per `RecipeType` | `viz-specialist` | M2 | All 37 `RecipeType` nodes render; 100-node fixture <16ms frame; visual snapshots in Storybook; export to SVG/PNG works |
| M4 | `apps/web` shell — Vite + Monaco editor, settings drawer (provider/model/keys), Zustand store, TanStack Query, route shell | `frontend-lead` | M1, M2 | App boots; Monaco loads pandas snippet; settings persisted; 401/429 surfaced with toasts |
| M5 | Conversion streaming (WS), per-node inspector panel, rule-vs-LLM diff view (side-by-side flow + JSON diff) | `frontend-lead` + `viz-specialist` | M1, M3, M4 | WS streams progress events; click node → inspector shows `RecipeSettings` subclass fields; diff highlights added/removed/changed nodes |
| M6 | Export bundle (`/export/{format}`: zip/json/yaml/svg/png/pdf) + recipe & processor catalog browser using `ProcessorCatalog` (122 entries) | `python-pro` + `frontend-lead` | M5 | Round-trip `flow.save()` ↔ download; catalog browser searchable, filterable by category; PDF renders multi-page |
| M7 | Commercial extras — cost/complexity score, share links (signed URL), audit log, snippet gallery, validation panel, team workspace stub | `frontend-lead` + `python-pro` | M5, M6 | Score reproducible from `FlowGraph` metrics; `/flows/{id}/share` returns short URL; `/audit` returns paginated events |
| M8 | E2E + visual regression hardening — Playwright, Vitest, Storybook test-runner, accessibility (axe) | `test-engineer` | M3–M7 | ≥80% line cov on `apps/api`; Playwright suites green headless+headed; baseline screenshots locked |
| M9 | Docusaurus docs site + DSS write-back design doc (`docs/future-dss-writeback.md`) + `prompt-engineer` reviews LLM prompts | `docusaurus-expert` + `prompt-engineer` + `code-reviewer` | M7 | Docs deploy preview; design doc reviewed; final code review pass on all packages |

---

## 2. Dependency DAG

```
                  M0 (monorepo)
                 /     |      \
              M1     M2       (shared infra)
              | \     |
              |  \    M3 ─────────┐
              |   \   |           |
              |    \  |           |
              M4 ───────┐         |
                   \    |         |
                    \   |         |
                     M5 ──────────┤
                     |            |
                     M6 ──────────┤
                     |            |
                     M7 ──────────┤
                                  |
                              M8 (hardening)
                                  |
                              M9 (docs + review)
```

Blocking edges: M0→all; M1→M4,M5,M6,M7; M2→M3,M4; M3→M5; M4→M5; M5→M6,M7; M6→M7; M3..M7→M8; M8→M9.

---

## 3. Repo layout

```
py-iku/
  py2dataiku/                       # untouched
  apps/
    api/
      pyproject.toml                # adds: fastapi, uvicorn[standard], pydantic>=2, websockets, python-multipart, weasyprint
      app/
        __init__.py
        main.py                     # FastAPI app, CORS, lifespan
        deps.py                     # config, auth stub, request id
        routes/
          convert.py                # POST /convert, WS /convert/stream
          catalog.py                # GET /catalog/recipes, /catalog/processors{/type}
          export.py                 # POST /export/{format}
          flows.py                  # POST /flows, GET /flows/{id}, /share
          audit.py                  # GET /audit
          health.py
        schemas/                    # Pydantic v2 mirrors of py-iku models
          flow.py                   # wraps DataikuFlow.to_dict() shape
          recipe.py                 # RecipeType, RecipeSettings union
          processor.py              # ProcessorType, PrepareStep
          events.py                 # WS event envelopes
        services/
          conversion.py             # thin wrapper over py2dataiku.api.convert
          streaming.py              # async generator → WS frames
          export_service.py         # delegates to py2dataiku.visualizers
          catalog_service.py        # ProcessorCatalog instance
          score.py                  # cost/complexity heuristic
        sinks.py                    # FlowSink ABC + ZipBundleSink, JsonSink, DSSApiSink (stub)
        store/
          flows_repo.py             # SQLite/JSON persistence
          audit_repo.py
        security/
          share_links.py            # HMAC-signed short URLs
          secrets.py                # API key handling (env + KMS-ready iface)
      tests/
        test_routes/
        test_sinks/
        conftest.py
    web/
      package.json                  # react@18, vite@5, typescript, @tanstack/react-query, zustand, monaco-editor, reactflow, d3, zod
      tsconfig.json
      vite.config.ts                # + monaco worker plugin, alias @flow-viz, @types
      index.html
      src/
        main.tsx
        app/
          router.tsx                # routes: /, /convert, /flow/:id, /catalog, /diff, /share/:token, /audit, /settings
          providers.tsx             # QueryClient, Theme, Toast
        features/
          editor/                   # Monaco wrapper, snippet gallery
          conversion/               # rule vs LLM picker, WS hook
          inspector/                # per-node panel
          diff/                     # side-by-side flow + JSON diff
          export/                   # download bundle UI
          catalog/                  # recipe + processor browser
          validation/               # validation panel
          settings/                 # provider/model/keys drawer
          deploy/                   # stub: Connections page, deploy badges
        state/
          flowStore.ts              # zustand
          settingsStore.ts
        api/
          client.ts                 # generated from packages/types
          ws.ts
        styles/
          tokens.css                # generated from design tokens
        components/                 # generic
      tests/
        e2e/                        # playwright
        unit/                       # vitest
      playwright.config.ts
  packages/
    flow-viz/
      package.json                  # peer: react, reactflow, d3
      src/
        FlowCanvas.tsx
        nodes/                      # one per RecipeType (37)
        edges/
        layout/                     # dagre/elk wrapper, zone overlay
        sim/                        # animated execution sim
        export/                     # toSvg, toPng, toPdf
        theme/                      # consumes tokens.json
        index.ts
      .storybook/
      stories/                      # Story per node + composite flows
      tests/                        # vitest + storybook test-runner
    types/
      package.json
      src/
        index.ts                    # generated TS from Pydantic schemas
        guards.ts                   # zod schemas
      scripts/
        codegen.ts                  # pulls /openapi.json → ts-types
  docs/                             # docusaurus
    docusaurus.config.ts
    sidebars.ts
    docs/
      intro.md
      api/
      guides/
      future-dss-writeback.md       # design doc (no impl)
  docker-compose.yml                # api + web + docs services
  .github/workflows/
    ci.yml                          # py + node + e2e + storybook visual
  pnpm-workspace.yaml
  package.json                      # root, scripts dispatch
  pyproject.toml                    # root unchanged; apps/api has its own
```

Key configs: `pnpm-workspace.yaml` (apps/*, packages/*, docs), `vite.config.ts` (alias + monaco workers), `playwright.config.ts` (chromium/webkit/firefox + visual snapshots), `docker-compose.yml` (api:8000, web:5173, docs:3000), `apps/api/pyproject.toml` (extras `[api]` adds fastapi stack), root `tsconfig.base.json` with project refs.

---

## 4. API contract

All JSON; WS frames are JSON envelopes `{event, seq, ts, payload}`. Auth: bearer token (stub for M1, real in M7). Errors map to py-iku `Py2DataikuError` hierarchy → RFC7807 problem+json.

| Method | Path | Request | Response | Notes |
|--------|------|---------|----------|-------|
| GET | `/health` | — | `{status, version, py_iku_version}` | reads `py2dataiku.__version__` |
| POST | `/convert` | `{code, mode: "rule"\|"llm", provider?, model?, options?}` | `DataikuFlow.to_dict()` + `{score, warnings[]}` | sync; ≤30s; uses `convert()` from py-iku |
| WS | `/convert/stream` | first frame `{code, mode, ...}` | events: `started`,`ast_parsed`,`recipe_created`,`processor_added`,`optimized`,`completed`,`error` | server pushes; client may send `cancel` |
| GET | `/catalog/recipes` | — | `[{type, name, category, icon, description}]` × 37 | from `RecipeType` enum + visualizer `icons.py` |
| GET | `/catalog/processors` | `?q=&category=` | `[{type, name, category, ...}]` × 122 | uses `ProcessorCatalog().list_processors()` |
| GET | `/catalog/processors/{type}` | path `type: ProcessorType` | full processor catalog entry | `catalog.get_processor(type)` |
| POST | `/export/{format}` | `{flow: DataikuFlow.to_dict(), opts?}`; format ∈ `zip\|json\|yaml\|svg\|png\|pdf` | binary stream (`Content-Disposition`) | json/yaml via `flow.save`; svg/png/pdf via `py2dataiku/visualizers/`; zip bundles json + svg + manifest |
| POST | `/flows` | `{flow, name, tags?}` | `{id, created_at}` | persists via `flows_repo` |
| GET | `/flows/{id}` | — | `{id, name, flow, created_at, updated_at}` | round-trips through `DataikuFlow.from_dict` |
| POST | `/flows/{id}/share` | `{ttl_seconds?, scopes?}` | `{token, url, expires_at}` | HMAC-signed; read-only viewer route |
| GET | `/share/{token}` | — | same as `GET /flows/{id}` | no auth; ratelimited |
| GET | `/audit` | `?since=&actor=&limit=` | `{items[], next_cursor}` | append-only event log |
| POST | `/score` | `{flow}` | `{complexity, cost_estimate, breakdown[]}` | reuses `FlowGraph` metrics |
| POST | `/diff` | `{a: flow, b: flow}` | `{added[], removed[], changed[]}` keyed by node id | for rule-vs-LLM view |

---

## 5. DSS write-back seam

- ABC location: `apps/api/sinks.py`
  ```
  class FlowSink(ABC):
      def write(self, flow: DataikuFlow, opts: SinkOptions) -> SinkResult: ...
      def dry_run(self, flow: DataikuFlow, opts: SinkOptions) -> DryRunReport: ...
      def capabilities(self) -> SinkCapabilities: ...
  ```
- Implementations shipped in M6/M7:
  - `ZipBundleSink` — packages json + svg + manifest into a zip; default for downloads.
  - `JsonSink` — single-file `flow.to_json()` output; used by `/export/json`.
  - `DSSApiSink` (stub) — raises `NotImplementedError` with structured `next_steps`; surfaces capability flag `supported=False` for UI gating.
- Stubbed UI affordances (built but disabled-by-flag):
  - **Connections page** (`/settings/connections`) — list/add DSS instances (host, project key, API key alias); save to settings store only.
  - **Per-node Deployment Status badge** — appears on `FlowCanvas` nodes; renders `not_deployed` for all nodes today; reads from `flow.metadata.deployment_status`.
  - **Dry-Run Diff modal** — invoked from a "Preview Deploy" CTA; calls `DSSApiSink.dry_run` which returns a fixed "DSS write-back not yet enabled" payload until M10.
- `docs/future-dss-writeback.md` will cover:
  - Auth model (API key vs OAuth, key rotation, scope minimization).
  - Idempotency strategy (deterministic recipe ids, content-hash check, upsert-or-skip).
  - Rollback (snapshot of previous DSS project state, reverse-diff apply, manual restore button).
  - Permissions matrix (admin vs editor vs viewer × create/update/delete recipe/dataset/connection).
  - Required `dataikuapi` surface (`DSSClient.get_project`, `project.create_recipe`, `recipe.set_definition_and_payload`, `dataset.set_schema`, `flow.replace_input/output`, error taxonomy).
  - Validation pre-flight (connection reachability, schema compatibility, recipe-type version match against DSS 14).
  - Telemetry & audit hooks (write events to `/audit` with diff hash + actor + dss_project_key).

---

## 6. Risk register

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM nondeterminism breaks visual regression baselines | Flaky CI, slow merges | Pin LLM responses via cassette fixtures (`pytest-recording`); run visual snapshots only on rule-based flows in CI; gate LLM-flow snapshots behind manual job |
| React Flow perf degrades >100 nodes (focus mode, animated sim) | Janky UX, 60fps miss | Virtualize off-screen nodes, memoize node renderers, switch to `elkjs` worker thread for layout, frame-budget telemetry in dev, perf budget test in M8 |
| py-iku model drift breaks generated TS types | Runtime parse failures | TS codegen from `/openapi.json` runs in CI; contract tests round-trip `DataikuFlow.to_dict()`; semver-pin py-iku in `apps/api/pyproject.toml`; nightly drift check job |
| LLM API key handling / leakage in browser | Security incident, compliance fail | Keys never sent to browser; user pastes into settings → POST to API → stored encrypted at rest (Fernet); BYO-key per session option; redact in audit log; CSP + secure cookies |
| DSS API future shape unknown (DSS 15+ may change) | Rework of `DSSApiSink` | Keep `FlowSink` ABC narrow; capture DSS shape in `docs/future-dss-writeback.md`; integration test against DSS Community Edition Docker; feature-flag rollout |
| Large Python files crash AST parse / OOM | API 500s, bad UX | Hard limit (e.g., 256KB) with 413 response; stream parse with timeout; offload to worker process; show actionable validation panel error citing `InvalidPythonCodeError` |

---

## 7. First-week execution order

1. `python-pro` — M0: scaffold pnpm workspace, root `package.json`, `pnpm-workspace.yaml`, root `tsconfig.base.json`, CI matrix, pre-commit. Verify existing `pytest` still green.
2. `[||]` `ui-ux-designer` — M2 kickoff: extract `themes.py` palette to `tokens.json`, draft Figma node spec for 37 `RecipeType` glyphs + 8 dataset variants.
3. `[||]` `python-pro` — M1 part A: create `apps/api/` skeleton, `/health`, lifespan, settings, problem+json error mapper for `Py2DataikuError`.
4. `python-pro` — M1 part B: implement `POST /convert` + Pydantic schemas mirroring `DataikuFlow`/`DataikuRecipe`/`PrepareStep`; emit `/openapi.json`.
5. `[||]` `frontend-lead` — M4 part A: bootstrap `apps/web` (Vite + TS + React 18), routing shell, theme provider, Zustand stores skeletons.
6. `[||]` `python-pro` — `packages/types` codegen script: `/openapi.json` → `.d.ts` + zod guards; wire to CI.
7. `viz-specialist` — M3 part A: `packages/flow-viz` skeleton, Storybook init, layout engine wrapper (`elkjs` in worker), 5 representative `RecipeType` nodes (PREPARE, GROUPING, JOIN, SPLIT, WINDOW) as smoke test.
8. `[||]` `frontend-lead` — M4 part B: Monaco editor integration, snippet picker stub, settings drawer (provider/model/keys), wire `/health`.
9. `python-pro` — M1 part C: `WS /convert/stream` with event envelopes; backpressure + cancel; unit tests with `pytest-asyncio`.
10. `[||]` `viz-specialist` — M3 part B: complete remaining 32 `RecipeType` nodes from catalog; zone overlay + minimap; visual snapshot baselines.
11. `test-engineer` — initial Playwright + Vitest config, smoke e2e (`/` loads, paste-and-convert rule-based), Storybook test-runner CI job.
12. `code-reviewer` — end-of-week review pass: API contract conformance to py-iku models, security review of key handling, perf budget check on `flow-viz`.
