import { describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { FlowCanvas } from "../src/FlowCanvas";
import type { MinimalFlow } from "../src/types";

const fixture: MinimalFlow = {
  nodes: [
    {
      id: "ds_in",
      type: "dataset",
      data: { datasetType: "INPUT", connectionType: "SQL_POSTGRESQL", name: "orders_raw" },
    },
    {
      id: "rec_prep",
      type: "recipe",
      data: { type: "PREPARE", name: "Clean orders", inputs: 1, outputs: 1 },
    },
    {
      id: "rec_group",
      type: "recipe",
      data: { type: "GROUPING", name: "Aggregate", inputs: 1, outputs: 1 },
    },
    {
      id: "rec_split",
      type: "recipe",
      data: { type: "SPLIT", name: "Split", inputs: 1, outputs: 2 },
    },
    {
      id: "ds_out",
      type: "dataset",
      data: { datasetType: "OUTPUT", connectionType: "SQL_BIGQUERY", name: "metrics_daily" },
    },
  ],
  edges: [
    { id: "e1", source: "ds_in", target: "rec_prep" },
    { id: "e2", source: "rec_prep", target: "rec_group" },
    { id: "e3", source: "rec_group", target: "rec_split" },
    { id: "e4", source: "rec_split", target: "ds_out" },
  ],
};

describe("<FlowCanvas>", () => {
  it("renders without crashing and applies the theme attribute", async () => {
    render(
      <div style={{ width: 800, height: 600 }}>
        <FlowCanvas flow={fixture} theme="dark" />
      </div>,
    );
    const canvas = await screen.findByTestId("flow-canvas");
    expect(canvas).toBeTruthy();
    expect(canvas.getAttribute("data-theme")).toBe("dark");
  });

  it("eventually shows the 5 nodes after layout", async () => {
    render(
      <div style={{ width: 800, height: 600 }}>
        <FlowCanvas flow={fixture} theme="light" />
      </div>,
    );
    await waitFor(
      () => {
        const recipeNodes = document.querySelectorAll('[data-recipe-type]');
        const datasetNodes = document.querySelectorAll('[data-dataset-type]');
        expect(recipeNodes.length + datasetNodes.length).toBe(5);
      },
      { timeout: 3000 },
    );
  });

  it("marks dimmedNodeIds as data-dimmed and signals lineage-dim mode", async () => {
    render(
      <div style={{ width: 800, height: 600 }}>
        <FlowCanvas
          flow={fixture}
          theme="light"
          dimmedNodeIds={["rec_prep", "rec_split"]}
          highlightedEdgeIds={["e2"]}
        />
      </div>,
    );
    const canvas = await screen.findByTestId("flow-canvas");
    // Sentinel attribute lets downstream styles + tests detect the active mode.
    expect(canvas.getAttribute("data-lineage-dim")).toBe("true");

    await waitFor(
      () => {
        const dimmed = document.querySelectorAll('[data-dimmed="true"]');
        // Both dimmed recipe nodes flip the dim flag.
        expect(dimmed.length).toBeGreaterThanOrEqual(2);
      },
      { timeout: 3000 },
    );
  });

  it("does not set data-lineage-dim when no dimmedNodeIds are passed", async () => {
    render(
      <div style={{ width: 800, height: 600 }}>
        <FlowCanvas flow={fixture} theme="light" />
      </div>,
    );
    const canvas = await screen.findByTestId("flow-canvas");
    // Empty / undefined dimmedNodeIds → attribute is absent (renders normal).
    expect(canvas.getAttribute("data-lineage-dim")).toBeNull();
  });

  it("hosts the React Flow edges container after layout", async () => {
    render(
      <div style={{ width: 800, height: 600 }}>
        <FlowCanvas flow={fixture} theme="light" />
      </div>,
    );
    // jsdom does not measure SVG geometry, so React Flow does not render
    // individual <g class="react-flow__edge"> children — but the edges
    // container is mounted, and the edge data is wired into the renderer
    // (verified via the elkLayout test). Asserting on the container avoids a
    // jsdom-only false negative without skipping coverage.
    await waitFor(
      () => {
        const edgesContainer = document.querySelector(".react-flow__edges");
        expect(edgesContainer).not.toBeNull();
      },
      { timeout: 3000 },
    );
  });
});
