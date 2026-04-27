import type { FlowTemplate } from "./templates-data";
import { TEMPLATE_CATEGORIES } from "./templates-data";
import styles from "./TemplatesPage.module.css";

export interface TemplateCardProps {
  template: FlowTemplate;
  onSelect: (template: FlowTemplate) => void;
}

function categoryLabel(value: FlowTemplate["category"]): string {
  return (
    TEMPLATE_CATEGORIES.find((c) => c.value === value)?.label ?? value
  );
}

export function TemplateCard({ template, onSelect }: TemplateCardProps): JSX.Element {
  return (
    <button
      type="button"
      className={styles.card}
      data-testid={`template-card-${template.id}`}
      onClick={() => onSelect(template)}
      aria-label={`Open template ${template.name}`}
    >
      <div className={styles.cardHead}>
        <h3 className={styles.cardTitle}>{template.name}</h3>
        <span
          className={styles.categoryChip}
          aria-label={`category ${template.category}`}
        >
          {categoryLabel(template.category)}
        </span>
      </div>
      <p className={styles.cardSummary}>{template.summary}</p>
      <div
        className={styles.personas}
        aria-label="Target personas"
        data-testid={`template-personas-${template.id}`}
      >
        {template.personas.map((p) => (
          <span key={p} className={styles.personaBadge}>
            {p}
          </span>
        ))}
      </div>
      <div className={styles.cardFoot}>
        <span className={styles.metric}>
          <span className={styles.metricStrong}>
            {template.estimatedSavingMinutes} min
          </span>
          {" "}saved
        </span>
        <span className={styles.metric}>
          <span className={styles.metricStrong}>
            {template.verifiedRecipes.length}
          </span>
          {" "}recipe{template.verifiedRecipes.length === 1 ? "" : "s"}
        </span>
      </div>
    </button>
  );
}
