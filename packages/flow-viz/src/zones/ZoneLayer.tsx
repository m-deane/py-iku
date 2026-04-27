/**
 * ZoneLayer — computes bounding boxes per zone group and renders the
 * `<Zone>` rectangles behind the React Flow node layer.
 *
 * The host (`<FlowCanvas>`) passes positioned React Flow nodes plus a
 * `Map<nodeId, ZoneId>`. We group nodes by zone, compute the
 * axis-aligned bounding box of each group (with `ZONE_PADDING` slack),
 * and emit one `<Zone>` per group. Empty groups are skipped.
 */

import type { JSX } from "react";
import type { Node as RFNode } from "reactflow";
import type { ThemeName, RecipeNodeData, DatasetNodeData } from "../types";
import { Zone, type ZoneRect } from "./Zone";
import {
  autoAssignZones,
  ZONE_LABELS,
  ZONE_ORDER,
  ZONE_PALETTE_INDEX,
  type ZoneId,
} from "./auto";
import { ZONE_PADDING } from "./tokens";
import { NODE_SIZES } from "../theme/tokens";

export interface ZoneLayerProps {
  /** React Flow nodes after layout (positions resolved). */
  nodes: RFNode<RecipeNodeData | DatasetNodeData>[];
  /**
   * Optional precomputed zone assignment map. If omitted, `autoAssignZones`
   * is invoked using `edges` (which must then be supplied).
   */
  assignment?: Map<string, ZoneId>;
  /** Light/dark theme. */
  theme: ThemeName;
}

function nodeBox(n: RFNode): ZoneRect {
  const isRecipe = n.type !== "dataset";
  const w = isRecipe ? NODE_SIZES.recipe.width : NODE_SIZES.dataset.width;
  const h = isRecipe ? NODE_SIZES.recipe.height : NODE_SIZES.dataset.height;
  return {
    x: n.position?.x ?? 0,
    y: n.position?.y ?? 0,
    width: w,
    height: h,
  };
}

function unionBox(boxes: ZoneRect[]): ZoneRect {
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (const b of boxes) {
    if (b.x < minX) minX = b.x;
    if (b.y < minY) minY = b.y;
    if (b.x + b.width > maxX) maxX = b.x + b.width;
    if (b.y + b.height > maxY) maxY = b.y + b.height;
  }
  return {
    x: minX - ZONE_PADDING,
    y: minY - ZONE_PADDING,
    width: maxX - minX + ZONE_PADDING * 2,
    height: maxY - minY + ZONE_PADDING * 2,
  };
}

export function ZoneLayer(props: ZoneLayerProps): JSX.Element {
  const { nodes, assignment, theme } = props;
  const map = assignment ?? new Map<string, ZoneId>();
  // Group nodes by zone id.
  const grouped = new Map<ZoneId, ZoneRect[]>();
  for (const n of nodes) {
    const z = map.get(n.id);
    if (!z) continue;
    const arr = grouped.get(z) ?? [];
    arr.push(nodeBox(n));
    grouped.set(z, arr);
  }
  return (
    <div
      style={{ position: "absolute", inset: 0, pointerEvents: "none", zIndex: 0 }}
      data-testid="zone-layer"
    >
      {ZONE_ORDER.filter((z) => (grouped.get(z) ?? []).length > 0).map((z) => (
        <Zone
          key={z}
          paletteIndex={ZONE_PALETTE_INDEX[z]}
          rect={unionBox(grouped.get(z) ?? [])}
          label={ZONE_LABELS[z]}
          theme={theme}
        />
      ))}
    </div>
  );
}

export { autoAssignZones };
export type { ZoneId };
