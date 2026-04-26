---
title: Overview
sidebar_position: 1
description: Introduction to packages/flow-viz — the React Flow visualization library for Dataiku flows.
---

# packages/flow-viz

`packages/flow-viz` is the visualization layer of py-iku Studio. It is a React component library built on [React Flow](https://reactflow.dev/) that renders `DataikuFlow` objects as interactive, animated graph canvases.

It is published as a pnpm workspace package (`@py-iku-studio/flow-viz`) and consumed exclusively by `apps/web`. It has no dependency on `apps/api` — it renders whatever `DataikuFlow.to_dict()` payload the web app passes to it.

## Key exports

```typescript
import {
  FlowCanvas,          // main rendered canvas component
  Zone,                // zone overlay container
  ZoneLayer,           // zone grouping layer
  useFocusMode,        // hook: collapse non-selected paths
  useExecutionSim,     // hook: animate execution progression
  toSvg,              // export canvas as SVG string
  toPng,              // export canvas as PNG blob
  toPdf,              // export canvas as PDF blob
} from "@py-iku-studio/flow-viz";
```

## FlowCanvas props

```typescript
interface FlowCanvasProps {
  flow: DataikuFlowDict;        // DataikuFlow.to_dict() payload
  selectedNodeId?: string;       // controlled selection
  onNodeSelect?: (id: string | null) => void;
  onReady?: () => void;          // called after ELK layout completes
  theme?: "light" | "dark";      // defaults to system preference
  showMinimap?: boolean;         // default true
  showControls?: boolean;        // default true
  readOnly?: boolean;            // disables drag (for /share/:token)
}
```

## Storybook

Each recipe type has a Storybook story. The Storybook static build is served at `/storybook/` in the Studio docs site (configured in `docusaurus.config.ts` via `staticDirectories`).

:::note Storybook link
The embedded Storybook is available at [/storybook/](pathname:///storybook/) once the docs site is running with the Storybook static build copied into `apps/docs/static/storybook/`.
:::

## Performance

The ELK layout engine runs in a Web Worker. Target frame budget: < 16ms for 100-node flows on a mid-range laptop. The performance budget is enforced in the Vitest suite in `packages/flow-viz/tests/perf.test.ts`.

Memoisation strategy:
- Each node component is wrapped in `React.memo` with a custom equality check on the `DataikuRecipe` or `DataikuDataset` dict.
- Off-screen nodes (outside the current viewport) are virtualized — their DOM is unmounted.
- The ELK layout result is cached keyed on the flow's node/edge fingerprint.
