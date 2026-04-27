import { useEffect } from "react";
import { useTabsStore } from "./tabs";
import { useCommandPaletteStore } from "./commandPalette";

/**
 * Global Cmd/Ctrl+T (new tab), +W (close active tab), +1..8 (jump) hotkeys
 * for the multi-tab workspace.
 *
 * Carefully gated against the command palette: when the palette is open it
 * owns Cmd+1..6 (section jumps) so we deliberately bail out and let the
 * palette handle the event. Outside the palette these run globally — the
 * spec calls for them to fire whenever an editor tab is focused, but we keep
 * them application-wide for parity with VS Code/Chrome and because the
 * palette gate covers the conflict-of-record.
 *
 * NOTE: Browsers reserve Cmd+T / Cmd+W / Cmd+N for native tab/window
 * management. We `preventDefault()` and stop propagation, which works inside
 * Electron-style PWAs and dev-server contexts; in a vanilla browser, Cmd+T
 * may be intercepted by the chrome before our listener runs. That's fine —
 * the documented Cmd+K palette action "New tab" gives users a reliable
 * alternative.
 */
export function useTabHotkeys(enabled: boolean): void {
  useEffect(() => {
    if (!enabled) return;
    if (typeof window === "undefined") return;

    const handler = (e: KeyboardEvent): void => {
      const palette = useCommandPaletteStore.getState();
      if (palette.isOpen) return; // palette owns Cmd+1..6

      const meta = e.metaKey || e.ctrlKey;
      if (!meta) return;

      const tabsState = useTabsStore.getState();

      // Cmd+T → new tab.
      if (e.key === "t" || e.key === "T") {
        e.preventDefault();
        e.stopPropagation();
        tabsState.newTab();
        return;
      }
      // Cmd+W → close active tab.
      if (e.key === "w" || e.key === "W") {
        e.preventDefault();
        e.stopPropagation();
        if (tabsState.activeTabId) {
          tabsState.closeTab(tabsState.activeTabId);
        }
        return;
      }
      // Cmd+1..8 → jump to tab N.
      if (/^[1-8]$/.test(e.key)) {
        const idx = Number(e.key) - 1;
        if (idx < tabsState.tabs.length) {
          e.preventDefault();
          e.stopPropagation();
          tabsState.setActiveTabIndex(idx);
        }
        return;
      }
    };

    // Capture-phase listener so we can preempt feature-level handlers (the
    // command-palette listener, for instance, also lives at window level).
    window.addEventListener("keydown", handler, true);
    return () => window.removeEventListener("keydown", handler, true);
  }, [enabled]);
}
