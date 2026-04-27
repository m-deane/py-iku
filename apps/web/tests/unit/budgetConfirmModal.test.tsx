/**
 * Budget-confirmation modal contract.
 *
 * Covers two layers:
 *
 * 1. The modal itself — message copy, confirm/cancel callbacks, ESC dismiss.
 * 2. The ConvertPage retry-on-confirm path — when the API returns 402, the
 *    page surfaces the modal; on confirm the convert call is re-fired with
 *    `force=true`.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, act, waitFor } from "@testing-library/react";
import { BudgetConfirmModal } from "../../src/features/conversion/BudgetConfirmModal";
import { ConvertPage } from "../../src/features/conversion/ConvertPage";
import { useFlowStore } from "../../src/state/flowStore";
import { useSettingsStore } from "../../src/state/settingsStore";
import { ApiError, type ConvertResponse } from "../../src/api/client";
import { getDefaultCode } from "../../src/features/editor/snippets";

describe("<BudgetConfirmModal />", () => {
  it("renders the projected cost and remaining-budget figures", () => {
    render(
      <BudgetConfirmModal
        projectedCostUsd={1.234}
        todayRemainingUsd={0.5}
        onConfirm={() => {}}
        onCancel={() => {}}
      />,
    );
    expect(screen.getByTestId("budget-confirm-cost")).toHaveTextContent("$1.23");
    expect(screen.getByTestId("budget-confirm-remaining")).toHaveTextContent(
      "$0.50",
    );
    expect(screen.getByTestId("budget-confirm-message")).toHaveTextContent(
      /proceed anyway\?/i,
    );
  });

  it("invokes onConfirm when the Proceed button is clicked", () => {
    const onConfirm = vi.fn();
    render(
      <BudgetConfirmModal
        projectedCostUsd={1}
        todayRemainingUsd={0}
        onConfirm={onConfirm}
        onCancel={() => {}}
      />,
    );
    fireEvent.click(screen.getByTestId("budget-confirm-confirm"));
    expect(onConfirm).toHaveBeenCalledOnce();
  });

  it("invokes onCancel when the Cancel button is clicked", () => {
    const onCancel = vi.fn();
    render(
      <BudgetConfirmModal
        projectedCostUsd={1}
        todayRemainingUsd={0}
        onConfirm={() => {}}
        onCancel={onCancel}
      />,
    );
    fireEvent.click(screen.getByTestId("budget-confirm-cancel"));
    expect(onCancel).toHaveBeenCalledOnce();
  });

  it("Esc dismisses the modal", () => {
    const onCancel = vi.fn();
    render(
      <BudgetConfirmModal
        projectedCostUsd={1}
        todayRemainingUsd={0}
        onConfirm={() => {}}
        onCancel={onCancel}
      />,
    );
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onCancel).toHaveBeenCalledOnce();
  });
});

describe("<ConvertPage /> — 402 budget retry seam", () => {
  beforeEach(() => {
    act(() => {
      useFlowStore.getState().reset();
      useFlowStore.getState().setCurrentCode(getDefaultCode());
      useFlowStore.getState().setConversionMode("rule");
      useSettingsStore.getState().reset();
    });
  });

  function fakeOk(): ConvertResponse {
    return {
      flow: { name: "f", recipes: [], datasets: [] },
      score: { complexity: 1, recipe_count: 0, dataset_count: 0 },
      warnings: [],
    };
  }

  it("surfaces the budget modal on 402 and re-fires convert with force=true on confirm", async () => {
    const budget402 = new ApiError({
      type: "https://py-iku.dev/errors/BudgetExceeded",
      title: "Budget exceeded",
      status: 402,
      detail: {
        title: "Budget exceeded",
        reason: "projected month-to-date $51.00 exceeds monthly cap $50.00",
        projected_cost_usd: 0.42,
        budget: {
          today_usd: 0.0,
          month_usd: 49.0,
          budget: { monthly_cap_usd: 50.0, per_call_cap_usd: 1.0, alert_threshold_pct: 80.0 },
          over_threshold: true,
          over_budget: false,
          pct_of_monthly_cap: 98.0,
        },
        // Mirrors the actual 422-style flat-detail from FastAPI HTTPException
      } as unknown as string,
    });
    const convertImpl = vi
      .fn()
      .mockRejectedValueOnce(budget402)
      .mockResolvedValueOnce(fakeOk());

    render(<ConvertPage useFallbackEditor convertImpl={convertImpl} />);
    fireEvent.click(screen.getByRole("button", { name: /^convert$/i }));

    // 1) Modal appears with the projected cost.
    await waitFor(() => {
      expect(screen.getByTestId("budget-confirm-modal")).toBeInTheDocument();
    });
    expect(screen.getByTestId("budget-confirm-cost")).toHaveTextContent("$0.42");

    // 2) Confirm → second convert call fires with `force` opts.
    fireEvent.click(screen.getByTestId("budget-confirm-confirm"));
    await waitFor(() => {
      expect(convertImpl).toHaveBeenCalledTimes(2);
    });
    const secondCall = convertImpl.mock.calls[1];
    // Second arg is the ClientOptions { force: true }.
    expect(secondCall[1]).toEqual({ force: true });
  });

  it("dismissing the budget modal does NOT re-fire convert", async () => {
    const budget402 = new ApiError({
      type: "https://py-iku.dev/errors/BudgetExceeded",
      title: "Budget exceeded",
      status: 402,
      detail: {
        projected_cost_usd: 0.1,
        budget: {
          month_usd: 0.0,
          budget: { monthly_cap_usd: 0.05, per_call_cap_usd: 0.05, alert_threshold_pct: 80.0 },
        },
      } as unknown as string,
    });
    const convertImpl = vi.fn().mockRejectedValue(budget402);

    render(<ConvertPage useFallbackEditor convertImpl={convertImpl} />);
    fireEvent.click(screen.getByRole("button", { name: /^convert$/i }));

    await waitFor(() => {
      expect(screen.getByTestId("budget-confirm-modal")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("budget-confirm-cancel"));

    await waitFor(() => {
      expect(screen.queryByTestId("budget-confirm-modal")).not.toBeInTheDocument();
    });
    // No retry occurred — convertImpl still has just the 1 (failed) call.
    expect(convertImpl).toHaveBeenCalledTimes(1);
  });
});
