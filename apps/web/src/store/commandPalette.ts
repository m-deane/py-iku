import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

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
      version: 3,
      // Persist only the durable bits; isOpen and currentArgs* are transient.
      partialize: (state) => ({
        pinnedIds: state.pinnedIds,
      }),
      migrate: (persisted, _version) => {
        // Older versions persisted `recent` + `recentSearches`; both have
        // been removed in v3. Strip them off the rehydrated blob so existing
        // users don't trip the JSON schema check.
        const p = (persisted as Partial<CommandPaletteState>) ?? {};
        return {
          pinnedIds: p.pinnedIds ?? [],
        } as Partial<CommandPaletteState>;
      },
    },
  ),
);
