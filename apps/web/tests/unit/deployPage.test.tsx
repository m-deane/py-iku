import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { DeployPage } from "../../src/features/deploy/DeployPage";
import {
  inSettleWindow,
  findActiveWindows,
} from "../../src/features/deploy/settle-window";
import type { MarketCalendarResponse } from "../../src/api/client";

function withProviders(ui: ReactNode): JSX.Element {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return (
    <MemoryRouter initialEntries={["/deploy"]}>
      <QueryClientProvider client={qc}>{ui}</QueryClientProvider>
    </MemoryRouter>
  );
}

const STATIC_CALENDAR: MarketCalendarResponse = {
  schedule_kind: "static-v1",
  note: "Static schedule for v1; real venue calendar integration is Wave 5+.",
  sessions: [
    {
      venue: "NYMEX",
      venue_name: "CME Globex — NYMEX",
      product: "WTI Crude (CL) prompt",
      timezone: "America/New_York",
      close_time: "14:30",
      settle_window_minutes: 30,
      note: "WTI prompt settle.",
    },
    {
      venue: "ICE-EUR",
      venue_name: "ICE Futures Europe",
      product: "Brent Crude (B) prompt",
      timezone: "Europe/London",
      close_time: "19:30",
      settle_window_minutes: 30,
      note: "Brent settlement.",
    },
  ],
};

describe("settle-window helpers", () => {
  it("inSettleWindow flags a clock inside the half-window", () => {
    // 14:30 NY close; 14:25 NY ⇒ inside the +/- 30 min half-window.
    // 2026-04-26 18:25 UTC = 14:25 NY (EDT, UTC-4).
    const now = new Date("2026-04-26T18:25:00Z");
    const result = inSettleWindow(STATIC_CALENDAR.sessions[0], now);
    expect(result.inWindow).toBe(true);
    expect(result.minutesToClose).toBe(5);
    expect(result.windowStart).toBe("14:00");
    expect(result.windowEnd).toBe("15:00");
  });

  it("inSettleWindow excludes a clock well outside the window", () => {
    const now = new Date("2026-04-26T03:00:00Z"); // 23:00 NY previous day
    const result = inSettleWindow(STATIC_CALENDAR.sessions[0], now);
    expect(result.inWindow).toBe(false);
  });

  it("findActiveWindows finds every venue currently in window", () => {
    // 14:30 NY = 19:30 London ⇒ both NYMEX (14:30) and ICE-EUR (19:30) close.
    const now = new Date("2026-04-26T18:30:00Z");
    const active = findActiveWindows(STATIC_CALENDAR.sessions, now);
    expect(active.length).toBe(2);
  });

  it("findActiveWindows is empty when all venues are outside their windows", () => {
    const now = new Date("2026-04-26T03:00:00Z"); // 03:00 UTC — quiet hour
    const active = findActiveWindows(STATIC_CALENDAR.sessions, now);
    expect(active.length).toBe(0);
  });
});

describe("<DeployPage />", () => {
  it("renders the calendar and a live Deploy button outside any window", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(STATIC_CALENDAR);
    render(
      withProviders(
        <DeployPage
          fetchCalendarImpl={fetchImpl}
          nowOverride={new Date("2026-04-26T03:00:00Z")}
        />,
      ),
    );

    await waitFor(() =>
      expect(screen.getByTestId("deploy-page")).toBeInTheDocument(),
    );
    const button = screen.getByTestId("deploy-button");
    expect(button).not.toBeDisabled();
    expect(button).toHaveAttribute("data-blocked", "false");
    expect(button).toHaveTextContent("Deploy to DSS");
    expect(screen.getByTestId("deploy-calendar")).toBeInTheDocument();
    expect(
      screen.getByTestId("deploy-session-NYMEX"),
    ).toHaveAttribute("data-in-window", "false");
  });

  it("disables the Deploy button + shows the tooltip when inside a settle window", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(STATIC_CALENDAR);
    render(
      withProviders(
        <DeployPage
          fetchCalendarImpl={fetchImpl}
          // 14:25 NY → inside NYMEX's 14:00–15:00 window.
          nowOverride={new Date("2026-04-26T18:25:00Z")}
        />,
      ),
    );

    await waitFor(() =>
      expect(screen.getByTestId("deploy-page")).toBeInTheDocument(),
    );
    const button = screen.getByTestId("deploy-button");
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute("data-blocked", "true");
    expect(button).toHaveTextContent("NYMEX");
    expect(
      screen.getByTestId("deploy-blocked-tooltip"),
    ).toHaveTextContent("NYMEX");
    expect(
      screen.getByTestId("deploy-session-NYMEX"),
    ).toHaveAttribute("data-in-window", "true");
  });

  it("renders an error state when the calendar fetch fails", async () => {
    const fetchImpl = vi.fn().mockRejectedValue(new Error("boom"));
    render(
      withProviders(
        <DeployPage
          fetchCalendarImpl={fetchImpl}
          nowOverride={new Date("2026-04-26T03:00:00Z")}
        />,
      ),
    );
    await waitFor(() =>
      expect(screen.getByTestId("deploy-page-error")).toBeInTheDocument(),
    );
  });
});
