import { create } from "zustand";

/**
 * Lightweight UI-only state. Anything that is *not* persisted and *not* tied
 * to the active flow lives here (drawer open/close, modal stacks, etc.).
 */
export interface UiState {
  settingsDrawerOpen: boolean;
  openSettingsDrawer: () => void;
  closeSettingsDrawer: () => void;
  toggleSettingsDrawer: () => void;
}

export const useUiStore = create<UiState>()((set) => ({
  settingsDrawerOpen: false,
  openSettingsDrawer: () => set({ settingsDrawerOpen: true }),
  closeSettingsDrawer: () => set({ settingsDrawerOpen: false }),
  toggleSettingsDrawer: () =>
    set((s) => ({ settingsDrawerOpen: !s.settingsDrawerOpen })),
}));
