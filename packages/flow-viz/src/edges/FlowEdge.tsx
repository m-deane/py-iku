import { memo } from "react";
import { BaseEdge, getBezierPath, type EdgeProps } from "reactflow";
import type { FlowEdge as FlowEdgeData } from "../types";

interface FlowEdgePropsExt extends EdgeProps {
  data?: FlowEdgeData["data"];
}

const ROW_BUCKET_WIDTH = { thin: 1.5, medium: 2.5, thick: 4 } as const;

const SCHEMA_TINT = {
  none: "var(--color-connection, #90a4ae)",
  modified: "#FFB300",
  break: "#E53935",
} as const;

/**
 * Custom flow edge.
 * - line style: solid for primary, dashed for optional (per `data.optional`)
 * - thickness: 3 row-count buckets (`data.rowBucket`)
 * - color tint: schema-change indicator (`data.schemaChange`)
 *
 * Animated stroke-dashoffset for the executing-state simulation is TODO:M3b.
 */
function FlowEdgeImpl(props: FlowEdgePropsExt): JSX.Element {
  const { sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, data } = props;
  const [edgePath] = getBezierPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
  });
  const optional = data?.optional ?? false;
  const bucket = data?.rowBucket ?? "medium";
  const schemaChange = data?.schemaChange ?? "none";

  return (
    <BaseEdge
      path={edgePath}
      style={{
        stroke: SCHEMA_TINT[schemaChange],
        strokeWidth: ROW_BUCKET_WIDTH[bucket],
        strokeDasharray: optional ? "6 4" : undefined,
        fill: "none",
      }}
    />
  );
}

export const FlowEdge = memo(FlowEdgeImpl);
FlowEdge.displayName = "FlowEdge";

export const edgeTypes = {
  flow: FlowEdge,
} as const;
