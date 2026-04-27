/**
 * ColumnLineageOverlay
 *
 * Inspector-side panel that lets the user click a column and see every
 * recipe-edge that operates on (or derives) it. The dimming itself is done
 * by emitting the highlighted-edge / highlighted-node IDs into a shared
 * state store — `packages/flow-viz`'s FlowCanvas honours
 * `data-highlighted-id` attributes via the existing focus-mode CSS hook.
 *
 * Visual rules (per ui-tokens.css):
 *   - Highlighted edges: `var(--accent)` stroke, 2px.
 *   - Dimmed siblings: opacity 0.25 via `data-dim="true"` attribute.
 *   - Active column chip: filled with `var(--accent-bg-soft)`.
 */
import { useEffect, useMemo, useState } from "react";
import {
  client as defaultClient,
  type LineageResponse,
  type Client,
} from "../../api/client";

export interface ColumnLineageOverlayProps {
  flow: Record<string, unknown> | null;
  /** Test seam — pass a stubbed client without mocking modules. */
  clientImpl?: Client;
  /**
   * Notify the surrounding canvas about the set of highlighted recipe edges.
   * Caller wires this into FlowCanvas focus / dimming state.
   */
  onHighlight?: (lineage: LineageResponse | null) => void;
}

interface ColumnSuggestion {
  name: string;
  source: "schema" | "step";
}

function discoverColumns(flow: Record<string, unknown> | null): ColumnSuggestion[] {
  if (!flow) return [];
  const out = new Map<string, ColumnSuggestion>();
  const datasets = (flow.datasets as Array<Record<string, unknown>>) ?? [];
  for (const d of datasets) {
    const schema = (d.schema as Array<Record<string, unknown>>) ?? [];
    for (const c of schema) {
      const name = c?.name;
      if (typeof name === "string") out.set(name, { name, source: "schema" });
    }
  }
  const recipes = (flow.recipes as Array<Record<string, unknown>>) ?? [];
  for (const r of recipes) {
    const steps = (r.steps as Array<Record<string, unknown>>) ?? [];
    for (const s of steps) {
      const params = (s.params as Record<string, unknown>) ?? {};
      const cols = params.columns;
      if (Array.isArray(cols)) {
        for (const c of cols) {
          if (typeof c === "string" && !out.has(c))
            out.set(c, { name: c, source: "step" });
        }
      }
      for (const k of ["column", "output_column", "new_column"] as const) {
        const v = params[k];
        if (typeof v === "string" && !out.has(v)) out.set(v, { name: v, source: "step" });
      }
      const renamings = params.renamings as Array<Record<string, unknown>> | undefined;
      if (Array.isArray(renamings)) {
        for (const ren of renamings) {
          for (const k of ["from", "to"] as const) {
            const v = ren?.[k];
            if (typeof v === "string" && !out.has(v))
              out.set(v, { name: v, source: "step" });
          }
        }
      }
    }
  }
  return Array.from(out.values()).sort((a, b) => a.name.localeCompare(b.name));
}

export function ColumnLineageOverlay(
  props: ColumnLineageOverlayProps,
): JSX.Element | null {
  const { flow, onHighlight } = props;
  const apiClient = props.clientImpl ?? defaultClient;
  const [active, setActive] = useState<string | null>(null);
  const [lineage, setLineage] = useState<LineageResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const columns = useMemo(() => discoverColumns(flow), [flow]);

  // Push the lineage object out via callback when it changes — tests and
  // the canvas integration layer subscribe to this rather than re-running
  // the API call on their own.
  useEffect(() => {
    onHighlight?.(lineage);
  }, [lineage, onHighlight]);

  const onPick = async (name: string): Promise<void> => {
    if (!flow) return;
    if (active === name) {
      setActive(null);
      setLineage(null);
      return;
    }
    setActive(name);
    setError(null);
    setLoading(true);
    try {
      const result = await apiClient.lineage(flow, name);
      setLineage(result);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
      setLineage(null);
    } finally {
      setLoading(false);
    }
  };

  if (!flow || columns.length === 0) {
    return (
      <section
        data-testid="column-lineage-overlay"
        aria-label="Column lineage"
        style={{
          padding: "0.6rem 0.8rem",
          border: "1px dashed var(--border, #eaecf0)",
          borderRadius: "var(--radius-md, 6px)",
          color: "var(--fg-muted, #5b6470)",
          fontSize: "var(--text-xs, 12px)",
        }}
      >
        No columns to inspect — convert a flow with declared schemas first.
      </section>
    );
  }

  return (
    <section
      data-testid="column-lineage-overlay"
      aria-label="Column lineage"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "0.5rem",
        padding: "0.6rem 0.8rem",
        border: "1px solid var(--border, #eaecf0)",
        borderRadius: "var(--radius-md, 6px)",
        background: "var(--surface-raised, #f7f8fa)",
      }}
    >
      <header
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "0.5rem",
        }}
      >
        <strong style={{ fontSize: "var(--text-sm, 13px)" }}>Column lineage</strong>
        {active ? (
          <button
            type="button"
            data-testid="column-lineage-clear"
            onClick={() => onPick(active)}
            style={{
              padding: "0.15rem 0.5rem",
              borderRadius: "var(--radius-sm, 4px)",
              border: "1px solid var(--border-strong, #d0d5dd)",
              background: "transparent",
              color: "inherit",
              cursor: "pointer",
              fontSize: "var(--text-xs, 12px)",
            }}
          >
            Clear
          </button>
        ) : null}
      </header>

      <div
        role="listbox"
        aria-label="Pick a column to inspect"
        data-testid="column-lineage-columns"
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "0.3rem",
          maxHeight: 96,
          overflow: "auto",
        }}
      >
        {columns.map((c) => {
          const isActive = active === c.name;
          return (
            <button
              key={c.name}
              type="button"
              role="option"
              aria-selected={isActive}
              data-testid={`column-chip-${c.name}`}
              onClick={() => onPick(c.name)}
              style={{
                padding: "0.2rem 0.55rem",
                borderRadius: "var(--radius-pill, 9999px)",
                border: "1px solid var(--border-strong, #d0d5dd)",
                background: isActive
                  ? "var(--accent-bg-soft, #ccfbf1)"
                  : "var(--surface, #fff)",
                color: isActive ? "var(--accent-hover, #0f766e)" : "inherit",
                cursor: "pointer",
                fontSize: "var(--text-xs, 12px)",
                fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
              }}
            >
              {c.name}
            </button>
          );
        })}
      </div>

      {loading ? (
        <div
          data-testid="column-lineage-loading"
          style={{ fontSize: "var(--text-xs, 12px)", color: "var(--fg-muted, #5b6470)" }}
        >
          Loading lineage…
        </div>
      ) : null}

      {error ? (
        <div
          role="alert"
          data-testid="column-lineage-error"
          style={{
            fontSize: "var(--text-xs, 12px)",
            color: "#b71c1c",
          }}
        >
          {error}
        </div>
      ) : null}

      {lineage ? <LineageSummary lineage={lineage} /> : null}
    </section>
  );
}

function LineageSummary({ lineage }: { lineage: LineageResponse }): JSX.Element {
  return (
    <div
      data-testid="column-lineage-summary"
      style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}
    >
      {lineage.aliases.length > 1 ? (
        <div style={{ fontSize: "var(--text-xs, 12px)" }}>
          <span style={{ color: "var(--fg-muted, #5b6470)" }}>Aliases:</span>{" "}
          <code data-testid="lineage-aliases">{lineage.aliases.join(" → ")}</code>
        </div>
      ) : null}

      <div
        data-testid="lineage-edges"
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "0.2rem",
          fontSize: "var(--text-xs, 12px)",
          fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
        }}
      >
        {lineage.edges.map((e, i) => (
          <div
            key={`${e.recipe_id}-${e.input_dataset}-${e.output_dataset}-${i}`}
            data-testid={`lineage-edge-${e.recipe_id}`}
            data-recipe-id={e.recipe_id}
            data-source={e.input_dataset}
            data-target={e.output_dataset}
            style={{
              padding: "0.2rem 0.4rem",
              borderLeft: "3px solid var(--accent, #0d9488)",
              background: "var(--surface, #fff)",
            }}
          >
            <strong>{e.recipe_id}</strong>
            <span style={{ color: "var(--fg-muted, #5b6470)" }}>
              {" "}
              · {e.kind} · {e.input_dataset} → {e.output_dataset}
            </span>
          </div>
        ))}
        {lineage.edges.length === 0 ? (
          <span style={{ color: "var(--fg-muted, #5b6470)" }}>
            No upstream / downstream edges touch this column.
          </span>
        ) : null}
      </div>
    </div>
  );
}
