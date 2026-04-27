import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { GrelLibraryPage } from "../../src/features/grel-library/GrelLibraryPage";
import {
  buildInsertSnippet,
  GREL_FORMULAS,
} from "../../src/features/grel-library/formulas-data";
import { useFlowStore } from "../../src/state/flowStore";

function renderPage(
  initialEntries: string[] = ["/grel"],
  navigateImpl?: (path: string) => void,
) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <GrelLibraryPage navigateImpl={navigateImpl} />
    </MemoryRouter>,
  );
}

describe("<GrelLibraryPage />", () => {
  beforeEach(() => {
    useFlowStore.getState().reset();
    useFlowStore.setState({ currentCode: "" });
  });

  it("ships at least 12 verified formulas", () => {
    expect(GREL_FORMULAS.length).toBeGreaterThanOrEqual(12);
  });

  it("renders every formula card on first paint", () => {
    renderPage();
    for (const f of GREL_FORMULAS) {
      expect(screen.getByTestId(`grel-card-${f.id}`)).toBeInTheDocument();
    }
    expect(screen.getByTestId("grel-count")).toHaveTextContent(
      `${GREL_FORMULAS.length} of ${GREL_FORMULAS.length} formulas`,
    );
  });

  it("filters to crack-spread category via chip", () => {
    renderPage();
    fireEvent.click(screen.getByTestId("grel-filter-crack-spread"));
    const crack = GREL_FORMULAS.filter((f) => f.category === "crack-spread");
    expect(crack.length).toBeGreaterThan(0);
    for (const f of crack) {
      expect(screen.getByTestId(`grel-card-${f.id}`)).toBeInTheDocument();
    }
    const heatRate = GREL_FORMULAS.find((f) => f.category === "heat-rate");
    expect(heatRate).toBeDefined();
    expect(
      screen.queryByTestId(`grel-card-${heatRate!.id}`),
    ).not.toBeInTheDocument();
  });

  it("filters by free-text query (fuse.js)", () => {
    renderPage();
    fireEvent.change(screen.getByTestId("grel-search"), {
      target: { value: "TTF" },
    });
    expect(
      screen.getByTestId("grel-card-basis-ttf-nbp"),
    ).toBeInTheDocument();
  });

  it("opens preview modal on card click", () => {
    renderPage();
    fireEvent.click(screen.getByTestId("grel-card-crack-3-2-1"));
    expect(screen.getByTestId("grel-preview-modal")).toBeInTheDocument();
    expect(screen.getByTestId("grel-preview-grel")).toHaveTextContent(
      "rbob_price",
    );
    expect(screen.getByTestId("grel-preview-pandas")).toHaveTextContent(
      "df[\"crack_3_2_1\"]",
    );
    expect(screen.getByTestId("grel-preview-instruments")).toHaveTextContent(
      "RB",
    );
    expect(
      screen.getByTestId("grel-preview-example-output"),
    ).toHaveTextContent("23.43");
  });

  it("opens preview from /grel?id=<id> deep link", () => {
    renderPage(["/grel?id=heat-rate-market"]);
    expect(screen.getByTestId("grel-preview-modal")).toBeInTheDocument();
    expect(screen.getByTestId("grel-preview-grel")).toHaveTextContent(
      "power_price",
    );
  });

  it("Insert into editor prepends the snippet to currentCode and routes to /editor", () => {
    const nav = vi.fn();
    useFlowStore.setState({ currentCode: "import pandas as pd\n" });
    renderPage(["/grel?id=crack-3-2-1"], nav);
    fireEvent.click(screen.getByTestId("grel-preview-insert"));
    const code = useFlowStore.getState().currentCode;
    const expectedHeader = buildInsertSnippet(
      GREL_FORMULAS.find((f) => f.id === "crack-3-2-1")!,
    );
    expect(code.startsWith(expectedHeader)).toBe(true);
    expect(code).toContain("import pandas as pd");
    expect(nav).toHaveBeenCalledWith("/editor");
  });

  it("shows the GREL string and pandas one-liner inside the modal", () => {
    renderPage(["/grel?id=basis-pjm-hh"]);
    const grel = screen.getByTestId("grel-preview-grel").textContent ?? "";
    const pandas = screen.getByTestId("grel-preview-pandas").textContent ?? "";
    expect(grel).toContain("pjm_w_price");
    expect(grel).toContain("henry_hub_price");
    expect(pandas).toContain("df[\"basis_pjm_hh\"]");
  });

  it("every formula has a non-empty grel string and a worked example", () => {
    for (const f of GREL_FORMULAS) {
      expect(f.grel.length).toBeGreaterThan(0);
      expect(f.pandas).toContain("df[");
      expect(typeof f.example.output).toBe("number");
      expect(Object.keys(f.example.inputs).length).toBeGreaterThan(0);
      expect(f.relatedInstruments.length).toBeGreaterThan(0);
    }
  });

  it("buildInsertSnippet renders a comment header followed by the pandas line", () => {
    const formula = GREL_FORMULAS[0];
    const snippet = buildInsertSnippet(formula);
    expect(snippet.startsWith(`# ${formula.name}`)).toBe(true);
    expect(snippet).toContain(`# GREL: ${formula.grel}`);
    expect(snippet).toContain(formula.pandas);
  });
});
