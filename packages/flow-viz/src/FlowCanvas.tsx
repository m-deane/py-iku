import { useEffect, useMemo, useState, type CSSProperties } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  ReactFlowProvider,
  type Edge as RFEdge,
  type Node as RFNode,
} from "reactflow";
import "reactflow/dist/style.css";
import clsx from "clsx";
import { layoutFlow } from "./layout/elkLayout";
import { nodeTypes } from "./nodes";
import { edgeTypes } from "./edges/FlowEdge";
import type { DatasetNodeData, MinimalFlow, RecipeNodeData, ThemeName } from "./types";
import styles from "./FlowCanvas.module.css";

export interface FlowCanvasProps {
  /**
   * Minimal flow representation. Will be replaced by `DataikuFlowModel` from
   * `@py-iku-studio/types` in M5; the conversion is mechanical (same field
   * names) so callers should not see breaking changes.
   */
  flow: MinimalFlow;
  theme?: ThemeName;
  showMinimap?: boolean;
  showControls?: boolean;
  showBackground?: boolean;
  className?: string;
  style?: CSSProperties;
}

function toRFNodes(flow: MinimalFlow): RFNode<RecipeNodeData | DatasetNodeData>[] {
  return flow.nodes.map((n) => {
    if (n.type === "recipe") {
      const data = n.data as RecipeNodeData;
      return {
        id: n.id,
        type: `recipe.${data.type}` in nodeTypes ? `recipe.${data.type}` : "recipe",
        data,
        position: n.position ?? { x: 0, y: 0 },
      };
    }
    return {
      id: n.id,
      type: "dataset",
      data: n.data as DatasetNodeData,
      position: n.position ?? { x: 0, y: 0 },
    };
  });
}

function toRFEdges(flow: MinimalFlow): RFEdge[] {
  return flow.edges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    type: "flow",
    data: e.data,
  }));
}

/**
 * Top-level flow canvas. Runs ELK layout once when `flow` changes, then hands
 * the positioned graph to React Flow. Theme is applied as a `data-theme`
 * attribute on the wrapper so that token CSS variables resolve correctly.
 *
 * NOT included in M3a (planned for M3b): focus mode, animated execution sim,
 * SVG/PNG/PDF export, zone overlays.
 */
export function FlowCanvas(props: FlowCanvasProps): JSX.Element {
  const {
    flow,
    theme = "light",
    showMinimap = true,
    showControls = true,
    showBackground = true,
    className,
    style,
  } = props;

  const initialNodes = useMemo(() => toRFNodes(flow), [flow]);
  const initialEdges = useMemo(() => toRFEdges(flow), [flow]);
  const [nodes, setNodes] = useState<RFNode[]>(initialNodes);
  const [edges, setEdges] = useState<RFEdge[]>(initialEdges);

  useEffect(() => {
    let cancelled = false;
    layoutFlow(initialNodes, initialEdges).then((laid) => {
      if (cancelled) return;
      setNodes(laid.nodes);
      setEdges(laid.edges);
    });
    return () => {
      cancelled = true;
    };
  }, [initialNodes, initialEdges]);

  return (
    <div
      className={clsx(styles.canvas, className)}
      data-theme={theme}
      data-testid="flow-canvas"
      style={{ width: "100%", height: "100%", ...style }}
    >
      <ReactFlowProvider>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          fitView
          proOptions={{ hideAttribution: true }}
        >
          {showBackground && <Background gap={16} />}
          {showControls && <Controls />}
          {showMinimap && <MiniMap pannable zoomable />}
        </ReactFlow>
      </ReactFlowProvider>
    </div>
  );
}
