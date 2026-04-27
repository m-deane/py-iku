import { useEffect, useState } from "react";
import { buildInsertSnippet, GREL_CATEGORIES, type GrelFormula } from "./formulas-data";
import styles from "./GrelLibraryPage.module.css";

export interface GrelFormulaPreviewProps {
  formula: GrelFormula | null;
  onClose: () => void;
  /** Prepend the comment+pandas snippet to whatever is currently in the editor. */
  onInsertIntoEditor: (formula: GrelFormula) => void;
}

function categoryLabel(value: GrelFormula["category"]): string {
  return GREL_CATEGORIES.find((c) => c.value === value)?.label ?? value;
}

export function GrelFormulaPreview(
  props: GrelFormulaPreviewProps,
): JSX.Element | null {
  const { formula, onClose, onInsertIntoEditor } = props;
  const [copiedGrel, setCopiedGrel] = useState(false);

  useEffect(() => {
    if (!formula) return;
    const onKey = (e: KeyboardEvent): void => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [formula, onClose]);

  useEffect(() => {
    setCopiedGrel(false);
  }, [formula?.id]);

  if (!formula) return null;

  const handleCopyGrel = async (): Promise<void> => {
    if (typeof navigator === "undefined" || !navigator.clipboard) return;
    try {
      await navigator.clipboard.writeText(formula.grel);
      setCopiedGrel(true);
      window.setTimeout(() => setCopiedGrel(false), 1800);
    } catch {
      // clipboard write can fail in test contexts; non-fatal.
    }
  };

  const insertSnippet = buildInsertSnippet(formula);

  return (
    <>
      <div
        className={styles.scrim}
        onClick={onClose}
        data-testid="grel-preview-scrim"
        aria-hidden="true"
      />
      <div
        className={styles.modal}
        role="dialog"
        aria-modal="true"
        aria-labelledby="grel-preview-title"
        data-testid="grel-preview-modal"
      >
        <header className={styles.modalHeader}>
          <div>
            <h2 id="grel-preview-title" className={styles.modalTitle}>
              {formula.name}
            </h2>
            <p className={styles.modalSubtitle}>
              <span className={styles.categoryChip}>
                {categoryLabel(formula.category)}
              </span>
              {"  "}
              {formula.description}
            </p>
          </div>
          <button
            type="button"
            className={styles.closeBtn}
            onClick={onClose}
            data-testid="grel-preview-close"
            aria-label="Close preview"
          >
            ×
          </button>
        </header>

        <div className={styles.modalBody}>
          <section className={styles.section}>
            <h3 className={styles.sectionTitle}>GREL expression</h3>
            <pre
              className={styles.codeBlock}
              data-testid="grel-preview-grel"
            >
              {formula.grel}
            </pre>
          </section>

          <section className={styles.section}>
            <h3 className={styles.sectionTitle}>pandas equivalent</h3>
            <pre
              className={styles.codeBlock}
              data-testid="grel-preview-pandas"
            >
              {formula.pandas}
            </pre>
          </section>

          <section className={styles.section}>
            <h3 className={styles.sectionTitle}>
              Unit · {formula.unit}
            </h3>
            <div
              className={styles.instrumentChips}
              data-testid="grel-preview-instruments"
            >
              {formula.relatedInstruments.map((i) => (
                <span key={i} className={styles.instrumentChip}>
                  {i}
                </span>
              ))}
            </div>
          </section>

          <section className={styles.section}>
            <h3 className={styles.sectionTitle}>Worked example</h3>
            <table
              className={styles.exampleTable}
              data-testid="grel-preview-example"
            >
              <thead>
                <tr>
                  <th>Input</th>
                  <th>Value</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(formula.example.inputs).map(([k, v]) => (
                  <tr key={k}>
                    <td>{k}</td>
                    <td className={styles.numeric}>{v}</td>
                  </tr>
                ))}
                <tr>
                  <td>
                    <strong>Output</strong>
                  </td>
                  <td className={styles.numeric}>
                    <strong data-testid="grel-preview-example-output">
                      {formula.example.output}
                    </strong>
                  </td>
                </tr>
              </tbody>
            </table>
            <p className={styles.exampleNotes}>{formula.example.notes}</p>
          </section>

          <section className={styles.section}>
            <h3 className={styles.sectionTitle}>
              Insert preview (commented header + pandas line)
            </h3>
            <pre
              className={styles.codeBlock}
              data-testid="grel-preview-insert-snippet"
            >
              {insertSnippet}
            </pre>
          </section>
        </div>

        <footer className={styles.modalFooter}>
          <button
            type="button"
            className={styles.primaryBtn}
            data-testid="grel-preview-insert"
            onClick={() => onInsertIntoEditor(formula)}
          >
            Insert into editor
          </button>
          <button
            type="button"
            className={styles.secondaryBtn}
            data-testid="grel-preview-copy-grel"
            onClick={() => void handleCopyGrel()}
          >
            Copy GREL
          </button>
          {copiedGrel ? (
            <span
              className={styles.copiedHint}
              role="status"
              data-testid="grel-preview-copied"
            >
              Copied
            </span>
          ) : null}
        </footer>
      </div>
    </>
  );
}
