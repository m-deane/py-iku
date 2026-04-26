import { create } from "zustand";

/**
 * Skeleton store for the active flow. M5 will replace `unknown` with the real
 * `DataikuFlow` type emitted by `packages/types` codegen.
 */
export type ConversionStatus = "idle" | "streaming" | "done" | "error";

export interface FlowState {
  currentFlow: unknown | null;
  conversionStatus: ConversionStatus;
  selectedNodeId: string | null;
  setFlow: (flow: unknown | null) => void;
  setConversionStatus: (status: ConversionStatus) => void;
  selectNode: (id: string | null) => void;
  reset: () => void;
}

export const useFlowStore = create<FlowState>()((set) => ({
  currentFlow: null,
  conversionStatus: "idle",
  selectedNodeId: null,
  setFlow: (currentFlow) => set({ currentFlow }),
  setConversionStatus: (conversionStatus) => set({ conversionStatus }),
  selectNode: (selectedNodeId) => set({ selectedNodeId }),
  reset: () => set({ currentFlow: null, conversionStatus: "idle", selectedNodeId: null }),
}));
