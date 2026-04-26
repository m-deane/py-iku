import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, act, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { DiffPage } from "../../src/features/diff/DiffPage";
import { useFlowStore } from "../../src/state/flowStore";
import type {
  ConvertResponse,
  DiffResponse,
} from "../../src/api/client";

function fakeConvertResponse(suffix: "rule" | "llm"): ConvertResponse {
  return {
    flow: {
      flow_name: `flow_${suffix}`,
      total_recipes: 1,
      total_datasets: 2,
      datasets: [],
      recipes: [],
    },
    score: { complexity: 1, recipe_count: 1, dataset_count: 2 },
    warnings: [],
  };
}

const FAKE_DIFF: DiffResponse = {
  added: [
    { id: "extra_recipe", recipe_type_a: null, recipe_type_b: "sort", diff: null },
  ],
  removed: [
    { id: "old_recipe", recipe_type_a: "split", recipe_type_b: null, diff: null },
  ],
  changed: [
    {
      id: "shared_recipe",
      recipe_type_a: "grouping",
      recipe_type_b: "grouping",
      diff: { keys: { a: ["x"], b: ["x", "y"] } },
    },
  ],
};

describe("<DiffPage />", () => {
  beforeEach(() => {
    act(() => {
      useFlowStore.getState().reset();
      useFlowStore.getState().setCurrentCode("import pandas as pd\n");
    });
  });

  it("renders the compare button and an empty diff state", () => {
    render(
      <MemoryRouter>
        <DiffPage />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("compare-button")).toBeInTheDocument();
    expect(screen.getByTestId("diff-empty")).toBeInTheDocument();
  });

  it("Compare triggers two convert calls then a diff call", async () => {
    const convertImpl = vi
      .fn()
      .mockResolvedValueOnce(fakeConvertResponse("rule"))
      .mockResolvedValueOnce(fakeConvertResponse("llm"));
    const diffImpl = vi.fn().mockResolvedValue(FAKE_DIFF);

    render(
      <MemoryRouter>
        <DiffPage convertImpl={convertImpl} diffImpl={diffImpl} />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByTestId("compare-button"));

    await waitFor(() => {
      expect(convertImpl).toHaveBeenCalledTimes(2);
    });
    await waitFor(() => {
      expect(diffImpl).toHaveBeenCalledTimes(1);
    });

    // First call rule, second call llm.
    const calls = (convertImpl as ReturnType<typeof vi.fn>).mock.calls;
    expect(calls[0][0].mode).toBe("rule");
    expect(calls[1][0].mode).toBe("llm");

    // diff() called with both flows.
    const [a, b] = (diffImpl as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(a.flow_name).toBe("flow_rule");
    expect(b.flow_name).toBe("flow_llm");
  });

  it("renders added/removed/changed entries from the diff response", async () => {
    const convertImpl = vi.fn().mockResolvedValue(fakeConvertResponse("rule"));
    const diffImpl = vi.fn().mockResolvedValue(FAKE_DIFF);
    render(
      <MemoryRouter>
        <DiffPage convertImpl={convertImpl} diffImpl={diffImpl} />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByTestId("compare-button"));
    await waitFor(() => {
      expect(screen.getByTestId("diff-list")).toBeInTheDocument();
    });
    expect(screen.getByTestId("diff-entry-extra_recipe")).toHaveAttribute(
      "data-kind",
      "added",
    );
    expect(screen.getByTestId("diff-entry-old_recipe")).toHaveAttribute(
      "data-kind",
      "removed",
    );
    expect(screen.getByTestId("diff-entry-shared_recipe")).toHaveAttribute(
      "data-kind",
      "changed",
    );
  });

  it("clicking an entry sets selectedNodeId in flowStore", async () => {
    const convertImpl = vi.fn().mockResolvedValue(fakeConvertResponse("rule"));
    const diffImpl = vi.fn().mockResolvedValue(FAKE_DIFF);
    render(
      <MemoryRouter>
        <DiffPage convertImpl={convertImpl} diffImpl={diffImpl} />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByTestId("compare-button"));
    await waitFor(() => {
      expect(screen.getByTestId("diff-entry-shared_recipe")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("diff-entry-shared_recipe"));
    expect(useFlowStore.getState().selectedNodeId).toBe("shared_recipe");
  });

  it("shows an error message when convert fails", async () => {
    const convertImpl = vi.fn().mockRejectedValue(new Error("boom"));
    const diffImpl = vi.fn();
    render(
      <MemoryRouter>
        <DiffPage convertImpl={convertImpl} diffImpl={diffImpl} />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByTestId("compare-button"));
    await waitFor(() => {
      expect(screen.getByTestId("diff-error")).toBeInTheDocument();
    });
    expect(diffImpl).not.toHaveBeenCalled();
  });
});
