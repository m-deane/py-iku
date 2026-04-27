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

export interface CommandPaletteState {
  isOpen: boolean;
  open: () => void;
  close: () => void;
  toggle: () => void;
  recent: RecentItem[];
  pushRecent: (item: Omit<RecentItem, "ts">) => void;
  clearRecent: () => void;
}

export const useCommandPaletteStore = create<CommandPaletteState>()(
  persist(
    (set) => ({
      isOpen: false,
      open: () => set({ isOpen: true }),
      close: () => set({ isOpen: false }),
      toggle: () => set((s) => ({ isOpen: !s.isOpen })),
      recent: [],
      pushRecent: (item) =>
        set((s) => {
          const ts = Date.now();
          // De-dupe by id, keep newest first, cap length.
          const filtered = s.recent.filter((r) => r.id !== item.id);
          const next = [{ ...item, ts }, ...filtered].slice(0, MAX_RECENT);
          return { recent: next };
        }),
      clearRecent: () => set({ recent: [] }),
    }),
    {
      name: "py-iku-studio-command-palette",
      storage: createJSONStorage(() => localStorage),
      version: 1,
      // Persist only the recent list; isOpen is always transient.
      partialize: (state) => ({ recent: state.recent }),
    },
  ),
);
