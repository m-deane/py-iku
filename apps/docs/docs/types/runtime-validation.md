---
title: Runtime Validation
sidebar_position: 3
description: Using Zod validators from packages/types to validate API responses at runtime.
---

# Runtime Validation

`packages/types` exports Zod schemas for all major API response types. These are used by `apps/web` to validate API responses at the boundary before trusting them.

## Why runtime validation

TypeScript types are erased at runtime. A schema change in the API that is not reflected in the committed snapshot (e.g. between deploys) would cause silent failures or incorrect rendering. Zod validation at the API client boundary catches this early.

## Using validators in apps/web

```typescript
import { ConvertResponseSchema } from "@py-iku-studio/types/guards";
import { z } from "zod";

const raw = await fetch("/convert", { method: "POST", body: ... }).then(r => r.json());

// Throws ZodError if schema mismatch
const response = ConvertResponseSchema.parse(raw);

// Or use safeParse to handle gracefully
const result = ConvertResponseSchema.safeParse(raw);
if (!result.success) {
  console.error("API schema mismatch:", result.error.format());
  // Surface in validation panel
  return;
}
const response = result.data;
```

## Available schemas

All schemas follow the naming convention `<TypeName>Schema`:

- `ConvertRequestSchema`, `ConvertResponseSchema`
- `DataikuFlowDictSchema`
- `RecipeCatalogEntrySchema`, `ProcessorCatalogEntrySchema`
- `DiffResponseSchema`
- `ScoreResponseSchema`
- `FlowRecordSchema`
- `ShareResponseSchema`
- `AuditEventSchema`
- `HealthResponseSchema`

## Zod integration with TanStack Query

In `apps/web`, TanStack Query's `queryFn` functions are wrapped to apply Zod parsing:

```typescript
const { data } = useQuery({
  queryKey: ["convert", code, mode],
  queryFn: async () => {
    const raw = await apiClient.post("/convert", { code, mode });
    return ConvertResponseSchema.parse(raw);
  },
});
// data is typed as z.infer<typeof ConvertResponseSchema>
```

This means TypeScript's inferred types and the runtime Zod types are always in sync.

## WebSocket event validation

WebSocket events are validated with the `WsEventSchema` discriminated union:

```typescript
import { WsEventSchema } from "@py-iku-studio/types/guards";

ws.onmessage = (event) => {
  const frame = WsEventSchema.parse(JSON.parse(event.data));
  // frame.event is narrowed to the specific event type
  if (frame.event === "recipe_created") {
    addRecipeNode(frame.payload.recipe_type, frame.payload.recipe_name);
  }
};
```
