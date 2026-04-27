import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import Fuse from "fuse.js";
import { useFlowStore } from "../../state/flowStore";
import { TemplateCard } from "./TemplateCard";
import { TemplatePreview } from "./TemplatePreview";
import {
  TEMPLATES,
  TEMPLATE_CATEGORIES,
  type FlowTemplate,
  type TemplateCategory,
} from "./templates-data";
import styles from "./TemplatesPage.module.css";

type FilterCategory = "all" | TemplateCategory;

export interface TemplatesPageProps {
  /** Test seam — overrides ``useNavigate`` so we can assert routing intent. */
  navigateImpl?: (path: string) => void;
  /** Test seam — render a textarea instead of Monaco when previewing source. */
  fallbackTextarea?: boolean;
}

/**
 * Trade-Blotter Recipe-Template Gallery — the third Library cluster page.
 *
 * Renders 10 fully-verified commodity-trading templates (trade capture,
 * position/P&L, curves, counterparty, power) drawn from the textbook's
 * worked-examples chapters. Every template's ``verifiedRecipes`` shape has
 * been captured from a real ``convert(...)`` call; round-trip tests in
 * ``apps/api/tests/test_routes/test_templates_round_trip.py`` re-run the
 * conversion and assert the shape matches.
 */
export function TemplatesPage(props: TemplatesPageProps = {}): JSX.Element {
  const navigate = useNavigate();
  const setCurrentCode = useFlowStore((s) => s.setCurrentCode);
  const [searchParams, setSearchParams] = useSearchParams();

  const [query, setQuery] = useState<string>("");
  const [filter, setFilter] = useState<FilterCategory>("all");
  const [activeId, setActiveId] = useState<string | null>(null);

  // Deep-link support: /templates?id=<template-id> opens the preview drawer.
  // The command palette uses this to jump straight to a named template.
  useEffect(() => {
    const idParam = searchParams.get("id");
    if (idParam && TEMPLATES.some((t) => t.id === idParam)) {
      setActiveId(idParam);
    }
  }, [searchParams]);

  // Pre-built fuse index — name + summary + tags + personas + category.
  const fuse = useMemo(
    () =>
      new Fuse(TEMPLATES as FlowTemplate[], {
        keys: ["name", "summary", "tags", "personas", "category"],
        threshold: 0.32,
        includeScore: false,
      }),
    [],
  );

  const filtered: FlowTemplate[] = useMemo(() => {
    const q = query.trim();
    let pool: FlowTemplate[] =
      q === ""
        ? [...TEMPLATES]
        : fuse.search(q).map((r) => r.item);
    if (filter !== "all") {
      pool = pool.filter((t) => t.category === filter);
    }
    return pool;
  }, [query, filter, fuse]);

  const activeTemplate: FlowTemplate | null = useMemo(
    () => TEMPLATES.find((t) => t.id === activeId) ?? null,
    [activeId],
  );

  const handleSelect = (template: FlowTemplate): void => {
    setActiveId(template.id);
    const next = new URLSearchParams(searchParams);
    next.set("id", template.id);
    setSearchParams(next, { replace: true });
  };

  const handleClose = (): void => {
    setActiveId(null);
    const next = new URLSearchParams(searchParams);
    next.delete("id");
    setSearchParams(next, { replace: true });
  };

  const handleOpenInEditor = (
    template: FlowTemplate,
    renderedSource?: string,
  ): void => {
    // Sprint 5 — parametric templates pass the placeholder-substituted
    // source through. Non-parametric templates (no ``parameters`` key)
    // pass nothing and fall back to the raw pythonSource.
    setCurrentCode(renderedSource ?? template.pythonSource);
    const navFn = props.navigateImpl ?? navigate;
    navFn("/convert");
  };

  const resetFilters = (): void => {
    setQuery("");
    setFilter("all");
  };

  return (
    <section className={styles.page} data-testid="templates-page" data-route="templates">
      <header className={styles.header}>
        <h1 className={styles.title}>Templates</h1>
        <span className={styles.count} data-testid="templates-count">
          {filtered.length} of {TEMPLATES.length} templates
        </span>
      </header>

      <p className={styles.subtitle}>
        Trade-blotter recipe templates for front-office commodity trading —
        WTI, Brent, Henry Hub, TTF, JKM, PJM, ERCOT. Every template is a
        real pandas script that has been round-tripped through{" "}
        <code>convert()</code>; the recipe shape under the title is the
        verified output, not an aspiration.
      </p>

      <div className={styles.controls}>
        <input
          type="search"
          className={styles.search}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search templates by name, tag, or commodity…"
          aria-label="Search templates"
          data-testid="templates-search"
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
          {TEMPLATE_CATEGORIES.map((c) => (
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
        <div className={styles.empty} data-testid="templates-empty">
          <p className={styles.emptyTitle}>No templates match this search</p>
          <span>
            Clear the filter to see all 10 trade-blotter templates —{" "}
            <button
              type="button"
              onClick={resetFilters}
              className={styles.secondaryBtn}
              data-testid="templates-reset"
            >
              reset filters
            </button>
          </span>
        </div>
      ) : (
        <div className={styles.grid} data-testid="templates-grid">
          {filtered.map((t) => (
            <TemplateCard key={t.id} template={t} onSelect={handleSelect} />
          ))}
        </div>
      )}

      <TemplatePreview
        template={activeTemplate}
        onClose={handleClose}
        onOpenInEditor={handleOpenInEditor}
        fallbackTextarea={props.fallbackTextarea}
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
      data-testid={`templates-filter-${props.value}`}
      onClick={props.onClick}
      className={`${styles.chip} ${props.active ? styles.chipActive : ""}`}
    >
      {props.children}
    </button>
  );
}
