import { Link } from "react-router-dom";
import { useFlowStore } from "../../state/flowStore";
import { ValidationPanel } from "./ValidationPanel";

/**
 * Top-level Validation route. The actual validation widget already lives in
 * `ValidationPanel` and is embedded inside `ConvertPage`; this page exposes
 * it as a stand-alone destination so it shows up under the sidebar's
 * Lifecycle cluster.
 */
export function ValidationPage(): JSX.Element {
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
        <h1 style={{ marginTop: 0 }}>Validation</h1>
        <p style={{ color: "var(--fg-muted, #5b6470)" }}>
          Convert a flow first to see DSS-readiness checks here.
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
      <h1 style={{ marginTop: 0 }}>Validation</h1>
      <ValidationPanel flow={flow as Record<string, unknown>} warnings={[]} defaultOpen />
    </section>
  );
}
