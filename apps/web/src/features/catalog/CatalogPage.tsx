import { useCallback, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { client } from "../../api/client";
import { RecipesList } from "./RecipesList";
import { ProcessorsList } from "./ProcessorsList";
import { CatalogDetailDrawer, type CatalogSelection } from "./CatalogDetailDrawer";
import styles from "./CatalogPage.module.css";

export type CatalogTab = "recipes" | "processors";

export interface CatalogPageProps {
  /** Test seam — swap in a stub client without mocking modules. */
  clientImpl?: typeof client;
}

function normaliseTab(raw: string | null): CatalogTab {
  return raw === "processors" ? "processors" : "recipes";
}

export function CatalogPage(props: CatalogPageProps): JSX.Element {
  const apiClient = props.clientImpl ?? client;
  const [searchParams, setSearchParams] = useSearchParams();
  const tab = normaliseTab(searchParams.get("tab"));
  const [selection, setSelection] = useState<CatalogSelection | null>(null);

  const setTab = useCallback(
    (next: CatalogTab) => {
      const params = new URLSearchParams(searchParams);
      params.set("tab", next);
      setSearchParams(params, { replace: true });
      // Close detail drawer when switching tabs.
      setSelection(null);
    },
    [searchParams, setSearchParams],
  );

  const onClose = useCallback(() => setSelection(null), []);

  return (
    <section className={styles.page} data-testid="catalog-page">
      <header className={styles.header}>
        <h1 className={styles.title}>Catalog</h1>
        <div role="tablist" aria-label="Catalog tabs" className={styles.tabs}>
          <TabButton
            active={tab === "recipes"}
            onClick={() => setTab("recipes")}
            label="Recipes"
          />
          <TabButton
            active={tab === "processors"}
            onClick={() => setTab("processors")}
            label="Processors"
          />
        </div>
      </header>

      {tab === "recipes" ? (
        <RecipesList
          clientImpl={apiClient}
          onSelect={(entry) => setSelection({ kind: "recipe", entry })}
        />
      ) : (
        <ProcessorsList
          clientImpl={apiClient}
          onSelect={(entry) => setSelection({ kind: "processor", entry })}
        />
      )}

      <CatalogDetailDrawer
        clientImpl={apiClient}
        selection={selection}
        onClose={onClose}
      />
    </section>
  );
}

function TabButton(props: {
  active: boolean;
  onClick: () => void;
  label: string;
}): JSX.Element {
  return (
    <button
      type="button"
      role="tab"
      aria-selected={props.active}
      onClick={props.onClick}
      className={`${styles.tab} ${props.active ? styles.tabActive : ""}`.trim()}
      data-testid={`catalog-tab-${props.label.toLowerCase()}`}
    >
      {props.label}
    </button>
  );
}

