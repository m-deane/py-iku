import { Link } from "react-router-dom";
import { useFlowStore } from "../../state/flowStore";
import { ExportButtons } from "./ExportButtons";

/**
 * Top-level Export route. Re-uses the existing `ExportButtons` widget
 * (already used inside `ConvertPage`) and surfaces it as a stand-alone
 * destination under the sidebar's Lifecycle cluster.
 */
export function ExportPage(): JSX.Element {
  const flow = useFlowStore((s) => s.currentFlow);

  return (
    <section
      style={{
        padding: "var(--space-6, 32px)",
        maxWidth: 880,
        margin: "0 auto",
      }}
    >
      <h1 style={{ marginTop: 0 }}>Export</h1>
      {!flow ? (
        <>
          <p style={{ color: "var(--fg-muted, #5b6470)" }}>
            Convert a flow first, then come back here to export to ZIP, JSON,
            YAML, SVG, PNG, or PDF.
          </p>
          <Link
            to="/convert"
            style={{
              display: "inline-block",
              padding: "var(--space-2, 8px) var(--space-4, 16px)",
              background: "var(--accent, #0d9488)",
              color: "var(--accent-fg, #ffffff)",
              textDecoration: "none",
              borderRadius: "var(--radius-md, 8px)",
              fontWeight: "var(--font-weight-semibold, 600)",
            }}
          >
            Open Convert
          </Link>
        </>
      ) : (
        <ExportButtons flow={flow as Record<string, unknown>} />
      )}
    </section>
  );
}
