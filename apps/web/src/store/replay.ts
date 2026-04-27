import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { ConversionMode } from "../state/flowStore";
import type { LlmProvider } from "../state/settingsStore";

/**
 * Replay / undo timeline store (Sprint 4 — power user).
 *
 * Captures every successful (or failed) conversion run so the user can scrub
 * back through their history, restore a previous source+result pair, or
 * compare a historical version against the current flow.
 *
 * Capacity: capped at MAX_RUNS (20). Older entries are dropped from the tail
 * with a `cleared` counter surfaced to the UI as a "Cleared older than X"
 * indicator.
 *
 * Persistence: localStorage via `zustand/persist` with key
 * `py-iku-studio-replay`. We deliberately do NOT persist the full flow JSON
 * untouched (it can be large) — instead the runs hold the raw payload but
 * the cap of 20 keeps the worst case bounded. If a flow is very large, the
 * older entries get pushed off naturally.
 */
export const MAX_RUNS = 20;

export type ReplayRunStatus = "success" | "error";

export interface ReplayRun {
  /** Stable client-generated id. */
  id: string;
  /** Wall-clock ms when the run completed. */
  timestamp: number;
  /** Source code that was converted. */
  source: string;
  /** Resulting flow JSON, or null if the run errored. */
  flow: Record<string, unknown> | null;
  /** Conversion mode used for this run. */
  mode: ConversionMode;
  /** LLM provider, when relevant. */
  provider?: LlmProvider;
  /** LLM model, when relevant. */
  model?: string;
  /** Outcome of the run. */
  status: ReplayRunStatus;
  /** Recipe count from the result (0 if errored or no flow). */
  recipeCount: number;
  /** Complexity score (rounded for display) — 0 if unknown. */
  complexity: number;
  /** Error title, if any. */
  errorTitle?: string;
  /**
   * Lightweight diff vs the previous run's flow. We don't compute a deep
   * structural diff (that's what the existing /diff page is for); we just
   * capture the deltas a user wants to see at a glance: recipe-count delta
   * and a small added/removed-recipes summary.
   */
  diffSummary?: ReplayDiffSummary;
}

export interface ReplayDiffSummary {
  /** previousRecipeCount → run.recipeCount delta. */
  recipeDelta: number;
  /** Recipe names added in this run. */
  added: string[];
  /** Recipe names removed in this run. */
  removed: string[];
}

export interface ReplayState {
  runs: ReplayRun[];
  /** How many runs were dropped off the tail to honour the MAX_RUNS cap. */
  cleared: number;
  /** Append a run. Newer runs are head-inserted. */
  recordRun: (
    entry: Omit<ReplayRun, "id" | "timestamp" | "diffSummary"> & {
      timestamp?: number;
      id?: string;
    },
  ) => void;
  /** Wipe history. */
  clear: () => void;
  /** Get a run by id. */
  get: (id: string) => ReplayRun | undefined;
}

let _idCounter = 0;
function makeRunId(): string {
  _idCounter += 1;
  return `run-${Date.now().toString(36)}-${_idCounter.toString(36)}`;
}

function recipeNamesOf(flow: Record<string, unknown> | null): string[] {
  if (!flow) return [];
  const recipes = flow.recipes;
  if (!Array.isArray(recipes)) return [];
  return recipes
    .map((r) => (r as { name?: string }).name)
    .filter((n): n is string => typeof n === "string");
}

function summariseDiff(
  prev: ReplayRun | undefined,
  next: Pick<ReplayRun, "flow" | "recipeCount">,
): ReplayDiffSummary {
  const prevNames = recipeNamesOf(prev?.flow ?? null);
  const nextNames = recipeNamesOf(next.flow);
  const prevSet = new Set(prevNames);
  const nextSet = new Set(nextNames);
  const added = nextNames.filter((n) => !prevSet.has(n));
  const removed = prevNames.filter((n) => !nextSet.has(n));
  return {
    recipeDelta: next.recipeCount - (prev?.recipeCount ?? 0),
    added,
    removed,
  };
}

export const useReplayStore = create<ReplayState>()(
  persist(
    (set, get) => ({
      runs: [],
      cleared: 0,

      recordRun: (entry) => {
        set((state) => {
          const ts = entry.timestamp ?? Date.now();
          const id = entry.id ?? makeRunId();
          const previous = state.runs[0];
          const diffSummary = summariseDiff(previous, {
            flow: entry.flow,
            recipeCount: entry.recipeCount,
          });
          const next: ReplayRun = {
            ...entry,
            id,
            timestamp: ts,
            diffSummary,
          };
          const head = [next, ...state.runs];
          const trimmed = head.slice(0, MAX_RUNS);
          const droppedThisCycle = head.length - trimmed.length;
          return {
            runs: trimmed,
            cleared: state.cleared + droppedThisCycle,
          };
        });
      },

      clear: () => set({ runs: [], cleared: 0 }),

      get: (id) => get().runs.find((r) => r.id === id),
    }),
    {
      name: "py-iku-studio-replay",
      storage: createJSONStorage(() => localStorage),
      version: 1,
      partialize: (state) => ({
        runs: state.runs,
        cleared: state.cleared,
      }),
    },
  ),
);

/**
 * Format a unix-ms timestamp as a short clock label ("14:32") for compact
 * timeline cells. Falls back to ISO date if the value is invalid.
 */
export function formatRunTimestamp(ts: number): string {
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return String(ts);
  return d.toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  });
}
