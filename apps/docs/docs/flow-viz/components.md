---
title: Components
sidebar_position: 2
description: FlowCanvas, node components, edge components, and supporting components in packages/flow-viz.
---

# Components

## FlowCanvas

The top-level canvas component. Renders the full `DataikuFlow` as a pannable, zoomable React Flow graph.

Source: `packages/flow-viz/src/FlowCanvas.tsx`

FlowCanvas handles:
1. Consuming the `DataikuFlow.to_dict()` payload.
2. Calling the ELK layout engine (Web Worker) to compute node positions.
3. Rendering node and edge components from the positioned graph.
4. Wiring up pan, zoom, selection, minimap, and controls.

## Recipe node components

One component per `RecipeType`, located in `packages/flow-viz/src/nodes/`. Each node component:

- Renders the Dataiku-faithful glyph (from `packages/flow-viz/src/icons.ts`).
- Uses the type-specific colour from `tokens.json` (light/dark variants).
- Shows the recipe name below the glyph.
- Accepts `selected`, `focused`, and `executing` props for visual state.

All 37 recipe type nodes are documented in Storybook.

### Visual state

| State | Visual |
|-------|--------|
| Default | Normal fill/border from tokens |
| Selected | 3px blue outline (`--ifm-color-primary`) |
| Focused | Full opacity; surrounding nodes faded to 30% |
| Executing | Animated pulsing border (execution sim) |
| Error | Red border overlay |

## Dataset node components

Dataset nodes are rectangles (not circles like recipe nodes). They use `packages/flow-viz/src/nodes/DatasetNode.tsx`.

Three visual variants by role:

| Role | Border colour | Background |
|------|--------------|-----------|
| Input | `#4A90D9` (blue) | `#E3F2FD` |
| Intermediate | `#78909C` (grey) | `#ECEFF1` |
| Output | `#43A047` (green) | `#E8F5E9` |

## Edge components

Edges are rendered as animated SVG paths. The default edge type is a smooth step with rounded corners. Edge colour matches the connection colour from `tokens.json` (`#90A4AE` in light mode).

Hover state: edge colour changes to `#1976D2` (connection hover from tokens).

## Zone and ZoneLayer

Zones are rectangular overlays that group related recipes visually. They render behind the nodes.

```typescript
// Usage in FlowCanvas
<ZoneLayer zones={flow.zones} />
```

Each zone has a fill and border colour from the `tokens.json` zone palette (8 colour slots, cycling if there are more than 8 zones).

## Minimap

A minimap component (bottom-right) shows the full graph at reduced scale. Click a region in the minimap to pan the main canvas to that position.

## Controls

Standard React Flow controls (zoom in / out / fit). Extended with:

- **Focus** button — toggles focus mode for the selected node.
- **Sim** button — toggles execution simulation.
- **Layout** button — re-runs ELK layout (useful if nodes were dragged).
