import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { ProcessorsList } from "../../src/features/catalog/ProcessorsList";
import type {
  ProcessorCatalogEntry,
  client as ClientType,
} from "../../src/api/client";

function p(over: Partial<ProcessorCatalogEntry>): ProcessorCatalogEntry {
  return {
    type: "ColumnRenamer",
    name: "ColumnRenamer",
    category: "Restructure",
    description: "Rename columns",
    required_params: [],
    optional_params: [],
    examples: {},
    ...over,
  } as ProcessorCatalogEntry;
}

function stubClient(items: ProcessorCatalogEntry[]): typeof ClientType {
  return {
    listProcessors: vi.fn(() => Promise.resolve(items)),
    getProcessor: vi.fn((name: string) =>
      Promise.resolve(items.find((x) => x.name === name)!),
    ),
  } as unknown as typeof ClientType;
}

function wrap(ui: ReactNode): JSX.Element {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return <QueryClientProvider client={qc}>{ui}</QueryClientProvider>;
}

describe("<ProcessorsList />", () => {
  it("renders processor cards from the API", async () => {
    const stub = stubClient([
      p({ name: "ColumnRenamer", category: "Restructure" }),
      p({ name: "FillEmptyWithValue", category: "Cleansing" }),
    ]);
    render(wrap(<ProcessorsList clientImpl={stub} onSelect={() => {}} />));
    await waitFor(() => {
      expect(screen.getByTestId("processor-card-ColumnRenamer")).toBeInTheDocument();
      expect(screen.getByTestId("processor-card-FillEmptyWithValue")).toBeInTheDocument();
    });
  });

  it("debounces search input → only the final keystroke fires a server-side q query", async () => {
    const stub = stubClient([p({ name: "ColumnRenamer" })]);
    // debounceMs=20 keeps the test fast while still proving rapid keystrokes
    // collapse into a single fetch with the final value.
    render(
      wrap(
        <ProcessorsList
          clientImpl={stub}
          onSelect={() => {}}
          debounceMs={20}
        />,
      ),
    );
    await waitFor(() => {
      expect(screen.getByTestId("processor-card-ColumnRenamer")).toBeInTheDocument();
    });

    const search = screen.getByTestId("processors-search") as HTMLInputElement;

    // Three rapid keystrokes within the debounce window — the debouncer should
    // collapse them into a single fetch with q="col".
    fireEvent.change(search, { target: { value: "c" } });
    fireEvent.change(search, { target: { value: "co" } });
    fireEvent.change(search, { target: { value: "col" } });

    await waitFor(() => {
      const calls = (stub.listProcessors as ReturnType<typeof vi.fn>).mock.calls;
      const matched = calls.find(
        (c) => c[0] && (c[0] as { q?: string }).q === "col",
      );
      expect(matched).toBeTruthy();
    });

    // No intermediate fetch with q="c" or q="co" — proves debouncing.
    const calls = (stub.listProcessors as ReturnType<typeof vi.fn>).mock.calls;
    const intermediate = calls.find(
      (c) => c[0] && ["c", "co"].includes((c[0] as { q?: string }).q ?? ""),
    );
    expect(intermediate).toBeUndefined();
  });

  it("filters by category via the dropdown", async () => {
    const stub = stubClient([
      p({ name: "ColumnRenamer", category: "Restructure" }),
      p({ name: "FillEmptyWithValue", category: "Cleansing" }),
    ]);
    render(
      wrap(
        <ProcessorsList
          clientImpl={stub}
          onSelect={() => {}}
          debounceMs={0}
        />,
      ),
    );
    await waitFor(() => {
      expect(screen.getByTestId("processor-card-ColumnRenamer")).toBeInTheDocument();
    });
    const select = screen.getByTestId("processors-category") as HTMLSelectElement;
    fireEvent.change(select, { target: { value: "Cleansing" } });
    await waitFor(() => {
      const calls = (stub.listProcessors as ReturnType<typeof vi.fn>).mock.calls;
      const matched = calls.find(
        (c) => c[0] && (c[0] as { category?: string }).category === "Cleansing",
      );
      expect(matched).toBeTruthy();
    });
  });
});
