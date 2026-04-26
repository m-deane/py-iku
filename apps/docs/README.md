# py-iku Studio Docs

Docusaurus 3 documentation site for py-iku Studio.

## Local development

```bash
# From repo root
pnpm install
pnpm --filter apps-docs start
# Open http://localhost:3000
```

Or from this directory:

```bash
npm start
```

## Build

```bash
pnpm --filter apps-docs build
# Output: apps/docs/build/
```

## Structure

```
apps/docs/
  docs/
    getting-started/    # introduction, quickstart, architecture
    user-guide/         # feature pages for each Studio UI feature
    api-reference/      # one page per API route family
    flow-viz/           # packages/flow-viz docs
    types/              # packages/types docs
    operations/         # deployment, CI, env vars
    contributing/       # recipe/processor guide, commit conventions
    roadmap.md
  scripts/
    sync-api-reference.ts  # TODO(M9-followup): auto-gen from OpenAPI snapshot
  src/css/
    custom.css          # brand colours from docs/design/tokens.json
  docusaurus.config.ts
  sidebars.ts
```

## Storybook integration

To serve the `flow-viz` Storybook inside the docs site:

```bash
# Build Storybook
pnpm --filter @py-iku-studio/flow-viz build-storybook

# Copy output into docs static dir
cp -r packages/flow-viz/storybook-static apps/docs/static/storybook

# Build docs (will include /storybook/ path)
pnpm --filter apps-docs build
```

## Deployment

The site deploys to GitHub Pages at `https://m-deane.github.io/py-iku/studio/` when a git tag is pushed. See `.github/workflows/studio-docs.yml`.
