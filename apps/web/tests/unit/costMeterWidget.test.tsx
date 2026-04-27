import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { CostMeterWidget } from "../../src/features/cost-meter/CostMeterWidget";
import type { CostSummary } from "../../src/api/client";

const OK_SUMMARY: CostSummary = {
  today_usd: 0.42,
  month_usd: 12.34,
  budget: {
    monthly_cap_usd: 50,
    per_call_cap_usd: 1,
    alert_threshold_pct: 80,
  },
  over_threshold: false,
  over_budget: false,
  pct_of_monthly_cap: 24.68,
};

const WARN_SUMMARY: CostSummary = {
  ...OK_SUMMARY,
  month_usd: 42.0,
  pct_of_monthly_cap: 84.0,
  over_threshold: true,
};

const DANGER_SUMMARY: CostSummary = {
  ...OK_SUMMARY,
  month_usd: 60.0,
  pct_of_monthly_cap: 120.0,
  over_threshold: true,
  over_budget: true,
};

describe("<CostMeterWidget />", () => {
  it("renders today + month totals when fetch succeeds", async () => {
    const stub = { getLlmCostSummary: vi.fn(async () => OK_SUMMARY) };
    render(<CostMeterWidget clientImpl={stub} pollMs={0} />);
    await waitFor(() => {
      expect(screen.getByTestId("cost-meter-today")).toHaveTextContent("$0.42 today");
    });
    expect(screen.getByTestId("cost-meter-month")).toHaveTextContent(
      "$12.34 / $50 mo",
    );
    expect(screen.getByTestId("cost-meter-widget")).toHaveAttribute("data-state", "ok");
  });

  it("colours warn when over the alert threshold", async () => {
    const stub = { getLlmCostSummary: vi.fn(async () => WARN_SUMMARY) };
    render(<CostMeterWidget clientImpl={stub} pollMs={0} />);
    await waitFor(() => {
      expect(screen.getByTestId("cost-meter-widget")).toHaveAttribute(
        "data-state",
        "warn",
      );
    });
  });

  it("colours danger when over the monthly budget", async () => {
    const stub = { getLlmCostSummary: vi.fn(async () => DANGER_SUMMARY) };
    render(<CostMeterWidget clientImpl={stub} pollMs={0} />);
    await waitFor(() => {
      expect(screen.getByTestId("cost-meter-widget")).toHaveAttribute(
        "data-state",
        "danger",
      );
    });
    expect(screen.getByTestId("cost-meter-widget")).toHaveAttribute(
      "data-over-budget",
      "true",
    );
  });

  it("falls back to a placeholder when the fetch throws", async () => {
    const stub = {
      getLlmCostSummary: vi.fn(async () => {
        throw new Error("offline");
      }),
    };
    render(<CostMeterWidget clientImpl={stub} pollMs={0} />);
    await waitFor(() => {
      expect(screen.getByTestId("cost-meter-widget")).toHaveAttribute(
        "data-state",
        "loading",
      );
    });
    expect(screen.getByTestId("cost-meter-widget")).toHaveTextContent("$—");
  });
});
