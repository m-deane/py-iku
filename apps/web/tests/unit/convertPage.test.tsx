import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, act, waitFor } from "@testing-library/react";
import { ConvertPage } from "../../src/features/conversion/ConvertPage";
import { useFlowStore } from "../../src/state/flowStore";
import { useSettingsStore } from "../../src/state/settingsStore";
import { ApiError, type ConvertResponse } from "../../src/api/client";
import { getDefaultCode } from "../../src/features/editor/snippets";

function fakeResponse(): ConvertResponse {
  return {
    flow: {
      name: "demo_flow",
      recipes: [
        { id: "groupby_1", type: "GROUPING", inputs: ["raw"], outputs: ["agg"] },
      ],
      datasets: [
        { id: "raw", type: "csv" },
        { id: "agg", type: "csv" },
      ],
    },
    score: {
      complexity: 7,
      recipe_count: 1,
      dataset_count: 2,
    },
    warnings: [],
  };
}

describe("<ConvertPage />", () => {
  beforeEach(() => {
    act(() => {
      useFlowStore.getState().reset();
      useFlowStore.getState().setCurrentCode(getDefaultCode());
      useFlowStore.getState().setConversionMode("rule");
      useSettingsStore.getState().reset();
    });
  });

  it("renders the editor + Convert button", () => {
    render(<ConvertPage useFallbackEditor />);
    expect(screen.getByLabelText(/python code/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^convert$/i })).toBeInTheDocument();
    // Mode toggle defaults to rule (uppercase rendering).
    expect(screen.getByRole("radio", { name: /rule/i })).toHaveAttribute("aria-checked", "true");
  });

  it("calls convert and shows the complexity stat on success", async () => {
    const convertImpl = vi.fn().mockResolvedValue(fakeResponse());
    render(<ConvertPage useFallbackEditor convertImpl={convertImpl} />);

    fireEvent.click(screen.getByRole("button", { name: /^convert$/i }));

    await waitFor(() => {
      expect(convertImpl).toHaveBeenCalledOnce();
    });
    await waitFor(() => {
      expect(screen.getByTestId("status-success")).toBeInTheDocument();
    });
    const successPanel = screen.getByTestId("status-success");
    expect(successPanel).toHaveTextContent(/complexity/i);
    expect(successPanel).toHaveTextContent("7");
    expect(successPanel).toHaveTextContent(/recipes/i);
    expect(successPanel).toHaveTextContent(/datasets/i);
  });

  it("disables the Convert button in LLM mode without a key alias", () => {
    act(() => {
      useFlowStore.getState().setConversionMode("llm");
      useSettingsStore.getState().setApiKeyAlias("");
    });
    render(<ConvertPage useFallbackEditor />);
    const btn = screen.getByRole("button", { name: /^convert$/i });
    expect(btn).toBeDisabled();
    expect(btn).toHaveAttribute("title", expect.stringMatching(/llm credentials/i));
  });

  it("enables the Convert button in LLM mode once a key alias is set", () => {
    act(() => {
      useFlowStore.getState().setConversionMode("llm");
      useSettingsStore.getState().setApiKeyAlias("anthropic-prod");
    });
    render(<ConvertPage useFallbackEditor />);
    const btn = screen.getByRole("button", { name: /^convert$/i });
    expect(btn).not.toBeDisabled();
  });

  it("renders an error status panel on a 400 ApiError", async () => {
    const convertImpl = vi.fn().mockRejectedValue(
      new ApiError({
        type: "https://py-iku.dev/problems/invalid-python",
        title: "Invalid Python",
        status: 400,
        detail: "SyntaxError on line 3",
      }),
    );
    render(<ConvertPage useFallbackEditor convertImpl={convertImpl} />);

    fireEvent.click(screen.getByRole("button", { name: /^convert$/i }));

    await waitFor(() => {
      expect(screen.getByTestId("status-error")).toBeInTheDocument();
    });
    expect(screen.getByTestId("status-error")).toHaveTextContent(/HTTP 400/);
    expect(screen.getByTestId("status-error")).toHaveTextContent(/invalid request/i);
    expect(screen.getByTestId("status-error")).toHaveTextContent(/SyntaxError on line 3/);
  });

  it("toggles between rule and llm modes via the radio group", () => {
    render(<ConvertPage useFallbackEditor />);
    const llmRadio = screen.getByRole("radio", { name: /llm/i });
    fireEvent.click(llmRadio);
    expect(useFlowStore.getState().conversionMode).toBe("llm");
  });
});
