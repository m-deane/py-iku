import { BrowserRouter, Navigate, Outlet, Route, Routes } from "react-router-dom";
import { AppLayout } from "../components/AppLayout";
import { AuditPage } from "../features/audit/AuditPage";
import { CatalogPage } from "../features/catalog/CatalogPage";
import { ConvertPage } from "../features/conversion/ConvertPage";
import { DiffPage } from "../features/diff/DiffPage";
import { SharePage } from "../features/share/SharePage";
import { SnippetGallery } from "../features/snippets/SnippetGallery";

function PlaceholderPage({
  title,
  body,
  disabled = false,
  hint,
}: {
  title: string;
  body: string;
  disabled?: boolean;
  hint?: string;
}): JSX.Element {
  return (
    <section style={{ padding: "2rem", maxWidth: 960, margin: "0 auto" }}>
      <h1 style={{ marginTop: 0 }}>{title}</h1>
      <p style={{ color: "var(--fg-muted, #5b6470)" }}>
        {body}
        {hint ? ` ${hint}` : ""}
      </p>
      {disabled ? (
        <button
          type="button"
          disabled
          aria-disabled="true"
          style={{
            marginTop: "1rem",
            padding: "0.5rem 1rem",
            opacity: 0.5,
            cursor: "not-allowed",
          }}
        >
          Disabled — not yet available
        </button>
      ) : null}
    </section>
  );
}

function HomePage(): JSX.Element {
  return (
    <section style={{ padding: "2rem", maxWidth: 960, margin: "0 auto" }}>
      <h1 style={{ marginTop: 0 }}>py-iku-studio</h1>
      <p style={{ fontSize: "1.05rem" }}>
        Convert pandas pipelines to Dataiku DSS flows. Review every recipe
        before you deploy.
      </p>
      <p style={{ color: "var(--fg-muted, #5b6470)", maxWidth: 640 }}>
        Paste a trade-capture script, a curve-build, or a counterparty rollup
        and Studio renders the equivalent Dataiku recipes, datasets, and DAG.
        Export as JSON, SVG, or a DSS-ready ZIP.
      </p>
      <div
        style={{
          display: "flex",
          gap: "0.75rem",
          marginTop: "1.25rem",
          flexWrap: "wrap",
        }}
      >
        <a
          href="/convert"
          style={{
            display: "inline-block",
            padding: "0.5rem 1rem",
            background: "var(--color-connectionhover, #1976d2)",
            color: "white",
            textDecoration: "none",
            borderRadius: 6,
            fontWeight: 600,
          }}
        >
          Paste Python →
        </a>
        <a
          href="/snippets"
          style={{
            display: "inline-block",
            padding: "0.5rem 1rem",
            border: "1px solid var(--color-grid, #e0e0e0)",
            color: "inherit",
            textDecoration: "none",
            borderRadius: 6,
          }}
        >
          Browse snippets
        </a>
        <a
          href="/catalog"
          style={{
            display: "inline-block",
            padding: "0.5rem 1rem",
            border: "1px solid var(--color-grid, #e0e0e0)",
            color: "inherit",
            textDecoration: "none",
            borderRadius: 6,
          }}
        >
          Open catalog
        </a>
      </div>
    </section>
  );
}

function RootLayout(): JSX.Element {
  return (
    <AppLayout>
      <Outlet />
    </AppLayout>
  );
}

export function AppRouter(): JSX.Element {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<RootLayout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/convert" element={<ConvertPage />} />
          <Route
            path="/flow/:id"
            element={
              <PlaceholderPage
                title="Flow viewer"
                body="Standalone flow viewer is not yet wired into this build. Open a flow from the Convert page to inspect its recipes and DAG."
              />
            }
          />
          <Route path="/catalog" element={<CatalogPage />} />
          <Route path="/diff" element={<DiffPage />} />
          <Route path="/snippets" element={<SnippetGallery />} />
          <Route path="/share/:token" element={<SharePage />} />
          <Route path="/audit" element={<AuditPage />} />
          <Route
            path="/settings"
            element={
              <PlaceholderPage
                title="Settings"
                body="Open the settings drawer from the gear icon in the header to configure provider, model alias, theme, and API base URL. A full settings page is on the roadmap."
              />
            }
          />
          <Route
            path="/settings/connections"
            element={
              <PlaceholderPage
                title="DSS Connections"
                body="Direct DSS write-back is a future capability. For now, export the flow as JSON or ZIP from the Convert page and import it into your DSS project."
                disabled
                hint="See docs/future-dss-writeback.md for the planned design."
              />
            }
          />
          <Route
            path="*"
            element={
              <PlaceholderPage
                title="404 — Not Found"
                body="That route does not exist in this build."
                hint="Use the header to navigate to Convert, Catalog, Snippets, Diff, or Audit."
              />
            }
          />
        </Route>
        <Route path="/index.html" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
