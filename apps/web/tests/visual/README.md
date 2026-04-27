# Visual regression suite

Playwright-driven full-page screenshot diffs for every navigable route in
`apps/web/src/app/router.tsx` × {light, dark} theme. Baselines committed
under `__screenshots__/` make UI regressions reviewable as image diffs in
PRs.

## Files

```
tests/visual/
├── README.md                  ← this file
├── _helpers.ts                ← `prepare(page)` shared bootstrap
├── snapshots.spec.ts          ← THE comprehensive route × theme grid
├── home.visual.spec.ts        ← legacy single-page specs (retained, but
├── convert.visual.spec.ts        snapshots.spec.ts is the source of truth
├── catalog.visual.spec.ts        for new baselines)
├── …
└── __screenshots__/           ← committed baseline PNGs
```

## Running

```bash
# From repo root or apps/web/:
pnpm --filter apps-web test:visual              # diff against baselines
pnpm --filter apps-web test:visual:update       # regenerate baselines
```

The dev server must be reachable at `http://localhost:5173`. In local runs
Playwright's `webServer` block (in `playwright.config.ts`) starts it for
you; in CI the orchestration script (`scripts/e2e.sh`) does the same.

## Updating baselines

Visual baselines are intentionally **not** required to pass for an in-flight
PR that changes UI on purpose. The workflow is:

1. Make your UI change.
2. Run `pnpm test:visual`. Failures are expected when the change is real.
3. Inspect the diffs in `apps/web/playwright-report/` (or open the PNG diff
   produced by Playwright in `apps/web/test-results/`).
4. If the diffs look correct, run `pnpm test:visual:update` to write new
   baselines, commit them with the UI change in the same PR, and call out
   "regenerated visual baselines" in the PR description.

Reviewers should diff the baseline PNGs as part of the PR review, the same
way they review code. A PR that updates baselines without calling out the
intent is a smell — ask the author what UI change drove the regen.

## Coverage grid

`snapshots.spec.ts` enumerates the full route list:

| Route               | id           |
|---------------------|--------------|
| `/`                 | home         |
| `/convert`          | convert      |
| `/catalog`          | catalog      |
| `/snippets`         | snippets     |
| `/diff`             | diff         |
| `/audit`            | audit        |
| `/settings`         | settings     |
| `/flow/:id`         | flow-id      |
| `/editor`           | editor       |
| `/inspector`        | inspector    |
| `/validation`       | validation   |
| `/export`           | export       |
| `/deploy`           | deploy       |
| `/share/:token`     | share-token  |
| `/templates`        | templates    |
| `/grel`             | grel         |
| `/lmp`              | lmp          |
| `/diff/curves`      | diff-curves  |
| `/llm-history`      | llm-history  |

Each row produces 2 baselines (`<id>-light.png` and `<id>-dark.png`), so a
fresh run captures **38 baseline PNGs**.

## Determinism notes

`prepare(page)` (in `_helpers.ts`) freezes `Date.now()` and disables CSS
animation/transitions globally, so timestamps and motion don't differ
between runs. The dark-theme grid uses `pinTheme(page, "dark")` to set
`<html data-theme="dark">` BEFORE React boots — this avoids a light→dark
flash on first paint that would alone be enough to fail diffs.

## When NOT to add a route here

If a route is purely error-state or behind an authentication wall, skip it.
The visual grid is meant to catch chrome regressions on the surfaces real
users see, not exhaustively cover every conditional render path. Use the
existing per-feature specs (`audit.visual.spec.ts`, etc.) for state-rich
visual coverage.
