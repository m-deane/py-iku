import { useEffect, useState } from "react";
import type { PluginCatalogEntry } from "../../api/client";

export interface PluginDetailDrawerProps {
  plugin: PluginCatalogEntry | null;
  onClose: () => void;
}

/**
 * Information-only "Install" drawer. Shows the canonical
 * ``pip install <pkg>`` command with a copy-button; v1 doesn't actually
 * invoke pip because that requires a package registry. A future Wave can
 * replace the copy button with a backend ``POST /plugins/install`` call.
 */
export function PluginDetailDrawer({
  plugin,
  onClose,
}: PluginDetailDrawerProps): JSX.Element | null {
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!plugin) return;
    const onKey = (e: KeyboardEvent): void => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [plugin, onClose]);

  useEffect(() => {
    setCopied(false);
  }, [plugin?.name]);

  if (!plugin) return null;

  const handleCopy = async (): Promise<void> => {
    if (typeof navigator === "undefined" || !navigator.clipboard) return;
    try {
      await navigator.clipboard.writeText(plugin.install_command);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      // best-effort; clipboard can fail in tests
    }
  };

  return (
    <>
      <div
        onClick={onClose}
        data-testid="plugin-detail-scrim"
        aria-hidden
        style={{
          position: "fixed",
          inset: 0,
          background: "rgba(0,0,0,0.4)",
          zIndex: 50,
        }}
      />
      <aside
        role="dialog"
        aria-modal="true"
        aria-labelledby="plugin-detail-title"
        data-testid="plugin-detail-drawer"
        style={{
          position: "fixed",
          top: 0,
          right: 0,
          width: "min(560px, 96vw)",
          height: "100vh",
          background: "var(--surface, #ffffff)",
          borderLeft: "1px solid var(--border, #eaecf0)",
          boxShadow: "-12px 0 36px rgba(0,0,0,0.10)",
          display: "flex",
          flexDirection: "column",
          zIndex: 51,
        }}
      >
        <header
          style={{
            padding: "var(--space-4, 16px)",
            borderBottom: "1px solid var(--border, #eaecf0)",
            display: "flex",
            justifyContent: "space-between",
            gap: 8,
          }}
        >
          <div>
            <h2
              id="plugin-detail-title"
              style={{
                margin: 0,
                fontSize: "var(--text-xl, 20px)",
              }}
            >
              {plugin.name}
            </h2>
            <p
              style={{
                margin: 0,
                fontSize: "var(--text-xs, 12px)",
                color: "var(--fg-muted, #5b6470)",
              }}
            >
              v{plugin.version} · {plugin.author}
            </p>
          </div>
          <button
            type="button"
            data-testid="plugin-detail-close"
            onClick={onClose}
            aria-label="Close"
            style={{
              border: "none",
              background: "transparent",
              fontSize: 24,
              cursor: "pointer",
            }}
          >
            ×
          </button>
        </header>

        <div
          style={{
            padding: "var(--space-4, 16px)",
            overflow: "auto",
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-4, 16px)",
            flex: 1,
          }}
        >
          <section>
            <h3 style={sectionTitle}>About</h3>
            <p style={{ margin: 0, fontSize: "var(--text-sm, 14px)" }}>
              {plugin.description}
            </p>
          </section>

          <section>
            <h3 style={sectionTitle}>Install</h3>
            <p
              style={{
                margin: "0 0 var(--space-2, 8px) 0",
                fontSize: "var(--text-xs, 12px)",
                color: "var(--fg-muted, #5b6470)",
              }}
            >
              v1 is information-only. Run this in your project venv:
            </p>
            <div
              style={{
                display: "flex",
                gap: 8,
                alignItems: "stretch",
                background: "var(--surface-raised, #f7f8fa)",
                border: "1px solid var(--border, #eaecf0)",
                borderRadius: "var(--radius-md, 6px)",
                padding: "var(--space-2, 8px) var(--space-3, 12px)",
              }}
            >
              <code
                data-testid="plugin-install-command"
                style={{
                  flex: 1,
                  fontFamily: "var(--font-mono, monospace)",
                  fontSize: "var(--text-sm, 13px)",
                }}
              >
                {plugin.install_command}
              </code>
              <button
                type="button"
                data-testid="plugin-install-copy"
                onClick={() => void handleCopy()}
                style={{
                  border: "1px solid var(--border, #eaecf0)",
                  borderRadius: "var(--radius-md, 6px)",
                  padding: "2px 12px",
                  fontSize: "var(--text-xs, 12px)",
                  cursor: "pointer",
                  background: "var(--surface, #ffffff)",
                }}
              >
                {copied ? "Copied" : "Copy"}
              </button>
            </div>
          </section>

          <section>
            <h3 style={sectionTitle}>
              Supported recipes ({plugin.supported_recipes.length})
            </h3>
            <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
              {plugin.supported_recipes.map((r) => (
                <span key={r} style={chipStyle}>
                  {r}
                </span>
              ))}
              {plugin.supported_recipes.length === 0 ? (
                <span style={{ color: "var(--fg-muted, #5b6470)", fontSize: "var(--text-xs, 12px)" }}>
                  None
                </span>
              ) : null}
            </div>
          </section>

          <section>
            <h3 style={sectionTitle}>
              Supported processors ({plugin.supported_processors.length})
            </h3>
            <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
              {plugin.supported_processors.map((p) => (
                <span key={p} style={chipStyle}>
                  {p}
                </span>
              ))}
              {plugin.supported_processors.length === 0 ? (
                <span style={{ color: "var(--fg-muted, #5b6470)", fontSize: "var(--text-xs, 12px)" }}>
                  None
                </span>
              ) : null}
            </div>
          </section>

          <section>
            <h3 style={sectionTitle}>Source</h3>
            <a
              href={plugin.source_code_url}
              target="_blank"
              rel="noopener noreferrer"
              data-testid="plugin-source-link"
              style={{
                fontSize: "var(--text-sm, 14px)",
                color: "var(--accent, #0d9488)",
                wordBreak: "break-all",
              }}
            >
              {plugin.source_code_url}
            </a>
          </section>
        </div>
      </aside>
    </>
  );
}

const sectionTitle: React.CSSProperties = {
  margin: "0 0 var(--space-2, 8px) 0",
  fontSize: "var(--text-xs, 12px)",
  textTransform: "uppercase",
  letterSpacing: "0.06em",
  color: "var(--fg-muted, #5b6470)",
};

const chipStyle: React.CSSProperties = {
  fontSize: "var(--text-xs, 11px)",
  padding: "2px 8px",
  borderRadius: 999,
  background: "var(--surface-raised, #f7f8fa)",
  color: "var(--fg, #101828)",
  border: "1px solid var(--border, #eaecf0)",
};
