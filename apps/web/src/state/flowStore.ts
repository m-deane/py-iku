import { create } from "zustand";
import type { DataikuFlow } from "@py-iku-studio/types";

export type ConversionStatus = "idle" | "streaming" | "running" | "done" | "error";
export type ConversionMode = "rule" | "llm";

/**
 * Snapshot of the lineage-driven dimming/highlight that the column lineage
 * overlay publishes for the canvas to honour.
 *
 * `dimmedNodeIds` — recipe ids to render at `var(--dim-opacity)`.
 * `highlightedEdgeIds` — edge ids to stroke with `var(--accent)`.
 *
 * Empty arrays mean "no lineage focus active". Cleared whenever the active
 * column is deselected.
 */
export interface LineageFocus {
  column: string | null;
  dimmedNodeIds: string[];
  highlightedEdgeIds: string[];
}

export const EMPTY_LINEAGE_FOCUS: LineageFocus = {
  column: null,
  dimmedNodeIds: [],
  highlightedEdgeIds: [],
};

export interface FlowState {
  currentCode: string;
  /** The active DataikuFlow, typed from @py-iku-studio/types codegen. */
  currentFlow: DataikuFlow | null;
  conversionStatus: ConversionStatus;
  conversionMode: ConversionMode;
  selectedNodeId: string | null;
  /** Lineage-overlay dimming domain, published by ColumnLineageOverlay. */
  lineageFocus: LineageFocus;
  setCurrentCode: (code: string) => void;
  setFlow: (flow: DataikuFlow | null) => void;
  setConversionStatus: (status: ConversionStatus) => void;
  setConversionMode: (mode: ConversionMode) => void;
  /** Select a node by id (or deselect by passing null). */
  selectNode: (id: string | null) => void;
  /** @deprecated Use selectNode instead. */
  setSelectedNodeId: (id: string | null) => void;
  clearSelection: () => void;
  /** Replace the lineage focus snapshot. Pass null to clear. */
  setLineageFocus: (focus: LineageFocus | null) => void;
  reset: () => void;
}

export const useFlowStore = create<FlowState>()((set) => ({
  currentCode: "",
  currentFlow: null,
  conversionStatus: "idle",
  conversionMode: "rule",
  selectedNodeId: null,
  lineageFocus: EMPTY_LINEAGE_FOCUS,
  setCurrentCode: (currentCode) => set({ currentCode }),
  setFlow: (currentFlow) => set({ currentFlow }),
  setConversionStatus: (conversionStatus) => set({ conversionStatus }),
  setConversionMode: (conversionMode) => set({ conversionMode }),
  selectNode: (selectedNodeId) => set({ selectedNodeId }),
  /** @deprecated Use selectNode instead — both do the same thing. */
  setSelectedNodeId: (selectedNodeId) => set({ selectedNodeId }),
  clearSelection: () => set({ selectedNodeId: null }),
  setLineageFocus: (focus) =>
    set({ lineageFocus: focus ?? EMPTY_LINEAGE_FOCUS }),
  reset: () =>
    set({
      currentFlow: null,
      conversionStatus: "idle",
      selectedNodeId: null,
      lineageFocus: EMPTY_LINEAGE_FOCUS,
    }),
}));
