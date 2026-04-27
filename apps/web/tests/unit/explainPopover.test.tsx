import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor, fireEvent, act } from "@testing-library/react";
import { ExplainPopover } from "../../src/features/explain/ExplainPopover";
import {
  useExplainCacheStore,
  clientCacheKey,
} from "../../src/features/explain/useExplainCache";
import { useChatStore } from "../../src/features/chat/chatStore";

const SAMPLE_RECIPE = {
  name: "agg_pnl_by_book",
  type: "GROUPING",
  inputs: ["enriched_trades"],
  outputs: ["pnl_by_book"],
  settings: {
    group_columns: ["book", "trade_date"],
    aggregations: [{ column: "pnl_usd", fn: "SUM" }],
  },
  confidence: "high",
};

const CANNED_RESPONSE = {
  what_this_does: "Aggregates trade rows by book and date.",
  trading_context: "Used in EOD MtM rollups for desk reporting.",
  watch_out_for:
    "If trade_date isn't normalised first rows can land in the wrong day.",
  recipe_type: "GROUPING",
  cache_key: "GROUPING:abc123",
  cache_hit: false,
  model: "mock",
  usage: {},
  cost_usd: 0,
};

beforeEach(() => {
  // Reset persisted client cache before each test.
  useExplainCacheStore.setState({ byKey: {} });
  useChatStore.setState({
    drawerOpen: false,
    drawerWidth: 0.3,
    historyByFlow: {},
    highlightedRecipeId: null,
  });
});

afterEach(() => {
  useExplainCacheStore.setState({ byKey: {} });
});

describe("clientCacheKey", () => {
  it("collapses across renames and confidence wobbles", () => {
    const a = clientCacheKey({ ...SAMPLE_RECIPE });
    const b = clientCacheKey({
      ...SAMPLE_RECIPE,
      name: "renamed",
      confidence: "medium",
      reasoning: "noise",
    });
    expect(a).toBe(b);
  });

  it("changes when settings change", () => {
    const a = clientCacheKey({ ...SAMPLE_RECIPE });
    const b = clientCacheKey({
      ...SAMPLE_RECIPE,
      settings: { ...SAMPLE_RECIPE.settings, group_columns: ["book"] },
    });
    expect(a).not.toBe(b);
  });
});

describe("<ExplainPopover />", () => {
  it("renders all three bullets after a successful fetch", async () => {
    const explainRecipe = vi.fn(async () => CANNED_RESPONSE);
    render(
      <ExplainPopover
        recipe={SAMPLE_RECIPE}
        open
        provider="mock"
        options={{ clientImpl: { explainRecipe }, disableCache: true }}
      />,
    );
    await waitFor(() => {
      expect(screen.getByTestId("explain-what")).toHaveTextContent(
        "Aggregates trade rows by book and date.",
      );
    });
    expect(screen.getByTestId("explain-trading")).toHaveTextContent(
      "EOD MtM rollups",
    );
    expect(screen.getByTestId("explain-watch")).toHaveTextContent(
      "wrong day",
    );
    expect(explainRecipe).toHaveBeenCalledTimes(1);
  });

  it("shows a loading state then transitions to the final content", async () => {
    let resolve!: (v: typeof CANNED_RESPONSE) => void;
    const explainRecipe = vi.fn(
      () =>
        new Promise<typeof CANNED_RESPONSE>((res) => {
          resolve = res;
        }),
    );
    render(
      <ExplainPopover
        recipe={SAMPLE_RECIPE}
        open
        options={{ clientImpl: { explainRecipe }, disableCache: true }}
      />,
    );
    expect(await screen.findByTestId("explain-loading")).toBeInTheDocument();
    act(() => resolve(CANNED_RESPONSE));
    await waitFor(() => {
      expect(screen.queryByTestId("explain-loading")).not.toBeInTheDocument();
      expect(screen.getByTestId("explain-what")).toBeInTheDocument();
    });
  });

  it("renders cached badge when cache_hit=true", async () => {
    const explainRecipe = vi.fn(async () => ({
      ...CANNED_RESPONSE,
      cache_hit: true,
    }));
    render(
      <ExplainPopover
        recipe={SAMPLE_RECIPE}
        open
        options={{ clientImpl: { explainRecipe }, disableCache: true }}
      />,
    );
    await waitFor(() =>
      expect(screen.getByTestId("explain-cache-badge")).toBeInTheDocument(),
    );
  });

  it("renders nothing when open=false", () => {
    const explainRecipe = vi.fn(async () => CANNED_RESPONSE);
    const { queryByTestId } = render(
      <ExplainPopover
        recipe={SAMPLE_RECIPE}
        open={false}
        options={{ clientImpl: { explainRecipe }, disableCache: true }}
      />,
    );
    expect(
      queryByTestId(`explain-popover-${SAMPLE_RECIPE.name}`),
    ).not.toBeInTheDocument();
    expect(explainRecipe).not.toHaveBeenCalled();
  });

  it("More button opens chat drawer + seeds the explanation as the first turn", async () => {
    const explainRecipe = vi.fn(async () => CANNED_RESPONSE);
    render(
      <ExplainPopover
        recipe={SAMPLE_RECIPE}
        open
        flowId="flow-test"
        options={{ clientImpl: { explainRecipe }, disableCache: true }}
      />,
    );
    await waitFor(() =>
      expect(screen.getByTestId("explain-more")).toBeInTheDocument(),
    );

    expect(useChatStore.getState().drawerOpen).toBe(false);
    fireEvent.click(screen.getByTestId("explain-more"));

    expect(useChatStore.getState().drawerOpen).toBe(true);
    const turns = useChatStore.getState().historyByFlow["flow-test"] ?? [];
    expect(turns.length).toBe(1);
    expect(turns[0].role).toBe("assistant");
    expect(turns[0].content).toContain(
      `[recipe:${SAMPLE_RECIPE.name}]`,
    );
    expect(turns[0].content).toContain("EOD MtM rollups");
  });

  it("More uses custom onMore callback when provided", async () => {
    const explainRecipe = vi.fn(async () => CANNED_RESPONSE);
    const onMore = vi.fn();
    render(
      <ExplainPopover
        recipe={SAMPLE_RECIPE}
        open
        onMore={onMore}
        options={{ clientImpl: { explainRecipe }, disableCache: true }}
      />,
    );
    await waitFor(() =>
      expect(screen.getByTestId("explain-more")).toBeInTheDocument(),
    );
    fireEvent.click(screen.getByTestId("explain-more"));
    expect(onMore).toHaveBeenCalledTimes(1);
    expect(onMore.mock.calls[0][0]).toBe(SAMPLE_RECIPE.name);
    expect(onMore.mock.calls[0][1]).toContain("EOD MtM rollups");
  });

  it("surfaces errors in an error region without crashing", async () => {
    const explainRecipe = vi.fn(async () => {
      throw new Error("boom");
    });
    render(
      <ExplainPopover
        recipe={SAMPLE_RECIPE}
        open
        options={{ clientImpl: { explainRecipe }, disableCache: true }}
      />,
    );
    await waitFor(() => {
      expect(screen.getByTestId("explain-error")).toHaveTextContent("boom");
    });
  });

  it("client-side cache short-circuits a second open with the same recipe", async () => {
    const explainRecipe = vi.fn(async () => CANNED_RESPONSE);
    const first = render(
      <ExplainPopover
        recipe={SAMPLE_RECIPE}
        open
        options={{ clientImpl: { explainRecipe }, disableCache: false }}
      />,
    );
    await waitFor(() =>
      expect(screen.getByTestId("explain-what")).toBeInTheDocument(),
    );
    expect(explainRecipe).toHaveBeenCalledTimes(1);
    first.unmount();

    // Fresh mount with the same recipe shape — the persisted client cache
    // serves the response without a network call.
    render(
      <ExplainPopover
        recipe={SAMPLE_RECIPE}
        open
        options={{ clientImpl: { explainRecipe }, disableCache: false }}
      />,
    );
    await waitFor(() =>
      expect(screen.getByTestId("explain-what")).toBeInTheDocument(),
    );
    expect(explainRecipe).toHaveBeenCalledTimes(1); // still 1 — cache hit
  });
});
