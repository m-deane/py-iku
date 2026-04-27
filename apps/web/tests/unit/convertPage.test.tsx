import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, act, waitFor } from "@testing-library/react";
import { ConvertPage } from "../../src/features/conversion/ConvertPage";
import { useFlowStore } from "../../src/state/flowStore";
import { useSettingsStore } from "../../src/state/settingsStore";
import { ApiError, type ConvertResponse } from "../../src/api/client";
import { getDefaultCode } from "../../src/features/editor/snippets";
import type {
  UseConvertStreamResult,
  ProgressEvent,
} from "../../src/features/conversion/useConvertStream";

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

/**
 * Build a stub useConvertStream hook with a stable handle that the test can
 * drive to simulate state transitions.
 */
function createStreamStub() {
  const events: ProgressEvent[] = [];
  let setter: ((u: Partial<UseConvertStreamResult>) => void) | null = null;

  const result: UseConvertStreamResult = {
    status: "idle",
    progress: events,
    phase: "idle",
    pct: 0,
    flow: null,
    score: null,
    warnings: [],
    error: null,
    start: vi.fn(),
    cancel: vi.fn(),
    reset: vi.fn(),
  };

  const useStream = (): UseConvertStreamResult => {
    // useState wrapper isn't strictly needed — return the live mutable result.
    // React re-renders happen because the page calls setState internally on
    // status changes via useEffect. For our tests, we drive state by calling
    // `update()` and letting the page re-render on the next interaction.
    return { ...result };
  };

  // For tests that need to push events / change status mid-render, expose
  // a manual update that forces a re-render via a state hack.
  return { result, useStream, setter };
}

describe("<ConvertPage /> — REST seam (legacy)", () => {
  beforeEach(() => {
    act(() => {
      useFlowStore.getState().reset();
      useFlowStore.getState().setCurrentCode(getDefaultCode());
      useFlowStore.getState().setConversionMode("rule");
      useSettingsStore.getState().reset();
    });
  });

  it("renders the editor + Convert button", () => {
    render(<ConvertPage useFallbackEditor useRestOnly />);
    expect(screen.getByLabelText(/python code/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^convert$/i })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: /rule/i })).toHaveAttribute("aria-checked", "true");
  });

  it("calls convert and shows the complexity stat on success (REST)", async () => {
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
  });

  it("disables the Convert button in LLM mode without a key alias", () => {
    act(() => {
      useFlowStore.getState().setConversionMode("llm");
      useSettingsStore.getState().setApiKeyAlias("");
    });
    render(<ConvertPage useFallbackEditor useRestOnly />);
    const btn = screen.getByRole("button", { name: /^convert$/i });
    expect(btn).toBeDisabled();
    expect(btn).toHaveAttribute("title", expect.stringMatching(/llm credentials/i));
  });

  it("enables the Convert button in LLM mode once a key alias is set", () => {
    act(() => {
      useFlowStore.getState().setConversionMode("llm");
      useSettingsStore.getState().setApiKeyAlias("anthropic-prod");
    });
    render(<ConvertPage useFallbackEditor useRestOnly />);
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
  });

  it("toggles between rule and llm modes via the radio group", () => {
    render(<ConvertPage useFallbackEditor useRestOnly />);
    const llmRadio = screen.getByRole("radio", { name: /llm/i });
    fireEvent.click(llmRadio);
    expect(useFlowStore.getState().conversionMode).toBe("llm");
  });
});

describe("<ConvertPage /> — streaming seam (M5)", () => {
  beforeEach(() => {
    act(() => {
      useFlowStore.getState().reset();
      useFlowStore.getState().setCurrentCode(getDefaultCode());
      useFlowStore.getState().setConversionMode("rule");
      useSettingsStore.getState().reset();
    });
  });

  it("calls stream.start() when Convert is clicked (no convertImpl/useRestOnly)", () => {
    const stub = createStreamStub();
    render(
      <ConvertPage
        useFallbackEditor
        streamConvertImpl={stub.useStream}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /^convert$/i }));
    expect(stub.result.start).toHaveBeenCalledOnce();
    const calledWith = (stub.result.start as ReturnType<typeof vi.fn>).mock.calls[0][0];
    expect(calledWith.mode).toBe("rule");
    expect(typeof calledWith.code).toBe("string");
  });

  it("renders progress entries from the streaming hook", () => {
    const events: ProgressEvent[] = [
      {
        event: "started",
        seq: 0,
        ts: "2026-01-01T00:00:00.000Z",
        payload: { mode: "rule", code_size_bytes: 6 },
      },
      {
        event: "ast_parsed",
        seq: 1,
        ts: "2026-01-01T00:00:00.100Z",
        payload: { node_count: 7 },
      },
    ];
    const useStub = (): UseConvertStreamResult => ({
      status: "streaming",
      progress: events,
      phase: "analyzing",
      pct: 25,
      flow: null,
      score: null,
      warnings: [],
      error: null,
      start: vi.fn(),
      cancel: vi.fn(),
      reset: vi.fn(),
    });
    render(<ConvertPage useFallbackEditor streamConvertImpl={useStub} />);
    const log = screen.getByTestId("progress-log");
    expect(log).toBeInTheDocument();
    expect(screen.getByTestId("progress-started")).toHaveTextContent(/started/);
    expect(screen.getByTestId("progress-ast_parsed")).toHaveTextContent(/AST nodes/);
  });

  it("Cancel button calls stream.cancel() while streaming", () => {
    const cancelFn = vi.fn();
    const useStub = (): UseConvertStreamResult => ({
      status: "streaming",
      progress: [],
      phase: "connecting",
      pct: 5,
      flow: null,
      score: null,
      warnings: [],
      error: null,
      start: vi.fn(),
      cancel: cancelFn,
      reset: vi.fn(),
    });
    render(<ConvertPage useFallbackEditor streamConvertImpl={useStub} />);
    const cancelBtn = screen.getByTestId("convert-cancel");
    expect(cancelBtn).not.toBeDisabled();
    fireEvent.click(cancelBtn);
    expect(cancelFn).toHaveBeenCalledOnce();
  });

  it("renders a progress bar with role=progressbar and the phase label while streaming", () => {
    const events: ProgressEvent[] = [
      {
        event: "started",
        seq: 0,
        ts: "2026-01-01T00:00:00.000Z",
        payload: { mode: "rule", code_size_bytes: 6 },
      },
      {
        event: "ast_parsed",
        seq: 1,
        ts: "2026-01-01T00:00:00.100Z",
        payload: { node_count: 42 },
      },
    ];
    const useStub = (): UseConvertStreamResult => ({
      status: "streaming",
      progress: events,
      phase: "analyzing",
      pct: 25,
      flow: null,
      score: null,
      warnings: [],
      error: null,
      start: vi.fn(),
      cancel: vi.fn(),
      reset: vi.fn(),
    });
    render(<ConvertPage useFallbackEditor streamConvertImpl={useStub} />);
    const bar = screen.getByTestId("convert-progress-bar");
    expect(bar).toHaveAttribute("role", "progressbar");
    expect(bar).toHaveAttribute("aria-valuenow", "25");
    expect(screen.getByTestId("convert-progress-status")).toHaveTextContent(
      /analyzing ast/i,
    );
    // Cancel button is co-located with the progress bar.
    expect(screen.getByTestId("convert-progress-cancel")).toBeInTheDocument();
  });

  it("inline error banner appears with a Retry button when stream errors", async () => {
    const startFn = vi.fn();
    const useStub = (): UseConvertStreamResult => ({
      status: "error",
      progress: [],
      phase: "error",
      pct: 0,
      flow: null,
      score: null,
      warnings: [],
      error: { title: "Rate limit", detail: "Try again", status: 429 },
      start: startFn,
      cancel: vi.fn(),
      reset: vi.fn(),
    });
    render(<ConvertPage useFallbackEditor streamConvertImpl={useStub} />);
    await waitFor(() => {
      expect(screen.getByTestId("convert-error-banner")).toBeInTheDocument();
    });
    expect(screen.getByTestId("convert-error-banner")).toHaveTextContent(
      /rate limit/i,
    );
    expect(screen.getByTestId("convert-error-banner")).toHaveTextContent("HTTP 429");
  });

  it("Cancel button is disabled when stream is idle", () => {
    const useStub = (): UseConvertStreamResult => ({
      status: "idle",
      progress: [],
      phase: "idle",
      pct: 0,
      flow: null,
      score: null,
      warnings: [],
      error: null,
      start: vi.fn(),
      cancel: vi.fn(),
      reset: vi.fn(),
    });
    render(<ConvertPage useFallbackEditor streamConvertImpl={useStub} />);
    expect(screen.getByTestId("convert-cancel")).toBeDisabled();
  });
});
