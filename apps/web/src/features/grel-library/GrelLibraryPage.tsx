import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import Fuse from "fuse.js";
import { useFlowStore } from "../../state/flowStore";
import { GrelFormulaCard } from "./GrelFormulaCard";
import { GrelFormulaPreview } from "./GrelFormulaPreview";
import {
  buildInsertSnippet,
  GREL_CATEGORIES,
  GREL_FORMULAS,
  type GrelFormula,
  type GrelFormulaCategory,
} from "./formulas-data";
import styles from "./GrelLibraryPage.module.css";

type FilterCategory = "all" | GrelFormulaCategory;

export interface GrelLibraryPageProps {
  /** Test seam — overrides ``useNavigate`` so we can assert routing. */
  navigateImpl?: (path: string) => void;
}

/**
 * GREL Formula Library — pre-built crack-spread / heat-rate / basis /
 * freight / differential formulas for front-office trading desks.
 *
 * Lives under the Library nav cluster alongside Catalog, Snippets, and
 * Templates. Each card opens a modal showing the GREL string, the pandas
 * equivalent, the unit semantics, the related instruments, and a worked
 * example. The "Insert into editor" button prepends a comment header plus
 * the pandas line to whatever is currently in the editor.
 */
export function GrelLibraryPage(
  props: GrelLibraryPageProps = {},
): JSX.Element {
  const navigate = useNavigate();
  const setCurrentCode = useFlowStore((s) => s.setCurrentCode);
  const currentCode = useFlowStore((s) => s.currentCode);
  const [searchParams, setSearchParams] = useSearchParams();

  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<FilterCategory>("all");
  const [activeId, setActiveId] = useState<string | null>(null);

  // Deep-link support: /grel?id=<formula-id> opens the modal.
  useEffect(() => {
    const idParam = searchParams.get("id");
    if (idParam && GREL_FORMULAS.some((f) => f.id === idParam)) {
      setActiveId(idParam);
    }
  }, [searchParams]);

  const fuse = useMemo(
    () =>
      new Fuse(GREL_FORMULAS as GrelFormula[], {
        keys: ["name", "description", "category", "relatedInstruments", "grel"],
        threshold: 0.32,
        includeScore: false,
      }),
    [],
  );

  const filtered: GrelFormula[] = useMemo(() => {
    const q = query.trim();
    let pool: GrelFormula[] =
      q === "" ? [...GREL_FORMULAS] : fuse.search(q).map((r) => r.item);
    if (filter !== "all") {
      pool = pool.filter((f) => f.category === filter);
    }
    return pool;
  }, [query, filter, fuse]);

  const activeFormula: GrelFormula | null = useMemo(
    () => GREL_FORMULAS.find((f) => f.id === activeId) ?? null,
    [activeId],
  );

  const handleSelect = (formula: GrelFormula): void => {
    setActiveId(formula.id);
    const next = new URLSearchParams(searchParams);
    next.set("id", formula.id);
    setSearchParams(next, { replace: true });
  };

  const handleClose = (): void => {
    setActiveId(null);
    const next = new URLSearchParams(searchParams);
    next.delete("id");
    setSearchParams(next, { replace: true });
  };

  const handleInsertIntoEditor = (formula: GrelFormula): void => {
    const snippet = buildInsertSnippet(formula);
    const merged =
      currentCode && currentCode.trim().length > 0
        ? `${snippet}\n${currentCode}`
        : snippet;
    setCurrentCode(merged);
    const navFn = props.navigateImpl ?? navigate;
    navFn("/editor");
  };

  const resetFilters = (): void => {
    setQuery("");
    setFilter("all");
  };

  return (
    <section className={styles.page} data-testid="grel-library-page">
      <header className={styles.header}>
        <h1 className={styles.title}>GREL Formula Library</h1>
        <span className={styles.count} data-testid="grel-count">
          {filtered.length} of {GREL_FORMULAS.length} formulas
        </span>
      </header>

      <p className={styles.subtitle}>
        Pre-built GREL expressions for front-office trading — crack spreads,
        heat rates, basis trades, freight netbacks, grade and locational
        differentials. Each formula carries the GREL string a desk would
        paste into a CREATE_COLUMN_WITH_GREL processor and the pandas
        equivalent a quant would write in a notebook.
      </p>

      <div className={styles.controls}>
        <input
          type="search"
          className={styles.search}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search by name, instrument, or formula text…"
          aria-label="Search formulas"
          data-testid="grel-search"
        />
        <div
          role="tablist"
          aria-label="Filter by category"
          className={styles.chips}
        >
          <CategoryChip
            active={filter === "all"}
            onClick={() => setFilter("all")}
            value="all"
          >
            All
          </CategoryChip>
          {GREL_CATEGORIES.map((c) => (
            <CategoryChip
              key={c.value}
              active={filter === c.value}
              onClick={() => setFilter(c.value)}
              value={c.value}
            >
              {c.label}
            </CategoryChip>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className={styles.empty} data-testid="grel-empty">
          <p>
            No formulas match this search.{" "}
            <button
              type="button"
              onClick={resetFilters}
              className={styles.secondaryBtn}
              data-testid="grel-reset"
            >
              reset filters
            </button>
          </p>
        </div>
      ) : (
        <div className={styles.grid} data-testid="grel-grid">
          {filtered.map((f) => (
            <GrelFormulaCard
              key={f.id}
              formula={f}
              onSelect={handleSelect}
            />
          ))}
        </div>
      )}

      <GrelFormulaPreview
        formula={activeFormula}
        onClose={handleClose}
        onInsertIntoEditor={handleInsertIntoEditor}
      />
    </section>
  );
}

interface CategoryChipProps {
  active: boolean;
  onClick: () => void;
  value: string;
  children: React.ReactNode;
}

function CategoryChip(props: CategoryChipProps): JSX.Element {
  return (
    <button
      type="button"
      role="tab"
      aria-selected={props.active}
      data-testid={`grel-filter-${props.value}`}
      onClick={props.onClick}
      className={`${styles.chip} ${props.active ? styles.chipActive : ""}`}
    >
      {props.children}
    </button>
  );
}
