/**
 * Fixtures store — holds the embedded fixture rows the user opted to load
 * from a shared flow. Subsequent conversions can reference these rows
 * without re-fetching the share token.
 *
 * Sprint 4D follow-up companion to share-with-embedded-fixtures: the
 * SharePage's "Run with embedded fixtures" button drops the inlined bundle
 * here, and downstream surfaces (e.g. the Convert page) can read the slice
 * to seed a sandbox or preview pane.
 *
 * Persistence is intentionally OFF — fixtures are session-scoped because a
 * recipient's share view should not silently retain other people's data
 * across reloads.
 */
import { create } from "zustand";

export interface FixturesPayload {
  /** Per-input-dataset row cap declared by the share producer. */
  nRows: number;
  /** Raw rows keyed by dataset name. */
  datasets: Record<string, Array<Record<string, unknown>>>;
}

export interface FixturesState {
  fixtures: FixturesPayload | null;
  /** Replace the loaded bundle. Pass null to clear. */
  setFixtures: (bundle: FixturesPayload | null) => void;
  /** Clear the slice — used when a tab/page unmounts. */
  reset: () => void;
}

export const useFixturesStore = create<FixturesState>()((set) => ({
  fixtures: null,
  setFixtures: (fixtures) => set({ fixtures }),
  reset: () => set({ fixtures: null }),
}));

/** Pure helper — counts rows across every dataset in *bundle*. */
export function totalFixtureRows(bundle: FixturesPayload | null): number {
  if (!bundle) return 0;
  return Object.values(bundle.datasets).reduce(
    (acc, rows) => acc + (Array.isArray(rows) ? rows.length : 0),
    0,
  );
}

/** Pure helper — counts the keys (datasets) in *bundle*. */
export function fixtureDatasetCount(bundle: FixturesPayload | null): number {
  if (!bundle) return 0;
  return Object.keys(bundle.datasets).length;
}
