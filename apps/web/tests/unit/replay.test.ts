import { describe, it, expect, beforeEach } from "vitest";
import {
  useReplayStore,
  formatRunTimestamp,
  MAX_RUNS,
} from "../../src/store/replay";

/**
 * Sprint 4 — replay/undo timeline store.
 *
 * Coverage:
 *   - recordRun head-inserts and computes a recipe-delta diff
 *   - cap at MAX_RUNS (20) with `cleared` counter ticking
 *   - clear wipes both runs and the cleared counter
 *   - localStorage persistence round-trip
 *   - formatRunTimestamp produces a HH:MM-ish label
 */
describe("replay store", () => {
  beforeEach(() => {
    localStorage.clear();
    useReplayStore.getState().clear();
  });

  it("starts empty", () => {
    expect(useReplayStore.getState().runs).toHaveLength(0);
    expect(useReplayStore.getState().cleared).toBe(0);
  });

  it("recordRun head-inserts the new run", () => {
    useReplayStore.getState().recordRun({
      source: "x = 1",
      flow: { recipes: [{ name: "a", type: "PREPARE" }] },
      mode: "rule",
      status: "success",
      recipeCount: 1,
      complexity: 1.0,
    });
    useReplayStore.getState().recordRun({
      source: "x = 2",
      flow: { recipes: [{ name: "a", type: "PREPARE" }, { name: "b", type: "JOIN" }] },
      mode: "rule",
      status: "success",
      recipeCount: 2,
      complexity: 2.5,
    });
    const runs = useReplayStore.getState().runs;
    expect(runs).toHaveLength(2);
    // Newest at head.
    expect(runs[0].source).toBe("x = 2");
    expect(runs[0].diffSummary?.recipeDelta).toBe(1);
    expect(runs[0].diffSummary?.added).toEqual(["b"]);
    expect(runs[0].diffSummary?.removed).toEqual([]);
  });

  it("captures error runs without a flow", () => {
    useReplayStore.getState().recordRun({
      source: "syntax broken",
      flow: null,
      mode: "rule",
      status: "error",
      recipeCount: 0,
      complexity: 0,
      errorTitle: "Could not parse Python",
    });
    const run = useReplayStore.getState().runs[0];
    expect(run.status).toBe("error");
    expect(run.errorTitle).toBe("Could not parse Python");
    expect(run.flow).toBeNull();
  });

  it("caps runs at MAX_RUNS and increments `cleared`", () => {
    for (let i = 0; i < MAX_RUNS + 5; i += 1) {
      useReplayStore.getState().recordRun({
        source: `code-${i}`,
        flow: { recipes: [] },
        mode: "rule",
        status: "success",
        recipeCount: 0,
        complexity: 0,
      });
    }
    const state = useReplayStore.getState();
    expect(state.runs).toHaveLength(MAX_RUNS);
    expect(state.cleared).toBe(5);
    // Newest at head still.
    expect(state.runs[0].source).toBe(`code-${MAX_RUNS + 4}`);
  });

  it("clear() wipes runs and cleared counter", () => {
    useReplayStore.getState().recordRun({
      source: "x",
      flow: null,
      mode: "rule",
      status: "error",
      recipeCount: 0,
      complexity: 0,
    });
    useReplayStore.getState().clear();
    expect(useReplayStore.getState().runs).toHaveLength(0);
    expect(useReplayStore.getState().cleared).toBe(0);
  });

  it("persists runs to localStorage under the documented key", () => {
    useReplayStore.getState().recordRun({
      source: "persist-me",
      flow: { recipes: [{ name: "r1", type: "PREPARE" }] },
      mode: "rule",
      status: "success",
      recipeCount: 1,
      complexity: 1.0,
    });
    const raw = localStorage.getItem("py-iku-studio-replay");
    expect(raw).not.toBeNull();
    const parsed = JSON.parse(raw as string);
    expect(parsed.state.runs).toHaveLength(1);
    expect(parsed.state.runs[0].source).toBe("persist-me");
  });

  it("formatRunTimestamp returns a HH:MM-ish label", () => {
    const label = formatRunTimestamp(new Date("2026-04-26T14:32:00Z").getTime());
    // Locale-dependent — just assert it contains digits and a colon.
    expect(label).toMatch(/\d/);
    expect(label).toMatch(/:/);
  });
});
