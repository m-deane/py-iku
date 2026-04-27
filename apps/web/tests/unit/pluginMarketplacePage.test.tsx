import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { PluginMarketplacePage } from "../../src/features/plugin-marketplace/PluginMarketplacePage";
import type {
  PluginCatalogResponse,
  PluginsInstalledResponse,
} from "../../src/api/client";

const CATALOG: PluginCatalogResponse = {
  count: 2,
  entries: [
    {
      name: "py-iku-trading-domain",
      version: "1.0.0",
      description: "Trade-blotter handlers (safe_fill, inner_match, etc.).",
      author: "py-iku core team",
      supported_recipes: ["JOIN", "TOP_N"],
      supported_processors: ["FILL_EMPTY_WITH_VALUE"],
      source_code_url: "https://example.com/trading",
      install_command: "pip install py-iku-trading-domain",
      tags: ["trading", "trade-blotter"],
    },
    {
      name: "py-iku-time-series",
      version: "0.5.0",
      description: "First-class .rolling / .resample / .shift handlers.",
      author: "py-iku core team",
      supported_recipes: ["WINDOW"],
      supported_processors: [],
      source_code_url: "https://example.com/ts",
      install_command: "pip install py-iku-time-series",
      tags: ["time-series", "WINDOW"],
    },
  ],
};

const INSTALLED: PluginsInstalledResponse = {
  plugins: {
    "demo-plugin": { version: "0.1.0", description: "Test plugin." },
  },
  recipe_mappings: { my_join: "join" },
  processor_mappings: { my_fill: "fill_empty_with_value" },
  method_handlers: ["safe_fill"],
  recipe_handlers: ["join"],
  processor_handlers: [],
};

function stub() {
  return {
    listPluginCatalog: vi.fn(async () => CATALOG),
    listPluginsInstalled: vi.fn(async () => INSTALLED),
  };
}

describe("<PluginMarketplacePage />", () => {
  it("renders one card per catalog entry", async () => {
    const cli = stub();
    render(<PluginMarketplacePage clientImpl={cli} />);
    await waitFor(() => {
      expect(screen.getByTestId("plugin-card-py-iku-trading-domain")).toBeInTheDocument();
    });
    expect(screen.getByTestId("plugin-card-py-iku-time-series")).toBeInTheDocument();
  });

  it("clicking Install opens the detail drawer with the pip command", async () => {
    const cli = stub();
    render(<PluginMarketplacePage clientImpl={cli} />);
    await waitFor(() =>
      expect(screen.getByTestId("plugin-card-py-iku-trading-domain")).toBeInTheDocument(),
    );
    fireEvent.click(screen.getByTestId("plugin-install-py-iku-trading-domain"));
    expect(screen.getByTestId("plugin-detail-drawer")).toBeInTheDocument();
    expect(screen.getByTestId("plugin-install-command")).toHaveTextContent(
      "pip install py-iku-trading-domain",
    );
  });

  it("filters the catalog by free-text search", async () => {
    const cli = stub();
    render(<PluginMarketplacePage clientImpl={cli} />);
    await waitFor(() =>
      expect(screen.getByTestId("plugin-card-py-iku-trading-domain")).toBeInTheDocument(),
    );
    fireEvent.change(screen.getByTestId("plugin-marketplace-search"), {
      target: { value: "rolling" },
    });
    await waitFor(() => {
      expect(screen.queryByTestId("plugin-card-py-iku-trading-domain")).toBeNull();
    });
    expect(screen.getByTestId("plugin-card-py-iku-time-series")).toBeInTheDocument();
  });

  it("Installed tab fetches /plugins/installed and renders mappings", async () => {
    const cli = stub();
    render(<PluginMarketplacePage clientImpl={cli} initialTab="installed" />);
    await waitFor(() => {
      expect(screen.getByTestId("plugin-installed-panel")).toBeInTheDocument();
    });
    expect(cli.listPluginsInstalled).toHaveBeenCalled();
    expect(screen.getByTestId("installed-plugins")).toHaveTextContent("demo-plugin");
    expect(screen.getByTestId("installed-recipe-mappings")).toHaveTextContent("my_join");
  });
});
