import { useState } from "react";

/**
 * Tiny recursive JSON pretty-printer. Used as a placeholder for the proper
 * flow visualization (which lands in M5 via `packages/flow-viz`). Keep this
 * lean — no third-party syntax highlighter.
 */
export interface JsonViewProps {
  value: unknown;
  /** Initial expand depth. Anything deeper renders collapsed. */
  initialDepth?: number;
}

export function JsonView({ value, initialDepth = 2 }: JsonViewProps): JSX.Element {
  return (
    <pre
      style={{
        margin: 0,
        padding: "0.75rem",
        fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, monospace",
        fontSize: 12,
        lineHeight: 1.5,
        background: "var(--color-grid, #f5f5f5)",
        color: "var(--color-fg, #212121)",
        borderRadius: 6,
        overflow: "auto",
        maxHeight: "60vh",
      }}
    >
      <Node value={value} depth={0} initialDepth={initialDepth} />
    </pre>
  );
}

function Node({
  value,
  depth,
  initialDepth,
}: {
  value: unknown;
  depth: number;
  initialDepth: number;
}): JSX.Element {
  if (value === null) return <Token text="null" kind="null" />;
  if (typeof value === "boolean") return <Token text={String(value)} kind="bool" />;
  if (typeof value === "number") return <Token text={String(value)} kind="number" />;
  if (typeof value === "string") return <Token text={JSON.stringify(value)} kind="string" />;
  if (Array.isArray(value)) {
    return <ArrayNode items={value} depth={depth} initialDepth={initialDepth} />;
  }
  if (typeof value === "object") {
    return <ObjectNode entries={Object.entries(value as Record<string, unknown>)} depth={depth} initialDepth={initialDepth} />;
  }
  return <Token text={String(value)} kind="other" />;
}

function ArrayNode({
  items,
  depth,
  initialDepth,
}: {
  items: unknown[];
  depth: number;
  initialDepth: number;
}): JSX.Element {
  const [open, setOpen] = useState(depth < initialDepth);
  if (items.length === 0) return <span>[]</span>;
  if (!open) {
    return (
      <span>
        <Toggle open={open} onClick={() => setOpen(true)} /> [{items.length}]
      </span>
    );
  }
  return (
    <span>
      <Toggle open={open} onClick={() => setOpen(false)} /> [
      {items.map((item, i) => (
        <div key={i} style={{ paddingLeft: 16 }}>
          <Node value={item} depth={depth + 1} initialDepth={initialDepth} />
          {i < items.length - 1 ? "," : ""}
        </div>
      ))}
      <span>]</span>
    </span>
  );
}

function ObjectNode({
  entries,
  depth,
  initialDepth,
}: {
  entries: [string, unknown][];
  depth: number;
  initialDepth: number;
}): JSX.Element {
  const [open, setOpen] = useState(depth < initialDepth);
  if (entries.length === 0) return <span>{"{}"}</span>;
  if (!open) {
    return (
      <span>
        <Toggle open={open} onClick={() => setOpen(true)} /> {"{"}
        {entries.length} keys{"}"}
      </span>
    );
  }
  return (
    <span>
      <Toggle open={open} onClick={() => setOpen(false)} /> {"{"}
      {entries.map(([k, v], i) => (
        <div key={k} style={{ paddingLeft: 16 }}>
          <span style={{ color: "var(--color-recipe-join-light-text, #1565c0)" }}>
            {JSON.stringify(k)}
          </span>
          : <Node value={v} depth={depth + 1} initialDepth={initialDepth} />
          {i < entries.length - 1 ? "," : ""}
        </div>
      ))}
      <span>{"}"}</span>
    </span>
  );
}

function Toggle({ open, onClick }: { open: boolean; onClick: () => void }): JSX.Element {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={open ? "Collapse" : "Expand"}
      style={{
        display: "inline-block",
        width: 14,
        height: 14,
        lineHeight: "12px",
        padding: 0,
        textAlign: "center",
        border: 0,
        background: "transparent",
        color: "inherit",
        cursor: "pointer",
        fontSize: 10,
      }}
    >
      {open ? "▾" : "▸"}
    </button>
  );
}

function Token({ text, kind }: { text: string; kind: string }): JSX.Element {
  const colorMap: Record<string, string> = {
    string: "var(--color-recipe-grouping-light-text, #2e7d32)",
    number: "var(--color-recipe-window-light-text, #00838f)",
    bool: "var(--color-recipe-prepare-light-text, #e65100)",
    null: "var(--color-grid, #888)",
    other: "inherit",
  };
  return <span style={{ color: colorMap[kind] ?? "inherit" }}>{text}</span>;
}
