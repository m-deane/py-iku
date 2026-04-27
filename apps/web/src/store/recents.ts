import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

/**
 * Recents + Pinned flow rail.
 *
 * Lightweight per-browser memory of conversions the user has just run, plus
 * an explicitly pinned subset that survives the rolling-10 cap. Each entry
 * is a thin descriptor; the actual source code is what gets re-loaded into
 * the editor when the user clicks an item.
 *
 * Storage:
 *   - localStorage via zustand `persist` middleware
 *   - key: "py-iku-studio-recents"
 *   - schema versioned (`version: 1`) so we can migrate later without a wipe
 *
 * Caps:
 *   - `recents` is capped at MAX_RECENTS (10). New items push older items off
 *     the tail. If a flow is re-converted, its existing recent entry is
 *     promoted to head rather than duplicated.
 *   - `pinned` is uncapped — the UI shows a "+ pin" affordance on each
 *     conversion result so the user opts in explicitly.
 */
export const MAX_RECENTS = 10;

export interface RecentFlow {
  /** Stable client-generated id. Matches across recents/pinned. */
  id: string;
  /** Display label — flow name, first input filename, or first comment line. */
  name: string;
  /** Full Python source, sufficient to reload the editor verbatim. */
  source: string;
  /** Number of recipes the conversion produced (for the rail subtitle). */
  recipeCount: number;
  /** Wall-clock ms timestamp when the entry was last touched. */
  timestamp: number;
}

export interface RecentsState {
  recents: RecentFlow[];
  pinned: RecentFlow[];
  /** Insert / promote a flow at the head of `recents`. */
  addRecent: (entry: Omit<RecentFlow, "timestamp"> & { timestamp?: number }) => void;
  /** Toggle pinned state. If pinned, also remains in recents (id is shared). */
  togglePin: (id: string) => void;
  /** True if id appears in `pinned`. */
  isPinned: (id: string) => boolean;
  /** Remove from both rails. */
  remove: (id: string) => void;
  /** Wipe both rails. */
  clear: () => void;
}

/**
 * Derive a sensible display label from a Python source blob.
 *
 * Order of preference:
 *   1. Explicit `name` from caller (preferred — the conversion API knows it)
 *   2. First non-empty `# comment` line (stripped of leading `#` and ws)
 *   3. First non-empty code line, truncated
 *   4. Fallback to "Untitled flow"
 */
export function deriveFlowName(source: string, explicit?: string): string {
  if (explicit && explicit.trim()) return explicit.trim().slice(0, 80);
  const lines = source.split(/\r?\n/);
  for (const line of lines) {
    const t = line.trim();
    if (!t) continue;
    if (t.startsWith("#")) {
      const stripped = t.replace(/^#+\s*/, "").trim();
      if (stripped) return stripped.slice(0, 80);
    }
  }
  for (const line of lines) {
    const t = line.trim();
    if (t) return t.slice(0, 80);
  }
  return "Untitled flow";
}

export const useRecentsStore = create<RecentsState>()(
  persist(
    (set, get) => ({
      recents: [],
      pinned: [],

      addRecent: (entry) => {
        const ts = entry.timestamp ?? Date.now();
        set((state) => {
          // Promote-or-insert: dedupe by id, head insert, then trim tail.
          const filtered = state.recents.filter((r) => r.id !== entry.id);
          const next: RecentFlow[] = [
            { ...entry, timestamp: ts },
            ...filtered,
          ].slice(0, MAX_RECENTS);

          // If this id is pinned, refresh the pinned copy in lockstep so
          // the rails never drift on name/recipeCount/timestamp.
          const pinnedIdx = state.pinned.findIndex((p) => p.id === entry.id);
          const pinned =
            pinnedIdx >= 0
              ? state.pinned.map((p, i) =>
                  i === pinnedIdx ? { ...entry, timestamp: ts } : p,
                )
              : state.pinned;

          return { recents: next, pinned };
        });
      },

      togglePin: (id) => {
        set((state) => {
          const already = state.pinned.find((p) => p.id === id);
          if (already) {
            return { pinned: state.pinned.filter((p) => p.id !== id) };
          }
          // Pull from recents to seed the pin (we don't pin unknown ids).
          const fromRecents = state.recents.find((r) => r.id === id);
          if (!fromRecents) return state;
          return { pinned: [fromRecents, ...state.pinned] };
        });
      },

      isPinned: (id) => get().pinned.some((p) => p.id === id),

      remove: (id) =>
        set((state) => ({
          recents: state.recents.filter((r) => r.id !== id),
          pinned: state.pinned.filter((p) => p.id !== id),
        })),

      clear: () => set({ recents: [], pinned: [] }),
    }),
    {
      name: "py-iku-studio-recents",
      storage: createJSONStorage(() => localStorage),
      version: 1,
      partialize: (state) => ({
        recents: state.recents,
        pinned: state.pinned,
      }),
    },
  ),
);

/**
 * Format a unix-ms timestamp as a relative-time string ("just now", "3 m",
 * "2 h", "yesterday", "Mar 14"). Kept inline so the rail component doesn't
 * have to pull in date-fns just for one helper.
 */
export function relativeTime(ts: number, now: number = Date.now()): string {
  const diff = Math.max(0, now - ts);
  const sec = Math.floor(diff / 1000);
  if (sec < 45) return "just now";
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min} m`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr} h`;
  const day = Math.floor(hr / 24);
  if (day === 1) return "yesterday";
  if (day < 7) return `${day} d`;
  // Fall back to a short calendar label for older items.
  const d = new Date(ts);
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}
