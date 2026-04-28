import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type CSSProperties,
  type MouseEvent as ReactMouseEvent,
} from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  ReactFlowProvider,
  useReactFlow,
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
  /** When true, render the DSS-style toolbar (Fit, Auto-layout, Mini-map). */
  showToolbar?: boolean;
  /** Optional override for the zone-id assignment. */
  zoneAssignment?: Map<string, ZoneId>;
  /** When true, dim non-focused nodes when one is selected. */
  focusOnSelect?: boolean;
  /** When set, animate execution status through the topological order. */
  simulation?: FlowCanvasSimulationProps;
  /** Fired when a node is selected or the selection is cleared. */
  onSelectionChange?: (id: string | null) => void;
  /** Externally controlled selection — overrides the canvas-internal state. */
  selectedNodeId?: string | null;
  /** External lineage-driven dimming. */
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

interface ToolbarProps {
  showMinimap: boolean;
  onToggleMinimap: () => void;
  onAutoLayout: () => void;
}

/**
 * Internal helper — runs `fitView` whenever node positions change after the
 * async ELK layout completes. Without this, the initial `fitView={true}`
 * prop on `<ReactFlow>` runs *before* positions land (the layout is async),
 * leaving the camera anchored at (0, 0) so all nodes appear off-screen.
 *
 * The signature key is the concatenation of every node id + position;
 * recomputing it on every render is cheap (≤ 50 nodes typical) and forces
 * `fitView` to re-fire when ELK delivers new coordinates.
 */
function FitViewOnLayout(props: { positionKey: string }): null {
  const rf = useReactFlow();
  useEffect(() => {
    if (!props.positionKey) return;
    // React Flow needs two frames to commit the laid-out node sizes
    // through its internal store: one for the position-state update we
    // just dispatched, and a second for measure-after-paint. Without
    // this double-rAF, fitView reads stale dimensions and either
    // over-zooms (scale=2 against a one-line subset of the graph) or
    // under-zooms entirely. Tested across 1-, 4-, 8- and 14-node flows.
    let frame2 = 0;
    const frame1 = requestAnimationFrame(() => {
      frame2 = requestAnimationFrame(() => {
        rf.fitView({ padding: 0.12, duration: 200 });
      });
    });
    return () => {
      cancelAnimationFrame(frame1);
      if (frame2) cancelAnimationFrame(frame2);
    };
  }, [props.positionKey, rf]);
  return null;
}

/** DSS-style toolbar — Fit / Auto-layout / Mini-map toggle. */
function Toolbar(props: ToolbarProps): JSX.Element {
  const { showMinimap, onToggleMinimap, onAutoLayout } = props;
  const rf = useReactFlow();
  const onFit = useCallback(() => {
    rf.fitView({ padding: 0.12, duration: 250 });
  }, [rf]);
  return (
    <div className={styles.toolbar} role="toolbar" aria-label="Flow canvas toolbar">
      <button
        type="button"
        className={styles.toolbarButton}
        onClick={onFit}
        data-testid="flow-toolbar-fit"
        aria-label="Fit flow to screen"
        title="Fit to screen"
      >
        <svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true">
          <path
            d="M2 5 V2 H5 M11 2 H14 V5 M14 11 V14 H11 M5 14 H2 V11"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        <span>Fit</span>
      </button>
      <button
        type="button"
        className={styles.toolbarButton}
        onClick={onAutoLayout}
        data-testid="flow-toolbar-layout"
        aria-label="Re-run auto layout"
        title="Auto-layout"
      >
        <svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true">
          <rect x="1.5" y="3" width="3.5" height="3" fill="none" stroke="currentColor" strokeWidth="1.3" />
          <rect x="6.5" y="7" width="3.5" height="3" fill="none" stroke="currentColor" strokeWidth="1.3" />
          <rect x="11" y="3" width="3.5" height="3" fill="none" stroke="currentColor" strokeWidth="1.3" />
          <line x1="3" y1="6" x2="3" y2="9" stroke="currentColor" strokeWidth="1.3" />
          <line x1="3" y1="9" x2="6.5" y2="9" stroke="currentColor" strokeWidth="1.3" />
          <line x1="13" y1="6" x2="13" y2="9" stroke="currentColor" strokeWidth="1.3" />
          <line x1="13" y1="9" x2="10" y2="9" stroke="currentColor" strokeWidth="1.3" />
        </svg>
        <span>Layout</span>
      </button>
      <button
        type="button"
        className={styles.toolbarButton}
        onClick={onToggleMinimap}
        data-testid="flow-toolbar-minimap"
        aria-label="Toggle mini-map"
        aria-pressed={showMinimap}
        title="Toggle mini-map"
      >
        <svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true">
          <rect x="1.5" y="2.5" width="13" height="11" rx="1" fill="none" stroke="currentColor" strokeWidth="1.3" />
          <rect x="9" y="8" width="4.5" height="4.5" fill="currentColor" opacity="0.4" />
        </svg>
        <span>Map</span>
      </button>
    </div>
  );
}

/**
 * Top-level flow canvas. Runs ELK layout once when `flow` changes, then hands
 * the positioned graph to React Flow. Theme is applied as a `data-theme`
 * attribute on the wrapper so that token CSS variables resolve correctly.
 */
export function FlowCanvas(props: FlowCanvasProps): JSX.Element {
  const {
    flow,
    theme = "light",
    showMinimap: showMinimapProp = true,
    showControls = true,
    showBackground = true,
    showZones = false,
    showToolbar = true,
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
  const [showMinimap, setShowMinimap] = useState<boolean>(showMinimapProp);
  const selectedNodeId =
    externalSelectedNodeId !== undefined ? externalSelectedNodeId : internalSelectedNodeId;

  // Keep internal mini-map state in sync when the prop changes.
  useEffect(() => {
    setShowMinimap(showMinimapProp);
  }, [showMinimapProp]);

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

  // Manual auto-layout trigger from the toolbar.
  const triggerAutoLayout = useCallback(() => {
    layoutFlow(nodes, edges).then((laid) => {
      setNodes(laid.nodes);
      setEdges(laid.edges);
    });
  }, [nodes, edges]);

  const focus = useMemo(() => {
    if (!focusOnSelect) {
      return { focusedIds: new Set<string>(), isFocusActive: false };
    }
    return computeFocus(selectedNodeId, flow.edges);
  }, [focusOnSelect, selectedNodeId, flow.edges]);

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

  const highlightedEdgeSet = useMemo(
    () => new Set(highlightedEdgeIds ?? []),
    [highlightedEdgeIds],
  );
  // Stable signature of the laid-out node positions; flips whenever ELK
  // produces new coordinates, which the `<FitViewOnLayout>` helper inside
  // ReactFlowProvider then uses to retrigger fitView.
  const positionKey = useMemo<string>(() => {
    return nodes
      .map((n) => `${n.id}:${Math.round(n.position?.x ?? 0)}:${Math.round(n.position?.y ?? 0)}`)
      .join(",");
  }, [nodes]);

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
          fitViewOptions={{ padding: 0.12 }}
          minZoom={0.1}
          maxZoom={2}
          onNodesChange={handleNodeChanges}
          onNodeClick={handleNodeClick}
          onPaneClick={handlePaneClick}
          proOptions={{ hideAttribution: true }}
        >
          {showBackground && <Background gap={16} />}
          {showControls && <Controls />}
          {showMinimap && (
            <MiniMap
              pannable
              zoomable
              position="bottom-right"
              style={{
                width: 140,
                height: 90,
                opacity: 0.92,
                borderRadius: 6,
                border: "1px solid var(--border, #eaecf0)",
                background:
                  theme === "dark"
                    ? "rgba(20, 24, 32, 0.9)"
                    : "rgba(255, 255, 255, 0.9)",
              }}
              maskColor={
                theme === "dark"
                  ? "rgba(20, 24, 32, 0.45)"
                  : "rgba(0, 0, 0, 0.06)"
              }
            />
          )}
        </ReactFlow>
        {showToolbar && (
          <Toolbar
            showMinimap={showMinimap}
            onToggleMinimap={() => setShowMinimap((v) => !v)}
            onAutoLayout={triggerAutoLayout}
          />
        )}
        <FitViewOnLayout positionKey={positionKey} />
      </ReactFlowProvider>
    </div>
  );
}
