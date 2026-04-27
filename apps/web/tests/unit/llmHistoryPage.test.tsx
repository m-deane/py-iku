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

type StubOverrides = {
  listLlmHistory?: (opts?: unknown) => Promise<unknown>;
  exportUserData?: (user: string) => Promise<unknown>;
  deleteUserData?: (user: string) => Promise<unknown>;
};

// We intentionally use `any` here because vitest's vi.fn typings clash with
// the strict client-impl signature; the tests assert behavior, not types.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function makeStub(overrides: StubOverrides = {}): any {
  return {
    listLlmHistory: vi.fn(overrides.listLlmHistory ?? (async () => PAGE)),
    exportUserData: vi.fn(
      overrides.exportUserData ??
        (async (user: string) => ({
          blob: new Blob(["{}"]),
          filename: `py-iku-studio-export-${user}-stub.zip`,
          contentType: "application/zip",
        })),
    ),
    deleteUserData: vi.fn(
      overrides.deleteUserData ?? (async (user: string) => ({ user, removed: 1 })),
    ),
  };
}

describe("<LlmHistoryPage />", () => {
  it("renders a row for each record", async () => {
    const stub = makeStub();
    render(<LlmHistoryPage clientImpl={stub} />);
    await waitFor(() => {
      expect(screen.getByTestId("llm-history-row-0")).toBeInTheDocument();
    });
    expect(screen.getByTestId("llm-history-row-0")).toHaveTextContent("anthropic");
    expect(screen.getByTestId("llm-history-row-1")).toHaveTextContent("rule");
  });

  it("re-fetches when filters apply", async () => {
    const stub = makeStub();
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
    const stub = makeStub();
    render(<LlmHistoryPage clientImpl={stub} />);
    await waitFor(() => {
      expect(screen.getByTestId("llm-history-summary")).toHaveTextContent("2 calls");
    });
    expect(screen.getByTestId("llm-history-summary")).toHaveTextContent("$0.0120");
  });

  it("Sprint 4D — passes the search query through to the backend", async () => {
    const stub = makeStub();
    render(<LlmHistoryPage clientImpl={stub} />);
    await waitFor(() =>
      expect(screen.getByTestId("llm-history-row-0")).toBeInTheDocument(),
    );
    fireEvent.change(screen.getByTestId("llm-history-search"), {
      target: { value: "rename column" },
    });
    fireEvent.click(screen.getByTestId("llm-history-search-go"));
    await waitFor(() =>
      expect(stub.listLlmHistory).toHaveBeenCalledWith(
        expect.objectContaining({ q: "rename column" }),
      ),
    );
  });

  it("Sprint 5 — surfaces severity chips and user column", async () => {
    const stub = makeStub({
      listLlmHistory: vi.fn(async () => ({
        ...PAGE,
        records: [
          { ...PAGE.records[0], cost_usd: 1.50, severity: "warning", user: "alice" },
        ],
        users: ["alice", "you"],
      })),
    });
    render(<LlmHistoryPage clientImpl={stub} />);
    await waitFor(() =>
      expect(screen.getByTestId("severity-chip-warning")).toBeInTheDocument(),
    );
    expect(screen.getByTestId("llm-history-row-0")).toHaveTextContent("alice");
  });

  it("Sprint 5 — GDPR export triggers saveBlob with the right filename", async () => {
    const saved: Array<{ filename: string }> = [];
    const stub = makeStub();
    render(
      <LlmHistoryPage
        clientImpl={stub}
        saveBlob={(_blob, filename) => saved.push({ filename })}
      />,
    );
    await waitFor(() =>
      expect(screen.getByTestId("llm-history-row-0")).toBeInTheDocument(),
    );
    fireEvent.click(screen.getByTestId("llm-history-gdpr-export"));
    await waitFor(() => {
      expect(stub.exportUserData).toHaveBeenCalledWith("you");
    });
    expect(saved).toHaveLength(1);
    expect(saved[0].filename).toMatch(/py-iku-studio-export-you-/);
  });

  it("Sprint 5 — Delete my data requires confirmation modal click", async () => {
    const stub = makeStub();
    render(<LlmHistoryPage clientImpl={stub} />);
    await waitFor(() =>
      expect(screen.getByTestId("llm-history-row-0")).toBeInTheDocument(),
    );
    fireEvent.click(screen.getByTestId("llm-history-gdpr-delete"));
    expect(screen.getByTestId("llm-history-delete-dialog")).toBeInTheDocument();
    expect(stub.deleteUserData).not.toHaveBeenCalled();
    fireEvent.click(screen.getByTestId("llm-history-delete-confirm"));
    await waitFor(() => {
      expect(stub.deleteUserData).toHaveBeenCalledWith("you");
    });
  });

  it("Sprint 5 — Delete cancel hides the confirmation modal without deleting", async () => {
    const stub = makeStub();
    render(<LlmHistoryPage clientImpl={stub} />);
    await waitFor(() =>
      expect(screen.getByTestId("llm-history-row-0")).toBeInTheDocument(),
    );
    fireEvent.click(screen.getByTestId("llm-history-gdpr-delete"));
    fireEvent.click(screen.getByTestId("llm-history-delete-cancel"));
    expect(stub.deleteUserData).not.toHaveBeenCalled();
  });
});
