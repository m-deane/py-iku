/**
 * Synthetic forward-curve fixtures for the curve-diff page.
 *
 * Two curves drawn from real WTI tenor structure (front-month CL through
 * 24-month deferred). Curve B is "today" with a small contango shift
 * relative to curve A's "yesterday" — exactly the shape a counterparty
 * snapshot would show after an overnight roll plus a Brent-led shift.
 *
 * Numbers are illustrative — they are NOT a price feed. They are designed
 * so a tenor-aware diff exposes both small and large deltas, which is
 * what the threshold highlighter is meant to surface.
 */

export interface CurvePoint {
  tenor: string;
  /** Forward date in ISO "YYYY-MM" — first of contract month. */
  forward_date: string;
  price: number;
}

export interface ForwardCurve {
  id: string;
  label: string;
  /** Counterparty / curve provider — for the "two date pickers" UI later. */
  source: string;
  as_of_date: string;
  commodity: string;
  unit: string;
  points: CurvePoint[];
}

const CURVE_A_POINTS: CurvePoint[] = [
  { tenor: "M+1", forward_date: "2026-05", price: 78.55 },
  { tenor: "M+2", forward_date: "2026-06", price: 78.32 },
  { tenor: "M+3", forward_date: "2026-07", price: 78.02 },
  { tenor: "M+4", forward_date: "2026-08", price: 77.71 },
  { tenor: "M+5", forward_date: "2026-09", price: 77.4 },
  { tenor: "M+6", forward_date: "2026-10", price: 77.08 },
  { tenor: "M+7", forward_date: "2026-11", price: 76.75 },
  { tenor: "M+8", forward_date: "2026-12", price: 76.4 },
  { tenor: "M+9", forward_date: "2027-01", price: 76.0 },
  { tenor: "M+10", forward_date: "2027-02", price: 75.62 },
  { tenor: "M+11", forward_date: "2027-03", price: 75.21 },
  { tenor: "M+12", forward_date: "2027-04", price: 74.79 },
  { tenor: "M+15", forward_date: "2027-07", price: 73.51 },
  { tenor: "M+18", forward_date: "2027-10", price: 72.4 },
  { tenor: "M+21", forward_date: "2028-01", price: 71.6 },
  { tenor: "M+24", forward_date: "2028-04", price: 71.05 },
];

// Today: a contango shift from M+1..M+6 (front rallied), and a small
// deferred fade. Roughly +0.6 / +0.45 / +0.3 across the front, then
// flattens, with a single big tenor jump at M+8 to test the threshold
// highlighter (Δ = +1.45 ⇒ |Δ%| ~1.9%).
const CURVE_B_POINTS: CurvePoint[] = [
  { tenor: "M+1", forward_date: "2026-05", price: 79.15 },
  { tenor: "M+2", forward_date: "2026-06", price: 78.77 },
  { tenor: "M+3", forward_date: "2026-07", price: 78.32 },
  { tenor: "M+4", forward_date: "2026-08", price: 77.84 },
  { tenor: "M+5", forward_date: "2026-09", price: 77.51 },
  { tenor: "M+6", forward_date: "2026-10", price: 77.12 },
  { tenor: "M+7", forward_date: "2026-11", price: 76.7 },
  { tenor: "M+8", forward_date: "2026-12", price: 77.85 },
  { tenor: "M+9", forward_date: "2027-01", price: 75.92 },
  { tenor: "M+10", forward_date: "2027-02", price: 75.48 },
  { tenor: "M+11", forward_date: "2027-03", price: 75.05 },
  { tenor: "M+12", forward_date: "2027-04", price: 74.6 },
  { tenor: "M+15", forward_date: "2027-07", price: 73.32 },
  { tenor: "M+18", forward_date: "2027-10", price: 72.18 },
  { tenor: "M+21", forward_date: "2028-01", price: 71.4 },
  { tenor: "M+24", forward_date: "2028-04", price: 70.83 },
];

export const CURVE_A: ForwardCurve = {
  id: "wti-2026-04-25",
  label: "WTI close — 2026-04-25",
  source: "Counterparty A snapshot",
  as_of_date: "2026-04-25",
  commodity: "WTI",
  unit: "USD/bbl",
  points: CURVE_A_POINTS,
};

export const CURVE_B: ForwardCurve = {
  id: "wti-2026-04-26",
  label: "WTI close — 2026-04-26",
  source: "Counterparty A snapshot",
  as_of_date: "2026-04-26",
  commodity: "WTI",
  unit: "USD/bbl",
  points: CURVE_B_POINTS,
};

export const FIXTURES: readonly ForwardCurve[] = [CURVE_A, CURVE_B];

export interface DiffRow {
  tenor: string;
  forward_date: string;
  price_a: number | null;
  price_b: number | null;
  delta_abs: number | null;
  delta_pct: number | null;
}

/**
 * Compute the curve diff. Tenors that exist in either curve are returned;
 * tenors missing from one side return ``null`` for that side and ``null``
 * for both deltas (so the table can render an em-dash).
 *
 * Pure function — no React, no DOM. Tests assert on it directly.
 */
export function computeDiff(a: ForwardCurve, b: ForwardCurve): DiffRow[] {
  const aByTenor = new Map(a.points.map((p) => [p.tenor, p]));
  const bByTenor = new Map(b.points.map((p) => [p.tenor, p]));
  const allTenors = new Set<string>([
    ...a.points.map((p) => p.tenor),
    ...b.points.map((p) => p.tenor),
  ]);

  const rows: DiffRow[] = [];
  for (const tenor of allTenors) {
    const pa = aByTenor.get(tenor) ?? null;
    const pb = bByTenor.get(tenor) ?? null;
    const price_a = pa?.price ?? null;
    const price_b = pb?.price ?? null;
    let delta_abs: number | null = null;
    let delta_pct: number | null = null;
    if (price_a !== null && price_b !== null) {
      delta_abs = price_b - price_a;
      delta_pct = price_a !== 0 ? (delta_abs / price_a) * 100 : null;
    }
    rows.push({
      tenor,
      forward_date:
        pa?.forward_date ?? pb?.forward_date ?? "—",
      price_a,
      price_b,
      delta_abs,
      delta_pct,
    });
  }
  // Sort by forward_date so the table reads as a real curve.
  rows.sort((x, y) => x.forward_date.localeCompare(y.forward_date));
  return rows;
}

/** Returns true when |delta_pct| (or |delta_abs| as a proxy) exceeds the threshold. */
export function exceedsThreshold(
  row: DiffRow,
  threshold_pct: number,
): boolean {
  if (row.delta_pct === null) return false;
  return Math.abs(row.delta_pct) >= threshold_pct;
}
