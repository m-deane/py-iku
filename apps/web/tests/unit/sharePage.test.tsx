import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { SharePage } from "../../src/features/share/SharePage";
import type { SavedFlowResponse } from "../../src/api/client";

const SAMPLE: SavedFlowResponse = {
  id: "f1",
  name: "demo-flow",
  flow: {
    flow_name: "demo-flow",
    total_recipes: 0,
    total_datasets: 0,
    datasets: [],
    recipes: [],
  },
  created_at: "2026-04-26T10:00:00Z",
  updated_at: "2026-04-26T10:00:00Z",
  tags: [],
};

function renderAt(path: string, clientImpl: { getShared: typeof Promise.resolve }) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route
          path="/share/:token"
          element={<SharePage clientImpl={clientImpl as never} />}
        />
      </Routes>
    </MemoryRouter>,
  );
}

describe("<SharePage />", () => {
  it("renders the shared flow when the token resolves", async () => {
    const stub = { getShared: vi.fn(async () => SAMPLE) };
    renderAt("/share/abc", stub as never);
    await waitFor(() => {
      expect(screen.getByTestId("share-flow")).toBeInTheDocument();
    });
    expect(screen.getAllByText(/demo-flow/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByTestId("share-edit-disabled")).toBeDisabled();
    expect(stub.getShared).toHaveBeenCalledWith("abc");
  });

  it("renders an error block on 410 expired", async () => {
    const stub = {
      getShared: vi.fn(async () => {
        const err: Error & { status?: number } = new Error("expired");
        err.status = 410;
        throw err;
      }),
    };
    renderAt("/share/expired", stub as never);
    await waitFor(() => {
      expect(screen.getByTestId("share-error")).toBeInTheDocument();
    });
    expect(screen.getByTestId("share-error")).toHaveTextContent(/410|expired/i);
  });

  it("renders an error block on 401 invalid signature", async () => {
    const stub = {
      getShared: vi.fn(async () => {
        const err: Error & { status?: number } = new Error("bad sig");
        err.status = 401;
        throw err;
      }),
    };
    renderAt("/share/bad", stub as never);
    await waitFor(() => {
      expect(screen.getByTestId("share-error")).toBeInTheDocument();
    });
    expect(screen.getByTestId("share-error")).toHaveTextContent(/401|invalid/i);
  });
});
