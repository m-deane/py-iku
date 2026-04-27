import { describe, it, expect, beforeEach } from "vitest";
import { useTabsStore, MAX_TABS } from "../../src/store/tabs";

/**
 * Sprint 4 — multi-tab workspace store.
 *
 * Coverage:
 *   - reset to single-tab baseline
 *   - new/close/setActive round-trip
 *   - cap at MAX_TABS (8)
 *   - drag-to-reorder via reorderTab
 *   - localStorage persistence round-trip via the persist middleware
 */
describe("tabs store", () => {
  beforeEach(() => {
    localStorage.clear();
    useTabsStore.getState().reset();
  });

  it("starts with one default tab", () => {
    const state = useTabsStore.getState();
    expect(state.tabs).toHaveLength(1);
    expect(state.activeTabId).toBe(state.tabs[0].id);
  });

  it("newTab appends and activates a new tab", () => {
    const id1 = useTabsStore.getState().tabs[0].id;
    const id2 = useTabsStore.getState().newTab({ title: "Curve build" });
    expect(id2).toBeTruthy();
    const state = useTabsStore.getState();
    expect(state.tabs).toHaveLength(2);
    expect(state.activeTabId).toBe(id2);
    expect(state.tabs[1].title).toBe("Curve build");
    expect(id1).not.toBe(id2);
  });

  it("caps at MAX_TABS", () => {
    while (useTabsStore.getState().tabs.length < MAX_TABS) {
      useTabsStore.getState().newTab();
    }
    expect(useTabsStore.getState().tabs).toHaveLength(MAX_TABS);
    const blocked = useTabsStore.getState().newTab();
    expect(blocked).toBeNull();
    expect(useTabsStore.getState().tabs).toHaveLength(MAX_TABS);
  });

  it("closeTab removes a non-active tab and keeps focus", () => {
    const a = useTabsStore.getState().tabs[0].id;
    const b = useTabsStore.getState().newTab() as string;
    useTabsStore.getState().setActiveTab(a);
    useTabsStore.getState().closeTab(b);
    const state = useTabsStore.getState();
    expect(state.tabs).toHaveLength(1);
    expect(state.activeTabId).toBe(a);
  });

  it("closeTab on the active tab focuses the previous tab", () => {
    const a = useTabsStore.getState().tabs[0].id;
    const b = useTabsStore.getState().newTab() as string;
    expect(useTabsStore.getState().activeTabId).toBe(b);
    useTabsStore.getState().closeTab(b);
    expect(useTabsStore.getState().activeTabId).toBe(a);
  });

  it("closeTab on the last tab replaces with a fresh tab", () => {
    const onlyId = useTabsStore.getState().tabs[0].id;
    useTabsStore.getState().closeTab(onlyId);
    const state = useTabsStore.getState();
    expect(state.tabs).toHaveLength(1);
    expect(state.tabs[0].id).not.toBe(onlyId);
  });

  it("setActiveTabIndex jumps to the Nth tab", () => {
    useTabsStore.getState().newTab();
    useTabsStore.getState().newTab();
    useTabsStore.getState().setActiveTabIndex(0);
    const tabs = useTabsStore.getState().tabs;
    expect(useTabsStore.getState().activeTabId).toBe(tabs[0].id);
    useTabsStore.getState().setActiveTabIndex(2);
    expect(useTabsStore.getState().activeTabId).toBe(tabs[2].id);
  });

  it("setActiveTabIndex out-of-range is a no-op", () => {
    const before = useTabsStore.getState().activeTabId;
    useTabsStore.getState().setActiveTabIndex(99);
    expect(useTabsStore.getState().activeTabId).toBe(before);
  });

  it("reorderTab swaps positions in place", () => {
    const a = useTabsStore.getState().tabs[0].id;
    const b = useTabsStore.getState().newTab() as string;
    const c = useTabsStore.getState().newTab() as string;
    useTabsStore.getState().reorderTab(0, 2);
    const ids = useTabsStore.getState().tabs.map((t) => t.id);
    expect(ids).toEqual([b, c, a]);
  });

  it("updateTab patches fields and bumps updatedAt", () => {
    const id = useTabsStore.getState().tabs[0].id;
    const before = useTabsStore.getState().tabs[0].updatedAt;
    // Wait at least a tick so updatedAt actually moves.
    return new Promise<void>((resolve) => {
      setTimeout(() => {
        useTabsStore.getState().updateTab(id, {
          code: "import pandas as pd",
          title: "Trade capture",
        });
        const t = useTabsStore.getState().tabs[0];
        expect(t.code).toBe("import pandas as pd");
        expect(t.title).toBe("Trade capture");
        expect(t.updatedAt).toBeGreaterThanOrEqual(before);
        resolve();
      }, 5);
    });
  });

  it("hydrateFromState restores tabs + active id (URL-as-state path)", () => {
    const seed = [
      {
        id: "shared-1",
        title: "Tab 1",
        code: "x = 1",
        lastFlow: null,
        mode: "rule" as const,
        provider: "anthropic" as const,
        scrollTop: 42,
        updatedAt: Date.now(),
      },
      {
        id: "shared-2",
        title: "Tab 2",
        code: "y = 2",
        lastFlow: null,
        mode: "llm" as const,
        provider: "openai" as const,
        scrollTop: 0,
        updatedAt: Date.now(),
      },
    ];
    useTabsStore.getState().hydrateFromState(seed, "shared-2");
    const state = useTabsStore.getState();
    expect(state.tabs.map((t) => t.id)).toEqual(["shared-1", "shared-2"]);
    expect(state.activeTabId).toBe("shared-2");
  });

  it("persists tabs to localStorage under the documented key", () => {
    useTabsStore.getState().newTab({ title: "Persist me" });
    // The persist middleware writes synchronously here.
    const raw = localStorage.getItem("py-iku-studio-tabs");
    expect(raw).not.toBeNull();
    const parsed = JSON.parse(raw as string);
    // shape: { state: { tabs: [...], activeTabId: "..." }, version: 1 }
    expect(parsed.state.tabs.length).toBeGreaterThanOrEqual(2);
    expect(parsed.state.tabs.some((t: { title: string }) => t.title === "Persist me")).toBe(true);
  });
});
