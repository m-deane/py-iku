import { useMemo, useState } from "react";
import {
  computeDiff,
  exceedsThreshold,
  FIXTURES,
  type DiffRow,
  type ForwardCurve,
} from "./curve-fixtures";
import styles from "./CurveDiffPage.module.css";

const DEFAULT_THRESHOLD_PCT = 1.0;

function formatPrice(p: number | null): string {
  if (p === null) return "—";
  return p.toFixed(2);
}

function formatPct(p: number | null): string {
  if (p === null) return "—";
  const sign = p > 0 ? "+" : "";
  return `${sign}${p.toFixed(2)}%`;
}

function formatAbs(p: number | null): string {
  if (p === null) return "—";
  const sign = p > 0 ? "+" : "";
  return `${sign}${p.toFixed(2)}`;
}

function summary(rows: DiffRow[], threshold: number): {
  flagged: number;
  maxAbs: number;
  meanAbs: number;
} {
  const validDeltas = rows
    .map((r) => r.delta_abs)
    .filter((d): d is number => d !== null);
  if (validDeltas.length === 0) {
    return { flagged: 0, maxAbs: 0, meanAbs: 0 };
  }
  const flagged = rows.filter((r) => exceedsThreshold(r, threshold)).length;
  const maxAbs = validDeltas.reduce(
    (acc, v) => (Math.abs(v) > Math.abs(acc) ? v : acc),
    0,
  );
  const meanAbs =
    validDeltas.reduce((s, v) => s + v, 0) / validDeltas.length;
  return { flagged, maxAbs, meanAbs };
}

export interface CurveDiffPageProps {
  /** Test seam — supply alternative curves. Defaults to the embedded fixtures. */
  curves?: readonly ForwardCurve[];
}

/**
 * Counterparty-curve diff — side-by-side comparison of two forward curves
 * with absolute and percentage deltas, threshold highlighting, and a
 * summary strip.
 *
 * v1 ships with two embedded fixtures (yesterday vs today WTI). The two
 * pickers select from the embedded set; later iterations swap in API-loaded
 * curves from a snapshot store.
 */
export function CurveDiffPage(
  props: CurveDiffPageProps = {},
): JSX.Element {
  const curves = props.curves ?? FIXTURES;

  // Default selection: first as A, last as B (so the synthetic example
  // shows non-zero deltas out of the box).
  const [aId, setAId] = useState<string>(curves[0]?.id ?? "");
  const [bId, setBId] = useState<string>(
    curves[curves.length - 1]?.id ?? "",
  );
  const [thresholdPct, setThresholdPct] = useState<number>(
    DEFAULT_THRESHOLD_PCT,
  );

  const a = useMemo(
    () => curves.find((c) => c.id === aId) ?? curves[0],
    [aId, curves],
  );
  const b = useMemo(
    () => curves.find((c) => c.id === bId) ?? curves[curves.length - 1],
    [bId, curves],
  );

  const rows: DiffRow[] = useMemo(() => {
    if (!a || !b) return [];
    return computeDiff(a, b);
  }, [a, b]);

  const { flagged, maxAbs, meanAbs } = useMemo(
    () => summary(rows, thresholdPct),
    [rows, thresholdPct],
  );

  return (
    <section className={styles.page} data-testid="curve-diff-page">
      <header className={styles.header}>
        <h1 className={styles.title}>Counterparty Curve Diff</h1>
      </header>

      <p className={styles.subtitle}>
        Pick two forward curves and Studio renders them tenor-by-tenor with
        absolute and percentage deltas. Tenors whose |Δ%| exceeds the
        highlight threshold get a warn-coloured row and a flag badge.
        Embedded fixtures are synthetic WTI yesterday-vs-today; later
        iterations swap in counterparty snapshots.
      </p>

      <div className={styles.pickers}>
        <CurvePicker
          label="Curve A (baseline)"
          curves={curves}
          value={aId}
          onChange={setAId}
          testIdPrefix="curve-a"
        />
        <CurvePicker
          label="Curve B (compare)"
          curves={curves}
          value={bId}
          onChange={setBId}
          testIdPrefix="curve-b"
        />
      </div>

      <div className={styles.thresholdRow}>
        <label
          className={styles.thresholdLabel}
          htmlFor="curve-diff-threshold"
        >
          Highlight when |Δ%| ≥
        </label>
        <input
          id="curve-diff-threshold"
          type="number"
          step="0.1"
          min={0}
          className={styles.thresholdInput}
          value={thresholdPct}
          onChange={(e) =>
            setThresholdPct(Number.parseFloat(e.target.value) || 0)
          }
          data-testid="curve-diff-threshold"
        />
        <span className={styles.thresholdLabel}>%</span>
      </div>

      <div className={styles.summaryStrip} data-testid="curve-diff-summary">
        <div className={styles.summaryItem}>
          <span className={styles.summaryLabel}>Tenors</span>
          <span className={styles.summaryValue}>{rows.length}</span>
        </div>
        <div className={styles.summaryItem}>
          <span className={styles.summaryLabel}>Flagged</span>
          <span
            className={styles.summaryValue}
            data-testid="curve-diff-flagged-count"
          >
            {flagged}
          </span>
        </div>
        <div className={styles.summaryItem}>
          <span className={styles.summaryLabel}>Max |Δ|</span>
          <span className={styles.summaryValue}>
            {formatAbs(maxAbs)}
          </span>
        </div>
        <div className={styles.summaryItem}>
          <span className={styles.summaryLabel}>Mean Δ</span>
          <span className={styles.summaryValue}>
            {formatAbs(meanAbs)}
          </span>
        </div>
      </div>

      {rows.length === 0 ? (
        <div className={styles.empty} data-testid="curve-diff-empty">
          Pick two curves to compare.
        </div>
      ) : (
        <div className={styles.tableWrap}>
          <table
            className={styles.table}
            data-testid="curve-diff-table"
          >
            <thead>
              <tr>
                <th scope="col">Tenor</th>
                <th scope="col">Forward</th>
                <th scope="col">A · {a?.unit}</th>
                <th scope="col">B · {b?.unit}</th>
                <th scope="col">Δ abs</th>
                <th scope="col">Δ %</th>
                <th scope="col" aria-label="flag"></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => {
                const isFlagged = exceedsThreshold(r, thresholdPct);
                const deltaClass =
                  r.delta_abs === null
                    ? styles.numericMuted
                    : r.delta_abs > 0
                      ? `${styles.numericCell} ${styles.deltaPos}`
                      : r.delta_abs < 0
                        ? `${styles.numericCell} ${styles.deltaNeg}`
                        : styles.numericCell;
                return (
                  <tr
                    key={r.tenor}
                    className={isFlagged ? styles.flagged : ""}
                    data-testid={`curve-diff-row-${r.tenor}`}
                    data-flagged={isFlagged ? "true" : "false"}
                  >
                    <td>{r.tenor}</td>
                    <td className={styles.numericMuted}>
                      {r.forward_date}
                    </td>
                    <td className={styles.numericCell}>
                      {formatPrice(r.price_a)}
                    </td>
                    <td className={styles.numericCell}>
                      {formatPrice(r.price_b)}
                    </td>
                    <td
                      className={deltaClass}
                      data-testid={`curve-diff-delta-${r.tenor}`}
                    >
                      {formatAbs(r.delta_abs)}
                    </td>
                    <td className={deltaClass}>
                      {formatPct(r.delta_pct)}
                    </td>
                    <td>
                      {isFlagged ? (
                        <span className={styles.flagBadge}>flag</span>
                      ) : null}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

interface CurvePickerProps {
  label: string;
  curves: readonly ForwardCurve[];
  value: string;
  onChange: (id: string) => void;
  testIdPrefix: string;
}

function CurvePicker(props: CurvePickerProps): JSX.Element {
  const { label, curves, value, onChange, testIdPrefix } = props;
  const active = curves.find((c) => c.id === value);
  return (
    <div
      className={styles.pickerCard}
      data-testid={`${testIdPrefix}-card`}
    >
      <span className={styles.pickerLabel}>{label}</span>
      <select
        className={styles.pickerSelect}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        aria-label={label}
        data-testid={`${testIdPrefix}-select`}
      >
        {curves.map((c) => (
          <option key={c.id} value={c.id}>
            {c.label}
          </option>
        ))}
      </select>
      {active ? (
        <span
          className={styles.pickerMeta}
          data-testid={`${testIdPrefix}-meta`}
        >
          {active.commodity} · {active.points.length} tenors · as_of {active.as_of_date}
        </span>
      ) : null}
    </div>
  );
}
