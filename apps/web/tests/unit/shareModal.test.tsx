import { describe, it, expect, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { ShareModal } from "../../src/features/share/ShareModal";
import type {
  CollabClient,
  Client,
  FixturePreviewResponse,
} from "../../src/api/client";

function makeClient(): Client {
  return {
    saveFlow: vi.fn(async () => ({ id: "saved-1", created_at: "2026-04-26" })),
    shareFlow: vi.fn(async () => ({
      token: "tok",
      url: "http://x/share/tok",
      expires_at: "2026-04-27",
    })),
  } as unknown as Client;
}

function makeCollab(): CollabClient {
  const preview: FixturePreviewResponse = {
    n_rows: 5,
    datasets: [
      {
        name: "trades_raw",
        columns: ["trade_id", "commodity", "notional"],
        sample_rows: [
          { trade_id: "abc", commodity: "Brent", notional: 1234 },
        ],
      },
    ],
  };
  return {
    listComments: vi.fn(),
    postComment: vi.fn(),
    deleteComment: vi.fn(),
    previewFixtures: vi.fn(async () => preview),
    bundleFixtures: vi.fn(async () => ({
      n_rows: 100,
      datasets: { trades_raw: [] },
    })),
    githubPublish: vi.fn(),
  } as unknown as CollabClient;
}

const FLOW = {
  flow_name: "demo-flow",
  total_recipes: 0,
  total_datasets: 0,
  datasets: [],
  recipes: [],
};

describe("<ShareModal />", () => {
  it("renders nothing when flow is null", () => {
    const { container } = render(
      <ShareModal
        flow={null}
        savedFlowId={null}
        onClose={() => {}}
        onShared={() => {}}
        clientImpl={makeClient()}
        collabImpl={makeCollab()}
      />,
    );
    expect(container.querySelector('[data-testid="share-modal"]')).toBeNull();
  });

  it("renders the disabled-preview state by default", () => {
    render(
      <ShareModal
        flow={FLOW}
        savedFlowId={null}
        onClose={() => {}}
        onShared={() => {}}
        clientImpl={makeClient()}
        collabImpl={makeCollab()}
      />,
    );
    expect(screen.getByTestId("fixture-preview-disabled")).toBeInTheDocument();
    expect(
      (screen.getByTestId("include-fixtures-checkbox") as HTMLInputElement).checked,
    ).toBe(false);
  });

  it("loads + renders the preview when fixtures checkbox is ticked", async () => {
    const collab = makeCollab();
    render(
      <ShareModal
        flow={FLOW}
        savedFlowId={null}
        onClose={() => {}}
        onShared={() => {}}
        clientImpl={makeClient()}
        collabImpl={collab}
      />,
    );
    fireEvent.click(screen.getByTestId("include-fixtures-checkbox"));
    await waitFor(() => {
      expect(collab.previewFixtures).toHaveBeenCalled();
    });
    await waitFor(() => {
      expect(screen.getByTestId("fixture-dataset-trades_raw")).toBeInTheDocument();
    });
    expect(screen.getByText("Brent")).toBeInTheDocument();
  });

  it("invokes saveFlow + shareFlow when Create link is clicked", async () => {
    const cli = makeClient();
    const onShared = vi.fn();
    render(
      <ShareModal
        flow={FLOW}
        savedFlowId={null}
        onClose={() => {}}
        onShared={onShared}
        clientImpl={cli}
        collabImpl={makeCollab()}
      />,
    );
    fireEvent.click(screen.getByTestId("share-modal-submit"));
    await waitFor(() => {
      expect(cli.saveFlow).toHaveBeenCalled();
      expect(cli.shareFlow).toHaveBeenCalledWith("saved-1", expect.any(Object));
      expect(onShared).toHaveBeenCalledWith(
        expect.objectContaining({ token: "tok" }),
      );
    });
  });
});
