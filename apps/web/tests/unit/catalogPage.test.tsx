import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { CatalogPage } from "../../src/features/catalog/CatalogPage";
import type {
  ProcessorCatalogEntry,
  RecipeCatalogEntry,
  client as ClientType,
} from "../../src/api/client";

function makeRecipe(over: Partial<RecipeCatalogEntry>): RecipeCatalogEntry {
  return {
    type: "grouping",
    name: "Group",
    category: "Visual",
    icon: "Σ",
    description: "Aggregate rows",
    pandas_examples: ["df.groupby()"],
    ...over,
  } as RecipeCatalogEntry;
}

function makeProcessor(over: Partial<ProcessorCatalogEntry>): ProcessorCatalogEntry {
  return {
    type: "ColumnRenamer",
    name: "ColumnRenamer",
    category: "Restructure",
    description: "Rename columns",
    required_params: ["renamings"],
    optional_params: [],
    examples: {},
    ...over,
  } as ProcessorCatalogEntry;
}

function stubClient(): typeof ClientType {
  const recipes: RecipeCatalogEntry[] = [
    makeRecipe({ type: "grouping", name: "Group", category: "Visual" }),
    makeRecipe({ type: "python", name: "Python", category: "Code" }),
  ];
  const processors: ProcessorCatalogEntry[] = [
    makeProcessor({ name: "ColumnRenamer", category: "Restructure" }),
    makeProcessor({ name: "FillEmptyWithValue", category: "Cleansing" }),
  ];
  return {
    listRecipes: vi.fn(() => Promise.resolve(recipes)),
    listProcessors: vi.fn(() => Promise.resolve(processors)),
    getProcessor: vi.fn((name: string) =>
      Promise.resolve(processors.find((p) => p.name === name)!),
    ),
  } as unknown as typeof ClientType;
}

function withProviders(
  ui: ReactNode,
  initialEntries: string[] = ["/catalog"],
): JSX.Element {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return (
    <MemoryRouter initialEntries={initialEntries}>
      <QueryClientProvider client={qc}>{ui}</QueryClientProvider>
    </MemoryRouter>
  );
}

describe("<CatalogPage />", () => {
  it("renders both tabs and defaults to recipes", async () => {
    const stub = stubClient();
    render(withProviders(<CatalogPage clientImpl={stub} />));
    expect(screen.getByTestId("catalog-tab-recipes")).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getByTestId("catalog-tab-processors")).toHaveAttribute(
      "aria-selected",
      "false",
    );
    await waitFor(() => {
      expect(screen.getByTestId("recipe-card-grouping")).toBeInTheDocument();
    });
    expect(stub.listRecipes).toHaveBeenCalled();
  });

  it("switches to processors tab when clicked", async () => {
    const stub = stubClient();
    render(withProviders(<CatalogPage clientImpl={stub} />));
    fireEvent.click(screen.getByTestId("catalog-tab-processors"));
    await waitFor(() => {
      expect(screen.getByTestId("processor-card-ColumnRenamer")).toBeInTheDocument();
    });
    expect(stub.listProcessors).toHaveBeenCalled();
  });

  it("honours ?tab=processors in the URL", async () => {
    const stub = stubClient();
    render(
      withProviders(<CatalogPage clientImpl={stub} />, ["/catalog?tab=processors"]),
    );
    expect(screen.getByTestId("catalog-tab-processors")).toHaveAttribute(
      "aria-selected",
      "true",
    );
    await waitFor(() => {
      expect(screen.getByTestId("processor-card-ColumnRenamer")).toBeInTheDocument();
    });
  });

  it("filters recipe list client-side via the search input", async () => {
    const stub = stubClient();
    render(withProviders(<CatalogPage clientImpl={stub} />));
    await waitFor(() => {
      expect(screen.getByTestId("recipe-card-grouping")).toBeInTheDocument();
    });
    const search = screen.getByTestId("recipes-search") as HTMLInputElement;
    fireEvent.change(search, { target: { value: "python" } });
    await waitFor(() => {
      expect(screen.queryByTestId("recipe-card-grouping")).not.toBeInTheDocument();
      expect(screen.getByTestId("recipe-card-python")).toBeInTheDocument();
    });
  });
});
