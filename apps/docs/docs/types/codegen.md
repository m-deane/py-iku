---
title: Code Generation
sidebar_position: 2
description: How TypeScript types are generated from the FastAPI OpenAPI snapshot.
---

# Code Generation

TypeScript types in `packages/types` are generated from the FastAPI OpenAPI snapshot at `packages/types/openapi.snapshot.json`.

## Codegen script

Script location: `packages/types/scripts/codegen.ts`

```bash
# Run codegen
cd packages/types
npx ts-node scripts/codegen.ts

# Or via pnpm
pnpm --filter @py-iku-studio/types codegen
```

The script:

1. Reads `openapi.snapshot.json`.
2. Uses `openapi-typescript` to generate TypeScript interfaces in `src/index.ts`.
3. Uses `zod-from-openapi` (or equivalent) to generate Zod schemas in `src/guards.ts`.
4. Writes a `src/enums.ts` file with string enum types for `RecipeType`, `ProcessorType`, etc.

## Snapshot update workflow

When `py2dataiku` models change (new recipe type, new processor type, changed schema), the snapshot needs updating:

1. Start the API: `cd apps/api && uvicorn app.main:app --port 8000`.
2. Fetch new snapshot: `curl http://localhost:8000/openapi.json > packages/types/openapi.snapshot.json`.
3. Re-run codegen: `pnpm --filter @py-iku-studio/types codegen`.
4. Check generated diffs: `git diff packages/types/src/`.
5. Commit snapshot and generated types together.

## Drift check in CI

The `types-drift` CI job runs `pnpm --filter @py-iku-studio/types check-drift`. This script:

1. Starts the API in a temporary process.
2. Fetches `/openapi.json`.
3. Compares against the committed `openapi.snapshot.json`.
4. Fails if they differ (any path, schema, or component change).

This prevents the TS types from silently going stale when the Python models change.

## Generated file locations

| File | Contents |
|------|---------|
| `packages/types/src/index.ts` | TypeScript interfaces for all API schemas |
| `packages/types/src/guards.ts` | Zod validators for runtime parsing |
| `packages/types/src/enums.ts` | String enums for `RecipeType`, `ProcessorType` |
| `packages/types/openapi.snapshot.json` | Committed snapshot (source of truth for CI) |
