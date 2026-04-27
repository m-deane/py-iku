import { useEffect, useMemo, useState } from "react";
import { MonacoEditor } from "../editor/MonacoEditor";
import { ParameterForm } from "./ParameterForm";
import type { FlowTemplate } from "./templates-data";
import {
  TEMPLATE_CATEGORIES,
  applyTemplateParameters,
  defaultParameterValues,
} from "./templates-data";
import styles from "./TemplatesPage.module.css";

export interface TemplatePreviewProps {
  template: FlowTemplate | null;
  onClose: () => void;
  /**
   * Sprint 5 — parametric templates. The page receives the *rendered*
   * source (placeholders substituted) so it can pre-load the editor with
   * the user's filled-in values.
   */
  onOpenInEditor: (template: FlowTemplate, renderedSource: string) => void;
  /** Test seam — render a textarea instead of Monaco in jsdom. */
  fallbackTextarea?: boolean;
}

function categoryLabel(value: FlowTemplate["category"]): string {
  return (
    TEMPLATE_CATEGORIES.find((c) => c.value === value)?.label ?? value
  );
}

export function TemplatePreview(props: TemplatePreviewProps): JSX.Element | null {
  const { template, onClose, onOpenInEditor, fallbackTextarea } = props;
  const [copied, setCopied] = useState(false);
  const [paramValues, setParamValues] = useState<Record<string, string>>({});

  // Close on Escape so the drawer behaves like a standard modal.
  useEffect(() => {
    if (!template) return;
    const onKey = (e: KeyboardEvent): void => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [template, onClose]);

  // Reset the "Copied" hint and re-seed parameter defaults whenever the
  // active template changes.
  useEffect(() => {
    setCopied(false);
    if (template) {
      setParamValues(defaultParameterValues(template));
    } else {
      setParamValues({});
    }
  }, [template?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  // Compute the rendered source — used both for the live preview and for
  // the "Copy" / "Open in Editor" actions, so what you see is what you get.
  const renderedSource = useMemo(() => {
    if (!template) return "";
    if (!template.parameters || template.parameters.length === 0) {
      return template.pythonSource;
    }
    return applyTemplateParameters(template.pythonSource, paramValues);
  }, [template, paramValues]);

  if (!template) return null;

  const handleCopy = async (): Promise<void> => {
    if (typeof navigator === "undefined" || !navigator.clipboard) return;
    try {
      await navigator.clipboard.writeText(renderedSource);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      // clipboard write can fail in test contexts; non-fatal.
    }
  };

  return (
    <>
      <div
        className={styles.drawerScrim}
        onClick={onClose}
        data-testid="template-preview-scrim"
        aria-hidden="true"
      />
      <aside
        className={styles.drawer}
        role="dialog"
        aria-modal="true"
        aria-labelledby="template-preview-title"
        data-testid="template-preview-drawer"
      >
        <header className={styles.drawerHeader}>
          <div>
            <h2 id="template-preview-title" className={styles.drawerTitle}>
              {template.name}
            </h2>
            <p className={styles.drawerSubtitle}>
              <span className={styles.categoryChip}>
                {categoryLabel(template.category)}
              </span>
              {"  "}
              {template.summary}
            </p>
          </div>
          <button
            type="button"
            className={styles.closeBtn}
            onClick={onClose}
            data-testid="template-preview-close"
            aria-label="Close preview"
          >
            ×
          </button>
        </header>

        <div className={styles.drawerBody}>
          <section
            className={styles.section}
            data-testid="template-preview-recipes"
          >
            <h3 className={styles.sectionTitle}>
              Verified recipes ({template.verifiedRecipes.length})
            </h3>
            <div className={styles.recipeChips}>
              {template.verifiedRecipes.map((r, i) => (
                <span
                  key={`${r}-${i}`}
                  className={styles.recipeChip}
                  data-testid={`recipe-chip-${r}-${i}`}
                >
                  {r}
                </span>
              ))}
            </div>
          </section>

          <section
            className={styles.section}
            data-testid="template-preview-datasets"
          >
            <h3 className={styles.sectionTitle}>
              Verified datasets ({template.verifiedDatasets.length})
            </h3>
            <div className={styles.datasetChips}>
              {template.verifiedDatasets.map((d) => (
                <span key={d} className={styles.datasetChip}>
                  {d}
                </span>
              ))}
            </div>
          </section>

          {template.parameters && template.parameters.length > 0 ? (
            <section
              className={styles.section}
              data-testid="template-preview-parameters"
            >
              <h3 className={styles.sectionTitle}>
                Parameters ({template.parameters.length})
              </h3>
              <ParameterForm
                parameters={template.parameters}
                values={paramValues}
                onChange={(name, value) =>
                  setParamValues((prev) => ({ ...prev, [name]: value }))
                }
              />
            </section>
          ) : null}

          <section className={styles.section}>
            <h3 className={styles.sectionTitle}>
              Python source
              {template.parameters && template.parameters.length > 0 ? (
                <span
                  style={{
                    marginLeft: 8,
                    fontSize: "var(--text-xs, 12px)",
                    color: "var(--fg-muted, #5b6470)",
                    fontWeight: 400,
                  }}
                >
                  (with substituted parameters)
                </span>
              ) : null}
            </h3>
            <div
              className={styles.editorHost}
              data-testid="template-preview-source"
            >
              <MonacoEditor
                value={renderedSource}
                readOnly
                height="380px"
                fallbackTextarea={fallbackTextarea}
              />
            </div>
          </section>

          <section className={styles.section}>
            <h3 className={styles.sectionTitle}>Tags</h3>
            <div className={styles.recipeChips}>
              {template.tags.map((t) => (
                <span key={t} className={styles.datasetChip}>
                  {t}
                </span>
              ))}
            </div>
          </section>
        </div>

        <footer className={styles.drawerFooter}>
          <button
            type="button"
            className={styles.primaryBtn}
            data-testid="template-preview-open"
            onClick={() => onOpenInEditor(template, renderedSource)}
          >
            Open in Editor
          </button>
          <button
            type="button"
            className={styles.secondaryBtn}
            data-testid="template-preview-copy"
            onClick={() => void handleCopy()}
          >
            Copy source
          </button>
          {copied ? (
            <span
              className={styles.copiedHint}
              role="status"
              data-testid="template-preview-copied"
            >
              Copied
            </span>
          ) : null}
        </footer>
      </aside>
    </>
  );
}
