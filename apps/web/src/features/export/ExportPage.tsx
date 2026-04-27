import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useFlowStore } from "../../state/flowStore";
import { GithubPrModal } from "../github/GithubPrModal";
import { ExportButtons } from "./ExportButtons";

/**
 * Top-level Export route. Re-uses the existing `ExportButtons` widget
 * (already used inside `ConvertPage`) and surfaces it as a stand-alone
 * destination under the sidebar's Lifecycle cluster.
 *
 * Wave 4D adds an "Open as PR" button next to the export buttons that
 * pushes the flow JSON + a rendered SVG preview to a GitHub branch and
 * opens a PR.
 */
export function ExportPage(): JSX.Element {
  const flow = useFlowStore((s) => s.currentFlow);
  const [githubOpen, setGithubOpen] = useState(false);
  const [searchParams, setSearchParams] = useSearchParams();

  // Auto-open the PR modal when the user lands here from the Cmd+K palette.
  useEffect(() => {
    if (searchParams.get("openPr") === "1" && flow) {
      setGithubOpen(true);
      const next = new URLSearchParams(searchParams);
      next.delete("openPr");
      setSearchParams(next, { replace: true });
    }
  }, [searchParams, flow, setSearchParams]);

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
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
          <ExportButtons flow={flow as Record<string, unknown>} />
          <div style={{ display: "flex", gap: "var(--space-2)", alignItems: "center" }}>
            <button
              type="button"
              onClick={() => setGithubOpen(true)}
              data-testid="open-as-pr-button"
              style={{
                padding: "var(--space-2) var(--space-4)",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--border-strong)",
                background: "var(--surface-raised)",
                color: "var(--fg)",
                cursor: "pointer",
                fontWeight: "var(--font-weight-medium)",
                fontSize: "var(--text-sm)",
              }}
            >
              Open as PR…
            </button>
            <span style={{ fontSize: "var(--text-xs)", color: "var(--fg-muted)" }}>
              Push flow.json + flow.svg to a GitHub branch and open a PR.
            </span>
          </div>
          <GithubPrModal
            flow={githubOpen ? (flow as Record<string, unknown>) : null}
            onClose={() => setGithubOpen(false)}
          />
        </div>
      )}
    </section>
  );
}
