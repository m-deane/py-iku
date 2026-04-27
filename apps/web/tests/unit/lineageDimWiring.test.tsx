/**
 * Lineage-dim wiring (ColumnLineageOverlay → flowStore.lineageFocus).
 *
 * The overlay publishes a LineageResponse via `onHighlight`. The ConvertPage
 * translates it into a `LineageFocus` snapshot on `flowStore` so any mounted
 * FlowCanvas can apply the dim/highlight CSS through the shared
 * `dimmedNodeIds` + `highlightedEdgeIds` props.
 *
 * This test exercises the inspector → store pipeline directly against the
 * overlay's public callback contract — the canvas-side rendering is asserted
 * separately in the flow-viz package's FlowCanvas.test.tsx.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import { ColumnLineageOverlay } from "../../src/features/inspector/ColumnLineageOverlay";
import { useFlowStore } from "../../src/state/flowStore";
import type { LineageResponse } from "../../src/api/client";

const SAMPLE_FLOW = {
  flow_name: "demo",
  recipes: [
    {
      name: "prep_x",
      type: "PREPARE",
      inputs: ["raw"],
      outputs: ["clean"],
      steps: [{ params: { columns: ["price"] } }],
    },
    {
      name: "agg_x",
      type: "GROUPING",
      inputs: ["clean"],
      outputs: ["pnl"],
      steps: [],
    },
  ],
  datasets: [
    { name: "raw", schema: [{ name: "price" }] },
    { name: "clean", schema: [{ name: "price" }] },
    { name: "pnl", schema: [] },
  ],
};

function makeStubLineage(): LineageResponse {
  return {
    column: "price",
    aliases: ["price"],
    input_datasets: ["raw"],
    output_datasets: ["clean"],
    edges: [
      {
        recipe_id: "prep_x",
        input_dataset: "raw",
        output_dataset: "clean",
        kind: "passthrough",
      },
    ],
    recipes: ["prep_x"],
    available_columns: ["price"],
  };
}

describe("ColumnLineageOverlay onHighlight contract", () => {
  beforeEach(() => {
    act(() => useFlowStore.getState().reset());
  });

  it("emits a LineageResponse to the onHighlight callback when a column is picked", async () => {
    const stubClient = { lineage: vi.fn(async () => makeStubLineage()) };
    const onHighlight = vi.fn();
    render(
      <ColumnLineageOverlay
        flow={SAMPLE_FLOW}
        clientImpl={stubClient as never}
        onHighlight={onHighlight}
      />,
    );

    fireEvent.click(screen.getByTestId("column-chip-price"));
    await waitFor(() => {
      expect(stubClient.lineage).toHaveBeenCalledWith(SAMPLE_FLOW, "price");
    });
    await waitFor(() => {
      // The post-resolve effect publishes the lineage object via callback.
      const lastCall =
        onHighlight.mock.calls[onHighlight.mock.calls.length - 1]?.[0];
      expect(lastCall?.recipes).toEqual(["prep_x"]);
      expect(lastCall?.edges).toHaveLength(1);
    });
  });

  it("emits null when the active column is cleared", async () => {
    const stubClient = { lineage: vi.fn(async () => makeStubLineage()) };
    const onHighlight = vi.fn();
    render(
      <ColumnLineageOverlay
        flow={SAMPLE_FLOW}
        clientImpl={stubClient as never}
        onHighlight={onHighlight}
      />,
    );

    fireEvent.click(screen.getByTestId("column-chip-price"));
    await waitFor(() => expect(stubClient.lineage).toHaveBeenCalled());
    // Click again to toggle off.
    fireEvent.click(screen.getByTestId("column-chip-price"));
    await waitFor(() => {
      const lastCall =
        onHighlight.mock.calls[onHighlight.mock.calls.length - 1]?.[0];
      expect(lastCall).toBeNull();
    });
  });
});
