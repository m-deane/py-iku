import { useState } from "react";
import { toast } from "sonner";
import { JsonView } from "../../components/JsonView";
import {
  client,
  ApiError,
  type ConvertResponse,
  type DiffResponse,
  type NodeDiff,
} from "../../api/client";
import { useFlowStore } from "../../state/flowStore";

export interface DiffPageProps {
  /** Test seam — replaces `client.convert`. */
  convertImpl?: typeof client.convert;
  /** Test seam — replaces `client.diff`. */
  diffImpl?: typeof client.diff;
}

type DiffEntryKind = "added" | "removed" | "changed";

interface FlattenedEntry extends NodeDiff {
  kind: DiffEntryKind;
}

function flatten(diff: DiffResponse | null): FlattenedEntry[] {
  if (!diff) return [];
  const out: FlattenedEntry[] = [];
  for (const e of diff.added) out.push({ ...e, kind: "added" });
  for (const e of diff.removed) out.push({ ...e, kind: "removed" });
  for (const e of diff.changed) out.push({ ...e, kind: "changed" });
  return out;
}

export function DiffPage(props: DiffPageProps): JSX.Element {
  const code = useFlowStore((s) => s.currentCode);
  const setSelectedNodeId = useFlowStore((s) => s.setSelectedNodeId);
  const selectedNodeId = useFlowStore((s) => s.selectedNodeId);

  const [flowA, setFlowA] = useState<ConvertResponse | null>(null);
  const [flowB, setFlowB] = useState<ConvertResponse | null>(null);
  const [diff, setDiff] = useState<DiffResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const convertFn = props.convertImpl ?? client.convert;
  const diffFn = props.diffImpl ?? client.diff;

  const onCompare = async (): Promise<void> => {
    if (busy) return;
    if (!code || code.trim().length === 0) {
      toast.error("No code to compare", {
        description: "Paste or pick a snippet on the Convert page first.",
      });
      return;
    }
    setBusy(true);
    setError(null);
    setDiff(null);
    try {
      const [a, b] = await Promise.all([
        convertFn({ code, mode: "rule" }),
        convertFn({ code, mode: "llm" }),
      ]);
      setFlowA(a);
      setFlowB(b);
      const diffResult = await diffFn(a.flow, b.flow);
      setDiff(diffResult);
    } catch (err) {
      const message =
        err instanceof ApiError
          ? `${err.title}: ${err.detail ?? ""}`
          : err instanceof Error
            ? err.message
            : String(err);
      setError(message);
      toast.error("Diff failed", { description: message });
    } finally {
      setBusy(false);
    }
  };

  const entries = flatten(diff);

  return (
    <section
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "1rem",
        padding: "1rem 1.25rem",
        maxWidth: 1400,
        margin: "0 auto",
      }}
    >
      <header
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.75rem",
          flexWrap: "wrap",
        }}
      >
        <h1 style={{ margin: 0, fontSize: "1.25rem" }}>Rule vs LLM Diff</h1>
        <button
          type="button"
          data-testid="compare-button"
          onClick={onCompare}
          disabled={busy}
          style={{
            padding: "0.5rem 1rem",
            borderRadius: 6,
            border: 0,
            background: busy
              ? "var(--color-grid, #ccc)"
              : "var(--color-connectionhover, #1976d2)",
            color: "white",
            cursor: busy ? "not-allowed" : "pointer",
            fontWeight: 600,
          }}
        >
          {busy ? "Comparing…" : "Compare current rule vs LLM"}
        </button>
        {error ? (
          <div
            data-testid="diff-error"
            role="alert"
            style={{ color: "#b71c1c", fontSize: 13 }}
          >
            {error}
          </div>
        ) : null}
      </header>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "1rem",
        }}
      >
        <FlowPanel label="Rule" flow={flowA} side="a" />
        <FlowPanel label="LLM" flow={flowB} side="b" />
      </div>

      <div>
        <h2 style={{ fontSize: "1rem", margin: "0 0 0.5rem 0" }}>Per-node diff</h2>
        {!diff ? (
          <div
            data-testid="diff-empty"
            style={{
              padding: "1rem",
              border: "1px dashed var(--color-grid, #e0e0e0)",
              borderRadius: 6,
              color: "var(--color-grid, #888)",
              fontSize: 13,
            }}
          >
            Run a comparison to populate the diff list.
          </div>
        ) : entries.length === 0 ? (
          <div
            data-testid="diff-no-changes"
            style={{
              padding: "1rem",
              border: "1px solid var(--color-grid, #e0e0e0)",
              borderRadius: 6,
              fontSize: 13,
            }}
          >
            No differences found between rule and LLM flows.
          </div>
        ) : (
          <ul data-testid="diff-list" style={{ listStyle: "none", margin: 0, padding: 0 }}>
            {entries.map((e) => (
              <DiffEntryRow
                key={`${e.kind}-${e.id}`}
                entry={e}
                selected={selectedNodeId === e.id}
                onClick={() => setSelectedNodeId(e.id)}
              />
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}

function FlowPanel({
  label,
  flow,
  side,
}: {
  label: string;
  flow: ConvertResponse | null;
  side: "a" | "b";
}): JSX.Element {
  return (
    <div
      data-testid={`flow-panel-${side}`}
      style={{
        border: "1px solid var(--color-grid, #e0e0e0)",
        borderRadius: 6,
        padding: "0.75rem",
        minHeight: 240,
      }}
    >
      <div
        style={{
          fontSize: 11,
          textTransform: "uppercase",
          color: "var(--color-grid, #888)",
          marginBottom: "0.25rem",
          letterSpacing: "0.04em",
        }}
      >
        {label} flow
      </div>
      {flow ? (
        <>
          <div style={{ fontSize: 12, marginBottom: 6 }}>
            {flow.flow ? Object.keys((flow.flow as Record<string, unknown>) ?? {}).length : 0} top-level keys
          </div>
          <JsonView value={flow.flow} initialDepth={1} />
        </>
      ) : (
        <div style={{ color: "var(--color-grid, #888)", fontSize: 13 }}>
          (empty — run compare)
        </div>
      )}
    </div>
  );
}

function DiffEntryRow({
  entry,
  selected,
  onClick,
}: {
  entry: FlattenedEntry;
  selected: boolean;
  onClick: () => void;
}): JSX.Element {
  const kindColor: Record<DiffEntryKind, string> = {
    added: "#2e7d32",
    removed: "#b71c1c",
    changed: "#e65100",
  };
  return (
    <li
      data-testid={`diff-entry-${entry.id}`}
      data-kind={entry.kind}
      style={{
        display: "flex",
        alignItems: "center",
        gap: "0.5rem",
        padding: "0.4rem 0.6rem",
        borderRadius: 4,
        cursor: "pointer",
        background: selected ? "var(--color-grid, #f0f0f0)" : "transparent",
        marginBottom: 2,
      }}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onClick();
        }
      }}
    >
      <span
        style={{
          fontSize: 11,
          fontWeight: 600,
          textTransform: "uppercase",
          padding: "0.1rem 0.4rem",
          borderRadius: 3,
          background: kindColor[entry.kind],
          color: "white",
        }}
      >
        {entry.kind}
      </span>
      <code style={{ fontSize: 13 }}>{entry.id}</code>
      <span style={{ fontSize: 12, color: "var(--color-grid, #666)" }}>
        {entry.recipe_type_a && entry.recipe_type_b
          ? entry.recipe_type_a === entry.recipe_type_b
            ? entry.recipe_type_a
            : `${entry.recipe_type_a} → ${entry.recipe_type_b}`
          : entry.recipe_type_a ?? entry.recipe_type_b ?? ""}
      </span>
    </li>
  );
}
