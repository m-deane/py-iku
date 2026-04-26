# Testing Guide

## Unit tests

### Python library (`py2dataiku`)
```bash
pytest tests/ -v                                  # all 1800+ tests
pytest tests/test_py2dataiku/test_api.py -v       # single file
pytest tests/ --cov=py2dataiku --cov-report=html  # with coverage
```

### API (`apps/api`)
```bash
cd apps/api
pytest tests/ -v
```

### Web app (`apps/web`)
```bash
pnpm --filter apps-web test        # vitest single run
pnpm --filter apps-web test:watch  # watch mode
```

### Flow-viz package
```bash
pnpm --filter @py-iku-studio/flow-viz test
```

### All workspaces at once (from repo root)
```bash
pnpm vitest run        # uses vitest.workspace.ts
# or
pnpm test              # runs pnpm -r test
```

## E2E tests (Playwright)

### Prerequisites
```bash
pnpm --filter apps-web exec playwright install --with-deps chromium webkit
```

### Run locally (two terminals)
Terminal 1 — API:
```bash
cd apps/api && uvicorn app.main:app --port 8000
```
Terminal 2 — web:
```bash
pnpm --filter apps-web dev
```
Terminal 3 — tests:
```bash
pnpm --filter apps-web exec playwright test --project=chromium
```

### Run with the bash launcher (starts everything for you)
```bash
bash scripts/e2e.sh                    # both browsers
bash scripts/e2e.sh --project=chromium # chromium only
bash scripts/e2e.sh --headed           # headed mode
```

### Run in Docker Compose
```bash
docker compose --profile e2e up --abort-on-container-exit --exit-code-from e2e
```

## Storybook visual tests (`packages/flow-viz`)
```bash
# Start Storybook dev server
pnpm --filter @py-iku-studio/flow-viz storybook

# Run test-storybook against it
pnpm --filter @py-iku-studio/flow-viz test-storybook
```

## Reports and artifacts

| Test type | Report location |
|-----------|----------------|
| Playwright | `apps/web/playwright-report/index.html` |
| Vitest coverage | `apps/web/coverage/index.html` |
| CI artifacts | GitHub Actions → workflow run → Artifacts |

## Playwright UI / debug mode
```bash
pnpm --filter apps-web exec playwright test --ui
pnpm --filter apps-web exec playwright test --debug
pnpm --filter apps-web exec playwright test --headed
```

## Update snapshots
```bash
pnpm --filter apps-web exec playwright test --update-snapshots
```

## What M8 still needs to add
- Visual regression snapshots locked per browser (Percy or Playwright `toHaveScreenshot`).
- Accessibility checks via `axe-playwright`.
- Performance budgets (Lighthouse CI or custom timing assertions).
- Full coverage gate on `apps/api` (target ≥80 % line coverage).
