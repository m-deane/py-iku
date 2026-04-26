import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { ValidationPanel } from "../../src/features/validation/ValidationPanel";
import type { ScoreResponse } from "../../src/api/client";

const SAMPLE_FLOW: Record<string, unknown> = {
  flow_name: "f",
  total_recipes: 2,
  total_datasets: 0,
  datasets: [],
  recipes: [
    { name: "r1", type: "grouping", inputs: [], outputs: [] },
    { name: "r2", type: "sort", inputs: [], outputs: [] },
  ],
};

const SAMPLE_SCORE: ScoreResponse = {
  recipe_count: 2,
  processor_count: 0,
  max_depth: 1,
  fan_out_max: 1,
  complexity: 3.5,
};

function makeStubClient(score: ScoreResponse = SAMPLE_SCORE) {
  return {
    score: vi.fn(async () => score),
  };
}

describe("<ValidationPanel />", () => {
  it("renders warnings when expanded", async () => {
    render(
      <ValidationPanel
        flow={SAMPLE_FLOW}
        warnings={["First warning", "Second warning"]}
        defaultOpen
        clientImpl={makeStubClient()}
      />,
    );
    expect(screen.getByTestId("validation-warnings")).toBeInTheDocument();
    expect(screen.getByTestId("validation-warning-0")).toHaveTextContent(
      /First warning/,
    );
    expect(screen.getByTestId("validation-warning-1")).toHaveTextContent(
      /Second warning/,
    );
  });

  it("renders the score breakdown after the score request resolves", async () => {
    const stub = makeStubClient(SAMPLE_SCORE);
    render(
      <ValidationPanel
        flow={SAMPLE_FLOW}
        warnings={[]}
        defaultOpen
        clientImpl={stub}
      />,
    );
    await waitFor(() => {
      expect(screen.getByTestId("validation-score-complexity")).toBeInTheDocument();
    });
    expect(stub.score).toHaveBeenCalledWith(SAMPLE_FLOW);
    expect(screen.getByTestId("validation-score-recipes")).toHaveTextContent("2");
  });

  it("collapses and re-expands on toggle", () => {
    render(
      <ValidationPanel
        flow={SAMPLE_FLOW}
        warnings={[]}
        defaultOpen={false}
        clientImpl={makeStubClient()}
      />,
    );
    expect(screen.queryByTestId("validation-panel-body")).not.toBeInTheDocument();
    fireEvent.click(screen.getByTestId("validation-panel-toggle"));
    expect(screen.getByTestId("validation-panel-body")).toBeInTheDocument();
    fireEvent.click(screen.getByTestId("validation-panel-toggle"));
    expect(screen.queryByTestId("validation-panel-body")).not.toBeInTheDocument();
  });

  it("counts recipe types", async () => {
    render(
      <ValidationPanel
        flow={SAMPLE_FLOW}
        warnings={[]}
        defaultOpen
        clientImpl={makeStubClient()}
      />,
    );
    expect(screen.getByTestId("validation-tally-grouping")).toHaveTextContent("1");
    expect(screen.getByTestId("validation-tally-sort")).toHaveTextContent("1");
  });
});
