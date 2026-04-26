import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { client as defaultClient, type RecipeCatalogEntry } from "../../api/client";
import styles from "./CatalogPage.module.css";

export interface RecipesListProps {
  clientImpl?: typeof defaultClient;
  onSelect: (entry: RecipeCatalogEntry) => void;
}

export function RecipesList(props: RecipesListProps): JSX.Element {
  const apiClient = props.clientImpl ?? defaultClient;
  const [q, setQ] = useState("");
  const [category, setCategory] = useState<string>("");

  const query = useQuery<RecipeCatalogEntry[]>({
    queryKey: ["catalog", "recipes"],
    queryFn: () => apiClient.listRecipes(),
  });

  const items = query.data ?? [];

  const categories = useMemo(() => {
    const set = new Set<string>();
    for (const r of items) set.add(r.category);
    return Array.from(set).sort();
  }, [items]);

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return items.filter((r) => {
      if (category && r.category !== category) return false;
      if (!needle) return true;
      return (
        r.name.toLowerCase().includes(needle) ||
        r.description.toLowerCase().includes(needle) ||
        r.type.toLowerCase().includes(needle)
      );
    });
  }, [items, q, category]);

  return (
    <div data-testid="recipes-list">
      <div className={styles.toolbar}>
        <input
          type="search"
          placeholder="Search recipes…"
          aria-label="Search recipes"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className={styles.searchInput}
          data-testid="recipes-search"
        />
        <select
          aria-label="Filter by category"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className={styles.categorySelect}
          data-testid="recipes-category"
        >
          <option value="">All categories</option>
          {categories.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        <span style={{ fontSize: 12, color: "var(--color-grid, #888)" }}>
          {filtered.length} of {items.length}
        </span>
      </div>

      {query.isLoading ? (
        <div className={styles.loading}>Loading recipes…</div>
      ) : query.isError ? (
        <div className={styles.error}>Failed to load recipes.</div>
      ) : filtered.length === 0 ? (
        <div className={styles.empty}>No recipes match.</div>
      ) : (
        <div className={styles.grid} role="list">
          {filtered.map((r) => (
            <button
              key={r.type}
              type="button"
              role="listitem"
              className={styles.card}
              data-testid={`recipe-card-${r.type}`}
              onClick={() => props.onSelect(r)}
            >
              <div className={styles.cardHeader}>
                <span className={styles.icon} aria-hidden>
                  {r.icon}
                </span>
                <span className={styles.cardTitle}>{r.name}</span>
              </div>
              <div className={styles.cardMeta}>
                <span className={styles.tag}>{r.category}</span>
                <span className={styles.tag}>{r.type}</span>
              </div>
              <div className={styles.cardDesc}>{r.description}</div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
