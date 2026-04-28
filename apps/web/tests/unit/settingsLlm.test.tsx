import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { Toaster } from "sonner";
import { LlmProviderSection } from "../../src/features/settings/LlmProviderSection";
import { useSettingsStore } from "../../src/state/settingsStore";

// Module-level mock — we replace the http client used by the component so
// we can assert exactly which endpoints get hit, without spinning up the
// FastAPI process. We re-export `ApiError` because the LlmProviderSection
// catches by `instanceof ApiError`.
vi.mock("../../src/api/client", () => {
  class ApiError extends Error {
    type: string;
    title: string;
    status: number;
    detail?: string;
    requestId?: string;
    data: Record<string, unknown> = {};
    constructor(problem: { type: string; title: string; status: number; detail?: string }) {
      super(problem.title);
      this.name = "ApiError";
      this.type = problem.type;
      this.title = problem.title;
      this.status = problem.status;
      this.detail = problem.detail;
    }
  }
  return {
    ApiError,
    client: {
      getLlmStatus: vi.fn(),
      saveLlmKey: vi.fn(),
      deleteLlmKey: vi.fn(),
      convert: vi.fn(),
    },
  };
});

import { client, ApiError } from "../../src/api/client";

const mockClient = client as unknown as {
  getLlmStatus: ReturnType<typeof vi.fn>;
  saveLlmKey: ReturnType<typeof vi.fn>;
  deleteLlmKey: ReturnType<typeof vi.fn>;
  convert: ReturnType<typeof vi.fn>;
};

describe("<LlmProviderSection />", () => {
  beforeEach(() => {
    useSettingsStore.getState().reset();
    mockClient.getLlmStatus.mockReset();
    mockClient.saveLlmKey.mockReset();
    mockClient.deleteLlmKey.mockReset();
    mockClient.convert.mockReset();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("renders the provider select, model field, and key input", async () => {
    mockClient.getLlmStatus.mockResolvedValue({
      provider: "anthropic",
      has_key: false,
      source: "none",
    });
    render(<LlmProviderSection />);
    await waitFor(() => {
      expect(screen.getByTestId("settings-llm-status")).toHaveTextContent(/not configured/i);
    });
    expect(screen.getByTestId("settings-llm-provider-select")).toBeInTheDocument();
    expect(screen.getByTestId("settings-llm-key-input")).toBeInTheDocument();
    expect(screen.getByTestId("settings-llm-test")).toBeDisabled();
  });

  it("shows a green status pill when the server reports has_key=true", async () => {
    mockClient.getLlmStatus.mockResolvedValue({
      provider: "anthropic",
      has_key: true,
      source: "file",
    });
    render(<LlmProviderSection />);
    await waitFor(() => {
      expect(screen.getByTestId("settings-llm-status")).toHaveTextContent(/configured/i);
    });
  });

  it("POSTs the key when Save is clicked and updates status", async () => {
    mockClient.getLlmStatus.mockResolvedValue({
      provider: "anthropic",
      has_key: false,
      source: "none",
    });
    mockClient.saveLlmKey.mockResolvedValue({
      provider: "anthropic",
      has_key: true,
      source: "file",
    });

    render(
      <>
        <Toaster />
        <LlmProviderSection />
      </>,
    );
    await waitFor(() =>
      expect(screen.getByTestId("settings-llm-status")).toHaveTextContent(/not configured/i),
    );

    const input = screen.getByTestId("settings-llm-key-input") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "sk-ant-real-key" } });

    const saveBtn = screen.getByTestId("settings-llm-key-save");
    expect(saveBtn).not.toBeDisabled();
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(mockClient.saveLlmKey).toHaveBeenCalledWith({
        provider: "anthropic",
        key: "sk-ant-real-key",
      });
    });
    await waitFor(() => {
      expect(screen.getByTestId("settings-llm-status")).toHaveTextContent(/configured/i);
    });
    // The input is cleared after a successful save (the key is gone from the
    // DOM, so it cannot leak via inspecting the rendered HTML).
    expect((screen.getByTestId("settings-llm-key-input") as HTMLInputElement).value).toBe("");
  });

  it("toggles password visibility when Show/Hide clicked", async () => {
    mockClient.getLlmStatus.mockResolvedValue({
      provider: "anthropic",
      has_key: false,
      source: "none",
    });
    render(<LlmProviderSection />);
    await waitFor(() =>
      expect(screen.getByTestId("settings-llm-key-input")).toBeInTheDocument(),
    );
    const input = screen.getByTestId("settings-llm-key-input") as HTMLInputElement;
    expect(input.type).toBe("password");
    fireEvent.click(screen.getByTestId("settings-llm-key-reveal"));
    expect(input.type).toBe("text");
  });

  it("Test connection POSTs a probe to /convert?mode=llm and reports OK", async () => {
    mockClient.getLlmStatus.mockResolvedValue({
      provider: "anthropic",
      has_key: true,
      source: "file",
    });
    mockClient.convert.mockResolvedValue({
      flow: { recipes: [{ name: "r1", type: "grouping" }] },
      score: { complexity: 1.2, recipe_count: 1, dataset_count: 2 },
      warnings: [],
    });

    render(<LlmProviderSection />);
    await waitFor(() => expect(screen.getByTestId("settings-llm-test")).not.toBeDisabled());

    fireEvent.click(screen.getByTestId("settings-llm-test"));

    await waitFor(() => {
      expect(mockClient.convert).toHaveBeenCalled();
    });
    const callArg = mockClient.convert.mock.calls[0][0];
    expect(callArg.mode).toBe("llm");
    await waitFor(() =>
      expect(screen.getByTestId("settings-llm-test-result")).toHaveTextContent(/OK/),
    );
  });

  it("Test connection surfaces a server error inline", async () => {
    mockClient.getLlmStatus.mockResolvedValue({
      provider: "anthropic",
      has_key: true,
      source: "env",
    });
    mockClient.convert.mockRejectedValue(
      new ApiError({
        type: "about:blank",
        title: "Authentication failed",
        status: 401,
        detail: "Invalid key",
      }),
    );
    render(<LlmProviderSection />);
    await waitFor(() => expect(screen.getByTestId("settings-llm-test")).not.toBeDisabled());

    fireEvent.click(screen.getByTestId("settings-llm-test"));

    await waitFor(() =>
      expect(screen.getByTestId("settings-llm-test-result")).toHaveTextContent(
        /Failed/i,
      ),
    );
  });

  it("never renders the saved key value back to the DOM", async () => {
    const sentinel = "sk-ant-DO-NOT-LEAK-9999";
    mockClient.getLlmStatus.mockResolvedValue({
      provider: "anthropic",
      has_key: true,
      source: "file",
    });
    mockClient.saveLlmKey.mockResolvedValue({
      provider: "anthropic",
      has_key: true,
      source: "file",
    });

    const { container } = render(<LlmProviderSection />);
    await waitFor(() => expect(screen.getByTestId("settings-llm-key-input")).toBeInTheDocument());
    const input = screen.getByTestId("settings-llm-key-input") as HTMLInputElement;
    fireEvent.change(input, { target: { value: sentinel } });
    fireEvent.click(screen.getByTestId("settings-llm-key-save"));
    await waitFor(() => expect(mockClient.saveLlmKey).toHaveBeenCalled());
    // After save the input is cleared and the key value should NOT appear in
    // the rendered HTML.
    await waitFor(() => {
      expect(container.innerHTML).not.toContain(sentinel);
    });
  });
});
