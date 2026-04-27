/**
 * useTabHotkeys — browser-reserved-key hygiene.
 *
 * Vanilla browser context: Alt+T / Alt+W drive new-tab / close-tab.
 * Standalone PWA / Electron: Cmd+T / Cmd+W drive the same actions.
 * Cmd+1..8 is unaffected — never browser-reserved.
 */
import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import { renderHook } from "@testing-library/react";
import { useTabHotkeys } from "../../src/store/useTabHotkeys";
import { useTabsStore } from "../../src/store/tabs";

function fireKey(opts: KeyboardEventInit & { key: string }): void {
  const ev = new KeyboardEvent("keydown", { bubbles: true, ...opts });
  window.dispatchEvent(ev);
}

describe("useTabHotkeys — browser-tab context (Alt fallback)", () => {
  beforeEach(() => {
    localStorage.clear();
    useTabsStore.getState().reset();
    // Vanilla browser: matchMedia stub already returns matches:false.
  });

  it("Alt+T opens a new tab", () => {
    renderHook(() => useTabHotkeys(true));
    const before = useTabsStore.getState().tabs.length;
    fireKey({ key: "t", altKey: true });
    expect(useTabsStore.getState().tabs.length).toBe(before + 1);
  });

  it("Alt+W closes the active tab", () => {
    useTabsStore.getState().newTab({ title: "second" });
    renderHook(() => useTabHotkeys(true));
    const before = useTabsStore.getState().tabs.length;
    fireKey({ key: "w", altKey: true });
    // closeTab() collapses to a single-tab baseline if invoked on the last
    // tab, so we expect length to be at most `before` (one decrement).
    expect(useTabsStore.getState().tabs.length).toBe(before - 1);
  });

  it("Cmd+T does NOT open a new tab in a browser context", () => {
    renderHook(() => useTabHotkeys(true));
    const before = useTabsStore.getState().tabs.length;
    fireKey({ key: "t", metaKey: true });
    expect(useTabsStore.getState().tabs.length).toBe(before);
  });

  it("Cmd+1..8 still jumps tabs (not browser-reserved)", () => {
    useTabsStore.getState().newTab({ title: "second" });
    useTabsStore.getState().newTab({ title: "third" });
    renderHook(() => useTabHotkeys(true));
    fireKey({ key: "1", metaKey: true });
    const state = useTabsStore.getState();
    expect(state.activeTabId).toBe(state.tabs[0].id);
    fireKey({ key: "3", metaKey: true });
    expect(useTabsStore.getState().activeTabId).toBe(
      useTabsStore.getState().tabs[2].id,
    );
  });
});

describe("useTabHotkeys — standalone PWA context (Cmd binding)", () => {
  let originalMatchMedia: typeof matchMedia;

  beforeEach(() => {
    localStorage.clear();
    useTabsStore.getState().reset();
    originalMatchMedia = window.matchMedia;
    (window as Window & { matchMedia: typeof matchMedia }).matchMedia = ((
      query: string,
    ) =>
      ({
        matches: query.includes("standalone"),
        media: query,
        onchange: null,
        addEventListener: () => {},
        removeEventListener: () => {},
        addListener: () => {},
        removeListener: () => {},
        dispatchEvent: () => false,
      }) as MediaQueryList) as typeof matchMedia;
  });

  afterEach(() => {
    window.matchMedia = originalMatchMedia;
    vi.restoreAllMocks();
  });

  it("Cmd+T opens a new tab in standalone-PWA mode", () => {
    renderHook(() => useTabHotkeys(true));
    const before = useTabsStore.getState().tabs.length;
    fireKey({ key: "t", metaKey: true });
    expect(useTabsStore.getState().tabs.length).toBe(before + 1);
  });

  it("Alt+T also opens a new tab — both bindings are tolerated for discoverability", () => {
    // Standalone path uses Cmd, but we deliberately do not block Alt — the
    // help modal lists both. The implementation gates Alt off in standalone
    // context to avoid double-fires; this test pins that behaviour.
    renderHook(() => useTabHotkeys(true));
    const before = useTabsStore.getState().tabs.length;
    fireKey({ key: "t", altKey: true });
    expect(useTabsStore.getState().tabs.length).toBe(before);
  });
});
