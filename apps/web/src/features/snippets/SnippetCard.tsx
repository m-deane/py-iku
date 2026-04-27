import type { Snippet } from "./snippets";

export interface SnippetCardProps {
  snippet: Snippet;
  onOpen: (snippet: Snippet) => void;
}

export function SnippetCard({ snippet, onOpen }: SnippetCardProps): JSX.Element {
  return (
    <article
      data-testid={`snippet-card-${snippet.id}`}
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "0.5rem",
        padding: "1rem",
        borderRadius: 8,
        border: "1px solid var(--color-grid, #e0e0e0)",
        background: "var(--color-background, #fafafa)",
        minHeight: 180,
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <h3 style={{ margin: 0, fontSize: "1rem" }}>{snippet.name}</h3>
        <span
          aria-label={`category ${snippet.category}`}
          style={{
            fontSize: 11,
            padding: "0.15rem 0.45rem",
            borderRadius: 999,
            background: "var(--color-grid, #e0e0e0)",
            color: "var(--color-fg, #212121)",
            textTransform: "uppercase",
            letterSpacing: 0.4,
          }}
        >
          {snippet.category}
        </span>
      </div>
      <p style={{ margin: 0, fontSize: 13, color: "var(--fg-muted, #5b6470)" }}>
        {snippet.description}
      </p>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
        {snippet.tags.slice(0, 5).map((t) => (
          <span
            key={t}
            style={{
              fontSize: 11,
              padding: "0.1rem 0.4rem",
              borderRadius: 4,
              border: "1px solid var(--color-grid, #e0e0e0)",
              color: "var(--fg-muted, #5b6470)",
            }}
          >
            {t}
          </span>
        ))}
      </div>
      <div style={{ marginTop: "auto" }}>
        <button
          type="button"
          data-testid={`snippet-open-${snippet.id}`}
          onClick={() => onOpen(snippet)}
          style={{
            padding: "0.4rem 0.8rem",
            borderRadius: 6,
            border: 0,
            background: "var(--color-connectionhover, #1976d2)",
            color: "white",
            cursor: "pointer",
            fontSize: 13,
          }}
        >
          Open in editor
        </button>
      </div>
    </article>
  );
}
