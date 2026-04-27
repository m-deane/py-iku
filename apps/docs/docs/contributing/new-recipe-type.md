---
title: Adding a New Recipe/Processor Type
sidebar_position: 2
description: Step-by-step guide to adding new RecipeType or ProcessorType values to py2dataiku and wiring them into Studio.
---

# Adding a New Recipe or Processor Type

This guide explains how to extend the `py2dataiku` library with a new recipe or processor type, and how to wire it through to Studio.

The authoritative Development Guidelines are in the root [`CLAUDE.md`](https://github.com/m-deane/py-iku/blob/main/CLAUDE.md) — this page cross-links those steps and adds the Studio-specific wiring.

## Adding a new RecipeType

### 1. Python library changes

Follow the steps in `CLAUDE.md` § "Adding New Recipe Types":

1. Add the value to `RecipeType` enum in `py2dataiku/models/dataiku_recipe.py`.
2. Add pandas mapping in `py2dataiku/mappings/pandas_mappings.py`.
3. Add a `RecipeSettings` subclass in `py2dataiku/models/recipe_settings.py`.
4. Add an example in `py2dataiku/examples/recipe_examples.py`.
5. Add a test in `tests/test_py2dataiku/test_recipe_examples.py`.

Run `python -m pytest tests/ -q` to confirm all tests pass.

### 2. API changes

The API automatically picks up new `RecipeType` values from the enum — no route changes needed. However:

- Rebuild the OpenAPI snapshot: `curl http://localhost:8000/openapi.json > packages/types/openapi.snapshot.json`.
- Re-run TS codegen: `pnpm --filter @py-iku-studio/types codegen`.
- Confirm `RecipeType` in `packages/types/src/enums.ts` includes the new value.

### 3. flow-viz node component

Create a new node component in `packages/flow-viz/src/nodes/`:

```typescript
// packages/flow-viz/src/nodes/MyNewRecipeNode.tsx
import { RecipeNodeBase } from "./RecipeNodeBase";
import { tokens } from "../theme/tokens";

export function MyNewRecipeNode({ data, selected, ...props }) {
  const colors = tokens.color.recipe.MY_NEW_RECIPE;
  return (
    <RecipeNodeBase
      label="My New Recipe"
      icon="default"  // or a custom icon key
      colors={colors}
      selected={selected}
      {...props}
    />
  );
}
```

Register the component in `packages/flow-viz/src/nodes/index.ts`:

```typescript
import { MyNewRecipeNode } from "./MyNewRecipeNode";
export const nodeTypes = {
  // ... existing types
  MY_NEW_RECIPE: MyNewRecipeNode,
};
```

### 4. Design tokens

Add colour tokens for the new type in `docs/design/tokens.json` under `color.recipe.MY_NEW_RECIPE` and `node.MY_NEW_RECIPE`. Choose a colour family that reflects the recipe's purpose.

### 5. Storybook story

```typescript
// packages/flow-viz/stories/MyNewRecipeNode.stories.tsx
import type { Meta, StoryObj } from "@storybook/react";
import { MyNewRecipeNode } from "../src/nodes/MyNewRecipeNode";

const meta: Meta = { component: MyNewRecipeNode };
export default meta;

export const Default: StoryObj = { args: { data: { label: "My New Recipe" } } };
export const Selected: StoryObj = { args: { data: { label: "My New Recipe" }, selected: true } };
```

### 6. Catalog browser

The catalog browser automatically shows all `RecipeType` values from `GET /catalog/recipes`. No UI changes needed if the description is in the API.

## Adding a new ProcessorType

Follow the steps in `CLAUDE.md` § "Adding New Processor Types":

1. Add to `ProcessorType` enum in `py2dataiku/models/prepare_step.py`.
2. Add entry in `ProcessorCatalog` in `py2dataiku/mappings/processor_catalog.py`.
3. Add example in `py2dataiku/examples/processor_examples.py`.
4. Add test in `tests/test_py2dataiku/test_processor_examples.py`.

No `flow-viz` changes needed for processor types — they appear inside PREPARE recipe nodes and are displayed in the Inspector panel. No design tokens needed.

## Checklist

- [ ] Python: enum + mapping + settings + example + test
- [ ] OpenAPI snapshot updated
- [ ] TS types regenerated
- [ ] flow-viz node component added
- [ ] Design token entry added
- [ ] Storybook story added
- [ ] `pnpm -r test` passes
- [ ] `python -m pytest tests/ -q` passes
