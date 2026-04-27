import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { CommandPalette } from "../../src/features/command-palette/CommandPalette";
import { useCommandPaletteHotkey } from "../../src/features/command-palette/useCommandPaletteHotkey";
import { useCommandPaletteStore } from "../../src/store/commandPalette";
import type { RecipeCatalogEntry } from "../../src/api/client";

// We can't mock the api/client at module level cleanly under vitest without
// wiring vi.mock. Instead, install a fetch stub on globalThis so the catalog
// query resolves with seeded recipes and the audit query returns an empty list.
function installFetchStub(recipes: RecipeCatalogEntry[]): void {
  const fetchImpl = vi.fn(async (input: RequestInfo | URL): Promise<Response> => {
    const url = typeof input === "string" ? input : input.toString();
    if (url.includes("/catalog/recipes")) {
      return new Response(JSON.stringify(recipes), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    }
    if (url.includes("/audit")) {
      return new Response(JSON.stringify({ events: [], next_cursor: null }), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    }
    return new Response("[]", {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  });
  globalThis.fetch = fetchImpl as unknown as typeof fetch;
}

// `Partial<RecipeCatalogEntry>` would forbid synthetic recipe types like
// "filter-value" that the IA work uses for catalog tests; widen to
// Record<string, unknown> and trust the final cast.
function makeRecipe(over: Record<string, unknown>): RecipeCatalogEntry {
  return {
    type: "filter",
    name: "Filter on Value",
    category: "Visual",
    icon: "▽",
    description: "Filter rows by an exact column value",
    pandas_examples: ["df[df.x == 'foo']"],
    ...over,
  } as unknown as RecipeCatalogEntry;
}

function Harness({ children }: { children: ReactNode }): JSX.Element {
  // Each test gets its own QueryClient so cached data doesn't leak.
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return (
    <QueryClientProvider client={client}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

function HotkeyMounted(): JSX.Element {
  useCommandPaletteHotkey();
  return <CommandPalette inlineForTesting />;
}

beforeEach(() => {
  // Reset the palette store between tests.
  const store = useCommandPaletteStore.getState();
  useCommandPaletteStore.setState({
    isOpen: false,
    recent: [],
  });
  void store;
  installFetchStub([
    makeRecipe({
      type: "filter-value",
      name: "Filter on Value",
    }),
    makeRecipe({
      type: "filter-numeric",
      name: "Filter on Numeric Range",
      description: "Filter rows where a numeric column falls in a range",
    }),
    makeRecipe({
      type: "filter-formula",
      name: "Filter on Formula",
      description: "Filter rows using a GREL formula",
    }),
    makeRecipe({
      type: "join",
      name: "Join",
      description: "Inner / outer join two datasets",
    }),
  ]);
});

describe("<CommandPalette />", () => {
  it("does not render when closed", () => {
    render(
      <Harness>
        <CommandPalette inlineForTesting />
      </Harness>,
    );
    expect(screen.queryByTestId("command-palette")).not.toBeInTheDocument();
  });

  it("opens via Cmd+K and renders the search input", async () => {
    render(
      <Harness>
        <HotkeyMounted />
      </Harness>,
    );
    act(() => {
      fireEvent.keyDown(document, { key: "k", metaKey: true });
    });
    const palette = await screen.findByTestId("command-palette");
    expect(palette).toBeInTheDocument();
    expect(palette).toHaveAttribute("role", "dialog");
    expect(palette).toHaveAttribute("aria-modal", "true");
    expect(screen.getByTestId("command-palette-input")).toBeInTheDocument();
  });

  it("opens via Ctrl+K (non-Mac shortcut)", async () => {
    render(
      <Harness>
        <HotkeyMounted />
      </Harness>,
    );
    act(() => {
      fireEvent.keyDown(document, { key: "k", ctrlKey: true });
    });
    expect(await screen.findByTestId("command-palette")).toBeInTheDocument();
  });

  it("closes on Esc", async () => {
    useCommandPaletteStore.setState({ isOpen: true });
    render(
      <Harness>
        <CommandPalette inlineForTesting />
      </Harness>,
    );
    expect(await screen.findByTestId("command-palette")).toBeInTheDocument();
    fireEvent.keyDown(screen.getByTestId("command-palette-backdrop"), {
      key: "Escape",
    });
    await waitFor(() =>
      expect(screen.queryByTestId("command-palette")).not.toBeInTheDocument(),
    );
  });

  it("filters recipes by fuzzy query 'filt'", async () => {
    useCommandPaletteStore.setState({ isOpen: true });
    render(
      <Harness>
        <CommandPalette inlineForTesting />
      </Harness>,
    );
    // Wait for catalog query to settle.
    await waitFor(() =>
      expect(screen.getByText("Filter on Value")).toBeInTheDocument(),
    );

    const input = screen.getByTestId("command-palette-input");
    fireEvent.change(input, { target: { value: "filt" } });

    await waitFor(() => {
      expect(screen.getByText("Filter on Value")).toBeInTheDocument();
      expect(screen.getByText("Filter on Numeric Range")).toBeInTheDocument();
      expect(screen.getByText("Filter on Formula")).toBeInTheDocument();
    });
    // The non-matching "Join" recipe should be hidden.
    expect(screen.queryByText("Join")).not.toBeInTheDocument();
  });

  it("'convert' query matches the Convert action", async () => {
    useCommandPaletteStore.setState({ isOpen: true });
    render(
      <Harness>
        <CommandPalette inlineForTesting />
      </Harness>,
    );
    fireEvent.change(screen.getByTestId("command-palette-input"), {
      target: { value: "convert" },
    });
    await waitFor(() => {
      // Convert action lives in the Actions section.
      expect(
        screen.getByTestId("command-palette-item-action:convert"),
      ).toBeInTheDocument();
    });
  });

  it("ArrowDown moves the active item and Enter invokes it", async () => {
    useCommandPaletteStore.setState({ isOpen: true });
    render(
      <Harness>
        <CommandPalette inlineForTesting />
      </Harness>,
    );
    await waitFor(() =>
      expect(screen.getByText("Filter on Value")).toBeInTheDocument(),
    );

    const backdrop = screen.getByTestId("command-palette-backdrop");
    // Move down a few times then hit Enter.
    fireEvent.keyDown(backdrop, { key: "ArrowDown" });
    fireEvent.keyDown(backdrop, { key: "ArrowDown" });
    fireEvent.keyDown(backdrop, { key: "Enter" });

    await waitFor(() => {
      // Invocation closes the palette.
      expect(screen.queryByTestId("command-palette")).not.toBeInTheDocument();
    });
    // And persists a recent item.
    expect(useCommandPaletteStore.getState().recent.length).toBe(1);
  });

  it("shows a 'Convert a script first' hint when no flow is loaded", async () => {
    useCommandPaletteStore.setState({ isOpen: true });
    render(
      <Harness>
        <CommandPalette inlineForTesting />
      </Harness>,
    );
    await waitFor(() =>
      expect(
        screen.getByText("Convert a script first"),
      ).toBeInTheDocument(),
    );
  });

  it("renders the Recently used section when recent has items and query is empty", async () => {
    useCommandPaletteStore.setState({
      isOpen: true,
      recent: [
        {
          id: "action:convert",
          section: "Actions",
          primary: "Convert",
          secondary: "x",
          icon: "→",
          ts: Date.now(),
        },
      ],
    });
    render(
      <Harness>
        <CommandPalette inlineForTesting />
      </Harness>,
    );
    await waitFor(() => {
      expect(
        screen.getByTestId("command-palette-section-recently-used"),
      ).toBeInTheDocument();
    });
  });
});
