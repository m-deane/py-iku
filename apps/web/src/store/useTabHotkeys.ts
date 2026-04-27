import { useEffect } from "react";
import { useTabsStore } from "./tabs";
import { useCommandPaletteStore } from "./commandPalette";

/**
 * Detect contexts where Cmd+T / Cmd+W are NOT browser-reserved — i.e.
 * standalone PWAs (display-mode: standalone) and Electron-style hosts. In
 * those contexts the chrome doesn't intercept the meta+T / meta+W keystrokes
 * before our window-level listener runs, so we can keep them as-is. In a
 * vanilla browser tab we fall back to Alt+T / Alt+W (still discoverable from
 * the help modal) so the shortcut never silently no-ops behind the user's
 * back.
 */
export function isStandaloneContext(): boolean {
  if (typeof window === "undefined") return false;
  const w = window as Window & {
    process?: { type?: string; versions?: { electron?: string } };
  };
  // Electron exposes `process.versions.electron`; the renderer can read it.
  if (w.process?.versions?.electron) return true;
  // PWA installed to home screen / dock.
  try {
    if (typeof window.matchMedia === "function") {
      if (window.matchMedia("(display-mode: standalone)").matches) return true;
      if (window.matchMedia("(display-mode: window-controls-overlay)").matches)
        return true;
    }
  } catch {
    /* matchMedia unsupported — treat as browser tab */
  }
  // iOS Safari standalone flag.
  const navStandalone = (window.navigator as Navigator & { standalone?: boolean })
    .standalone;
  if (navStandalone === true) return true;
  return false;
}

/**
 * Global Cmd/Ctrl+T (new tab), +W (close active tab), +1..8 (jump) hotkeys
 * for the multi-tab workspace.
 *
 * Browser-reserved-key hygiene:
 *   - Cmd+T / Cmd+W are intercepted by the browser before our listener fires.
 *     In browser tabs we therefore listen for **Alt+T / Alt+W** instead. In
 *     standalone-PWA / Electron contexts we keep Cmd+T / Cmd+W (the chrome
 *     doesn't reserve them there). Both bindings are listed in the help
 *     modal so users discover whichever applies.
 *   - Cmd+1..8 are NOT browser-reserved — they remain on Cmd as before.
 *
 * Carefully gated against the command palette: when the palette is open it
 * owns Cmd+1..6 (section jumps) so we deliberately bail out and let the
 * palette handle the event.
 */
export function useTabHotkeys(enabled: boolean): void {
  useEffect(() => {
    if (!enabled) return;
    if (typeof window === "undefined") return;

    const standalone = isStandaloneContext();

    const handler = (e: KeyboardEvent): void => {
      const palette = useCommandPaletteStore.getState();
      if (palette.isOpen) return; // palette owns Cmd+1..6

      const tabsState = useTabsStore.getState();
      const meta = e.metaKey || e.ctrlKey;
      const alt = e.altKey;
      const key = e.key.toLowerCase();

      // New tab.
      const newTabHit = standalone
        ? meta && (key === "t")
        : alt && (key === "t");
      if (newTabHit) {
        e.preventDefault();
        e.stopPropagation();
        tabsState.newTab();
        return;
      }
      // Close active tab.
      const closeTabHit = standalone
        ? meta && (key === "w")
        : alt && (key === "w");
      if (closeTabHit) {
        e.preventDefault();
        e.stopPropagation();
        if (tabsState.activeTabId) {
          tabsState.closeTab(tabsState.activeTabId);
        }
        return;
      }
      // Cmd+1..8 → jump to tab N (browser-safe — no chrome conflict).
      if (meta && /^[1-8]$/.test(e.key)) {
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
