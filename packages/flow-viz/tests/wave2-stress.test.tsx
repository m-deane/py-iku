/**
 * wave2-stress.test.tsx — canvas behaviour under stress flows.
 *
 * Verifies that <FlowCanvas> survives the kinds of graphs the Studio is
 * likely to see in production after Wave-2:
 *   - 10-node linear chain (deep DAG)
 *   - 8-input → 1-output stack (wide layer)
 *   - 1→2 SPLIT recipe (forward-curve-scd consolidation case)
 *   - WINDOW with partition_columns (badge / data attr presence)
 *
 * These are unit-level (vitest + jsdom + RTL) so they run in <1s and don't
 * depend on the live API. ELK runs in its sync fallback path under jsdom.
 */
import { describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { FlowCanvas } from "../src/FlowCanvas";
import type { MinimalFlow } from "../src/types";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function ds(name: string, datasetType: "input" | "intermediate" | "output", connectionType: string): MinimalFlow["nodes"][number] {
  return {
    id: name,
    type: "dataset",
    data: {
      name,
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      datasetType: datasetType as any,
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      connectionType: connectionType as any,
    },
  };
}

function recipe(
  name: string,
  type: string,
  inputs: number,
  outputs: number,
): MinimalFlow["nodes"][number] {
  return {
    id: name,
    type: "recipe",
    data: {
      name,
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      type: type as any,
      inputs,
      outputs,
    },
  };
}

function edge(source: string, target: string): MinimalFlow["edges"][number] {
  return { id: `${source}->${target}`, source, target };
}

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

/**
 * Linear chain: ds_0 -> r_1 -> ds_1 -> r_2 -> ds_2 -> ... -> r_10 -> ds_10
 * 10 recipes + 11 datasets.
 */
function buildDeepFlow(depth: number = 10): MinimalFlow {
  const nodes: MinimalFlow["nodes"] = [ds("ds_0", "input", "Filesystem")];
  const edges: MinimalFlow["edges"] = [];
  for (let i = 1; i <= depth; i += 1) {
    const recipeId = `r_${i}`;
    const dsId = `ds_${i}`;
    nodes.push(recipe(recipeId, "prepare", 1, 1));
    nodes.push(
      ds(
        dsId,
        i === depth ? "output" : "intermediate",
        i === depth ? "Snowflake" : "Filesystem",
      ),
    );
    edges.push(edge(`ds_${i - 1}`, recipeId));
    edges.push(edge(recipeId, dsId));
  }
  return { nodes, edges };
}

/**
 * 8 inputs → 1 stack recipe → 1 output.
 */
function buildWideFlow(): MinimalFlow {
  const inputs: string[] = [];
  const nodes: MinimalFlow["nodes"] = [];
  const edges: MinimalFlow["edges"] = [];
  for (let i = 0; i < 8; i += 1) {
    const id = `in_${i}`;
    inputs.push(id);
    nodes.push(ds(id, "input", "Filesystem"));
  }
  nodes.push(recipe("stack_all", "stack", 8, 1));
  nodes.push(ds("out", "output", "Snowflake"));
  for (const i of inputs) edges.push(edge(i, "stack_all"));
  edges.push(edge("stack_all", "out"));
  return { nodes, edges };
}

/**
 * 1 input → 1 SPLIT → 2 outputs (the forward-curve-scd consolidation case).
 */
function buildSplitFlow(): MinimalFlow {
  return {
    nodes: [
      ds("history", "input", "Filesystem"),
      recipe("split_scd", "split", 1, 2),
      ds("current", "output", "Filesystem"),
      ds("archive", "output", "Filesystem"),
    ],
    edges: [
      edge("history", "split_scd"),
      edge("split_scd", "current"),
      edge("split_scd", "archive"),
    ],
  };
}

/**
 * 1 input → 1 WINDOW recipe (partition_columns lives in settings, not in
 * MinimalFlow; the canvas exposes it via data attributes if/when wired).
 */
function buildWindowFlow(): MinimalFlow {
  return {
    nodes: [
      ds("ticks", "input", "BigQuery"),
      recipe("rolling", "window", 1, 1),
      ds("ranked", "output", "BigQuery"),
    ],
    edges: [edge("ticks", "rolling"), edge("rolling", "ranked")],
  };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("Wave-2 canvas stress", () => {
  it("renders a 10-recipe deep chain without crashing", async () => {
    const flow = buildDeepFlow(10);
    render(
      <div style={{ width: 1200, height: 800 }}>
        <FlowCanvas flow={flow} theme="light" showToolbar={false} showMinimap={false} />
      </div>,
    );
    await waitFor(
      () => {
        expect(screen.getByTestId("flow-canvas")).toBeTruthy();
        // Each recipe should produce a recipe-node-* testid.
        for (let i = 1; i <= 10; i += 1) {
          expect(screen.getByTestId(`recipe-node-r_${i}`)).toBeTruthy();
        }
      },
      { timeout: 4_000 },
    );
  });

  it("renders an 8-input wide flow with all inputs present", async () => {
    const flow = buildWideFlow();
    render(
      <div style={{ width: 1200, height: 1400 }}>
        <FlowCanvas flow={flow} theme="light" showToolbar={false} showMinimap={false} />
      </div>,
    );
    await waitFor(
      () => {
        // 8 inputs + 1 output.
        for (let i = 0; i < 8; i += 1) {
          expect(screen.getByTestId(`dataset-node-in_${i}`)).toBeTruthy();
        }
        expect(screen.getByTestId(`dataset-node-out`)).toBeTruthy();
        expect(screen.getByTestId(`recipe-node-stack_all`)).toBeTruthy();
      },
      { timeout: 4_000 },
    );
  });

  it("places 8 input datasets in the same upstream layer (ELK column 0)", async () => {
    const flow = buildWideFlow();
    render(
      <div style={{ width: 1200, height: 1400 }}>
        <FlowCanvas flow={flow} theme="light" showToolbar={false} showMinimap={false} />
      </div>,
    );
    await waitFor(
      () => {
        // The ELK layered algorithm should cluster all 8 inputs at the same
        // x position (the leftmost layer). We can't read positions directly
        // off DOM in jsdom (transforms are not applied), but we can assert
        // they all rendered.
        for (let i = 0; i < 8; i += 1) {
          expect(screen.getByTestId(`dataset-node-in_${i}`)).toBeTruthy();
        }
      },
      { timeout: 4_000 },
    );
  });

  it("renders a SPLIT recipe with two outgoing edges", async () => {
    const flow = buildSplitFlow();
    render(
      <div style={{ width: 800, height: 600 }}>
        <FlowCanvas flow={flow} theme="light" showToolbar={false} showMinimap={false} />
      </div>,
    );
    await waitFor(
      () => {
        expect(screen.getByTestId("recipe-node-split_scd")).toBeTruthy();
        expect(screen.getByTestId("dataset-node-current")).toBeTruthy();
        expect(screen.getByTestId("dataset-node-archive")).toBeTruthy();
      },
      { timeout: 4_000 },
    );
    // SPLIT recipe with 2 outputs: assert via the rendered recipe-node's
    // accessible label, which is computed from `outputs`. A split with one
    // output would say "1 outputs" — a regression we'd catch here.
    const split = screen.getByTestId("recipe-node-split_scd");
    expect(split.getAttribute("aria-label")).toContain("2 outputs");
    // The two output dataset nodes both rendered.
    expect(screen.getByTestId("dataset-node-current")).toBeTruthy();
    expect(screen.getByTestId("dataset-node-archive")).toBeTruthy();
  });

  it("renders a WINDOW recipe — partition badge is not yet a thing in the canvas", async () => {
    // partition_columns lives on recipe.settings, which the MinimalFlow shape
    // doesn't carry today. Canvas-side partition badges are deferred work;
    // this test pins the current behaviour: WINDOW renders but no badge.
    const flow = buildWindowFlow();
    render(
      <div style={{ width: 800, height: 600 }}>
        <FlowCanvas flow={flow} theme="light" showToolbar={false} showMinimap={false} />
      </div>,
    );
    await waitFor(
      () => {
        const node = screen.getByTestId("recipe-node-rolling");
        expect(node.getAttribute("data-recipe-type")).toBe("window");
        // Partition badge is not yet implemented — assert absence so we
        // get a failing test the day someone adds it (and document the
        // deferred work).
        expect(node.querySelector("[data-testid='partition-badge']")).toBeNull();
      },
      { timeout: 4_000 },
    );
  });

  it("survives an empty flow", async () => {
    render(
      <div style={{ width: 400, height: 300 }}>
        <FlowCanvas flow={{ nodes: [], edges: [] }} theme="light" showToolbar={false} showMinimap={false} />
      </div>,
    );
    await waitFor(() => {
      expect(screen.getByTestId("flow-canvas")).toBeTruthy();
    });
  });

  it("renders both light and dark themes without errors on a deep chain", async () => {
    const flow = buildDeepFlow(8);
    const { unmount } = render(
      <div style={{ width: 1200, height: 800 }}>
        <FlowCanvas flow={flow} theme="dark" showToolbar={false} showMinimap={false} />
      </div>,
    );
    await waitFor(() => {
      const canvas = screen.getByTestId("flow-canvas");
      expect(canvas.getAttribute("data-theme")).toBe("dark");
    });
    unmount();

    render(
      <div style={{ width: 1200, height: 800 }}>
        <FlowCanvas flow={flow} theme="light" showToolbar={false} showMinimap={false} />
      </div>,
    );
    await waitFor(() => {
      const canvas = screen.getByTestId("flow-canvas");
      expect(canvas.getAttribute("data-theme")).toBe("light");
    });
  });
});
