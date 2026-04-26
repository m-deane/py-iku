---
title: Overview
sidebar_position: 1
description: packages/types — generated TypeScript types and Zod validators from the FastAPI OpenAPI schema.
---

# packages/types

`packages/types` (`@py-iku-studio/types`) provides TypeScript type definitions and Zod runtime validators for the py-iku Studio API. All types are generated from the FastAPI OpenAPI schema — they are not hand-authored.

## Key exports

```typescript
import type {
  DataikuFlowDict,
  DataikuRecipeDict,
  PrepareStepDict,
  FlowGraphDict,
  ConvertRequest,
  ConvertResponse,
  RecipeCatalogEntry,
  ProcessorCatalogEntry,
  DiffResponse,
  ScoreResponse,
  ExportRequest,
  FlowRecord,
  ShareResponse,
  AuditEvent,
  HealthResponse,
} from "@py-iku-studio/types";

// Zod runtime validators
import {
  ConvertResponseSchema,
  DataikuFlowDictSchema,
  AuditEventSchema,
} from "@py-iku-studio/types/guards";
```

## Enum values

```typescript
import { RecipeType, ProcessorType, DatasetType } from "@py-iku-studio/types";

// e.g. RecipeType.GROUPING === "GROUPING"
```

## OpenAPI snapshot

The committed snapshot at `packages/types/openapi.snapshot.json` is the source for type generation. It was captured from the running API at the end of M7 using:

```bash
curl http://localhost:8000/openapi.json > packages/types/openapi.snapshot.json
```

A CI job (`types-drift`) checks that the snapshot stays in sync with the running API by comparing a fresh `/openapi.json` against the snapshot. See [CI Matrix](/operations/ci-matrix).
