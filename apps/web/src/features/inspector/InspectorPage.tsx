import { Link } from "react-router-dom";
import { useFlowStore } from "../../state/flowStore";
import { NodeInspector } from "./NodeInspector";

/**
 * Standalone Inspector entry. The IA review flagged the inspector as one of
 * the modules buried inside `ConvertPage`; we surface a top-level route here
 * so it shows up in the sidebar's Build cluster, but the full extraction is
 * tracked separately. If there's no current flow we render an empty state
 * pointing the user at Convert.
 */
export function InspectorPage(): JSX.Element {
  const flow = useFlowStore((s) => s.currentFlow);

  if (!flow) {
    return (
      <section
        style={{
          padding: "var(--space-6, 32px)",
          maxWidth: 720,
          margin: "0 auto",
        }}
      >
        <h1 style={{ marginTop: 0 }}>Inspector</h1>
        <p style={{ color: "var(--fg-muted, #5b6470)" }}>
          No flow is loaded. Convert a script first, then return here to drill
          into individual recipes and processors.
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
      </section>
    );
  }

  return (
    <section style={{ padding: "var(--space-5, 24px)" }}>
      <h1 style={{ marginTop: 0 }}>Inspector</h1>
      <NodeInspector />
    </section>
  );
}
