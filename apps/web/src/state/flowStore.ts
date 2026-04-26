import { create } from "zustand";

/**
 * Skeleton store for the active flow. M5 will replace `unknown` with the real
 * `DataikuFlow` type emitted by `packages/types` codegen.
 */
export type ConversionStatus = "idle" | "streaming" | "running" | "done" | "error";
export type ConversionMode = "rule" | "llm";

export interface FlowState {
  currentCode: string;
  currentFlow: unknown | null;
  conversionStatus: ConversionStatus;
  conversionMode: ConversionMode;
  selectedNodeId: string | null;
  setCurrentCode: (code: string) => void;
  setFlow: (flow: unknown | null) => void;
  setConversionStatus: (status: ConversionStatus) => void;
  setConversionMode: (mode: ConversionMode) => void;
  selectNode: (id: string | null) => void;
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
  reset: () =>
    set({
      currentFlow: null,
      conversionStatus: "idle",
      selectedNodeId: null,
    }),
}));
