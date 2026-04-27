import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { LlmHistoryPage } from "../../src/features/llm-history/LlmHistoryPage";
import type {
  LlmHistoryListResponse,
  LlmHistoryRecord,
} from "../../src/api/client";

const PAGE: LlmHistoryListResponse = {
  records: [
    {
      ts: "2026-04-26T10:00:00Z",
      mode: "llm",
      provider: "anthropic",
      model: "claude-3-5-sonnet-latest",
      prompt_tokens: 1000,
      completion_tokens: 500,
      cost_usd: 0.012,
      status: "success",
      flow_id: "flow-abc",
      feature: "chat",
    } as LlmHistoryRecord,
    {
      ts: "2026-04-26T09:55:00Z",
      mode: "rule",
      provider: "rule",
      model: "rule-engine",
      prompt_tokens: 0,
      completion_tokens: 0,
      cost_usd: 0,
      status: "success",
      flow_id: null,
      feature: "convert",
    } as LlmHistoryRecord,
  ],
  next_cursor: null,
};

describe("<LlmHistoryPage />", () => {
  it("renders a row for each record", async () => {
    const stub = { listLlmHistory: vi.fn(async () => PAGE) };
    render(<LlmHistoryPage clientImpl={stub} />);
    await waitFor(() => {
      expect(screen.getByTestId("llm-history-row-0")).toBeInTheDocument();
    });
    expect(screen.getByTestId("llm-history-row-0")).toHaveTextContent("anthropic");
    expect(screen.getByTestId("llm-history-row-1")).toHaveTextContent("rule");
  });

  it("re-fetches when filters apply", async () => {
    const stub = { listLlmHistory: vi.fn(async () => PAGE) };
    render(<LlmHistoryPage clientImpl={stub} />);
    await waitFor(() =>
      expect(screen.getByTestId("llm-history-row-0")).toBeInTheDocument(),
    );
    fireEvent.change(screen.getByTestId("llm-history-provider"), {
      target: { value: "anthropic" },
    });
    fireEvent.click(screen.getByTestId("llm-history-apply"));
    await waitFor(() => {
      expect(stub.listLlmHistory).toHaveBeenCalledWith(
        expect.objectContaining({ provider: "anthropic" }),
      );
    });
  });

  it("shows totals for loaded rows", async () => {
    const stub = { listLlmHistory: vi.fn(async () => PAGE) };
    render(<LlmHistoryPage clientImpl={stub} />);
    await waitFor(() => {
      expect(screen.getByTestId("llm-history-summary")).toHaveTextContent("2 calls");
    });
    expect(screen.getByTestId("llm-history-summary")).toHaveTextContent("$0.0120");
  });
});
