/**
 * Focus mode — given a selected node, compute the set of ancestor +
 * descendant node IDs and return both the focused set and a flag.
 *
 * Pure / synchronous: no React state, no effects. The caller is expected
 * to feed the result into `<FlowCanvas>` so non-focused nodes pick up
 * `data.dimmed = true`.
 */

import { useMemo } from "react";
import type { FlowEdge as FlowEdgeModel } from "../types";

export interface FocusModeResult {
  /** Set of node IDs in focus (selected + ancestors + descendants). */
  focusedIds: ReadonlySet<string>;
  /** True iff a node is currently selected and focus mode should apply. */
  isFocusActive: boolean;
}

interface AdjacencyMaps {
  forward: Map<string, string[]>;
  reverse: Map<string, string[]>;
}

function buildAdjacency(edges: readonly FlowEdgeModel[]): AdjacencyMaps {
  const forward = new Map<string, string[]>();
  const reverse = new Map<string, string[]>();
  for (const e of edges) {
    const f = forward.get(e.source) ?? [];
    f.push(e.target);
    forward.set(e.source, f);
    const r = reverse.get(e.target) ?? [];
    r.push(e.source);
    reverse.set(e.target, r);
  }
  return { forward, reverse };
}

function bfs(start: string, adj: Map<string, string[]>): Set<string> {
  const visited = new Set<string>();
  const queue: string[] = [start];
  while (queue.length > 0) {
    const cur = queue.shift() as string;
    if (visited.has(cur)) continue;
    visited.add(cur);
    const next = adj.get(cur) ?? [];
    for (const n of next) {
      if (!visited.has(n)) queue.push(n);
    }
  }
  return visited;
}

/**
 * Compute the focused subgraph for a given selection.
 *
 * @param selectedNodeId - currently selected node id, or null/undefined
 * @param edges - flow edges
 */
export function useFocusMode(
  selectedNodeId: string | null | undefined,
  edges: readonly FlowEdgeModel[],
): FocusModeResult {
  return useMemo<FocusModeResult>(() => {
    if (!selectedNodeId) {
      return { focusedIds: new Set<string>(), isFocusActive: false };
    }
    const { forward, reverse } = buildAdjacency(edges);
    const descendants = bfs(selectedNodeId, forward);
    const ancestors = bfs(selectedNodeId, reverse);
    const focused = new Set<string>([
      selectedNodeId,
      ...descendants,
      ...ancestors,
    ]);
    return { focusedIds: focused, isFocusActive: true };
  }, [selectedNodeId, edges]);
}

/**
 * Synchronous (non-hook) variant — used by tests and by the imperative
 * code paths in `FlowCanvas` that compute focus inside an effect rather
 * than as a memo.
 */
export function computeFocus(
  selectedNodeId: string | null | undefined,
  edges: readonly FlowEdgeModel[],
): FocusModeResult {
  if (!selectedNodeId) {
    return { focusedIds: new Set<string>(), isFocusActive: false };
  }
  const { forward, reverse } = buildAdjacency(edges);
  const descendants = bfs(selectedNodeId, forward);
  const ancestors = bfs(selectedNodeId, reverse);
  const focused = new Set<string>([
    selectedNodeId,
    ...descendants,
    ...ancestors,
  ]);
  return { focusedIds: focused, isFocusActive: true };
}
