import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

/**
 * Stable identifier for a recently-used palette invocation.
 *
 * `id` is the palette item id (`recipe:GROUPING`, `action:convert`, etc.).
 * The display fields are denormalised so the "Recently used" section can
 * render even after the underlying source list (e.g. catalog) hasn't loaded.
 */
export interface RecentItem {
  id: string;
  section: string;
  primary: string;
  secondary?: string;
  icon?: string;
  /** Epoch ms — newest first when surfaced. */
  ts: number;
}

const MAX_RECENT = 10;
const MAX_RECENT_SEARCHES = 10;
const MAX_PINNED = 30;

/**
 * Snapshot of an in-progress argument-collection step.
 *
 * The palette enters argument-collection mode when the user invokes an item
 * that declared `args: ArgSpec[]`. Each entry records the value chosen at
 * that step so the breadcrumb (e.g. "Convert / rule") can render even after
 * the user has tabbed past it. See `ArgSpec` in the palette `types.ts`.
 */
export interface ArgStepValue {
  /** ArgSpec.key — uniquely identifies which argument was filled. */
  key: string;
  /** ArgSpec.label — pre-resolved so the breadcrumb doesn't need the spec. */
  label: string;
  /** Raw value chosen by the user. */
  value: unknown;
  /** Display label for the chosen value (e.g. "rule" → "Rule-based"). */
  display: string;
}

export interface CommandPaletteState {
  isOpen: boolean;
  open: () => void;
  close: () => void;
  toggle: () => void;

  recent: RecentItem[];
  pushRecent: (item: Omit<RecentItem, "ts">) => void;
  clearRecent: () => void;

  /** Last-N raw query strings the user typed and then invoked from. */
  recentSearches: string[];
  pushRecentSearch: (query: string) => void;
  clearRecentSearches: () => void;

  /** IDs of palette items the user has explicitly pinned. */
  pinnedIds: string[];
  togglePin: (id: string) => void;
  isPinned: (id: string) => boolean;
  clearPinned: () => void;

  /**
   * Argument-collection state. When `currentArgsItemId` is set, the palette
   * is in multi-step mode for that item; `currentArgs` records each step's
   * resolved value in the order it was collected.
   */
  currentArgsItemId: string | null;
  currentArgs: ArgStepValue[];
  beginArgs: (itemId: string) => void;
  pushArg: (step: ArgStepValue) => void;
  popArg: () => void;
  clearArgs: () => void;
}

export const useCommandPaletteStore = create<CommandPaletteState>()(
  persist(
    (set, get) => ({
      isOpen: false,
      open: () => set({ isOpen: true }),
      close: () =>
        set({
          isOpen: false,
          // Closing always cancels any in-flight arg collection.
          currentArgsItemId: null,
          currentArgs: [],
        }),
      toggle: () => set((s) => ({ isOpen: !s.isOpen })),

      recent: [],
      pushRecent: (item) =>
        set((s) => {
          const ts = Date.now();
          const filtered = s.recent.filter((r) => r.id !== item.id);
          const next = [{ ...item, ts }, ...filtered].slice(0, MAX_RECENT);
          return { recent: next };
        }),
      clearRecent: () => set({ recent: [] }),

      recentSearches: [],
      pushRecentSearch: (query) =>
        set((s) => {
          const trimmed = query.trim();
          if (!trimmed) return s;
          const filtered = s.recentSearches.filter((q) => q !== trimmed);
          return {
            recentSearches: [trimmed, ...filtered].slice(0, MAX_RECENT_SEARCHES),
          };
        }),
      clearRecentSearches: () => set({ recentSearches: [] }),

      pinnedIds: [],
      togglePin: (id) =>
        set((s) => {
          if (s.pinnedIds.includes(id)) {
            return { pinnedIds: s.pinnedIds.filter((x) => x !== id) };
          }
          return { pinnedIds: [id, ...s.pinnedIds].slice(0, MAX_PINNED) };
        }),
      isPinned: (id) => get().pinnedIds.includes(id),
      clearPinned: () => set({ pinnedIds: [] }),

      currentArgsItemId: null,
      currentArgs: [],
      beginArgs: (itemId) =>
        set({ currentArgsItemId: itemId, currentArgs: [] }),
      pushArg: (step) =>
        set((s) => ({ currentArgs: [...s.currentArgs, step] })),
      popArg: () =>
        set((s) => ({
          // Drop the last collected step but keep the item active. The
          // palette interprets "Esc with zero remaining args" as "cancel"
          // via its own check on currentArgs.length, not by clearing here.
          currentArgs: s.currentArgs.slice(0, -1),
        })),
      clearArgs: () => set({ currentArgsItemId: null, currentArgs: [] }),
    }),
    {
      name: "py-iku-studio-command-palette",
      storage: createJSONStorage(() => localStorage),
      version: 2,
      // Persist only the durable bits; isOpen and currentArgs* are transient.
      partialize: (state) => ({
        recent: state.recent,
        recentSearches: state.recentSearches,
        pinnedIds: state.pinnedIds,
      }),
      migrate: (persisted, version) => {
        // v1 only persisted `recent`. Initialise the new fields when loading
        // an older blob so existing users don't trip the JSON schema check.
        const p = (persisted as Partial<CommandPaletteState>) ?? {};
        if (version < 2) {
          return {
            recent: p.recent ?? [],
            recentSearches: [],
            pinnedIds: [],
          } as Partial<CommandPaletteState>;
        }
        return p as Partial<CommandPaletteState>;
      },
    },
  ),
);
