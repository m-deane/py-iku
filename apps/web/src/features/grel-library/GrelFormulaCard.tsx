import type { GrelFormula } from "./formulas-data";
import { GREL_CATEGORIES } from "./formulas-data";
import styles from "./GrelLibraryPage.module.css";

export interface GrelFormulaCardProps {
  formula: GrelFormula;
  onSelect: (formula: GrelFormula) => void;
}

function categoryLabel(value: GrelFormula["category"]): string {
  return GREL_CATEGORIES.find((c) => c.value === value)?.label ?? value;
}

export function GrelFormulaCard({
  formula,
  onSelect,
}: GrelFormulaCardProps): JSX.Element {
  return (
    <button
      type="button"
      className={styles.card}
      data-testid={`grel-card-${formula.id}`}
      onClick={() => onSelect(formula)}
      aria-label={`Open formula ${formula.name}`}
    >
      <div className={styles.cardHead}>
        <h3 className={styles.cardTitle}>{formula.name}</h3>
        <span
          className={styles.categoryChip}
          aria-label={`category ${formula.category}`}
        >
          {categoryLabel(formula.category)}
        </span>
      </div>
      <p className={styles.cardSummary}>{formula.description}</p>
      <code
        className={styles.cardGrel}
        title={formula.grel}
        data-testid={`grel-card-grel-${formula.id}`}
      >
        {formula.grel}
      </code>
      <div className={styles.cardFoot}>
        <span className={styles.metric}>
          <span className={styles.metricStrong}>{formula.unit}</span>
        </span>
        <div
          className={styles.instrumentChips}
          data-testid={`grel-card-instruments-${formula.id}`}
        >
          {formula.relatedInstruments.map((i) => (
            <span key={i} className={styles.instrumentChip}>
              {i}
            </span>
          ))}
        </div>
      </div>
    </button>
  );
}
