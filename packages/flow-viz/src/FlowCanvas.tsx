import { useEffect, useMemo, useState, type CSSProperties, type MouseEvent as ReactMouseEvent } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  ReactFlowProvider,
  type Edge as RFEdge,
  type Node as RFNode,
  type NodeChange,
  applyNodeChanges,
} from "reactflow";
import "reactflow/dist/style.css";
import clsx from "clsx";
import { layoutFlow } from "./layout/elkLayout";
import { nodeTypes } from "./nodes";
import { edgeTypes } from "./edges/FlowEdge";
import { ZoneLayer, autoAssignZones, type ZoneId } from "./zones";
import { computeFocus } from "./focus/useFocusMode";
import { topologicalSort, useExecutionSim, type SimNodeStatus } from "./sim/useExecutionSim";
import type {
  DatasetNodeData,
  MinimalFlow,
  RecipeNodeData,
  ThemeName,
} from "./types";
import styles from "./FlowCanvas.module.css";

export interface FlowCanvasSimulationProps {
  /** Auto-start the sim on mount. */
  autoplay?: boolean;
  /** Step duration in ms. Default: 600. */
  stepMs?: number;
}

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
  /** When true, render the zone overlay layer behind the nodes. */
  showZones?: boolean;
  /** Optional override for the zone-id assignment. */
  zoneAssignment?: Map<string, ZoneId>;
  /** When true, dim non-focused nodes when one is selected. */
  focusOnSelect?: boolean;
  /** When set, animate execution status through the topological order. */
  simulation?: FlowCanvasSimulationProps;
  /**
   * Fired when a node is selected or the selection is cleared. Pass null
   * when the user clicks empty canvas. Used by the M5 NodeInspector panel.
   */
  onSelectionChange?: (id: string | null) => void;
  /** Externally controlled selection — overrides the canvas-internal state. */
  selectedNodeId?: string | null;
  /**
   * External lineage-driven dimming. When non-empty, every node *not* in this
   * set is rendered at `var(--dim-opacity)` and every edge whose id is in
   * `highlightedEdgeIds` is stroked with `var(--accent)`.
   *
   * Wired by the ColumnLineageOverlay → ConvertPage path. Kept independent
   * from `focusOnSelect` because the lineage panel publishes its own dimming
   * domain (recipe ids touched by the column) which is generally different
   * from selection-driven focus.
   */
  dimmedNodeIds?: string[];
  /** Edge ids to stroke with `var(--accent)` (lineage highlight). */
  highlightedEdgeIds?: string[];
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

function simStatusToNodeStatus(s: SimNodeStatus): "executing" | "done" | "pending" {
  return s;
}

/**
 * Top-level flow canvas. Runs ELK layout once when `flow` changes, then hands
 * the positioned graph to React Flow. Theme is applied as a `data-theme`
 * attribute on the wrapper so that token CSS variables resolve correctly.
 *
 * M3b additions:
 *   - `showZones` toggles the auto-zone overlay layer (input / prep / ml / output).
 *   - `focusOnSelect` dims non-focused nodes on selection.
 *   - `simulation` plays an executing → done animation in topological order.
 */
export function FlowCanvas(props: FlowCanvasProps): JSX.Element {
  const {
    flow,
    theme = "light",
    showMinimap = true,
    showControls = true,
    showBackground = true,
    showZones = false,
    zoneAssignment,
    focusOnSelect = false,
    simulation,
    onSelectionChange,
    selectedNodeId: externalSelectedNodeId,
    dimmedNodeIds,
    highlightedEdgeIds,
    className,
    style,
  } = props;

  const initialNodes = useMemo(() => toRFNodes(flow), [flow]);
  const initialEdges = useMemo(() => toRFEdges(flow), [flow]);
  const [nodes, setNodes] = useState<RFNode[]>(initialNodes);
  const [edges, setEdges] = useState<RFEdge[]>(initialEdges);
  const [internalSelectedNodeId, setInternalSelectedNodeId] = useState<string | null>(null);
  const selectedNodeId =
    externalSelectedNodeId !== undefined ? externalSelectedNodeId : internalSelectedNodeId;

  // Run layout when flow changes.
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

  // Compute focus dim set whenever selection or graph changes.
  const focus = useMemo(() => {
    if (!focusOnSelect) {
      return { focusedIds: new Set<string>(), isFocusActive: false };
    }
    return computeFocus(selectedNodeId, flow.edges);
  }, [focusOnSelect, selectedNodeId, flow.edges]);

  // Wire execution simulation when requested.
  const topo = useMemo<readonly string[]>(
    () => topologicalSort(flow.nodes, flow.edges),
    [flow.nodes, flow.edges],
  );
  const sim = useExecutionSim(flow.nodes, flow.edges, {
    autoplay: simulation?.autoplay,
    stepMs: simulation?.stepMs,
    topologicalOrder: topo,
  });
  const simEnabled = simulation !== undefined;

  // Compose dim + sim status into rendered nodes. Lineage-driven dimming
  // (`dimmedNodeIds`) is OR-ed into the existing focus dim signal so a column
  // pick from the inspector and a focus-on-select selection both contribute.
  const lineageDimSet = useMemo(
    () => new Set(dimmedNodeIds ?? []),
    [dimmedNodeIds],
  );
  const lineageDimActive = lineageDimSet.size > 0;
  const renderedNodes = useMemo<RFNode[]>(() => {
    return nodes.map((n) => {
      const isFocused = focus.isFocusActive ? focus.focusedIds.has(n.id) : true;
      const focusDim = focus.isFocusActive && !isFocused;
      const lineageDim = lineageDimActive && lineageDimSet.has(n.id);
      const dimmed = focusDim || lineageDim;
      const simStatus = simEnabled ? sim.nodeStatuses.get(n.id) : undefined;
      const status =
        simStatus === undefined
          ? (n.data as { status?: string }).status
          : simStatusToNodeStatus(simStatus);
      return {
        ...n,
        data: {
          ...(n.data as Record<string, unknown>),
          dimmed: dimmed || (n.data as { dimmed?: boolean }).dimmed,
          status: status ?? "none",
        },
      };
    });
  }, [nodes, focus, simEnabled, sim.nodeStatuses, lineageDimActive, lineageDimSet]);

  // Compose lineage-highlighted edges. Highlighted edges get `data-highlighted`
  // + an inline accent stroke so renderers downstream of <ReactFlow/> can
  // honour either signal.
  const highlightedEdgeSet = useMemo(
    () => new Set(highlightedEdgeIds ?? []),
    [highlightedEdgeIds],
  );
  const renderedEdges = useMemo<RFEdge[]>(() => {
    if (highlightedEdgeSet.size === 0) return edges;
    return edges.map((e) => {
      const highlighted = highlightedEdgeSet.has(e.id);
      if (!highlighted) return e;
      return {
        ...e,
        data: { ...(e.data as Record<string, unknown> | undefined), highlighted: true },
        style: { ...(e.style ?? {}), stroke: "var(--accent)", strokeWidth: 2 },
      };
    });
  }, [edges, highlightedEdgeSet]);

  function handleNodeChanges(changes: NodeChange[]): void {
    setNodes((prev) => applyNodeChanges(changes, prev));
    for (const c of changes) {
      if (c.type === "select") {
        const next = c.selected ? c.id : null;
        if (externalSelectedNodeId === undefined) {
          setInternalSelectedNodeId(next);
        }
        onSelectionChange?.(next);
      }
    }
  }

  function handleNodeClick(_evt: ReactMouseEvent, node: RFNode): void {
    if (externalSelectedNodeId === undefined) {
      setInternalSelectedNodeId(node.id);
    }
    onSelectionChange?.(node.id);
  }

  function handlePaneClick(): void {
    if (externalSelectedNodeId === undefined) {
      setInternalSelectedNodeId(null);
    }
    onSelectionChange?.(null);
  }

  return (
    <div
      className={clsx(styles.canvas, className)}
      data-theme={theme}
      data-testid="flow-canvas"
      data-zones={showZones ? "true" : undefined}
      data-focus={focus.isFocusActive ? "true" : undefined}
      data-sim={simEnabled ? "true" : undefined}
      data-lineage-dim={lineageDimActive ? "true" : undefined}
      style={{ width: "100%", height: "100%", ...style }}
    >
      <ReactFlowProvider>
        {showZones && (
          <ZoneLayer
            nodes={nodes as RFNode<RecipeNodeData | DatasetNodeData>[]}
            assignment={zoneAssignment ?? autoAssignZones(flow.nodes, flow.edges)}
            theme={theme}
          />
        )}
        <ReactFlow
          nodes={renderedNodes}
          edges={renderedEdges}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          fitView
          onNodesChange={handleNodeChanges}
          onNodeClick={handleNodeClick}
          onPaneClick={handlePaneClick}
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
