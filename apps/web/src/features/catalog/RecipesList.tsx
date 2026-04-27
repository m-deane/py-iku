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
        <span style={{ fontSize: 12, color: "var(--fg-muted, #5b6470)" }}>
          {filtered.length} of {items.length}
        </span>
      </div>

      {query.isLoading ? (
        <div className={styles.loading}>Loading recipes…</div>
      ) : query.isError ? (
        <div className={styles.error}>Failed to load recipes.</div>
      ) : items.length === 0 ? (
        <div
          className={styles.empty}
          data-testid="recipes-empty"
          style={{ fontStyle: "normal", padding: "1.25rem 1rem" }}
        >
          <strong style={{ display: "block", marginBottom: 4 }}>
            Recipe catalog unavailable
          </strong>
          The catalog renders the 37 Dataiku DSS recipe types served by the
          API. Confirm the API base URL in settings, then reload.
        </div>
      ) : filtered.length === 0 ? (
        <div
          className={styles.empty}
          data-testid="recipes-empty"
          style={{ fontStyle: "normal", padding: "1.25rem 1rem" }}
        >
          <strong style={{ display: "block", marginBottom: 4 }}>
            No recipes match this search
          </strong>
          Clear the search box or pick a different category — the full set
          covers prepare, joins, splits, windows, top-N, grouping, pivots, and
          statistics.
        </div>
      ) : (
        <ul className={`${styles.grid} ${styles.cardList}`.trim()} role="list">
          {filtered.map((r) => (
            <li key={r.type} className={styles.cardListItem}>
              <button
                type="button"
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
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
