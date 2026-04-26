---
title: Focus Mode
sidebar_position: 7
description: useFocusMode hook — highlight a selected node and fade the rest of the graph.
---

# Focus Mode

Focus mode is a UX feature that helps users understand a single node's position in the graph. When enabled, the selected node and its direct ancestors/descendants are rendered at full opacity; all other nodes fade to 30%.

## Hook

```typescript
import { useFocusMode } from "@py-iku-studio/flow-viz";

const { isFocused, activateFocus, deactivateFocus, focusedNodeId } =
  useFocusMode();
```

`FlowCanvas` manages focus mode internally and exposes a **Focus** toggle button in the controls panel. The hook is exported for custom canvas implementations.

## Behaviour

When a node is selected and Focus is activated:

1. `useFocusMode` calls `flow.graph.subgraph(nodeId)` to find all ancestors and descendants of the selected node via BFS on the `FlowGraph` DAG.
2. All nodes outside the subgraph receive the CSS class `flow-node--faded` (opacity 0.3).
3. All edges outside the subgraph are hidden (`display: none`).
4. The selected node and its subgraph render at full opacity.

Deactivate by:
- Clicking **Focus** again.
- Clicking an empty area of the canvas.
- Pressing `Escape`.

## Subgraph discovery

Subgraph discovery is delegated to `FlowGraph.subgraph(nodeId)` in the `py2dataiku` Python model. In `packages/flow-viz`, the TypeScript equivalent is implemented in `packages/flow-viz/src/layout/subgraph.ts` operating on the adjacency list derived from React Flow's edge list.

## Keyboard shortcut

`F` key: toggle focus mode for the currently selected node. If no node is selected, the shortcut has no effect.

## Accessibility

Focus mode changes are announced to screen readers via an `aria-live="polite"` region that emits "Focus mode active for [recipe name]" or "Focus mode off".
