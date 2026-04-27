import type { PluginCatalogEntry } from "../../api/client";

export interface PluginCardProps {
  plugin: PluginCatalogEntry;
  onSelect: (plugin: PluginCatalogEntry) => void;
}

/**
 * Marketplace card — clicking opens the install-instructions drawer. The card
 * itself is information-only; the actual ``pip install`` is a copy-paste
 * action because v1 has no package registry to back a real install flow.
 */
export function PluginCard({ plugin, onSelect }: PluginCardProps): JSX.Element {
  return (
    <article
      data-testid={`plugin-card-${plugin.name}`}
      style={{
        border: "1px solid var(--border, #eaecf0)",
        borderRadius: "var(--radius-md, 8px)",
        padding: "var(--space-4, 16px)",
        background: "var(--surface, #ffffff)",
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-2, 8px)",
        minHeight: 220,
      }}
    >
      <header style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
        <div>
          <h3
            style={{
              margin: 0,
              fontSize: "var(--text-base, 16px)",
              fontWeight: 600,
            }}
          >
            {plugin.name}
          </h3>
          <span
            style={{
              fontSize: "var(--text-xs, 12px)",
              color: "var(--fg-muted, #5b6470)",
            }}
          >
            v{plugin.version} · {plugin.author}
          </span>
        </div>
      </header>

      <p
        style={{
          margin: 0,
          fontSize: "var(--text-sm, 14px)",
          color: "var(--fg, #101828)",
          lineHeight: 1.5,
          flex: 1,
        }}
      >
        {plugin.description}
      </p>

      <div
        style={{ display: "flex", flexWrap: "wrap", gap: 4 }}
        data-testid={`plugin-card-tags-${plugin.name}`}
      >
        {plugin.tags.map((t) => (
          <span
            key={t}
            style={{
              fontSize: "var(--text-xs, 11px)",
              padding: "2px 8px",
              borderRadius: 999,
              background: "var(--surface-raised, #f7f8fa)",
              color: "var(--fg-muted, #5b6470)",
              border: "1px solid var(--border, #eaecf0)",
            }}
          >
            {t}
          </span>
        ))}
      </div>

      <footer style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span
          style={{
            fontSize: "var(--text-xs, 12px)",
            color: "var(--fg-muted, #5b6470)",
          }}
        >
          {plugin.supported_recipes.length} recipes ·{" "}
          {plugin.supported_processors.length} processors
        </span>
        <button
          type="button"
          data-testid={`plugin-install-${plugin.name}`}
          onClick={() => onSelect(plugin)}
          style={{
            padding: "var(--space-2, 6px) var(--space-3, 12px)",
            border: "1px solid var(--accent, #0d9488)",
            borderRadius: "var(--radius-md, 6px)",
            background: "var(--accent, #0d9488)",
            color: "var(--accent-fg, #ffffff)",
            fontSize: "var(--text-sm, 14px)",
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          Install
        </button>
      </footer>
    </article>
  );
}
