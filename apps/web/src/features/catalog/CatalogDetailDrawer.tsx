import { useQuery } from "@tanstack/react-query";
import {
  client as defaultClient,
  type ProcessorCatalogEntry,
  type RecipeCatalogEntry,
} from "../../api/client";
import styles from "./CatalogDetailDrawer.module.css";

export type CatalogSelection =
  | { kind: "recipe"; entry: RecipeCatalogEntry }
  | { kind: "processor"; entry: ProcessorCatalogEntry };

export interface CatalogDetailDrawerProps {
  selection: CatalogSelection | null;
  onClose: () => void;
  clientImpl?: typeof defaultClient;
}

export function CatalogDetailDrawer(props: CatalogDetailDrawerProps): JSX.Element | null {
  const { selection, onClose } = props;
  if (!selection) return null;

  return (
    <aside
      className={styles.panel}
      role="complementary"
      aria-label="Catalog detail"
      data-testid="catalog-detail-drawer"
    >
      <header className={styles.header}>
        <h2 className={styles.title}>
          {selection.kind === "recipe" ? selection.entry.name : selection.entry.name}
        </h2>
        <button
          type="button"
          className={styles.closeButton}
          onClick={onClose}
          aria-label="Close catalog detail"
          data-testid="catalog-detail-close"
        >
          ×
        </button>
      </header>

      {selection.kind === "recipe" ? (
        <RecipeDetail entry={selection.entry} />
      ) : (
        <ProcessorDetail
          entry={selection.entry}
          clientImpl={props.clientImpl ?? defaultClient}
        />
      )}
    </aside>
  );
}

function RecipeDetail({ entry }: { entry: RecipeCatalogEntry }): JSX.Element {
  const examples = entry.pandas_examples ?? [];
  return (
    <div data-testid="catalog-recipe-detail">
      <div className={styles.metaRow}>
        <span className={styles.tag}>{entry.category}</span>
        <span className={styles.tag}>{entry.type}</span>
        <span className={styles.tag} aria-label="icon">
          {entry.icon}
        </span>
      </div>
      <section className={styles.section}>
        <div className={styles.sectionTitle}>Description</div>
        <div className={styles.body}>{entry.description}</div>
      </section>
      <section className={styles.section}>
        <div className={styles.sectionTitle}>pandas examples</div>
        {examples.length === 0 ? (
          <div className={styles.empty}>(none)</div>
        ) : (
          <ul className={styles.list}>
            {examples.map((ex) => (
              <li key={ex}>
                <code className={styles.code}>{ex}</code>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

function ProcessorDetail(props: {
  entry: ProcessorCatalogEntry;
  clientImpl: typeof defaultClient;
}): JSX.Element {
  // Re-fetch the canonical processor record. The list view already gives us
  // most of the metadata, but a dedicated lookup keeps the drawer in sync if
  // ProcessorCatalog adds extra fields later.
  const detail = useQuery<ProcessorCatalogEntry>({
    queryKey: ["catalog", "processor", props.entry.name],
    queryFn: () => props.clientImpl.getProcessor(props.entry.name),
    initialData: props.entry,
  });

  const entry = detail.data ?? props.entry;
  const required = entry.required_params ?? [];
  const optional = entry.optional_params ?? [];
  const examples = entry.examples ?? {};

  return (
    <div data-testid="catalog-processor-detail">
      <div className={styles.metaRow}>
        <span className={styles.tag}>{entry.category}</span>
        {typeof entry.type === "string" ? (
          <span className={styles.tag} data-testid="processor-detail-type">
            {entry.type}
          </span>
        ) : null}
      </div>
      <section className={styles.section}>
        <div className={styles.sectionTitle}>Description</div>
        <div className={styles.body}>{entry.description}</div>
      </section>
      <section className={styles.section}>
        <div className={styles.sectionTitle}>
          Required params ({required.length})
        </div>
        {required.length === 0 ? (
          <div className={styles.empty}>(none)</div>
        ) : (
          <ul className={styles.list}>
            {required.map((p) => (
              <li key={p}>
                <code>{p}</code>
              </li>
            ))}
          </ul>
        )}
      </section>
      <section className={styles.section}>
        <div className={styles.sectionTitle}>
          Optional params ({optional.length})
        </div>
        {optional.length === 0 ? (
          <div className={styles.empty}>(none)</div>
        ) : (
          <ul className={styles.list}>
            {optional.map((p) => (
              <li key={p}>
                <code>{p}</code>
              </li>
            ))}
          </ul>
        )}
      </section>
      {Object.keys(examples).length > 0 ? (
        <section className={styles.section}>
          <div className={styles.sectionTitle}>Example</div>
          <code className={styles.code}>
            {JSON.stringify(examples, null, 2)}
          </code>
        </section>
      ) : null}
    </div>
  );
}
