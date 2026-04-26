---
title: Layout Engine
sidebar_position: 4
description: ELK-based DAG layout in packages/flow-viz — configuration, worker usage, and tuning.
---

# Layout Engine

`packages/flow-viz` uses [Eclipse Layout Kernel (ELK)](https://eclipse.dev/elk/) to compute node positions for the flow DAG. ELK runs in a Web Worker to avoid blocking the main thread during layout computation.

## Layout algorithm

The default algorithm is `layered` (Sugiyama-style), which places nodes in layers corresponding to DAG depth. Configuration:

```typescript
const ELK_OPTIONS = {
  "elk.algorithm": "layered",
  "elk.direction": "RIGHT",
  "elk.layered.spacing.nodeNodeBetweenLayers": "180",  // tokens.space.layerSpacing
  "elk.spacing.nodeNode": "100",                        // tokens.space.nodeSpacing
  "elk.layered.crossingMinimization.strategy": "LAYER_SWEEP",
  "elk.layered.nodePlacement.strategy": "NETWORK_SIMPLEX",
};
```

The spacing values are sourced directly from `tokens.json` (`space.layerSpacing`, `space.nodeSpacing`).

## Web Worker

The ELK layout runs in `packages/flow-viz/src/layout/elk.worker.ts`. The worker is loaded using Vite's `?worker` import syntax:

```typescript
import ElkWorker from "./layout/elk.worker?worker";
const worker = new ElkWorker();
```

Worker communication uses `postMessage` / `onmessage` with a request/response envelope keyed on a correlation id. Layout results are cached in a `Map` keyed on a fingerprint of the flow's nodes and edges, so re-renders without structural changes do not re-run ELK.

## Zone overlay layout

Zones (coloured grouping rectangles) are computed as a post-processing step after ELK layout. For each zone, the bounding box of its member nodes is computed, then expanded by `tokens.space.zonePadding` (20px) on all sides. Zones are rendered in a layer beneath all nodes.

## Performance targets

| Metric | Target | Measured in |
|--------|--------|-------------|
| Layout time for 100 nodes | < 300ms | `packages/flow-viz/tests/perf.test.ts` |
| Frame render time | < 16ms | Vitest performance test |
| Worker round-trip | < 50ms overhead | Measured via `performance.now()` |

## Tuning

If layout is too slow for very large flows (> 200 nodes), consider:

1. Setting `"elk.layered.crossingMinimization.strategy": "NONE"` for a faster but lower-quality layout.
2. Subsetting the flow to the visible subgraph before sending to ELK.
3. Switching to `dagre` (available as a fallback in `packages/flow-viz/src/layout/dagre.ts`).

## Manual repositioning

Users can drag nodes to reposition them after layout. Dragged positions override the ELK result and are stored in `flowStore.layoutOverrides`. Clicking the **Layout** button in the controls clears overrides and re-runs ELK.
