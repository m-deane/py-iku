import { create } from "zustand";
import type { DataikuFlow } from "@py-iku-studio/types";

export type ConversionStatus = "idle" | "streaming" | "running" | "done" | "error";
export type ConversionMode = "rule" | "llm";

export interface FlowState {
  currentCode: string;
  /** The active DataikuFlow, typed from @py-iku-studio/types codegen. */
  currentFlow: DataikuFlow | null;
  conversionStatus: ConversionStatus;
  conversionMode: ConversionMode;
  selectedNodeId: string | null;
  setCurrentCode: (code: string) => void;
  setFlow: (flow: DataikuFlow | null) => void;
  setConversionStatus: (status: ConversionStatus) => void;
  setConversionMode: (mode: ConversionMode) => void;
  /** Select a node by id (or deselect by passing null). */
  selectNode: (id: string | null) => void;
  /** @deprecated Use selectNode instead. */
  setSelectedNodeId: (id: string | null) => void;
  clearSelection: () => void;
  reset: () => void;
}

export const useFlowStore = create<FlowState>()((set) => ({
  currentCode: "",
  currentFlow: null,
  conversionStatus: "idle",
  conversionMode: "rule",
  selectedNodeId: null,
  setCurrentCode: (currentCode) => set({ currentCode }),
  setFlow: (currentFlow) => set({ currentFlow }),
  setConversionStatus: (conversionStatus) => set({ conversionStatus }),
  setConversionMode: (conversionMode) => set({ conversionMode }),
  selectNode: (selectedNodeId) => set({ selectedNodeId }),
  /** @deprecated Use selectNode instead — both do the same thing. */
  setSelectedNodeId: (selectedNodeId) => set({ selectedNodeId }),
  clearSelection: () => set({ selectedNodeId: null }),
  reset: () =>
    set({
      currentFlow: null,
      conversionStatus: "idle",
      selectedNodeId: null,
    }),
}));
