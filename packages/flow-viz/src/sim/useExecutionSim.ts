/**
 * Execution simulation hook.
 *
 * Animates a "running → done" status traveling through nodes in
 * topological order. The hook is shape-agnostic: it accepts an optional
 * pre-computed topo order, otherwise it computes one locally from the
 * edge list using Kahn's algorithm.
 *
 * State machine per node:
 *
 *   pending → executing → done
 *
 * The simulation advances one node per `stepMs` interval. It does NOT
 * mutate React Flow nodes — instead it returns a `Map<nodeId, status>`
 * that the caller folds into node `data` before re-rendering.
 *
 * The animation respects `prefers-reduced-motion`: when the user has
 * requested reduced motion the simulation still runs to completion but
 * each step takes one frame instead of `stepMs`.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { FlowEdge as FlowEdgeModel, FlowNode } from "../types";

export type SimNodeStatus = "pending" | "executing" | "done";

export interface UseExecutionSimOptions {
  /** Time between transitions, in ms. Default: 600. */
  stepMs?: number;
  /** When true, the sim auto-starts on mount. Default: false. */
  autoplay?: boolean;
  /** Optional pre-computed topological order of node IDs. */
  topologicalOrder?: readonly string[];
}

export interface UseExecutionSimResult {
  /** Current status per node. */
  nodeStatuses: ReadonlyMap<string, SimNodeStatus>;
  /** True while the simulation is advancing. */
  isRunning: boolean;
  /** True once every node is `done`. */
  isComplete: boolean;
  /** Index of the currently executing node (0-based) or -1 when idle. */
  cursor: number;
  /** Start (or resume) the simulation from `cursor`. */
  start: () => void;
  /** Pause the simulation. The next start resumes from the same cursor. */
  pause: () => void;
  /** Reset every node back to "pending" and stop. */
  reset: () => void;
}

/** Topological sort using Kahn's algorithm. Returns ids in execution order. */
export function topologicalSort(
  nodes: readonly FlowNode[],
  edges: readonly FlowEdgeModel[],
): string[] {
  const indeg = new Map<string, number>();
  const adj = new Map<string, string[]>();
  for (const n of nodes) {
    indeg.set(n.id, 0);
    adj.set(n.id, []);
  }
  for (const e of edges) {
    if (!indeg.has(e.target)) indeg.set(e.target, 0);
    if (!adj.has(e.source)) adj.set(e.source, []);
    indeg.set(e.target, (indeg.get(e.target) ?? 0) + 1);
    adj.get(e.source)?.push(e.target);
  }
  const queue: string[] = [];
  for (const [id, d] of indeg) {
    if (d === 0) queue.push(id);
  }
  const out: string[] = [];
  while (queue.length > 0) {
    const cur = queue.shift() as string;
    out.push(cur);
    for (const nxt of adj.get(cur) ?? []) {
      const d = (indeg.get(nxt) ?? 0) - 1;
      indeg.set(nxt, d);
      if (d === 0) queue.push(nxt);
    }
  }
  // Append any remaining (cycle) nodes so the sim still progresses.
  if (out.length < nodes.length) {
    for (const n of nodes) if (!out.includes(n.id)) out.push(n.id);
  }
  return out;
}

/** Returns true if the user has requested reduced motion via OS/browser settings. */
function prefersReducedMotion(): boolean {
  if (typeof window === "undefined" || !window.matchMedia) return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function useExecutionSim(
  nodes: readonly FlowNode[],
  edges: readonly FlowEdgeModel[],
  options: UseExecutionSimOptions = {},
): UseExecutionSimResult {
  // Honour prefers-reduced-motion: collapse each step to a single animation
  // frame (≈0 ms) so the sim completes instantly without visual motion.
  const stepMs = prefersReducedMotion() ? 0 : (options.stepMs ?? 600);
  const order = useMemo<readonly string[]>(
    () => options.topologicalOrder ?? topologicalSort(nodes, edges),
    [nodes, edges, options.topologicalOrder],
  );

  const initialStatuses = useMemo<Map<string, SimNodeStatus>>(() => {
    const m = new Map<string, SimNodeStatus>();
    for (const id of order) m.set(id, "pending");
    return m;
  }, [order]);

  const [nodeStatuses, setNodeStatuses] = useState<Map<string, SimNodeStatus>>(
    initialStatuses,
  );
  const [cursor, setCursor] = useState<number>(-1);
  const [isRunning, setIsRunning] = useState<boolean>(options.autoplay ?? false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Re-init when order changes.
  useEffect(() => {
    setNodeStatuses(new Map(initialStatuses));
    setCursor(-1);
  }, [initialStatuses]);

  const isComplete = useMemo<boolean>(
    () => order.length > 0 && Array.from(nodeStatuses.values()).every((s) => s === "done"),
    [nodeStatuses, order.length],
  );

  // Tick: advance one step.
  useEffect(() => {
    if (!isRunning) return;
    if (isComplete) {
      setIsRunning(false);
      return;
    }
    timerRef.current = setTimeout(() => {
      setNodeStatuses((prev) => {
        const next = new Map(prev);
        // Mark previous executing as done
        const prevIdx = cursor;
        if (prevIdx >= 0 && prevIdx < order.length) {
          next.set(order[prevIdx], "done");
        }
        // Advance cursor and mark new node executing
        const newIdx = prevIdx + 1;
        if (newIdx < order.length) {
          next.set(order[newIdx], "executing");
        }
        return next;
      });
      setCursor((c) => c + 1);
    }, cursor < 0 ? 0 : stepMs);
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [isRunning, isComplete, cursor, order, stepMs]);

  const start = useCallback((): void => {
    setIsRunning(true);
  }, []);
  const pause = useCallback((): void => {
    setIsRunning(false);
  }, []);
  const reset = useCallback((): void => {
    setIsRunning(false);
    setCursor(-1);
    setNodeStatuses(new Map(initialStatuses));
  }, [initialStatuses]);

  return {
    nodeStatuses,
    isRunning,
    isComplete,
    cursor,
    start,
    pause,
    reset,
  };
}
