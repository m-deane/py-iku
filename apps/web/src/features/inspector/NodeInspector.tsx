import clsx from "clsx";
import { JsonView } from "../../components/JsonView";
import { useFlowStore } from "../../state/flowStore";
import {
  RecipeSettingsModelSchema,
  type DataikuRecipeModel,
  type DataikuDatasetModel,
  type DataikuFlowModel,
} from "@py-iku-studio/types";
import styles from "./NodeInspector.module.css";

export interface NodeInspectorProps {
  /** Test seam — pass an explicit flow + selection without going through flowStore. */
  flow?: DataikuFlowModel | null;
  selectedNodeId?: string | null;
  onClose?: () => void;
}

type NodeKind = "recipe" | "dataset" | null;

interface ResolvedNode {
  kind: NodeKind;
  recipe?: DataikuRecipeModel;
  dataset?: DataikuDatasetModel;
}

function resolveNode(
  flow: DataikuFlowModel | null | undefined,
  id: string | null | undefined,
): ResolvedNode {
  if (!flow || !id) return { kind: null };
  for (const r of flow.recipes ?? []) {
    if (r.name === id) return { kind: "recipe", recipe: r };
  }
  for (const d of flow.datasets ?? []) {
    if (d.name === id) return { kind: "dataset", dataset: d };
  }
  return { kind: null };
}

export function NodeInspector(props: NodeInspectorProps): JSX.Element | null {
  const flowFromStore = useFlowStore((s) => s.currentFlow);
  const selectedFromStore = useFlowStore((s) => s.selectedNodeId);
  const clearSelection = useFlowStore((s) => s.clearSelection);

  const flow = (props.flow !== undefined ? props.flow : flowFromStore) as
    | DataikuFlowModel
    | null;
  const selectedNodeId =
    props.selectedNodeId !== undefined ? props.selectedNodeId : selectedFromStore;

  if (!selectedNodeId) return null;

  const node = resolveNode(flow, selectedNodeId);
  const onClose = props.onClose ?? clearSelection;

  return (
    <aside
      className={clsx(styles.panel)}
      role="complementary"
      aria-label="Node inspector"
      data-testid="node-inspector"
    >
      <header className={styles.header}>
        <h2 className={styles.title}>{selectedNodeId}</h2>
        <button
          type="button"
          className={styles.closeButton}
          onClick={onClose}
          aria-label="Close inspector"
          data-testid="inspector-close"
        >
          ×
        </button>
      </header>

      {node.kind === "recipe" && node.recipe ? (
        <RecipeInspector recipe={node.recipe} />
      ) : node.kind === "dataset" && node.dataset ? (
        <DatasetInspector dataset={node.dataset} />
      ) : (
        <div className={styles.empty} data-testid="inspector-empty">
          Node "{selectedNodeId}" not found in current flow.
        </div>
      )}
    </aside>
  );
}

function RecipeInspector({ recipe }: { recipe: DataikuRecipeModel }): JSX.Element {
  // py-iku to_dict() flattens settings fields onto the recipe alongside the
  // standard fields. We extract the structural fields and treat everything
  // else as settings for parsing/display.
  const STRUCTURAL = new Set([
    "name",
    "type",
    "inputs",
    "outputs",
    "source_lines",
    "notes",
    "settings",
  ]);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const recipeAny = recipe as Record<string, any>;
  const settingsLike: Record<string, unknown> = { kind: recipe.type };
  for (const [k, v] of Object.entries(recipeAny)) {
    if (!STRUCTURAL.has(k)) settingsLike[k] = v;
  }

  // Try schema parse first; fall back to JsonView for unknown discriminator values.
  const parsed = RecipeSettingsModelSchema.safeParse(settingsLike);

  return (
    <div data-testid="recipe-inspector">
      <div className={styles.metaRow}>
        <span className={styles.tag} data-testid="recipe-type">
          {recipe.type}
        </span>
        <span className={styles.tag}>
          {(recipe.inputs ?? []).length} in
        </span>
        <span className={styles.tag}>
          {(recipe.outputs ?? []).length} out
        </span>
      </div>

      <section className={styles.section}>
        <div className={styles.sectionTitle}>Inputs</div>
        {(recipe.inputs ?? []).length === 0 ? (
          <div className={styles.empty}>none</div>
        ) : (
          <ul style={{ margin: 0, paddingLeft: 18 }}>
            {(recipe.inputs ?? []).map((n) => (
              <li key={n}>{n}</li>
            ))}
          </ul>
        )}
      </section>

      <section className={styles.section}>
        <div className={styles.sectionTitle}>Outputs</div>
        {(recipe.outputs ?? []).length === 0 ? (
          <div className={styles.empty}>none</div>
        ) : (
          <ul style={{ margin: 0, paddingLeft: 18 }}>
            {(recipe.outputs ?? []).map((n) => (
              <li key={n}>{n}</li>
            ))}
          </ul>
        )}
      </section>

      <section className={styles.section}>
        <div className={styles.sectionTitle}>Settings</div>
        {parsed.success ? (
          <SettingsKVList settings={parsed.data} />
        ) : (
          <div data-testid="settings-fallback">
            <JsonView value={settingsLike} initialDepth={1} />
          </div>
        )}
      </section>
    </div>
  );
}

function SettingsKVList({
  settings,
}: {
  settings: Record<string, unknown>;
}): JSX.Element {
  const entries = Object.entries(settings).filter(([k]) => k !== "kind");
  if (entries.length === 0) {
    return <div className={styles.empty}>(no settings)</div>;
  }
  return (
    <dl className={styles.kvList} data-testid="settings-kvlist">
      {entries.map(([k, v]) => (
        <FragmentRow key={k} k={k} v={v} />
      ))}
    </dl>
  );
}

function FragmentRow({ k, v }: { k: string; v: unknown }): JSX.Element {
  return (
    <>
      <dt className={styles.kvKey}>{k}</dt>
      <dd className={styles.kvValue} style={{ margin: 0 }}>
        {renderValue(v)}
      </dd>
    </>
  );
}

function renderValue(v: unknown): JSX.Element | string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "string" || typeof v === "number" || typeof v === "boolean") {
    return String(v);
  }
  if (Array.isArray(v) && v.every((x) => typeof x === "string" || typeof x === "number")) {
    return (v as (string | number)[]).join(", ");
  }
  return <JsonView value={v} initialDepth={0} />;
}

function DatasetInspector({
  dataset,
}: {
  dataset: DataikuDatasetModel;
}): JSX.Element {
  // The Pydantic alias serializes to "schema" in JSON; the TS codegen exposes
  // it as `schema`. Some payloads might also include `schema_` from Python repr.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const dsAny = dataset as any;
  const schemaCols = (dsAny.schema ?? dsAny.schema_ ?? []) as unknown[];
  return (
    <div data-testid="dataset-inspector">
      <div className={styles.metaRow}>
        <span className={styles.tag} data-testid="dataset-type">
          {dataset.type}
        </span>
        <span className={styles.tag}>{dataset.connection_type}</span>
      </div>
      <section className={styles.section}>
        <div className={styles.sectionTitle}>Schema</div>
        <div data-testid="schema-count">
          {schemaCols.length} column{schemaCols.length === 1 ? "" : "s"}
        </div>
      </section>
      {dataset.source_variable ? (
        <section className={styles.section}>
          <div className={styles.sectionTitle}>Source variable</div>
          <div className={styles.kvValue}>{dataset.source_variable}</div>
        </section>
      ) : null}
      {dataset.source_line ? (
        <section className={styles.section}>
          <div className={styles.sectionTitle}>Source line</div>
          <div className={styles.kvValue}>{dataset.source_line}</div>
        </section>
      ) : null}
    </div>
  );
}
