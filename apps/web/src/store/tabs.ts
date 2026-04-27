import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { ConversionMode } from "../state/flowStore";
import type { LlmProvider } from "../state/settingsStore";

/**
 * Multi-tab workspace store (Sprint 4 — power user).
 *
 * Each tab carries the per-editor state that previously lived as a singleton on
 * `flowStore` + `settingsStore`: the in-progress source code, the last
 * converted flow JSON, the chosen mode/provider, the editor scroll position,
 * and a friendly title.
 *
 * Capacity: hard-capped at MAX_TABS (8). New tabs are appended; older tabs
 * remain in place until the user closes them.
 *
 * Persistence: localStorage via `zustand/persist` so a reload restores the
 * full workspace. Key: `py-iku-studio-tabs`. Schema versioned (v1) so future
 * fields can migrate cleanly.
 *
 * IMPORTANT: this store is *additive* and does NOT replace `flowStore`. The
 * tabs feature is gated behind `settings.multiTabEnabled`; when off, the tab
 * UI is hidden entirely and `flowStore` continues to drive the page exactly
 * as before. When on, the page reads/writes through this store and mirrors
 * the active tab back to `flowStore` so the rest of the app (recents, share,
 * inspector) keeps working without per-feature plumbing changes.
 */
export const MAX_TABS = 8;

export interface WorkspaceTab {
  /** Stable client-generated id. */
  id: string;
  /** User-visible label rendered on the tab strip. */
  title: string;
  /** Python source backing the editor. */
  code: string;
  /**
   * Last successful conversion result, persisted so the tab "remembers" its
   * flow when the user round-trips to another tab and back.
   */
  lastFlow: Record<string, unknown> | null;
  /** Conversion mode selected on this tab. */
  mode: ConversionMode;
  /** LLM provider selected on this tab (relevant when `mode === "llm"`). */
  provider: LlmProvider;
  /** LLM model selected on this tab (relevant when `mode === "llm"`). */
  model?: string;
  /**
   * Editor scroll position. Stored as `scrollTop` rather than line number so
   * the restore is exact even if the editor's font/zoom changes between
   * sessions.
   */
  scrollTop: number;
  /** Wall-clock ms when the tab was last touched (for sort/debug). */
  updatedAt: number;
}

export interface TabsState {
  tabs: WorkspaceTab[];
  activeTabId: string | null;
  /**
   * Create a new tab and switch to it. Returns the new id, or null if the
   * cap is already reached.
   */
  newTab: (seed?: Partial<Omit<WorkspaceTab, "id" | "updatedAt">>) => string | null;
  /** Close a tab. If it was active, focus shifts to the previous tab (or the next). */
  closeTab: (id: string) => void;
  /** Switch the active tab. No-op if the id is unknown. */
  setActiveTab: (id: string) => void;
  /** Jump to the Nth tab (0-indexed). No-op if the index is out of range. */
  setActiveTabIndex: (index: number) => void;
  /** Patch fields on a tab in place. Bumps `updatedAt`. */
  updateTab: (id: string, patch: Partial<Omit<WorkspaceTab, "id">>) => void;
  /** Reorder a tab by index (drag-to-reorder). */
  reorderTab: (fromIndex: number, toIndex: number) => void;
  /** Replace the entire tab list (used by URL-as-state restore). */
  hydrateFromState: (tabs: WorkspaceTab[], activeTabId: string | null) => void;
  /** Wipe all tabs. Reset back to a single empty tab. */
  reset: () => void;
}

let _idCounter = 0;
function makeTabId(): string {
  _idCounter += 1;
  return `tab-${Date.now().toString(36)}-${_idCounter.toString(36)}`;
}

function makeDefaultTab(seed?: Partial<Omit<WorkspaceTab, "id" | "updatedAt">>): WorkspaceTab {
  return {
    id: makeTabId(),
    title: seed?.title ?? "Untitled",
    code: seed?.code ?? "",
    lastFlow: seed?.lastFlow ?? null,
    mode: seed?.mode ?? "rule",
    provider: seed?.provider ?? "anthropic",
    model: seed?.model,
    scrollTop: seed?.scrollTop ?? 0,
    updatedAt: Date.now(),
  };
}

const initialTab = makeDefaultTab({ title: "Tab 1" });

export const useTabsStore = create<TabsState>()(
  persist(
    (set, get) => ({
      tabs: [initialTab],
      activeTabId: initialTab.id,

      newTab: (seed) => {
        const state = get();
        if (state.tabs.length >= MAX_TABS) return null;
        const tab = makeDefaultTab({
          title: seed?.title ?? `Tab ${state.tabs.length + 1}`,
          ...seed,
        });
        set({ tabs: [...state.tabs, tab], activeTabId: tab.id });
        return tab.id;
      },

      closeTab: (id) => {
        set((state) => {
          // Never close the last tab — replace it with a fresh one to keep the
          // workspace usable. This matches the editor-tab behaviour in VS Code.
          if (state.tabs.length === 1 && state.tabs[0].id === id) {
            const fresh = makeDefaultTab({ title: "Tab 1" });
            return { tabs: [fresh], activeTabId: fresh.id };
          }
          const idx = state.tabs.findIndex((t) => t.id === id);
          if (idx < 0) return state;
          const nextTabs = state.tabs.filter((t) => t.id !== id);
          let nextActive = state.activeTabId;
          if (state.activeTabId === id) {
            // Focus the previous tab if there is one; otherwise the next.
            const fallback = nextTabs[Math.max(0, idx - 1)] ?? nextTabs[0];
            nextActive = fallback.id;
          }
          return { tabs: nextTabs, activeTabId: nextActive };
        });
      },

      setActiveTab: (id) => {
        set((state) => {
          if (!state.tabs.some((t) => t.id === id)) return state;
          return { activeTabId: id };
        });
      },

      setActiveTabIndex: (index) => {
        set((state) => {
          const tab = state.tabs[index];
          if (!tab) return state;
          return { activeTabId: tab.id };
        });
      },

      updateTab: (id, patch) => {
        set((state) => ({
          tabs: state.tabs.map((t) =>
            t.id === id ? { ...t, ...patch, updatedAt: Date.now() } : t,
          ),
        }));
      },

      reorderTab: (fromIndex, toIndex) => {
        set((state) => {
          if (
            fromIndex < 0 ||
            toIndex < 0 ||
            fromIndex >= state.tabs.length ||
            toIndex >= state.tabs.length ||
            fromIndex === toIndex
          ) {
            return state;
          }
          const next = [...state.tabs];
          const [moved] = next.splice(fromIndex, 1);
          next.splice(toIndex, 0, moved);
          return { tabs: next };
        });
      },

      hydrateFromState: (tabs, activeTabId) => {
        if (!Array.isArray(tabs) || tabs.length === 0) return;
        const safe = tabs.slice(0, MAX_TABS);
        const active =
          activeTabId && safe.some((t) => t.id === activeTabId)
            ? activeTabId
            : safe[0].id;
        set({ tabs: safe, activeTabId: active });
      },

      reset: () => {
        const fresh = makeDefaultTab({ title: "Tab 1" });
        set({ tabs: [fresh], activeTabId: fresh.id });
      },
    }),
    {
      name: "py-iku-studio-tabs",
      storage: createJSONStorage(() => localStorage),
      version: 1,
      partialize: (state) => ({
        tabs: state.tabs,
        activeTabId: state.activeTabId,
      }),
    },
  ),
);

/** Pure helper — returns the active tab or undefined. Used by selectors. */
export function selectActiveTab(state: TabsState): WorkspaceTab | undefined {
  if (!state.activeTabId) return undefined;
  return state.tabs.find((t) => t.id === state.activeTabId);
}
