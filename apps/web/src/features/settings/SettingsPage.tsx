import { useSettingsStore } from "../../state/settingsStore";
import { useUiStore } from "../../state/uiStore";
import { LlmProviderSection } from "./LlmProviderSection";

/**
 * Full Settings surface. The gear-drawer (`SettingsDrawer`) stays for in-flow
 * quick toggles; this page is the canonical, deeper view that mirrors the
 * same store and exposes the rest of the surface area:
 *
 *   - Provider keys / aliases (read-only masked echo of the alias)
 *   - Theme
 *   - API base URL
 *   - Telemetry opt-out (placeholder)
 *
 * All form mutations route through the same `useSettingsStore` actions the
 * drawer uses, so the two surfaces never diverge.
 */
export function SettingsPage(): JSX.Element {
  const settings = useSettingsStore();
  const openDrawer = useUiStore((s) => s.openSettingsDrawer);

  const themePref: "light" | "dark" | "system" = settings.theme ?? "system";

  return (
    <section
      data-route="settings"
      data-testid="settings-page"
      style={{
        padding: "var(--space-6, 32px)",
        maxWidth: 880,
        margin: "0 auto",
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-6, 32px)",
      }}
    >
      <header style={{ display: "flex", alignItems: "baseline", gap: "var(--space-3, 12px)" }}>
        <h1 style={{ margin: 0, fontSize: "var(--text-2xl, 28px)" }}>Settings</h1>
        <button
          type="button"
          onClick={openDrawer}
          style={{
            border: "1px solid var(--border, #eaecf0)",
            background: "transparent",
            color: "var(--fg, #101828)",
            borderRadius: "var(--radius-md, 8px)",
            padding: "var(--space-1, 4px) var(--space-3, 12px)",
            fontSize: "var(--text-sm, 14px)",
            cursor: "pointer",
          }}
        >
          Open quick-edit drawer
        </button>
      </header>

      <p style={{ color: "var(--fg-muted, #5b6470)", margin: 0 }}>
        Full settings page. The gear icon in the header opens the same store as
        a quick-access drawer; this page is the canonical deeper surface.
      </p>

      <LlmProviderSection />

      <Card title="API connection" description="Where the Studio app calls the FastAPI backend.">
        <Row label="API base URL">
          <input
            type="url"
            value={settings.apiBaseUrl}
            onChange={(e) => settings.setApiBaseUrl(e.target.value)}
            aria-label="API base URL"
          />
        </Row>
      </Card>

      <Card title="Appearance" description="Theme follows the OS by default.">
        <Row label="Theme">
          <select
            value={themePref}
            onChange={(e) => {
              const v = e.target.value as "light" | "dark" | "system";
              if (v === "system") {
                useSettingsStore.setState({ theme: null });
              } else {
                settings.setTheme(v);
              }
            }}
            aria-label="Theme"
          >
            <option value="system">System</option>
            <option value="light">Light</option>
            <option value="dark">Dark</option>
          </select>
        </Row>
      </Card>

      <Card title="Telemetry" description="Anonymous usage events. No code or flow content is ever sent.">
        <Row label="Opt out">
          <label style={{ display: "inline-flex", gap: "var(--space-2, 8px)" }}>
            <input type="checkbox" disabled aria-label="Telemetry opt-out" />
            <span style={{ color: "var(--fg-muted, #5b6470)" }}>(coming soon)</span>
          </label>
        </Row>
      </Card>
    </section>
  );
}

function Card({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
}): JSX.Element {
  return (
    <section
      style={{
        border: "1px solid var(--border, #eaecf0)",
        borderRadius: "var(--radius-lg, 12px)",
        padding: "var(--space-5, 24px)",
        background: "var(--surface, #ffffff)",
        boxShadow: "var(--shadow-sm)",
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-3, 12px)",
      }}
    >
      <header>
        <h2 style={{ margin: 0, fontSize: "var(--text-md, 17px)" }}>{title}</h2>
        {description ? (
          <p style={{ margin: "var(--space-1, 4px) 0 0", color: "var(--fg-muted, #5b6470)", fontSize: "var(--text-sm, 14px)" }}>
            {description}
          </p>
        ) : null}
      </header>
      <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3, 12px)" }}>
        {children}
      </div>
    </section>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }): JSX.Element {
  return (
    <label
      style={{
        display: "grid",
        gridTemplateColumns: "180px 1fr",
        alignItems: "center",
        gap: "var(--space-3, 12px)",
        fontSize: "var(--text-sm, 14px)",
      }}
    >
      <span style={{ color: "var(--fg-muted, #5b6470)" }}>{label}</span>
      <span>{children}</span>
    </label>
  );
}
