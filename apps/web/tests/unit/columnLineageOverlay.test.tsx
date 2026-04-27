import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ColumnLineageOverlay } from "../../src/features/inspector/ColumnLineageOverlay";
import type { Client, LineageResponse } from "../../src/api/client";

const FLOW = {
  flow_name: "v5",
  total_recipes: 2,
  total_datasets: 4,
  datasets: [
    { name: "df", type: "input", connection_type: "Filesystem", schema: [] },
    { name: "df_p", type: "intermediate", connection_type: "Filesystem", schema: [] },
    { name: "big", type: "output", connection_type: "Filesystem", schema: [] },
    { name: "small", type: "output", connection_type: "Filesystem", schema: [] },
  ],
  recipes: [
    {
      name: "prepare_1",
      type: "prepare",
      inputs: ["df"],
      outputs: ["df_p"],
      steps: [
        {
          type: "ColumnRenamer",
          params: { renamings: [{ from: "price", to: "px" }] },
        },
      ],
    },
    { name: "split_1", type: "split", inputs: ["df_p"], outputs: ["big", "small"] },
  ],
};

function stubClient(lineage: LineageResponse): Client {
  return {
    lineage: vi.fn(async (_flow: unknown, _col: string) => lineage),
  } as unknown as Client;
}

describe("<ColumnLineageOverlay />", () => {
  it("discovers columns from PREPARE renamings", () => {
    render(<ColumnLineageOverlay flow={FLOW} clientImpl={stubClient({} as LineageResponse)} />);
    expect(screen.getByTestId("column-chip-px")).toBeInTheDocument();
    expect(screen.getByTestId("column-chip-price")).toBeInTheDocument();
  });

  it("calls /flows/lineage and shows the resolved aliases on click", async () => {
    const lineage: LineageResponse = {
      column: "px",
      aliases: ["price", "px"],
      input_datasets: ["df"],
      output_datasets: ["big", "small"],
      edges: [
        {
          recipe_id: "prepare_1",
          input_dataset: "df",
          output_dataset: "df_p",
          kind: "rename",
        },
        {
          recipe_id: "split_1",
          input_dataset: "df_p",
          output_dataset: "big",
          kind: "split",
        },
      ],
      recipes: ["prepare_1", "split_1"],
      available_columns: ["price", "px"],
    };
    const stub = stubClient(lineage);
    render(<ColumnLineageOverlay flow={FLOW} clientImpl={stub} />);
    fireEvent.click(screen.getByTestId("column-chip-px"));
    await waitFor(() => {
      expect(screen.getByTestId("column-lineage-summary")).toBeInTheDocument();
    });
    expect(screen.getByTestId("lineage-aliases")).toHaveTextContent("price → px");
    // Both recipe edges are highlighted.
    expect(screen.getByTestId("lineage-edge-prepare_1")).toBeInTheDocument();
    expect(screen.getByTestId("lineage-edge-split_1")).toBeInTheDocument();
  });

  it("dims sibling edges via the data-recipe-id attribute (sentinel for canvas integration)", async () => {
    const lineage: LineageResponse = {
      column: "px",
      aliases: ["px"],
      input_datasets: [],
      output_datasets: [],
      edges: [
        { recipe_id: "prepare_1", input_dataset: "df", output_dataset: "df_p", kind: "rename" },
      ],
      recipes: ["prepare_1"],
      available_columns: ["px"],
    };
    render(<ColumnLineageOverlay flow={FLOW} clientImpl={stubClient(lineage)} />);
    fireEvent.click(screen.getByTestId("column-chip-px"));
    await waitFor(() => {
      const edge = screen.getByTestId("lineage-edge-prepare_1");
      // Recipe id is published so the canvas can map highlighted edges by id.
      expect(edge.getAttribute("data-recipe-id")).toBe("prepare_1");
      expect(edge.getAttribute("data-source")).toBe("df");
      expect(edge.getAttribute("data-target")).toBe("df_p");
    });
  });

  it("emits the lineage payload to onHighlight (canvas dimming integration point)", async () => {
    const lineage: LineageResponse = {
      column: "px",
      aliases: ["px"],
      input_datasets: [],
      output_datasets: [],
      edges: [],
      recipes: [],
      available_columns: ["px"],
    };
    const onHighlight = vi.fn();
    render(
      <ColumnLineageOverlay
        flow={FLOW}
        clientImpl={stubClient(lineage)}
        onHighlight={onHighlight}
      />,
    );
    fireEvent.click(screen.getByTestId("column-chip-px"));
    await waitFor(() => {
      expect(onHighlight).toHaveBeenCalled();
    });
    const last = onHighlight.mock.calls.at(-1)?.[0];
    expect(last?.column).toBe("px");
  });

  it("falls back to a friendly message when there are no columns", () => {
    render(
      <ColumnLineageOverlay
        flow={{ datasets: [], recipes: [] }}
        clientImpl={stubClient({} as LineageResponse)}
      />,
    );
    expect(screen.getByTestId("column-lineage-overlay")).toHaveTextContent(
      /no columns to inspect/i,
    );
  });
});
