import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { CatalogPage } from "../../src/features/catalog/CatalogPage";
import {
  CatalogDetailDrawer,
  type CatalogSelection,
} from "../../src/features/catalog/CatalogDetailDrawer";
import type {
  ProcessorCatalogEntry,
  RecipeCatalogEntry,
  client as ClientType,
} from "../../src/api/client";

function recipe(over: Partial<RecipeCatalogEntry>): RecipeCatalogEntry {
  return {
    type: "grouping",
    name: "Group",
    category: "Visual",
    icon: "Σ",
    description: "Aggregate rows by keys",
    pandas_examples: ["df.groupby('a').sum()"],
    ...over,
  } as RecipeCatalogEntry;
}

function processor(over: Partial<ProcessorCatalogEntry>): ProcessorCatalogEntry {
  return {
    type: "ColumnRenamer",
    name: "ColumnRenamer",
    category: "Restructure",
    description: "Rename one or more columns",
    required_params: ["renamings"],
    optional_params: ["preserve"],
    examples: { renamings: [{ from: "a", to: "b" }] },
    ...over,
  } as ProcessorCatalogEntry;
}

function stubClient(): typeof ClientType {
  const recipes = [recipe({})];
  const procs = [processor({})];
  return {
    listRecipes: vi.fn(() => Promise.resolve(recipes)),
    listProcessors: vi.fn(() => Promise.resolve(procs)),
    getProcessor: vi.fn((name: string) =>
      Promise.resolve(procs.find((p) => p.name === name)!),
    ),
  } as unknown as typeof ClientType;
}

function wrap(ui: ReactNode, entries: string[] = ["/catalog"]): JSX.Element {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <MemoryRouter initialEntries={entries}>
      <QueryClientProvider client={qc}>{ui}</QueryClientProvider>
    </MemoryRouter>
  );
}

describe("<CatalogDetailDrawer /> via CatalogPage", () => {
  it("opens with recipe metadata when a recipe card is clicked", async () => {
    const stub = stubClient();
    render(wrap(<CatalogPage clientImpl={stub} />));
    await waitFor(() => {
      expect(screen.getByTestId("recipe-card-grouping")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("recipe-card-grouping"));
    expect(screen.getByTestId("catalog-detail-drawer")).toBeInTheDocument();
    expect(screen.getByTestId("catalog-recipe-detail")).toBeInTheDocument();
    // pandas example renders
    expect(screen.getByText(/df.groupby\('a'\).sum\(\)/)).toBeInTheDocument();
  });

  it("opens with processor detail and triggers getProcessor()", async () => {
    const stub = stubClient();
    render(
      wrap(<CatalogPage clientImpl={stub} />, ["/catalog?tab=processors"]),
    );
    await waitFor(() => {
      expect(screen.getByTestId("processor-card-ColumnRenamer")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("processor-card-ColumnRenamer"));
    expect(screen.getByTestId("catalog-processor-detail")).toBeInTheDocument();
    await waitFor(() => {
      expect(stub.getProcessor).toHaveBeenCalledWith("ColumnRenamer");
    });
  });

  it("close button dismisses the drawer", async () => {
    const stub = stubClient();
    render(wrap(<CatalogPage clientImpl={stub} />));
    await waitFor(() => {
      expect(screen.getByTestId("recipe-card-grouping")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("recipe-card-grouping"));
    expect(screen.getByTestId("catalog-detail-drawer")).toBeInTheDocument();
    fireEvent.click(screen.getByTestId("catalog-detail-close"));
    await waitFor(() => {
      expect(screen.queryByTestId("catalog-detail-drawer")).not.toBeInTheDocument();
    });
  });
});

describe("<CatalogDetailDrawer /> standalone", () => {
  it("renders nothing when selection is null", () => {
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const { container } = render(
      <QueryClientProvider client={qc}>
        <CatalogDetailDrawer selection={null} onClose={() => {}} />
      </QueryClientProvider>,
    );
    expect(container.firstChild).toBeNull();
  });

  it("calls onClose when close button is clicked", () => {
    const onClose = vi.fn();
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const selection: CatalogSelection = { kind: "recipe", entry: recipe({}) };
    render(
      <QueryClientProvider client={qc}>
        <CatalogDetailDrawer
          selection={selection}
          onClose={onClose}
        />
      </QueryClientProvider>,
    );
    fireEvent.click(screen.getByTestId("catalog-detail-close"));
    expect(onClose).toHaveBeenCalledOnce();
  });
});

