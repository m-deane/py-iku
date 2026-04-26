---
title: Execution Simulation
sidebar_position: 8
description: useExecutionSim hook — animate data flowing through the DAG node by node.
---

# Execution Simulation

The execution simulation (`useExecutionSim`) animates a visual progression through the flow graph, showing which recipe would execute at each "tick" if the flow were actually run in Dataiku DSS.

## Hook

```typescript
import { useExecutionSim } from "@py-iku-studio/flow-viz";

const {
  isRunning,
  currentNodeId,
  executedNodeIds,
  start,
  pause,
  reset,
  speed,          // 1 = normal, 2 = fast, 0.5 = slow
  setSpeed,
} = useExecutionSim(flow);
```

`FlowCanvas` exposes a **Sim** button that toggles simulation. The hook is exported for custom implementations.

## Execution order

The simulation progresses in topological order (using `FlowGraph`'s topological sort). At each step, one recipe node becomes "executing" (pulsing border animation), then transitions to "executed" (dimmed, checkmark overlay), and the next node in topological order begins.

Datasets are not given individual execution ticks — they are marked as "ready" when all their producing recipes have executed.

## Visual encoding

| State | Node style |
|-------|-----------|
| Not yet executed | Default style |
| Currently executing | Pulsing orange border + spinner |
| Executed | Dimmed (60% opacity) + green checkmark |
| Blocked (dependency not yet executed) | Default (greyed out in some themes) |

The pulsing animation is a CSS keyframe animation (`@keyframes pulse-border`) defined in `packages/flow-viz/src/styles/sim.css`.

## Speed control

- `1×`: 800ms per recipe node.
- `2×`: 400ms per node.
- `0.5×`: 1600ms per node.

The speed can be adjusted while the simulation is running.

## Auto-loop

By default, the simulation stops after the last node executes and shows a "Simulation complete" banner. Toggle **Loop** in the Sim controls to restart automatically.

## Accuracy note

The execution simulation is a visual approximation. It does not model DSS's actual parallelism (multiple recipes on independent branches can run simultaneously in DSS). The simulation always runs serially in topological order. A parallel simulation mode is planned for M10.
