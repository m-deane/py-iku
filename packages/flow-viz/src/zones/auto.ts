/**
 * Auto-zone heuristic.
 *
 * Given a flow's nodes + edges, returns a `Map<nodeId, ZoneId>` assigning
 * each node to one of four predefined zones:
 *
 *   - "input"  — dataset nodes with no incoming edges
 *   - "output" — nodes with no outgoing edges
 *   - "ml"     — recipe nodes whose category is "ml"
 *   - "prep"   — everything else
 *
 * The zone IDs map to fixed palette indices that match the predefined
 * zone roles in `node-spec.md` section 4:
 *
 *   input → 0  (blue)
 *   prep  → 1  (purple)
 *   ml    → 2  (green)
 *   output → 3 (orange)
 */

import type { DatasetNodeData, FlowNode, RecipeNodeData } from "../types";
import type { FlowEdge as FlowEdgeModel } from "../types";
import { categoryFor } from "../nodes/categories";

export type ZoneId = "input" | "prep" | "ml" | "output";

export const ZONE_LABELS: Record<ZoneId, string> = {
  input: "Input",
  prep: "Prep",
  ml: "ML",
  output: "Output",
};

export const ZONE_PALETTE_INDEX: Record<ZoneId, number> = {
  input: 0,
  prep: 1,
  ml: 2,
  output: 3,
};

/** Stable iteration order for rendering. */
export const ZONE_ORDER: readonly ZoneId[] = ["input", "prep", "ml", "output"];

/** Compute the zone assignment for every node. */
export function autoAssignZones(
  nodes: readonly FlowNode[],
  edges: readonly FlowEdgeModel[],
): Map<string, ZoneId> {
  const incoming = new Map<string, number>();
  const outgoing = new Map<string, number>();
  for (const n of nodes) {
    incoming.set(n.id, 0);
    outgoing.set(n.id, 0);
  }
  for (const e of edges) {
    incoming.set(e.target, (incoming.get(e.target) ?? 0) + 1);
    outgoing.set(e.source, (outgoing.get(e.source) ?? 0) + 1);
  }

  const assignment = new Map<string, ZoneId>();
  for (const n of nodes) {
    if (n.type === "dataset") {
      const data = n.data as DatasetNodeData;
      if ((incoming.get(n.id) ?? 0) === 0) {
        assignment.set(n.id, "input");
      } else if ((outgoing.get(n.id) ?? 0) === 0) {
        assignment.set(n.id, "output");
      } else {
        assignment.set(n.id, "prep");
      }
      // suppress unused — type narrowing
      void data;
      continue;
    }
    const data = n.data as RecipeNodeData;
    if (categoryFor(data.type) === "ml") {
      assignment.set(n.id, "ml");
      continue;
    }
    if ((outgoing.get(n.id) ?? 0) === 0) {
      assignment.set(n.id, "output");
    } else {
      assignment.set(n.id, "prep");
    }
  }
  return assignment;
}
