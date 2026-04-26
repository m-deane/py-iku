---
title: CI Matrix
sidebar_position: 2
description: GitHub Actions jobs, coverage gates, and test suites in the CI pipeline.
---

# CI Matrix

The CI pipeline is defined in `.github/workflows/ci.yml`. It runs on every push to `main` and `claude/**` branches, and on all pull requests.

## Jobs

### python

Runs on Python 3.11 and 3.12 (matrix). Steps:

1. `pip install -e ".[dev]"`
2. `pytest tests/ -x --tb=short` — runs all 2372+ `py2dataiku` unit tests.
3. `ruff check py2dataiku/`
4. `mypy py2dataiku/`

### api

Coverage gate for `apps/api`. Steps:

1. `pip install -e ".[dev]" && pip install -e "apps/api[dev]"`
2. `pytest apps/api/tests --cov=apps/api/app --cov-fail-under=80`
3. Uploads coverage XML as artifact.

### node

Runs all Node packages. Steps:

1. `pnpm install --ignore-scripts`
2. `pnpm -r --if-present build`
3. Tests: `@py-iku-studio/types`, `@py-iku-studio/flow-viz`, `apps-web` (with `--coverage`).
4. Uploads web coverage as artifact.

### types-drift

Checks that `openapi.snapshot.json` matches the running API. Depends on: `[node]`. Steps:

1. Installs Python + Node deps.
2. Runs `pnpm --filter @py-iku-studio/types check-drift`.

Fails if any path, schema, or component differs. This job is `continue-on-error: false` — it must pass.

### e2e

Playwright end-to-end tests. Depends on: `[node]`. Steps:

1. Installs Playwright browsers (chromium, webkit).
2. Installs Python + API deps.
3. Runs `bash scripts/e2e.sh --project=chromium --project=visual --project=a11y`.
4. Uploads Playwright report on failure.

### storybook

Storybook visual regression tests. Depends on: `[node]`. Steps:

1. Builds Storybook static site.
2. Starts `http-server` on port 6006.
3. Runs `test-storybook` against the static build.

### studio-docs

Builds the Studio Docusaurus site. Steps:

1. `pnpm install --ignore-scripts`
2. `pnpm --filter apps-docs build`
3. Uploads `apps/docs/build/` as artifact.

## Coverage gates

| Suite | Gate | Tool |
|-------|------|------|
| `py2dataiku` tests | None (all pass or fail) | pytest |
| `apps/api` | ≥ 80% line coverage | pytest-cov |
| `apps/web` | Configured in `vitest.config.ts` | vitest |
| Playwright | Pass all tests | playwright |

## Visual regression

Visual snapshots are stored in `packages/flow-viz/tests/__snapshots__/`. On the first run in a new environment, run `npx playwright test --update-snapshots` to establish baselines. Subsequent runs compare against these baselines; pixel diffs above the threshold fail the job.

LLM-generated flow snapshots are excluded from visual regression (non-deterministic). Only rule-based flows are used as baselines.

## Accessibility

The `a11y` Playwright project runs axe-core against every route in `apps/web`. Violations at severity `serious` or `critical` fail the job.
