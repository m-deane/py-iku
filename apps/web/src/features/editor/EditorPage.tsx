import { Link } from "react-router-dom";
import { RecentsRail } from "../../components/RecentsRail";

/**
 * Standalone editor entry. The full editor experience currently lives inside
 * `ConvertPage`; this page renders the Recents/Pinned rail next to a CTA that
 * routes the user into Convert with their picked source pre-loaded.
 */
export function EditorPage(): JSX.Element {
  return (
    <div style={{ display: "flex", height: "100%", minHeight: "60vh" }}>
      <RecentsRail navigateTo="/convert" />
      <section
        style={{
          flex: 1,
          padding: "var(--space-6, 32px)",
          display: "flex",
          flexDirection: "column",
          gap: "var(--space-4, 16px)",
        }}
      >
        <h1 style={{ margin: 0, fontSize: "var(--text-2xl, 28px)" }}>Editor</h1>
        <p style={{ color: "var(--fg-muted, #5b6470)", margin: 0, maxWidth: 640 }}>
          Pick a flow from the rail to load it into the editor, or jump
          straight into a fresh Convert session.
        </p>
        <div>
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
        </div>
      </section>
    </div>
  );
}
