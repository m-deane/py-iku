import { describe, it, expect, beforeEach } from "vitest";
import {
  useRecentsStore,
  deriveFlowName,
  relativeTime,
  MAX_RECENTS,
} from "../../src/store/recents";

describe("recents store", () => {
  beforeEach(() => {
    useRecentsStore.getState().clear();
  });

  it("addRecent inserts at head and dedupes by id", () => {
    const store = useRecentsStore.getState();
    store.addRecent({ id: "a", name: "Alpha", source: "x", recipeCount: 1 });
    store.addRecent({ id: "b", name: "Beta", source: "y", recipeCount: 2 });
    store.addRecent({ id: "a", name: "Alpha2", source: "x2", recipeCount: 3 });
    const recents = useRecentsStore.getState().recents;
    expect(recents).toHaveLength(2);
    expect(recents[0].id).toBe("a");
    expect(recents[0].name).toBe("Alpha2");
    expect(recents[1].id).toBe("b");
  });

  it("recents is capped at MAX_RECENTS (10)", () => {
    const store = useRecentsStore.getState();
    for (let i = 0; i < MAX_RECENTS + 5; i += 1) {
      store.addRecent({
        id: `id-${i}`,
        name: `n-${i}`,
        source: `s-${i}`,
        recipeCount: 0,
      });
    }
    const recents = useRecentsStore.getState().recents;
    expect(recents).toHaveLength(MAX_RECENTS);
    // Newest at head, oldest pushed off the tail.
    expect(recents[0].id).toBe(`id-${MAX_RECENTS + 4}`);
  });

  it("togglePin promotes an existing recent into pinned and back", () => {
    const store = useRecentsStore.getState();
    store.addRecent({ id: "a", name: "Alpha", source: "x", recipeCount: 1 });
    expect(useRecentsStore.getState().isPinned("a")).toBe(false);
    store.togglePin("a");
    expect(useRecentsStore.getState().isPinned("a")).toBe(true);
    expect(useRecentsStore.getState().pinned).toHaveLength(1);
    store.togglePin("a");
    expect(useRecentsStore.getState().isPinned("a")).toBe(false);
    expect(useRecentsStore.getState().pinned).toHaveLength(0);
  });

  it("togglePin on an unknown id is a no-op", () => {
    const store = useRecentsStore.getState();
    store.togglePin("ghost");
    expect(useRecentsStore.getState().pinned).toHaveLength(0);
  });

  it("addRecent on a pinned id refreshes the pinned copy in lockstep", () => {
    const store = useRecentsStore.getState();
    store.addRecent({ id: "a", name: "First", source: "x", recipeCount: 1 });
    store.togglePin("a");
    store.addRecent({ id: "a", name: "Second", source: "y", recipeCount: 4 });
    const pinned = useRecentsStore.getState().pinned;
    expect(pinned[0].name).toBe("Second");
    expect(pinned[0].recipeCount).toBe(4);
  });

  it("remove drops the entry from both rails", () => {
    const store = useRecentsStore.getState();
    store.addRecent({ id: "a", name: "A", source: "x", recipeCount: 0 });
    store.togglePin("a");
    store.remove("a");
    expect(useRecentsStore.getState().recents).toHaveLength(0);
    expect(useRecentsStore.getState().pinned).toHaveLength(0);
  });
});

describe("deriveFlowName", () => {
  it("prefers the explicit name when given", () => {
    expect(deriveFlowName("# comment\nx = 1", "Trade Capture")).toBe(
      "Trade Capture",
    );
  });

  it("falls back to the first non-empty comment line", () => {
    expect(deriveFlowName("\n\n# Counterparty rollup\nimport pandas")).toBe(
      "Counterparty rollup",
    );
  });

  it("falls back to first code line if no comments at all", () => {
    expect(deriveFlowName("import pandas as pd\nx = 1")).toBe(
      "import pandas as pd",
    );
  });

  it("returns Untitled flow for empty source", () => {
    expect(deriveFlowName("")).toBe("Untitled flow");
    expect(deriveFlowName("   \n  \n")).toBe("Untitled flow");
  });

  it("truncates long names", () => {
    const long = "a".repeat(200);
    expect(deriveFlowName(long).length).toBeLessThanOrEqual(80);
  });
});

describe("relativeTime", () => {
  const NOW = 1_700_000_000_000;
  it("returns 'just now' under 45s", () => {
    expect(relativeTime(NOW - 30_000, NOW)).toBe("just now");
  });
  it("returns minutes under an hour", () => {
    expect(relativeTime(NOW - 5 * 60_000, NOW)).toBe("5 m");
  });
  it("returns hours under a day", () => {
    expect(relativeTime(NOW - 3 * 3_600_000, NOW)).toBe("3 h");
  });
  it("returns 'yesterday' for ~1 day ago", () => {
    expect(relativeTime(NOW - 26 * 3_600_000, NOW)).toBe("yesterday");
  });
  it("returns days for under a week", () => {
    expect(relativeTime(NOW - 4 * 24 * 3_600_000, NOW)).toBe("4 d");
  });
  it("returns a calendar label for older items", () => {
    const out = relativeTime(NOW - 30 * 24 * 3_600_000, NOW);
    expect(out).toMatch(/[A-Za-z]+ \d+/); // e.g. "Oct 23"
  });
});
