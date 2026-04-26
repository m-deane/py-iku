import { BrowserRouter, Navigate, Outlet, Route, Routes } from "react-router-dom";
import { AppLayout } from "../components/AppLayout";
import { ConvertPage } from "../features/conversion/ConvertPage";

function PlaceholderPage({
  title,
  milestone,
  disabled = false,
  hint,
}: {
  title: string;
  milestone: string;
  disabled?: boolean;
  hint?: string;
}): JSX.Element {
  return (
    <section style={{ padding: "2rem", maxWidth: 960, margin: "0 auto" }}>
      <h1 style={{ marginTop: 0 }}>{title}</h1>
      <p style={{ color: "var(--color-grid, #888)" }}>
        {milestone} will fill this in.
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
          Future feature — disabled
        </button>
      ) : null}
    </section>
  );
}

function HomePage(): JSX.Element {
  return (
    <section style={{ padding: "2rem", maxWidth: 960, margin: "0 auto" }}>
      <h1 style={{ marginTop: 0 }}>py-iku-studio</h1>
      <p>Convert pandas / numpy / scikit-learn code to Dataiku DSS recipes and flows.</p>
      <p style={{ color: "var(--color-grid, #888)" }}>M5/M6/M7 will fill this home page.</p>
      <a
        href="/convert"
        style={{
          display: "inline-block",
          marginTop: "1rem",
          padding: "0.5rem 1rem",
          background: "var(--color-connectionhover, #1976d2)",
          color: "white",
          textDecoration: "none",
          borderRadius: 6,
        }}
      >
        Paste Python →
      </a>
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
            element={<PlaceholderPage title="Flow viewer" milestone="M5" />}
          />
          <Route
            path="/catalog"
            element={<PlaceholderPage title="Catalog browser" milestone="M6" />}
          />
          <Route
            path="/diff"
            element={<PlaceholderPage title="Rule-vs-LLM diff" milestone="M5" />}
          />
          <Route
            path="/share/:token"
            element={<PlaceholderPage title="Read-only share view" milestone="M7" />}
          />
          <Route path="/audit" element={<PlaceholderPage title="Audit log" milestone="M7" />} />
          <Route
            path="/settings"
            element={<PlaceholderPage title="Settings" milestone="M4b/M5" />}
          />
          <Route
            path="/settings/connections"
            element={
              <PlaceholderPage
                title="DSS Connections"
                milestone="M7+"
                disabled
                hint="DSS write-back is a future capability — see docs/future-dss-writeback.md."
              />
            }
          />
          <Route
            path="*"
            element={
              <PlaceholderPage
                title="404 — Not Found"
                milestone="The current build"
                hint="Use the header to navigate."
              />
            }
          />
        </Route>
        <Route path="/index.html" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
