/**
 * Schema-snapshot store.
 *
 * Per-source (hashed) schema snapshots persisted in localStorage. We key on a
 * cheap djb2-style hash of the *source code* so re-converting the same script
 * promotes the existing entry instead of stacking duplicates.
 *
 * The stored value is the *minimum* data the drift service needs: a flow dict
 * containing only datasets-with-schemas. Persisting full flows here would
 * bloat localStorage on long sessions; we keep snapshots tight.
 */
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export interface SchemaSnapshot {
  /** Truncated dict — only `datasets` and identifying metadata. */
  flow: Record<string, unknown>;
  /** Wall-clock timestamp of when the snapshot was last refreshed. */
  capturedAt: string;
}

export interface SchemaSnapshotsState {
  snapshots: Record<string, SchemaSnapshot>;
  /** Save / overwrite a snapshot for the given source-hash. */
  put: (sourceHash: string, snapshot: SchemaSnapshot) => void;
  /** Read a snapshot for the given source-hash. */
  get: (sourceHash: string) => SchemaSnapshot | null;
  /** Drop a snapshot. */
  remove: (sourceHash: string) => void;
  /** Wipe everything — used by tests + Settings → "Clear cache". */
  clear: () => void;
}

export function hashSource(source: string): string {
  let h = 5381;
  for (let i = 0; i < source.length; i += 1) {
    h = ((h << 5) + h + source.charCodeAt(i)) | 0;
  }
  return `src-${(h >>> 0).toString(36)}`;
}

/**
 * Project a flow dict down to the minimal shape we need to detect drift.
 * Anything other than `datasets` (and their schemas) is dropped to keep
 * localStorage tight.
 */
export function projectForSnapshot(
  flow: Record<string, unknown>,
): Record<string, unknown> {
  const datasets = Array.isArray(flow.datasets) ? flow.datasets : [];
  return {
    flow_name: flow.flow_name ?? "snapshot",
    total_datasets: datasets.length,
    total_recipes: 0,
    datasets,
    recipes: [],
  };
}

export const useSchemaSnapshots = create<SchemaSnapshotsState>()(
  persist(
    (set, get) => ({
      snapshots: {},
      put: (sourceHash, snapshot) => {
        set((state) => ({
          snapshots: { ...state.snapshots, [sourceHash]: snapshot },
        }));
      },
      get: (sourceHash) => get().snapshots[sourceHash] ?? null,
      remove: (sourceHash) => {
        set((state) => {
          const next = { ...state.snapshots };
          delete next[sourceHash];
          return { snapshots: next };
        });
      },
      clear: () => set({ snapshots: {} }),
    }),
    {
      name: "py-iku-schema-snapshots",
      storage: createJSONStorage(() => localStorage),
      version: 1,
    },
  ),
);
