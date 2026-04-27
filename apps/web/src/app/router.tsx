import { lazy, Suspense } from "react";
import { BrowserRouter, Navigate, Outlet, Route, Routes } from "react-router-dom";
import { AppLayout } from "../components/AppLayout";
import { RouteSkeleton } from "../components/RouteSkeleton";
import { RecentsRail } from "../components/RecentsRail";

// Lazy chunks — anything past the editor/landing first paint loads on demand.
// Each `lazy(() => import(...))` is its own Vite chunk in `dist/assets/`.
const ConvertPage = lazy(() =>
  import("../features/conversion/ConvertPage").then((m) => ({ default: m.ConvertPage })),
);
const DiffPage = lazy(() =>
  import("../features/diff/DiffPage").then((m) => ({ default: m.DiffPage })),
);
const AuditPage = lazy(() =>
  import("../features/audit/AuditPage").then((m) => ({ default: m.AuditPage })),
);
const SettingsPage = lazy(() =>
  import("../features/settings/SettingsPage").then((m) => ({ default: m.SettingsPage })),
);
const CatalogPage = lazy(() =>
  import("../features/catalog/CatalogPage").then((m) => ({ default: m.CatalogPage })),
);
const SnippetGallery = lazy(() =>
  import("../features/snippets/SnippetGallery").then((m) => ({ default: m.SnippetGallery })),
);
const ValidationPage = lazy(() =>
  import("../features/validation/ValidationPage").then((m) => ({
    default: m.ValidationPage,
  })),
);
const ExportPage = lazy(() =>
  import("../features/export/ExportPage").then((m) => ({ default: m.ExportPage })),
);
const DeployPage = lazy(() =>
  import("../features/deploy/DeployPage").then((m) => ({ default: m.DeployPage })),
);
const SharePage = lazy(() =>
  import("../features/share/SharePage").then((m) => ({ default: m.SharePage })),
);
const InspectorPage = lazy(() =>
  import("../features/inspector/InspectorPage").then((m) => ({ default: m.InspectorPage })),
);
const TemplatesPage = lazy(() =>
  import("../features/templates/TemplatesPage").then((m) => ({ default: m.TemplatesPage })),
);
const LlmHistoryPage = lazy(() =>
  import("../features/llm-history/LlmHistoryPage").then((m) => ({
    default: m.LlmHistoryPage,
  })),
);
const GrelLibraryPage = lazy(() =>
  import("../features/grel-library/GrelLibraryPage").then((m) => ({
    default: m.GrelLibraryPage,
  })),
);
const LmpBrowserPage = lazy(() =>
  import("../features/lmp-browser/LmpBrowserPage").then((m) => ({
    default: m.LmpBrowserPage,
  })),
);
const CurveDiffPage = lazy(() =>
  import("../features/curve-diff/CurveDiffPage").then((m) => ({
    default: m.CurveDiffPage,
  })),
);
// FlowViewer is a route-level wrapper rendered inline (no separate page module
// today). We still split it so /flow/:id loads on demand.
const FlowViewer = lazy(() =>
  import("../features/conversion/FlowViewer").then((m) => ({ default: m.FlowViewer })),
);

// First-paint critical — keep eager. The Editor is the user's landing surface
// once the first route is opened, so it never benefits from a Suspense gap.
import { EditorPage } from "../features/editor/EditorPage";

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
    <div style={{ display: "flex", minHeight: "60vh" }}>
      <RecentsRail navigateTo="/convert" />
      <section style={{ padding: "2rem", maxWidth: 960, flex: 1 }}>
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
              background: "var(--accent, #0d9488)",
              color: "var(--accent-fg, #ffffff)",
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
              border: "1px solid var(--border, #eaecf0)",
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
              border: "1px solid var(--border, #eaecf0)",
              color: "inherit",
              textDecoration: "none",
              borderRadius: 6,
            }}
          >
            Open catalog
          </a>
        </div>
      </section>
    </div>
  );
}

function RootLayout(): JSX.Element {
  return (
    <AppLayout>
      <Suspense fallback={<RouteSkeleton />}>
        <Outlet />
      </Suspense>
    </AppLayout>
  );
}

export function AppRouter(): JSX.Element {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<RootLayout />}>
          {/* Build cluster ----------------------------------------------- */}
          <Route path="/" element={<HomePage />} />
          <Route path="/editor" element={<EditorPage />} />
          <Route path="/convert" element={<ConvertPage />} />
          <Route path="/inspector" element={<InspectorPage />} />
          <Route path="/flow/:id" element={<FlowViewer />} />

          {/* Library cluster --------------------------------------------- */}
          <Route path="/catalog" element={<CatalogPage />} />
          <Route path="/snippets" element={<SnippetGallery />} />
          <Route path="/templates" element={<TemplatesPage />} />
          <Route path="/grel" element={<GrelLibraryPage />} />
          <Route path="/lmp" element={<LmpBrowserPage />} />

          {/* Lifecycle cluster ------------------------------------------- */}
          <Route path="/diff" element={<DiffPage />} />
          <Route path="/diff/curves" element={<CurveDiffPage />} />
          <Route path="/validation" element={<ValidationPage />} />
          <Route path="/export" element={<ExportPage />} />
          <Route path="/deploy" element={<DeployPage />} />
          <Route path="/share/:token" element={<SharePage />} />
          <Route
            path="/share"
            element={
              <PlaceholderPage
                title="Share"
                body="Save a flow first to generate a shareable link. Open Convert, run a conversion, then click the share button on the result panel."
              />
            }
          />
          <Route path="/audit" element={<AuditPage />} />

          {/* Account cluster --------------------------------------------- */}
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/llm-history" element={<LlmHistoryPage />} />
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
                hint="Use the sidebar to navigate to Build, Library, Lifecycle, or Account."
              />
            }
          />
        </Route>
        <Route path="/index.html" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
