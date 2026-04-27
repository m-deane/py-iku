/**
 * Global "Show only low-confidence" toggle for the canvas. When ``on``,
 * the parent canvas dims high/rule-based recipes to opacity 0.3 (the
 * actual dimming is applied by setting `data.dimmed` on each non-low
 * recipe node — flow-viz already supports the `dimmed` field).
 */

export interface LowConfidenceToggleProps {
  enabled: boolean;
  onChange: (next: boolean) => void;
}

export function LowConfidenceToggle(
  props: LowConfidenceToggleProps,
): JSX.Element {
  return (
    <label
      data-testid="low-confidence-toggle"
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "0.4rem",
        padding: "0.3rem 0.6rem",
        borderRadius: "var(--radius-sm, 4px)",
        border: "1px solid var(--border, #e0e0e0)",
        cursor: "pointer",
        fontSize: "var(--text-xs, 12px)",
        background: props.enabled
          ? "var(--danger-bg, #fee4e2)"
          : "transparent",
        color: props.enabled ? "var(--danger-fg, #b42318)" : "inherit",
      }}
    >
      <input
        type="checkbox"
        data-testid="low-confidence-toggle-checkbox"
        checked={props.enabled}
        onChange={(e) => props.onChange(e.target.checked)}
        aria-label="Show only low-confidence recipes"
      />
      Show only low-confidence
    </label>
  );
}
