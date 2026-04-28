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
const SettingsPage = lazy(() =>
  import("../features/settings/SettingsPage").then((m) => ({ default: m.SettingsPage })),
);
const CatalogPage = lazy(() =>
  import("../features/catalog/CatalogPage").then((m) => ({ default: m.CatalogPage })),
);
const InspectorPage = lazy(() =>
  import("../features/inspector/InspectorPage").then((m) => ({ default: m.InspectorPage })),
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
  hint,
}: {
  title: string;
  body: string;
  hint?: string;
}): JSX.Element {
  return (
    <section style={{ padding: "2rem", maxWidth: 960, margin: "0 auto" }}>
      <h1 style={{ marginTop: 0 }}>{title}</h1>
      <p style={{ color: "var(--fg-muted, #5b6470)" }}>
        {body}
        {hint ? ` ${hint}` : ""}
      </p>
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

          {/* Account cluster --------------------------------------------- */}
          <Route path="/settings" element={<SettingsPage />} />

          <Route
            path="*"
            element={
              <PlaceholderPage
                title="404 — Not Found"
                body="That route does not exist in this build."
                hint="Use the sidebar to navigate to Build, Library, or Account."
              />
            }
          />
        </Route>
        <Route path="/index.html" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
