import { useEffect, useMemo, useState } from "react";
import {
  client as defaultClient,
  type PluginCatalogEntry,
  type PluginCatalogResponse,
} from "../../api/client";
import { PluginCard } from "./PluginCard";
import { PluginDetailDrawer } from "./PluginDetailDrawer";
import { useInstalledPlugins } from "./useInstalledPlugins";

type Tab = "catalog" | "installed";

export interface PluginMarketplacePageProps {
  /** Test seam — swap in a stub fetcher. */
  clientImpl?: {
    listPluginCatalog: typeof defaultClient.listPluginCatalog;
    listPluginsInstalled: typeof defaultClient.listPluginsInstalled;
  };
  /** Test seam — preselect tab. */
  initialTab?: Tab;
}

/**
 * Plugin marketplace page (route: ``/plugins``). Sits in the Library cluster
 * next to Templates / Snippets / GREL Formulas.
 *
 * Two tabs:
 *  * **Catalog** — bundled metadata served by ``GET /plugins/catalog``.
 *    Each card has an Install button that opens an info drawer with a
 *    copy-pastable ``pip install`` command. v1 is information-only.
 *  * **Installed** — live introspection of the global ``PluginRegistry``
 *    from ``GET /plugins/installed`` (recipe / processor mappings + plugin
 *    metadata).
 */
export function PluginMarketplacePage(
  props: PluginMarketplacePageProps = {},
): JSX.Element {
  const cli = props.clientImpl ?? defaultClient;
  const [tab, setTab] = useState<Tab>(props.initialTab ?? "catalog");
  const [catalog, setCatalog] = useState<PluginCatalogResponse | null>(null);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [catalogLoading, setCatalogLoading] = useState(false);
  const [active, setActive] = useState<PluginCatalogEntry | null>(null);
  const [query, setQuery] = useState("");

  const installed = useInstalledPlugins({
    clientImpl: cli,
    enabled: tab === "installed",
  });

  useEffect(() => {
    let cancelled = false;
    setCatalogLoading(true);
    setCatalogError(null);
    cli
      .listPluginCatalog()
      .then((res) => {
        if (!cancelled) setCatalog(res);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setCatalogError(err instanceof Error ? err.message : String(err));
        }
      })
      .finally(() => {
        if (!cancelled) setCatalogLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [cli]);

  const filtered = useMemo<PluginCatalogEntry[]>(() => {
    if (!catalog) return [];
    const q = query.trim().toLowerCase();
    if (!q) return catalog.entries;
    return catalog.entries.filter((p) => {
      const hay = [
        p.name,
        p.description,
        p.author,
        ...p.tags,
        ...p.supported_recipes,
        ...p.supported_processors,
      ]
        .join(" ")
        .toLowerCase();
      return hay.includes(q);
    });
  }, [catalog, query]);

  return (
    <section
      data-testid="plugin-marketplace-page"
      style={{
        padding: "var(--space-6, 32px)",
        maxWidth: 1200,
        margin: "0 auto",
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-4, 16px)",
      }}
    >
      <header style={{ display: "flex", alignItems: "baseline", gap: 12 }}>
        <h1 style={{ margin: 0, fontSize: "var(--text-2xl, 28px)" }}>Plugins</h1>
        <span style={{ color: "var(--fg-muted, #5b6470)", fontSize: "var(--text-sm, 14px)" }}>
          Extend py-iku with third-party recipe handlers and processor mappings.
        </span>
      </header>

      <nav
        role="tablist"
        aria-label="Plugin tabs"
        style={{
          display: "flex",
          gap: 4,
          borderBottom: "1px solid var(--border, #eaecf0)",
        }}
      >
        <TabButton
          tab="catalog"
          active={tab === "catalog"}
          onClick={() => setTab("catalog")}
        >
          Catalog{catalog ? ` (${catalog.count})` : ""}
        </TabButton>
        <TabButton
          tab="installed"
          active={tab === "installed"}
          onClick={() => setTab("installed")}
        >
          Installed
        </TabButton>
      </nav>

      {tab === "catalog" ? (
        <>
          <input
            type="search"
            data-testid="plugin-marketplace-search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search plugins by name, tag, or recipe…"
            style={{
              padding: "var(--space-2, 8px) var(--space-3, 12px)",
              border: "1px solid var(--border, #eaecf0)",
              borderRadius: "var(--radius-md, 6px)",
              fontSize: "var(--text-sm, 14px)",
            }}
          />

          {catalogLoading ? (
            <p data-testid="plugin-marketplace-loading">Loading catalog…</p>
          ) : null}
          {catalogError ? (
            <p
              role="alert"
              data-testid="plugin-marketplace-error"
              style={{ color: "var(--danger, #b91c1c)" }}
            >
              {catalogError}
            </p>
          ) : null}

          <div
            data-testid="plugin-marketplace-grid"
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
              gap: "var(--space-4, 16px)",
            }}
          >
            {filtered.map((p) => (
              <PluginCard
                key={p.name}
                plugin={p}
                onSelect={(plugin) => setActive(plugin)}
              />
            ))}
          </div>
        </>
      ) : (
        <InstalledPanel installed={installed} />
      )}

      <PluginDetailDrawer plugin={active} onClose={() => setActive(null)} />
    </section>
  );
}

function TabButton(props: {
  tab: Tab;
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}): JSX.Element {
  return (
    <button
      type="button"
      role="tab"
      aria-selected={props.active}
      data-testid={`plugin-tab-${props.tab}`}
      onClick={props.onClick}
      style={{
        padding: "var(--space-2, 8px) var(--space-3, 16px)",
        border: "none",
        borderBottom: props.active
          ? "2px solid var(--accent, #0d9488)"
          : "2px solid transparent",
        background: "transparent",
        cursor: "pointer",
        fontSize: "var(--text-sm, 14px)",
        fontWeight: props.active ? 600 : 500,
        color: props.active ? "var(--fg, #101828)" : "var(--fg-muted, #5b6470)",
        marginBottom: -1,
      }}
    >
      {props.children}
    </button>
  );
}

function InstalledPanel({
  installed,
}: {
  installed: ReturnType<typeof useInstalledPlugins>;
}): JSX.Element {
  if (installed.loading) {
    return <p data-testid="plugin-installed-loading">Loading installed plugins…</p>;
  }
  if (installed.error) {
    return (
      <p
        role="alert"
        data-testid="plugin-installed-error"
        style={{ color: "var(--danger, #b91c1c)" }}
      >
        {installed.error}
      </p>
    );
  }
  const data = installed.data;
  if (!data) {
    return <p>No data.</p>;
  }
  const recipeRows = Object.entries(data.recipe_mappings);
  const processorRows = Object.entries(data.processor_mappings);
  const pluginRows = Object.entries(data.plugins);

  return (
    <div
      data-testid="plugin-installed-panel"
      style={{ display: "flex", flexDirection: "column", gap: "var(--space-4, 16px)" }}
    >
      <Section title={`Plugins registered (${pluginRows.length})`} testId="installed-plugins">
        {pluginRows.length === 0 ? (
          <p style={mutedTip}>No plugins registered. Install one from the Catalog tab.</p>
        ) : (
          <ul style={{ margin: 0, padding: 0, listStyle: "none" }}>
            {pluginRows.map(([name, meta]) => (
              <li key={name} style={listItemStyle}>
                <strong>{name}</strong>{" "}
                <span style={{ color: "var(--fg-muted, #5b6470)" }}>
                  v{(meta as Record<string, unknown>).version as string} —{" "}
                  {(meta as Record<string, unknown>).description as string}
                </span>
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section
        title={`Recipe mappings (${recipeRows.length})`}
        testId="installed-recipe-mappings"
      >
        {recipeRows.length === 0 ? (
          <p style={mutedTip}>No custom recipe mappings.</p>
        ) : (
          <Table
            headers={["pandas method", "Dataiku recipe"]}
            rows={recipeRows.map(([k, v]) => [k, v])}
          />
        )}
      </Section>

      <Section
        title={`Processor mappings (${processorRows.length})`}
        testId="installed-processor-mappings"
      >
        {processorRows.length === 0 ? (
          <p style={mutedTip}>No custom processor mappings.</p>
        ) : (
          <Table
            headers={["pandas method", "Dataiku processor"]}
            rows={processorRows.map(([k, v]) => [k, v])}
          />
        )}
      </Section>

      <Section
        title={`Method handlers (${data.method_handlers.length})`}
        testId="installed-method-handlers"
      >
        {data.method_handlers.length === 0 ? (
          <p style={mutedTip}>No custom method handlers.</p>
        ) : (
          <ul style={{ margin: 0, padding: "0 0 0 1.25rem" }}>
            {data.method_handlers.map((m) => (
              <li key={m}>{m}</li>
            ))}
          </ul>
        )}
      </Section>
    </div>
  );
}

function Section({
  title,
  children,
  testId,
}: {
  title: string;
  children: React.ReactNode;
  testId?: string;
}): JSX.Element {
  return (
    <section
      data-testid={testId}
      style={{
        border: "1px solid var(--border, #eaecf0)",
        borderRadius: "var(--radius-md, 8px)",
        padding: "var(--space-3, 12px) var(--space-4, 16px)",
      }}
    >
      <h3
        style={{
          margin: "0 0 var(--space-2, 8px) 0",
          fontSize: "var(--text-sm, 14px)",
          color: "var(--fg-muted, #5b6470)",
          textTransform: "uppercase",
          letterSpacing: "0.06em",
        }}
      >
        {title}
      </h3>
      {children}
    </section>
  );
}

function Table({
  headers,
  rows,
}: {
  headers: string[];
  rows: string[][];
}): JSX.Element {
  return (
    <table
      style={{
        width: "100%",
        borderCollapse: "collapse",
        fontSize: "var(--text-sm, 14px)",
      }}
    >
      <thead>
        <tr>
          {headers.map((h) => (
            <th
              key={h}
              style={{
                textAlign: "left",
                padding: "4px 8px",
                fontWeight: 600,
                color: "var(--fg-muted, #5b6470)",
                fontSize: "var(--text-xs, 12px)",
                textTransform: "uppercase",
              }}
            >
              {h}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr key={i} style={{ borderTop: "1px solid var(--border, #eaecf0)" }}>
            {row.map((cell, j) => (
              <td
                key={j}
                style={{
                  padding: "4px 8px",
                  fontFamily: j === 1 ? "var(--font-mono, monospace)" : undefined,
                }}
              >
                {cell}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

const mutedTip: React.CSSProperties = {
  margin: 0,
  fontSize: "var(--text-sm, 14px)",
  color: "var(--fg-muted, #5b6470)",
};

const listItemStyle: React.CSSProperties = {
  padding: "var(--space-2, 6px) 0",
  fontSize: "var(--text-sm, 14px)",
  borderBottom: "1px dashed var(--border, #eaecf0)",
};
