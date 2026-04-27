/**
 * ConfidencePanel — summary of LLM mapping confidence for a converted flow.
 *
 * Layout:
 *   [count summary]  "12 recipes converted • 11 high (≥85%) • 1 medium (≥60%) • 0 low"
 *   [segmented bar]  green / amber / red proportional to bucket counts
 *   [actions]        "Review low-confidence →" appears iff `low > 0`
 *
 * Click handlers:
 *   - clicking a segment selects the matching band so the canvas can
 *     highlight just those recipes (parent-driven via `onSelectBand`).
 *   - clicking "Review low-confidence →" sets the band filter to "low"
 *     and turns the global low-only toggle on (parent owns that state).
 *
 * Tokens used (semantic, no inline hex):
 *   --success-bg / --success-fg / --success-border  (high)
 *   --warn-bg    / --warn-fg    / --warn-border     (medium)
 *   --danger-bg  / --danger-fg  / --danger-border   (low)
 *   --surface-sunken / --fg-muted                    (rule-based)
 */

import type { Recipe } from "../../api/types";
import { bandFor } from "@flow-viz/index";

export interface ConfidenceCounts {
  total: number;
  high: number;
  medium: number;
  low: number;
  ruleBased: number;
}

export type SelectableBand = "high" | "medium" | "low" | "rule-based" | null;

export interface ConfidencePanelProps {
  recipes: ReadonlyArray<Recipe>;
  /** Callback when the user clicks a segment or the "Review" button. */
  onSelectBand?: (band: SelectableBand) => void;
  /** Currently-selected band — drives an active-state ring on the segment. */
  selectedBand?: SelectableBand;
  /** Optional click handler for the global "Review low-confidence" CTA. */
  onReviewLow?: () => void;
}

/** Pure helper exported for tests. */
export function countConfidence(
  recipes: ReadonlyArray<Recipe>,
): ConfidenceCounts {
  let high = 0;
  let medium = 0;
  let low = 0;
  let ruleBased = 0;
  for (const r of recipes) {
    const band = bandFor(r.confidence);
    if (band === "high") high += 1;
    else if (band === "medium") medium += 1;
    else if (band === "low") low += 1;
    else ruleBased += 1;
  }
  return { total: recipes.length, high, medium, low, ruleBased };
}

interface SegmentDef {
  band: Exclude<SelectableBand, null>;
  label: string;
  count: number;
  bg: string;
  fg: string;
  border: string;
  testId: string;
}

function segments(counts: ConfidenceCounts): SegmentDef[] {
  return [
    {
      band: "high",
      label: "high",
      count: counts.high,
      bg: "var(--success-bg, var(--surface-sunken, #ecfdf5))",
      fg: "var(--success-fg, #027a48)",
      border: "var(--success-border, #6ce9a6)",
      testId: "confidence-segment-high",
    },
    {
      band: "medium",
      label: "medium",
      count: counts.medium,
      bg: "var(--warn-bg, #fef3c7)",
      fg: "var(--warn-fg, #b54708)",
      border: "var(--warn-border, #fcd34d)",
      testId: "confidence-segment-medium",
    },
    {
      band: "low",
      label: "low",
      count: counts.low,
      bg: "var(--danger-bg, #fee4e2)",
      fg: "var(--danger-fg, #b42318)",
      border: "var(--danger-border, #fecdca)",
      testId: "confidence-segment-low",
    },
    {
      band: "rule-based",
      label: "rule-based",
      count: counts.ruleBased,
      bg: "var(--surface-sunken, #f2f4f7)",
      fg: "var(--fg-muted, #5b6470)",
      border: "var(--border, #e0e0e0)",
      testId: "confidence-segment-rule-based",
    },
  ];
}

export function ConfidencePanel(props: ConfidencePanelProps): JSX.Element {
  const counts = countConfidence(props.recipes);
  const segs = segments(counts);
  const denom = Math.max(1, counts.total);
  const showReview = counts.low > 0;

  return (
    <section
      data-testid="confidence-panel"
      aria-label="Conversion confidence summary"
      style={{
        border: "1px solid var(--border, #e0e0e0)",
        borderRadius: "var(--radius-md, 6px)",
        padding: "0.6rem 0.8rem",
        marginBottom: "0.75rem",
        background: "var(--surface, transparent)",
      }}
    >
      <header
        data-testid="confidence-panel-summary"
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "0.4rem",
          alignItems: "baseline",
          fontSize: "var(--text-sm, 13px)",
          marginBottom: "0.5rem",
        }}
      >
        <strong>{counts.total} recipes converted</strong>
        <span style={{ color: "var(--fg-muted, #5b6470)" }}>
          • {counts.high} high (≥85%) • {counts.medium} medium (≥60%) •{" "}
          {counts.low} low
          {counts.ruleBased > 0 ? ` • ${counts.ruleBased} rule-based` : null}
        </span>
      </header>
      <div
        role="group"
        aria-label="Confidence band distribution"
        style={{
          display: "flex",
          height: 10,
          borderRadius: "var(--radius-pill, 9999px)",
          overflow: "hidden",
          background: "var(--surface-sunken, #f2f4f7)",
        }}
      >
        {segs.map((s) => {
          const pct = (s.count / denom) * 100;
          if (pct === 0) return null;
          const active = props.selectedBand === s.band;
          return (
            <button
              key={s.band}
              type="button"
              data-testid={s.testId}
              data-band={s.band}
              data-count={s.count}
              aria-label={`${s.count} ${s.label} confidence recipes`}
              aria-pressed={active}
              onClick={() => props.onSelectBand?.(active ? null : s.band)}
              style={{
                flex: `${pct} 0 0`,
                background: s.bg,
                color: s.fg,
                border: 0,
                outline: active ? `2px solid ${s.border}` : "none",
                outlineOffset: -2,
                cursor: "pointer",
                padding: 0,
                margin: 0,
              }}
              title={`${s.count} ${s.label}`}
            />
          );
        })}
      </div>
      {showReview && (
        <div style={{ marginTop: "0.5rem" }}>
          <button
            type="button"
            data-testid="confidence-review-low"
            onClick={() => {
              props.onReviewLow?.();
              props.onSelectBand?.("low");
            }}
            style={{
              padding: "0.35rem 0.7rem",
              borderRadius: "var(--radius-sm, 4px)",
              border: "1px solid var(--danger-border, #fecdca)",
              background: "var(--danger-bg, #fee4e2)",
              color: "var(--danger-fg, #b42318)",
              cursor: "pointer",
              fontSize: "var(--text-xs, 12px)",
              fontWeight: 600,
            }}
          >
            Review low-confidence →
          </button>
        </div>
      )}
    </section>
  );
}
