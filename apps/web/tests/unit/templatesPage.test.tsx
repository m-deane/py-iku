import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { TemplatesPage } from "../../src/features/templates/TemplatesPage";
import { TEMPLATES } from "../../src/features/templates/templates-data";
import { useFlowStore } from "../../src/state/flowStore";

function renderPage(
  initialEntries: string[] = ["/templates"],
  navigateImpl?: (path: string) => void,
) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <TemplatesPage navigateImpl={navigateImpl} fallbackTextarea />
    </MemoryRouter>,
  );
}

describe("<TemplatesPage />", () => {
  beforeEach(() => {
    useFlowStore.getState().reset();
    useFlowStore.setState({ currentCode: "" });
  });

  it("renders all 10 templates on first paint", () => {
    expect(TEMPLATES.length).toBe(10);
    renderPage();
    for (const t of TEMPLATES) {
      expect(screen.getByTestId(`template-card-${t.id}`)).toBeInTheDocument();
    }
    expect(screen.getByTestId("templates-count")).toHaveTextContent(
      "10 of 10 templates",
    );
  });

  it("renders three columns of cards in the grid", () => {
    renderPage();
    expect(screen.getByTestId("templates-grid")).toBeInTheDocument();
  });

  it("filters by category chip", () => {
    renderPage();
    fireEvent.click(screen.getByTestId("templates-filter-power"));
    const powerIds = TEMPLATES.filter((t) => t.category === "power").map(
      (t) => t.id,
    );
    expect(powerIds.length).toBeGreaterThan(0);
    for (const id of powerIds) {
      expect(screen.getByTestId(`template-card-${id}`)).toBeInTheDocument();
    }
    // A trade-capture template should not be in the DOM.
    const tradeCapture = TEMPLATES.find((t) => t.category === "trade-capture");
    expect(tradeCapture).toBeDefined();
    expect(
      screen.queryByTestId(`template-card-${tradeCapture!.id}`),
    ).not.toBeInTheDocument();
  });

  it("filters by search query (fuse.js)", () => {
    renderPage();
    fireEvent.change(screen.getByTestId("templates-search"), {
      target: { value: "PJM" },
    });
    // PJM templates should be present.
    expect(
      screen.getByTestId("template-card-pjm-lmp-tick-analytics"),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("template-card-pjm-hub-locational-analysis"),
    ).toBeInTheDocument();
    // Counterparty roll-up should not match "PJM".
    expect(
      screen.queryByTestId("template-card-counterparty-exposure-rollup"),
    ).not.toBeInTheDocument();
  });

  it("shows an empty state when nothing matches", () => {
    renderPage();
    fireEvent.change(screen.getByTestId("templates-search"), {
      target: { value: "zzz-no-match-zzz" },
    });
    expect(screen.getByTestId("templates-empty")).toBeInTheDocument();
  });

  it("resets filters from the empty state", () => {
    renderPage();
    fireEvent.change(screen.getByTestId("templates-search"), {
      target: { value: "zzz-no-match-zzz" },
    });
    fireEvent.click(screen.getByTestId("templates-reset"));
    expect(screen.getByTestId("templates-grid")).toBeInTheDocument();
    expect(screen.queryByTestId("templates-empty")).not.toBeInTheDocument();
  });

  it("opens the preview drawer on card click", () => {
    renderPage();
    fireEvent.click(
      screen.getByTestId("template-card-forward-curve-scd"),
    );
    expect(
      screen.getByTestId("template-preview-drawer"),
    ).toBeInTheDocument();
    // Verified-recipes section shows the recorded shape.
    expect(screen.getByTestId("template-preview-recipes")).toHaveTextContent(
      /Verified recipes \(1\)/,
    );
    expect(
      screen.getByTestId("template-preview-datasets"),
    ).toBeInTheDocument();
  });

  it("opens the drawer when /templates?id=<id> is in the URL", () => {
    renderPage(["/templates?id=trade-event-aggregation"]);
    expect(
      screen.getByTestId("template-preview-drawer"),
    ).toBeInTheDocument();
  });

  it("'Open in Editor' sets currentCode and navigates to /convert", () => {
    const nav = vi.fn();
    renderPage(["/templates?id=trade-ingestion-validation"], nav);
    fireEvent.click(screen.getByTestId("template-preview-open"));
    expect(useFlowStore.getState().currentCode).toMatch(/pd\.read_csv/);
    expect(nav).toHaveBeenCalledWith("/convert");
  });

  it("closes the drawer on close button click", () => {
    renderPage(["/templates?id=trade-ingestion-validation"]);
    expect(
      screen.getByTestId("template-preview-drawer"),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByTestId("template-preview-close"));
    expect(
      screen.queryByTestId("template-preview-drawer"),
    ).not.toBeInTheDocument();
  });

  it("renders persona badges on each card", () => {
    renderPage();
    const target = TEMPLATES[0];
    const badges = screen.getByTestId(`template-personas-${target.id}`);
    for (const p of target.personas) {
      expect(badges).toHaveTextContent(p);
    }
  });

  it("every template carries a non-empty verifiedRecipes list", () => {
    for (const t of TEMPLATES) {
      expect(t.verifiedRecipes.length).toBeGreaterThan(0);
      expect(t.pythonSource).toMatch(/import pandas/);
    }
  });
});
