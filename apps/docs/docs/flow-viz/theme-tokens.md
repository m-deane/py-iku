---
title: Theme & Tokens
sidebar_position: 3
description: How design tokens flow from themes.py through tokens.json into flow-viz.
---

# Theme & Design Tokens

The visual design of py-iku Studio derives from the Dataiku DSS visual language. Colours, sizes, and typographic values are captured as tokens in `docs/design/tokens.json`.

## Token origin

```
py2dataiku/visualizers/themes.py
         ↓ (extracted during M2)
docs/design/tokens.json
         ↓ (consumed by)
packages/flow-viz/src/theme/
apps/web/src/styles/tokens.css
apps/docs/src/css/custom.css
```

The `themes.py` file is the source of truth. Changes to the DSS visual language should be made there first, then reflected in `tokens.json`. The token extraction is manual in M9; autogeneration is planned for M10.

## Token structure

`tokens.json` has five top-level sections:

| Section | Contents |
|---------|---------|
| `color.theme` | Light/dark backgrounds, grid lines, connection colours, dataset variants, recipe variants, zone palette |
| `color.recipe` | Per-`RecipeType` light/dark colour pairs (bg, border, text) |
| `color.dataset` | Per-role colour pairs (INPUT, INTERMEDIATE, OUTPUT) |
| `color.connection` | Per-`DatasetConnectionType` colour pairs |
| `typography` | Font family (base, mono), font sizes for node labels, font weights |
| `space` | Layer spacing (180), node spacing (100), padding (40), zone padding (20) |
| `radius` | Dataset border radius (6), recipe border radius (10) |
| `node` | Width/height/icon/label per `RecipeType` |

## Using tokens in flow-viz

```typescript
import { tokens } from "../theme/tokens";

// Get recipe colour for GROUPING in light mode
const { bg, border, text } = tokens.color.recipe.GROUPING.light;

// Get dataset colour for input role
const { bg, border } = tokens.color.dataset.INPUT.light;

// Get zone colour (cycling)
const zoneIndex = zoneNumber % tokens.color.theme.light.zone.length;
const { fill, border } = tokens.color.theme.light.zone[zoneIndex];
```

## Dark mode

`FlowCanvas` accepts a `theme` prop (`"light"` | `"dark"`). When `"dark"` is set, all token lookups switch to the `.dark` variant. The default follows the system `prefers-color-scheme`.

## TODO items from tokens.json

Several token values are marked `"TODO:designer-decision"` in the current `tokens.json`:

- `color.theme.dark.connection.connectionHover`
- `color.theme.dark.dataset.error` (bg, border, text)
- `shadow.node`, `shadow.nodeHover`, `shadow.nodeSelected`

These need designer input before M10. Until then, `flow-viz` uses hardcoded fallbacks for these values.
