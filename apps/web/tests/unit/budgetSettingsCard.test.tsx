import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { BudgetSettingsCard } from "../../src/features/cost-meter/BudgetSettingsCard";
import type { BudgetSettings } from "../../src/api/client";

const INITIAL: BudgetSettings = {
  monthly_cap_usd: 50,
  per_call_cap_usd: 0.5,
  alert_threshold_pct: 80,
};

describe("<BudgetSettingsCard />", () => {
  it("loads the initial budget and saves it back", async () => {
    const get = vi.fn(async () => INITIAL);
    const put = vi.fn(async (b: BudgetSettings) => b);
    render(<BudgetSettingsCard clientImpl={{ getLlmBudget: get, putLlmBudget: put }} />);
    await waitFor(() =>
      expect(screen.getByTestId("budget-monthly")).toHaveValue(50),
    );

    fireEvent.change(screen.getByTestId("budget-monthly"), {
      target: { value: "100" },
    });
    fireEvent.click(screen.getByTestId("budget-save"));
    await waitFor(() => {
      expect(put).toHaveBeenCalledWith(
        expect.objectContaining({ monthly_cap_usd: 100 }),
      );
    });
  });

  it("clamps the threshold to [0, 100]", async () => {
    const get = vi.fn(async () => INITIAL);
    const put = vi.fn(async (b: BudgetSettings) => b);
    render(<BudgetSettingsCard clientImpl={{ getLlmBudget: get, putLlmBudget: put }} />);
    await waitFor(() => screen.getByTestId("budget-threshold"));
    fireEvent.change(screen.getByTestId("budget-threshold"), {
      target: { value: "150" },
    });
    expect(screen.getByTestId("budget-threshold")).toHaveValue(100);
  });
});
