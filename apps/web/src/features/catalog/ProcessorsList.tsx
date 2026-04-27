import { useEffect, useMemo, useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { client as defaultClient, type ProcessorCatalogEntry } from "../../api/client";
import styles from "./CatalogPage.module.css";

export interface ProcessorsListProps {
  clientImpl?: typeof defaultClient;
  onSelect: (entry: ProcessorCatalogEntry) => void;
  /** Debounce delay for the search input in ms (test override). */
  debounceMs?: number;
}

export function ProcessorsList(props: ProcessorsListProps): JSX.Element {
  const apiClient = props.clientImpl ?? defaultClient;
  const debounceMs = props.debounceMs ?? 300;
  const [rawQ, setRawQ] = useState("");
  const [debouncedQ, setDebouncedQ] = useState("");
  const [category, setCategory] = useState<string>("");

  // Debounce the search input → server-side filtering uses the debounced value.
  useEffect(() => {
    const handle = setTimeout(() => setDebouncedQ(rawQ.trim()), debounceMs);
    return () => clearTimeout(handle);
  }, [rawQ, debounceMs]);

  const query = useQuery<ProcessorCatalogEntry[]>({
    queryKey: ["catalog", "processors", debouncedQ, category],
    queryFn: () =>
      apiClient.listProcessors({
        q: debouncedQ || undefined,
        category: category || undefined,
      }),
    placeholderData: keepPreviousData,
  });

  const items = query.data ?? [];

  // Categories collected from the un-filtered first response. We refetch the
  // category list separately (no q, no category) to keep the dropdown stable
  // across searches.
  const categoriesQuery = useQuery<ProcessorCatalogEntry[]>({
    queryKey: ["catalog", "processors", "all-for-categories"],
    queryFn: () => apiClient.listProcessors(),
    // 5 min default stale time inherited from QueryClient defaults.
  });
  const categories = useMemo(() => {
    const set = new Set<string>();
    for (const p of categoriesQuery.data ?? items) set.add(p.category);
    return Array.from(set).sort();
  }, [categoriesQuery.data, items]);

  return (
    <div data-testid="processors-list">
      <div className={styles.toolbar}>
        <input
          type="search"
          placeholder="Search processors…"
          aria-label="Search processors"
          value={rawQ}
          onChange={(e) => setRawQ(e.target.value)}
          className={styles.searchInput}
          data-testid="processors-search"
        />
        <select
          aria-label="Filter by category"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className={styles.categorySelect}
          data-testid="processors-category"
        >
          <option value="">All categories</option>
          {categories.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        <span style={{ fontSize: 12, color: "var(--fg-muted, #5b6470)" }}>
          {items.length} result{items.length === 1 ? "" : "s"}
        </span>
      </div>

      {query.isLoading ? (
        <div className={styles.loading}>Loading processors…</div>
      ) : query.isError ? (
        <div className={styles.error}>Failed to load processors.</div>
      ) : items.length === 0 ? (
        <div
          className={styles.empty}
          data-testid="processors-empty"
          style={{ fontStyle: "normal", padding: "1.25rem 1rem" }}
        >
          <strong style={{ display: "block", marginBottom: 4 }}>
            {debouncedQ || category
              ? "No processors match this search"
              : "Processor catalog unavailable"}
          </strong>
          {debouncedQ || category
            ? "Clear the search box or category to see all 100 processor types — column transforms, filters, splits, formulas, and date/time helpers."
            : "The catalog lists every processor that can run inside a PREPARE recipe. Confirm the API base URL in settings, then reload."}
        </div>
      ) : (
        <ul className={`${styles.grid} ${styles.cardList}`.trim()} role="list">
          {items.map((p) => (
            <li key={p.name} className={styles.cardListItem}>
              <button
                type="button"
                className={styles.card}
                data-testid={`processor-card-${p.name}`}
                onClick={() => props.onSelect(p)}
              >
                <div className={styles.cardHeader}>
                  <span className={styles.icon} aria-hidden>
                    ⚙
                  </span>
                  <span className={styles.cardTitle}>{p.name}</span>
                </div>
                <div className={styles.cardMeta}>
                  <span className={styles.tag}>{p.category}</span>
                </div>
                <div className={styles.cardDesc}>{p.description}</div>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
