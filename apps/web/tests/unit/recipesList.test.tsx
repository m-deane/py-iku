import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { RecipesList } from "../../src/features/catalog/RecipesList";
import type {
  RecipeCatalogEntry,
  client as ClientType,
} from "../../src/api/client";

function r(over: Partial<RecipeCatalogEntry>): RecipeCatalogEntry {
  return {
    type: "grouping",
    name: "Group",
    category: "Visual",
    icon: "Σ",
    description: "Aggregate rows",
    pandas_examples: [],
    ...over,
  } as RecipeCatalogEntry;
}

function wrap(ui: ReactNode): JSX.Element {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return <QueryClientProvider client={qc}>{ui}</QueryClientProvider>;
}

describe("<RecipesList /> — backend-down recovery", () => {
  it("renders skeleton placeholders while loading", () => {
    let resolveFn: ((items: RecipeCatalogEntry[]) => void) | null = null;
    const stub = {
      listRecipes: vi.fn(
        () =>
          new Promise<RecipeCatalogEntry[]>((resolve) => {
            resolveFn = resolve;
          }),
      ),
    } as unknown as typeof ClientType;
    render(wrap(<RecipesList clientImpl={stub} onSelect={() => {}} />));
    expect(screen.getByTestId("recipes-skeleton")).toBeInTheDocument();
    (resolveFn as unknown as ((items: RecipeCatalogEntry[]) => void) | null)?.(
      [],
    );
  });

  it("renders an error banner with Retry button on failure and refetches on click", async () => {
    let attempts = 0;
    const stub = {
      listRecipes: vi.fn(() => {
        attempts += 1;
        if (attempts === 1) return Promise.reject(new Error("ECONNREFUSED"));
        return Promise.resolve([r({ type: "grouping", name: "Group" })]);
      }),
    } as unknown as typeof ClientType;

    render(wrap(<RecipesList clientImpl={stub} onSelect={() => {}} />));

    await waitFor(() => {
      expect(screen.getByTestId("recipes-error-banner")).toBeInTheDocument();
    });

    const retry = screen.getByTestId("recipes-error-banner-retry");
    fireEvent.click(retry);

    await waitFor(() => {
      expect(screen.getByTestId("recipe-card-grouping")).toBeInTheDocument();
    });
    expect(stub.listRecipes).toHaveBeenCalledTimes(2);
  });
});
