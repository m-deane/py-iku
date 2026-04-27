import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";
import type { ChatCitation } from "../../api/client";

/**
 * Chat-with-flow store. History is keyed by ``flowId`` so switching between
 * flows surfaces the right conversation. The drawer's open/close state is
 * persisted too — a trader who closes it on Convert expects it to stay closed
 * when they come back.
 */
export type ChatRole = "user" | "assistant" | "system";

export interface ChatTurn {
  id: string;
  role: ChatRole;
  content: string;
  /** Server-side citations — only present on assistant turns. */
  citations?: ChatCitation[];
  ts: number;
  /** True while the assistant turn is still streaming. */
  pending?: boolean;
}

export interface ChatState {
  /** Open state of the right-side drawer. */
  drawerOpen: boolean;
  /** Width of the drawer as a fraction of viewport (0.25–0.5). */
  drawerWidth: number;
  /** Per-flow history. Key = flow id. */
  historyByFlow: Record<string, ChatTurn[]>;
  /** Currently-highlighted recipe id (for canvas hover sync). */
  highlightedRecipeId: string | null;

  setOpen: (open: boolean) => void;
  toggleOpen: () => void;
  setWidth: (w: number) => void;
  appendTurn: (flowId: string, turn: ChatTurn) => void;
  patchAssistantTurn: (
    flowId: string,
    turnId: string,
    patch: Partial<ChatTurn>,
  ) => void;
  clearHistory: (flowId: string) => void;
  setHighlight: (recipeId: string | null) => void;
}

const DEFAULTS = {
  drawerOpen: false,
  drawerWidth: 0.3,
  historyByFlow: {} as Record<string, ChatTurn[]>,
  highlightedRecipeId: null as string | null,
};

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      ...DEFAULTS,
      setOpen: (drawerOpen) => set({ drawerOpen }),
      toggleOpen: () => set((s) => ({ drawerOpen: !s.drawerOpen })),
      setWidth: (drawerWidth) =>
        set({
          drawerWidth: Math.min(0.5, Math.max(0.25, drawerWidth)),
        }),
      appendTurn: (flowId, turn) =>
        set((s) => {
          const list = s.historyByFlow[flowId] ?? [];
          return {
            historyByFlow: {
              ...s.historyByFlow,
              [flowId]: [...list, turn],
            },
          };
        }),
      patchAssistantTurn: (flowId, turnId, patch) =>
        set((s) => {
          const list = s.historyByFlow[flowId] ?? [];
          const idx = list.findIndex((t) => t.id === turnId);
          if (idx === -1) return s;
          const updated: ChatTurn[] = [...list];
          updated[idx] = { ...updated[idx], ...patch };
          return {
            historyByFlow: {
              ...s.historyByFlow,
              [flowId]: updated,
            },
          };
        }),
      clearHistory: (flowId) =>
        set((s) => {
          const next = { ...s.historyByFlow };
          delete next[flowId];
          return { historyByFlow: next };
        }),
      setHighlight: (highlightedRecipeId) => set({ highlightedRecipeId }),
    }),
    {
      name: "py-iku-studio-chat",
      version: 1,
      storage: createJSONStorage(() => localStorage),
      // Don't persist the volatile highlight state.
      partialize: (state) => ({
        drawerOpen: state.drawerOpen,
        drawerWidth: state.drawerWidth,
        historyByFlow: state.historyByFlow,
      }),
    },
  ),
);

/** Stable hash → flow id when the caller doesn't have one yet. */
export function flowIdFromCode(code: string): string {
  let h = 5381;
  for (let i = 0; i < code.length; i += 1) {
    h = ((h << 5) + h + code.charCodeAt(i)) | 0;
  }
  return `flow-${(h >>> 0).toString(36)}`;
}
