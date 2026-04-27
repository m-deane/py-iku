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
import { useFlowStore } from "../../src/state/flowStore";
import { useSettingsStore } from "../../src/state/settingsStore";
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
    if (url.includes("/api/version")) {
      return new Response(
        JSON.stringify({
          api_version: "0.1.0",
          py_iku_version: "0.3.0",
          commit: "abc1234",
          commit_message: "feat: polish command palette",
          source: "git",
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      );
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
  useCommandPaletteStore.setState({
    isOpen: false,
    recent: [],
    recentSearches: [],
    pinnedIds: [],
    currentArgsItemId: null,
    currentArgs: [],
  });
  // Reset flow + settings.
  useFlowStore.setState({ conversionMode: "rule", currentFlow: null });
  useSettingsStore.setState({ llmProvider: "anthropic" });

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
        <CommandPalette inlineForTesting forcePreviewVisible={false} />
      </Harness>,
    );
    await waitFor(() =>
      expect(
        screen.getByTestId("command-palette-item-recipe:filter-value"),
      ).toBeInTheDocument(),
    );

    const input = screen.getByTestId("command-palette-input");
    fireEvent.change(input, { target: { value: "filt" } });

    await waitFor(() => {
      expect(
        screen.getByTestId("command-palette-item-recipe:filter-value"),
      ).toBeInTheDocument();
      expect(
        screen.getByTestId("command-palette-item-recipe:filter-numeric"),
      ).toBeInTheDocument();
      expect(
        screen.getByTestId("command-palette-item-recipe:filter-formula"),
      ).toBeInTheDocument();
    });
    expect(
      screen.queryByTestId("command-palette-item-recipe:join"),
    ).not.toBeInTheDocument();
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
      expect(
        screen.getByTestId("command-palette-item-action:convert"),
      ).toBeInTheDocument();
    });
  });

  it("ArrowDown moves the active item and Enter invokes it", async () => {
    useCommandPaletteStore.setState({ isOpen: true });
    render(
      <Harness>
        <CommandPalette inlineForTesting forcePreviewVisible={false} />
      </Harness>,
    );
    await waitFor(() =>
      expect(
        screen.getByTestId("command-palette-item-recipe:filter-value"),
      ).toBeInTheDocument(),
    );

    const backdrop = screen.getByTestId("command-palette-backdrop");
    fireEvent.keyDown(backdrop, { key: "ArrowDown" });
    fireEvent.keyDown(backdrop, { key: "ArrowDown" });
    fireEvent.keyDown(backdrop, { key: "Enter" });

    // Wait through the 150ms scale animation before invocation lands.
    await waitFor(
      () => {
        expect(screen.queryByTestId("command-palette")).not.toBeInTheDocument();
      },
      { timeout: 1000 },
    );
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

// ---------------------------------------------------------------------------
// Sprint 3 polish — multi-step args, pinning, section jump, preview pane,
// recent searches, and the keyboard-shortcuts sub-modal.
// ---------------------------------------------------------------------------

describe("<CommandPalette /> Sprint 3 polish", () => {
  it("multi-step Convert: rule mode runs the conversion with mode=rule", async () => {
    useCommandPaletteStore.setState({ isOpen: true });
    render(
      <Harness>
        <CommandPalette inlineForTesting forcePreviewVisible={false} />
      </Harness>,
    );
    // Wait until the catalog has loaded so the Convert action is rendered.
    await waitFor(() =>
      expect(
        screen.getByTestId("command-palette-item-action:convert"),
      ).toBeInTheDocument(),
    );

    // Fire the row directly (skips animation timing edge cases).
    fireEvent.click(
      screen.getByTestId("command-palette-item-action:convert"),
    );

    // After the 150ms animation, we enter arg-collection mode and the
    // breadcrumb shows the action name.
    await waitFor(
      () => {
        expect(
          screen.getByTestId("command-palette-breadcrumb"),
        ).toBeInTheDocument();
      },
      { timeout: 1000 },
    );

    // Pick rule.
    fireEvent.click(screen.getByTestId("command-palette-item-arg:mode:rule"));

    // Args complete (rule skips Provider via the `when` gate) — palette closes
    // and the conversion mode is set to rule.
    await waitFor(
      () => {
        expect(
          screen.queryByTestId("command-palette"),
        ).not.toBeInTheDocument();
      },
      { timeout: 1000 },
    );
    expect(useFlowStore.getState().conversionMode).toBe("rule");
  });

  it("Esc inside an arg step backs up to the previous step", async () => {
    useCommandPaletteStore.setState({ isOpen: true });
    render(
      <Harness>
        <CommandPalette inlineForTesting forcePreviewVisible={false} />
      </Harness>,
    );
    await waitFor(() =>
      expect(
        screen.getByTestId("command-palette-item-action:convert"),
      ).toBeInTheDocument(),
    );
    fireEvent.click(
      screen.getByTestId("command-palette-item-action:convert"),
    );
    await waitFor(() =>
      expect(
        screen.getByTestId("command-palette-breadcrumb"),
      ).toBeInTheDocument(),
    );

    // Pick llm so we get the Provider step (won't be skipped).
    fireEvent.click(screen.getByTestId("command-palette-item-arg:mode:llm"));
    await waitFor(() =>
      expect(
        screen.getByTestId("command-palette-item-arg:provider:anthropic"),
      ).toBeInTheDocument(),
    );

    // Esc → back to mode step.
    fireEvent.keyDown(screen.getByTestId("command-palette-backdrop"), {
      key: "Escape",
    });
    await waitFor(() =>
      expect(
        screen.getByTestId("command-palette-item-arg:mode:rule"),
      ).toBeInTheDocument(),
    );
  });

  it("pin/unpin persists across reopen", async () => {
    useCommandPaletteStore.setState({ isOpen: true });
    const { rerender } = render(
      <Harness>
        <CommandPalette inlineForTesting forcePreviewVisible={false} />
      </Harness>,
    );
    await waitFor(() =>
      expect(
        screen.getByTestId("command-palette-item-recipe:filter-value"),
      ).toBeInTheDocument(),
    );

    // Pin the Filter on Value row.
    const pinBtn = screen.getByTestId(
      "command-palette-pin-recipe:filter-value",
    );
    fireEvent.click(pinBtn);
    expect(useCommandPaletteStore.getState().pinnedIds).toContain(
      "recipe:filter-value",
    );

    // Close + reopen — the pin should still be there.
    useCommandPaletteStore.setState({ isOpen: false });
    rerender(
      <Harness>
        <CommandPalette inlineForTesting forcePreviewVisible={false} />
      </Harness>,
    );
    useCommandPaletteStore.setState({ isOpen: true });
    rerender(
      <Harness>
        <CommandPalette inlineForTesting forcePreviewVisible={false} />
      </Harness>,
    );

    // Pinned section should now render.
    await waitFor(() => {
      expect(
        screen.getByTestId("command-palette-section-pinned"),
      ).toBeInTheDocument();
    });
  });

  it("Cmd+P pins the highlighted item", async () => {
    useCommandPaletteStore.setState({ isOpen: true });
    render(
      <Harness>
        <CommandPalette inlineForTesting forcePreviewVisible={false} />
      </Harness>,
    );
    await waitFor(() =>
      expect(
        screen.getByTestId("command-palette-item-recipe:filter-value"),
      ).toBeInTheDocument(),
    );
    const backdrop = screen.getByTestId("command-palette-backdrop");
    fireEvent.keyDown(backdrop, { key: "p", metaKey: true });
    expect(useCommandPaletteStore.getState().pinnedIds.length).toBe(1);
  });

  it("Cmd+3 from empty palette focuses the first Snippets item", async () => {
    useCommandPaletteStore.setState({ isOpen: true });
    render(
      <Harness>
        <CommandPalette inlineForTesting forcePreviewVisible={false} />
      </Harness>,
    );
    await waitFor(() =>
      expect(
        screen.getByTestId("command-palette-item-recipe:filter-value"),
      ).toBeInTheDocument(),
    );
    // Visible section order with empty query, no pin/recent:
    // 1. Recipes, 2. Datasets, 3. Snippets, 4. Actions, 5. Help
    // (Audit events is empty under the test stub, so dropped.)
    const backdrop = screen.getByTestId("command-palette-backdrop");
    fireEvent.keyDown(backdrop, { key: "3", metaKey: true });

    await waitFor(() => {
      // The first item in the Snippets section should be aria-selected.
      const snippetSection = screen.getByTestId(
        "command-palette-section-snippets",
      );
      const first = snippetSection.querySelector(
        '[role="option"]',
      ) as HTMLElement | null;
      expect(first).not.toBeNull();
      expect(first?.getAttribute("aria-selected")).toBe("true");
    });
  });

  it("highlighting a snippet renders source first 10 lines in the preview pane", async () => {
    useCommandPaletteStore.setState({ isOpen: true });
    render(
      <Harness>
        <CommandPalette inlineForTesting forcePreviewVisible={true} />
      </Harness>,
    );
    await waitFor(() =>
      expect(
        screen.getByTestId("command-palette-item-recipe:filter-value"),
      ).toBeInTheDocument(),
    );
    // Hover the first snippet to highlight it.
    const snippetSection = screen.getByTestId(
      "command-palette-section-snippets",
    );
    const firstSnippet = snippetSection.querySelector(
      '[role="option"]',
    ) as HTMLElement | null;
    expect(firstSnippet).not.toBeNull();
    fireEvent.mouseMove(firstSnippet!);

    await waitFor(() => {
      const preview = screen.getByTestId("command-palette-preview-snippet");
      expect(preview).toBeInTheDocument();
      // First snippet is groupby-agg from snippets.ts; it starts with `import pandas as pd`.
      expect(preview.querySelector("pre")?.textContent ?? "").toContain(
        "import pandas as pd",
      );
      // 10-line cap: the rendered <pre> should never exceed 10 newlines.
      const text = preview.querySelector("pre")?.textContent ?? "";
      const newlines = (text.match(/\n/g) ?? []).length;
      expect(newlines).toBeLessThanOrEqual(9);
    });
  });

  it("recent searches: query → invoke → reopen → empty input shows query as tag", async () => {
    useCommandPaletteStore.setState({ isOpen: true });
    const { rerender } = render(
      <Harness>
        <CommandPalette inlineForTesting forcePreviewVisible={false} />
      </Harness>,
    );
    await waitFor(() =>
      expect(
        screen.getByTestId("command-palette-item-recipe:filter-value"),
      ).toBeInTheDocument(),
    );
    fireEvent.change(screen.getByTestId("command-palette-input"), {
      target: { value: "join" },
    });
    await waitFor(() =>
      expect(
        screen.getByTestId("command-palette-item-recipe:join"),
      ).toBeInTheDocument(),
    );
    // Click invokes — closes the palette.
    fireEvent.click(screen.getByTestId("command-palette-item-recipe:join"));
    await waitFor(
      () =>
        expect(
          screen.queryByTestId("command-palette"),
        ).not.toBeInTheDocument(),
      { timeout: 1000 },
    );

    // Reopen — empty input shows recent searches as tags.
    useCommandPaletteStore.setState({ isOpen: true });
    rerender(
      <Harness>
        <CommandPalette inlineForTesting forcePreviewVisible={false} />
      </Harness>,
    );
    await waitFor(() => {
      expect(
        screen.getByTestId("command-palette-recent-searches"),
      ).toBeInTheDocument();
      expect(screen.getByTestId("recent-search-join")).toBeInTheDocument();
    });
  });

  it("Help → Show keyboard shortcuts opens the sub-modal", async () => {
    useCommandPaletteStore.setState({ isOpen: true });
    render(
      <Harness>
        <CommandPalette inlineForTesting forcePreviewVisible={false} />
      </Harness>,
    );
    await waitFor(() =>
      expect(
        screen.getByTestId("command-palette-item-help:shortcuts"),
      ).toBeInTheDocument(),
    );
    fireEvent.click(
      screen.getByTestId("command-palette-item-help:shortcuts"),
    );
    await waitFor(
      () => {
        expect(
          screen.getByTestId("command-palette-shortcuts-modal"),
        ).toBeInTheDocument();
      },
      { timeout: 1000 },
    );
    // The modal lists every shortcut row — assert a representative subset.
    expect(
      screen.getByText("Open / close command palette"),
    ).toBeInTheDocument();
    expect(screen.getByText("Pin highlighted item")).toBeInTheDocument();
    expect(screen.getByText("Jump to section")).toBeInTheDocument();
  });

  it("match count line appears while typing", async () => {
    useCommandPaletteStore.setState({ isOpen: true });
    render(
      <Harness>
        <CommandPalette inlineForTesting forcePreviewVisible={false} />
      </Harness>,
    );
    await waitFor(() =>
      expect(
        screen.getByTestId("command-palette-item-recipe:filter-value"),
      ).toBeInTheDocument(),
    );
    fireEvent.change(screen.getByTestId("command-palette-input"), {
      target: { value: "filt" },
    });
    await waitFor(() => {
      const count = screen.getByTestId("command-palette-match-count");
      expect(count.textContent ?? "").toMatch(/result/);
    });
  });
});
