/**
 * SharePage with embedded fixtures.
 *
 * Asserts:
 *   - The "Includes fixture data: N datasets, M rows" indicator renders when
 *     the API surfaces a `fixtures` payload.
 *   - Clicking "Run with embedded fixtures" pushes the rows into the
 *     fixturesStore Zustand slice.
 *   - The button transitions to a disabled "Loaded" state after a click.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";
import {
  render,
  screen,
  waitFor,
  fireEvent,
  act,
} from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { SharePage } from "../../src/features/share/SharePage";
import { useFixturesStore } from "../../src/store/fixturesStore";
import type { SavedFlowResponse } from "../../src/api/client";

const SAMPLE_WITH_FIXTURES: SavedFlowResponse = {
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
  fixtures: {
    n_rows: 3,
    datasets: {
      trades_raw: [
        { trade_id: "T1" },
        { trade_id: "T2" },
        { trade_id: "T3" },
      ],
      ref_data: [
        { ccy: "USD" },
        { ccy: "EUR" },
      ],
    },
  },
};

function renderAt(
  path: string,
  clientImpl: { getShared: typeof Promise.resolve },
) {
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

describe("<SharePage /> with embedded fixtures", () => {
  beforeEach(() => {
    act(() => useFixturesStore.getState().reset());
  });

  it("shows the 'Includes fixture data' indicator with dataset+row counts", async () => {
    const stub = { getShared: vi.fn(async () => SAMPLE_WITH_FIXTURES) };
    renderAt("/share/abc", stub as never);
    await waitFor(() => {
      expect(screen.getByTestId("share-fixtures-indicator")).toBeInTheDocument();
    });
    expect(screen.getByTestId("share-fixtures-summary")).toHaveTextContent(
      /2 datasets, 5 rows/i,
    );
  });

  it("loads the bundle into fixturesStore when 'Run with embedded fixtures' is clicked", async () => {
    const stub = { getShared: vi.fn(async () => SAMPLE_WITH_FIXTURES) };
    renderAt("/share/abc", stub as never);
    await waitFor(() => {
      expect(screen.getByTestId("share-fixtures-load")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("share-fixtures-load"));

    const loaded = useFixturesStore.getState().fixtures;
    expect(loaded).not.toBeNull();
    expect(loaded?.nRows).toBe(3);
    expect(Object.keys(loaded?.datasets ?? {})).toEqual([
      "trades_raw",
      "ref_data",
    ]);

    // Button now reflects loaded-state.
    await waitFor(() => {
      expect(screen.getByTestId("share-fixtures-load")).toBeDisabled();
    });
  });

  it("does not render the indicator when fixtures are absent", async () => {
    const sample: SavedFlowResponse = {
      ...SAMPLE_WITH_FIXTURES,
      fixtures: null,
    };
    const stub = { getShared: vi.fn(async () => sample) };
    renderAt("/share/abc", stub as never);
    await waitFor(() => {
      expect(screen.getByTestId("share-flow")).toBeInTheDocument();
    });
    expect(
      screen.queryByTestId("share-fixtures-indicator"),
    ).not.toBeInTheDocument();
  });
});
