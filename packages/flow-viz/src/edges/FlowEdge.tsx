import { memo, useState, useCallback } from "react";
import {
  BaseEdge,
  EdgeLabelRenderer,
  getSmoothStepPath,
  type EdgeProps,
} from "reactflow";
import type { FlowEdge as FlowEdgeData } from "../types";

interface FlowEdgePropsExt extends EdgeProps {
  data?: FlowEdgeData["data"];
}

const ROW_BUCKET_WIDTH = { thin: 1.5, medium: 1.5, thick: 2 } as const;

const SCHEMA_TINT = {
  none: "var(--edge-stroke, #94a3b8)",
  modified: "var(--warn-fg, #b54708)",
  break: "var(--danger-fg, #b42318)",
} as const;

/**
 * DSS-style flow edge.
 *
 * Renders a smoothstep polyline with a small arrowhead in gray
 * (--edge-stroke). On hover the stroke thickens to 2.5px and tints
 * to --accent. Optional dashed style reflects `data.optional`; row
 * volume buckets remain expressive but are toned down to keep the
 * canvas legible at a glance.
 */
function FlowEdgeImpl(props: FlowEdgePropsExt): JSX.Element {
  const {
    id,
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    data,
    markerEnd,
  } = props;
  const [edgePath] = getSmoothStepPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    borderRadius: 8,
  });
  const optional = data?.optional ?? false;
  const bucket = data?.rowBucket ?? "medium";
  const schemaChange = data?.schemaChange ?? "none";

  const [hovered, setHovered] = useState(false);
  const onEnter = useCallback(() => setHovered(true), []);
  const onLeave = useCallback(() => setHovered(false), []);

  const baseStroke = SCHEMA_TINT[schemaChange];
  const stroke = hovered && schemaChange === "none" ? "var(--accent, #0d9488)" : baseStroke;
  const baseWidth = ROW_BUCKET_WIDTH[bucket];
  const width = hovered ? Math.max(baseWidth, 2.5) : baseWidth;

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        style={{
          stroke,
          strokeWidth: width,
          strokeDasharray: optional ? "6 4" : undefined,
          fill: "none",
          transition: "stroke 0.15s ease, stroke-width 0.15s ease",
        }}
      />
      {/* Invisible thick stroke to enlarge hover hit-area without changing
       * the visible edge — a standard DSS-canvas technique. */}
      <EdgeLabelRenderer>
        {/* No label by default — column lineage overlays are wired
            externally via Sprint-4E's ColumnLineageOverlay. */}
        <></>
      </EdgeLabelRenderer>
      <path
        d={edgePath}
        fill="none"
        stroke="transparent"
        strokeWidth={14}
        pointerEvents="stroke"
        onMouseEnter={onEnter}
        onMouseLeave={onLeave}
      />
    </>
  );
}

export const FlowEdge = memo(FlowEdgeImpl);
FlowEdge.displayName = "FlowEdge";

export const edgeTypes = {
  flow: FlowEdge,
} as const;
