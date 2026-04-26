import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { SnippetGallery } from "../../src/features/snippets/SnippetGallery";
import { SNIPPETS } from "../../src/features/snippets/snippets";
import { useFlowStore } from "../../src/state/flowStore";

function renderGallery(navigateImpl?: (path: string) => void) {
  return render(
    <MemoryRouter>
      <SnippetGallery navigateImpl={navigateImpl} />
    </MemoryRouter>,
  );
}

describe("<SnippetGallery />", () => {
  it("renders one card per snippet on first paint", () => {
    renderGallery();
    for (const s of SNIPPETS) {
      expect(screen.getByTestId(`snippet-card-${s.id}`)).toBeInTheDocument();
    }
  });

  it("filters by category", () => {
    renderGallery();
    fireEvent.click(screen.getByTestId("snippet-filter-sklearn"));
    const sklearnIds = SNIPPETS.filter((s) => s.category === "sklearn").map((s) => s.id);
    expect(sklearnIds.length).toBeGreaterThan(0);
    for (const id of sklearnIds) {
      expect(screen.getByTestId(`snippet-card-${id}`)).toBeInTheDocument();
    }
    // A pandas snippet should not be in the DOM.
    const pandasOnly = SNIPPETS.find((s) => s.category === "pandas");
    expect(pandasOnly).toBeDefined();
    expect(
      screen.queryByTestId(`snippet-card-${pandasOnly!.id}`),
    ).not.toBeInTheDocument();
  });

  it("filters by search query", () => {
    renderGallery();
    fireEvent.change(screen.getByTestId("snippet-gallery-search"), {
      target: { value: "merge" },
    });
    expect(
      screen.getByTestId("snippet-card-merge-two-dataframes"),
    ).toBeInTheDocument();
    // "groupby-agg" should not match "merge".
    expect(
      screen.queryByTestId("snippet-card-groupby-agg"),
    ).not.toBeInTheDocument();
  });

  it("opens a snippet by setting code in the store and navigating to /convert", () => {
    const nav = vi.fn();
    renderGallery(nav);
    fireEvent.click(screen.getByTestId("snippet-open-merge-two-dataframes"));
    expect(useFlowStore.getState().currentCode).toMatch(/pd\.merge/);
    expect(nav).toHaveBeenCalledWith("/convert");
  });

  it("shows an empty state when nothing matches", () => {
    renderGallery();
    fireEvent.change(screen.getByTestId("snippet-gallery-search"), {
      target: { value: "zzz-no-match-zzz" },
    });
    expect(screen.getByTestId("snippet-gallery-empty")).toBeInTheDocument();
  });
});
