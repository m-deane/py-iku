import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { LmpBrowserPage } from "../../src/features/lmp-browser/LmpBrowserPage";
import {
  buildNodeSnippet,
  LMP_ISOS,
  LMP_NODES,
} from "../../src/features/lmp-browser/lmp-data";

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/lmp"]}>
      <LmpBrowserPage />
    </MemoryRouter>,
  );
}

describe("<LmpBrowserPage />", () => {
  it("ships at least 60 nodes covering all six ISOs", () => {
    expect(LMP_NODES.length).toBeGreaterThanOrEqual(60);
    for (const iso of LMP_ISOS) {
      const count = LMP_NODES.filter((n) => n.iso === iso).length;
      expect(count).toBeGreaterThanOrEqual(10);
    }
  });

  it("renders the table with all 60 rows on first paint", () => {
    renderPage();
    expect(screen.getByTestId("lmp-count")).toHaveTextContent(
      `${LMP_NODES.length} of ${LMP_NODES.length} nodes`,
    );
    expect(screen.getByTestId("lmp-table")).toBeInTheDocument();
    expect(screen.getByTestId("lmp-stale-banner")).toBeInTheDocument();
  });

  it("filters by ISO chip", () => {
    renderPage();
    fireEvent.click(screen.getByTestId("lmp-filter-PJM"));
    const pjmCount = LMP_NODES.filter((n) => n.iso === "PJM").length;
    expect(screen.getByTestId("lmp-count")).toHaveTextContent(
      `${pjmCount} of ${LMP_NODES.length} nodes`,
    );
    // An ERCOT node should disappear.
    const ercot = LMP_NODES.find((n) => n.iso === "ERCOT")!;
    expect(
      screen.queryByTestId(`lmp-row-ERCOT-${ercot.node_id}`),
    ).not.toBeInTheDocument();
  });

  it("filters by free-text search", () => {
    renderPage();
    fireEvent.change(screen.getByTestId("lmp-search"), {
      target: { value: "WESTERN" },
    });
    // PJM Western Hub should be present.
    expect(
      screen.getByTestId("lmp-row-PJM-51217"),
    ).toBeInTheDocument();
  });

  it("Copy snippet button writes the canonical pandas pattern", async () => {
    const copy = vi.fn().mockResolvedValue(undefined);
    render(
      <MemoryRouter>
        <LmpBrowserPage copyImpl={copy} />
      </MemoryRouter>,
    );
    const node = LMP_NODES.find((n) => n.iso === "PJM" && n.node_id === "51217")!;
    fireEvent.click(screen.getByTestId(`lmp-copy-PJM-${node.node_id}`));
    expect(copy).toHaveBeenCalledTimes(1);
    const arg = copy.mock.calls[0][0] as string;
    expect(arg).toBe(buildNodeSnippet(node));
    expect(arg).toContain("pd.read_csv");
    expect(arg).toContain(`df["node_id"] == "${node.node_id}"`);
  });

  it("buildNodeSnippet includes ISO source citation", () => {
    const node = LMP_NODES.find((n) => n.iso === "ERCOT")!;
    const snippet = buildNodeSnippet(node);
    expect(snippet).toContain("# source:");
    expect(snippet).toContain("ERCOT MIS");
  });

  it("each ISO chip is selectable via tab role", () => {
    renderPage();
    for (const iso of LMP_ISOS) {
      expect(screen.getByTestId(`lmp-filter-${iso}`)).toHaveAttribute(
        "role",
        "tab",
      );
    }
  });
});
