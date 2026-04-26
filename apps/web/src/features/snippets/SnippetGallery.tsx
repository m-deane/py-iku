import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useFlowStore } from "../../state/flowStore";
import { SnippetCard } from "./SnippetCard";
import {
  SNIPPET_CATEGORIES,
  SNIPPETS,
  type Snippet,
  type SnippetCategory,
} from "./snippets";

export interface SnippetGalleryProps {
  /** Test seam — overrides ``useNavigate`` so we can assert routing intent. */
  navigateImpl?: (path: string) => void;
}

type FilterCategory = "all" | SnippetCategory;

export function SnippetGallery(props: SnippetGalleryProps): JSX.Element {
  const navigate = useNavigate();
  const setCurrentCode = useFlowStore((s) => s.setCurrentCode);
  const [filter, setFilter] = useState<FilterCategory>("all");
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return SNIPPETS.filter((s) => {
      if (filter !== "all" && s.category !== filter) return false;
      if (!q) return true;
      if (s.name.toLowerCase().includes(q)) return true;
      if (s.description.toLowerCase().includes(q)) return true;
      return s.tags.some((t) => t.toLowerCase().includes(q));
    });
  }, [filter, query]);

  const onOpen = (snippet: Snippet): void => {
    setCurrentCode(snippet.code);
    const navFn = props.navigateImpl ?? navigate;
    navFn("/convert");
  };

  return (
    <section
      style={{
        padding: "1.25rem",
        maxWidth: 1200,
        margin: "0 auto",
        display: "flex",
        flexDirection: "column",
        gap: "1rem",
      }}
    >
      <header style={{ display: "flex", alignItems: "baseline", gap: "1rem" }}>
        <h1 style={{ margin: 0, fontSize: "1.4rem" }}>Snippets</h1>
        <span style={{ color: "var(--color-grid, #888)", fontSize: 13 }}>
          {filtered.length} of {SNIPPETS.length} examples
        </span>
      </header>

      <div
        style={{
          display: "flex",
          gap: "0.75rem",
          alignItems: "center",
          flexWrap: "wrap",
        }}
      >
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search snippets…"
          aria-label="Search snippets"
          data-testid="snippet-gallery-search"
          style={{
            flex: "0 1 280px",
            padding: "0.4rem 0.6rem",
            borderRadius: 6,
            border: "1px solid var(--color-grid, #e0e0e0)",
            background: "transparent",
            color: "inherit",
          }}
        />
        <div
          role="tablist"
          aria-label="Filter by category"
          style={{ display: "inline-flex", gap: 4, flexWrap: "wrap" }}
        >
          <CategoryButton
            value="all"
            active={filter === "all"}
            onClick={() => setFilter("all")}
          >
            All
          </CategoryButton>
          {SNIPPET_CATEGORIES.map((cat) => (
            <CategoryButton
              key={cat}
              value={cat}
              active={filter === cat}
              onClick={() => setFilter(cat)}
            >
              {cat}
            </CategoryButton>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <p
          data-testid="snippet-gallery-empty"
          style={{ color: "var(--color-grid, #888)" }}
        >
          No snippets match the current filter.
        </p>
      ) : (
        <div
          data-testid="snippet-gallery-grid"
          style={{
            display: "grid",
            gap: "0.75rem",
            gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
          }}
        >
          {filtered.map((s) => (
            <SnippetCard key={s.id} snippet={s} onOpen={onOpen} />
          ))}
        </div>
      )}
    </section>
  );
}

function CategoryButton(props: {
  value: FilterCategory;
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}): JSX.Element {
  return (
    <button
      type="button"
      role="tab"
      aria-selected={props.active}
      data-testid={`snippet-filter-${props.value}`}
      onClick={props.onClick}
      style={{
        padding: "0.3rem 0.7rem",
        borderRadius: 999,
        border: "1px solid var(--color-grid, #e0e0e0)",
        background: props.active
          ? "var(--color-connectionhover, #1976d2)"
          : "transparent",
        color: props.active ? "white" : "inherit",
        cursor: "pointer",
        fontSize: 12,
        textTransform: "uppercase",
        letterSpacing: 0.4,
      }}
    >
      {props.children}
    </button>
  );
}
