import { useState, useContext, useCallback } from "react";
import { UNSAFE_NavigationContext } from "react-router-dom";
import {
  useReplayStore,
  formatRunTimestamp,
  MAX_RUNS,
  type ReplayRun,
} from "../store/replay";
import { useFlowStore } from "../state/flowStore";

/**
 * Router-tolerant navigate function. Returns a callback that drives the
 * router's `navigator.push` when a router is mounted, or a no-op if not (so
 * unit tests that render this component standalone don't blow up).
 *
 * We deliberately avoid `useNavigate` directly — that hook calls
 * `invariant(...)` and throws when there's no router context. Instead we
 * subscribe to `UNSAFE_NavigationContext` ourselves and only call its
 * `navigator` when present. No conditional-hook calls.
 */
function useSafeNavigate(): (
  to: string,
  options?: { state?: unknown },
) => void {
  const ctx = useContext(UNSAFE_NavigationContext);
  return useCallback(
    (to, options) => {
      if (!ctx || !ctx.navigator) return;
      ctx.navigator.push(to, options?.state);
    },
    [ctx],
  );
}

/**
 * Replay / undo timeline (Sprint 4 — power user feature 2).
 *
 * Renders a horizontal strip of up to MAX_RUNS cells at the bottom of the
 * Convert page. Each cell shows mini-stats (mode, recipe count, complexity,
 * success/error). Clicking a cell restores its source + result to the
 * editor; "Compare with current" navigates to /diff with the historical
 * version pre-selected.
 *
 * Collapsible — closed by default to keep the convert surface clean.
 */
export interface ReplayTimelineProps {
  /** Optional override — the page can pass its own restore handler so the
   *  store update + editor re-mount happens at the right scope. */
  onRestore?: (run: ReplayRun) => void;
}

export function ReplayTimeline(props: ReplayTimelineProps): JSX.Element | null {
  const runs = useReplayStore((s) => s.runs);
  const cleared = useReplayStore((s) => s.cleared);
  const setCurrentCode = useFlowStore((s) => s.setCurrentCode);
  const setFlow = useFlowStore((s) => s.setFlow);
  const navigate = useSafeNavigate();
  const [open, setOpen] = useState(false);

  if (runs.length === 0) {
    return (
      <section
        data-testid="replay-timeline-empty"
        style={{
          marginTop: "var(--space-3, 12px)",
          padding: "var(--space-3, 12px)",
          border: "1px dashed var(--border, #eaecf0)",
          borderRadius: "var(--radius-md, 8px)",
          color: "var(--fg-muted, #5b6470)",
          fontSize: "var(--text-xs, 12px)",
        }}
      >
        Replay timeline is empty. Run a conversion to start capturing history.
      </section>
    );
  }

  const restore = (run: ReplayRun): void => {
    if (props.onRestore) {
      props.onRestore(run);
      return;
    }
    setCurrentCode(run.source);
    if (run.flow) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      setFlow(run.flow as any);
    }
  };

  return (
    <section
      data-testid="replay-timeline"
      aria-label="Replay timeline"
      style={{
        marginTop: "var(--space-3, 12px)",
        border: "1px solid var(--border, #eaecf0)",
        borderRadius: "var(--radius-md, 8px)",
        background: "var(--surface, #ffffff)",
      }}
    >
      <header
        style={{
          display: "flex",
          alignItems: "center",
          gap: "var(--space-2, 8px)",
          padding: "var(--space-2, 8px) var(--space-3, 12px)",
          borderBottom: open
            ? "1px solid var(--border, #eaecf0)"
            : "none",
        }}
      >
        <button
          type="button"
          data-testid="replay-timeline-toggle"
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
          style={{
            background: "transparent",
            border: 0,
            color: "var(--fg, #101828)",
            cursor: "pointer",
            fontSize: "var(--text-sm, 14px)",
            fontWeight: 600,
            padding: 0,
          }}
        >
          {open ? "▾" : "▸"} Replay timeline
        </button>
        <span
          style={{
            color: "var(--fg-muted, #5b6470)",
            fontSize: "var(--text-xs, 12px)",
          }}
        >
          {runs.length} run{runs.length === 1 ? "" : "s"} (cap {MAX_RUNS})
        </span>
        {cleared > 0 ? (
          <span
            data-testid="replay-cleared-indicator"
            style={{
              marginLeft: "auto",
              color: "var(--fg-subtle, #8a93a1)",
              fontSize: "var(--text-xs, 12px)",
              fontStyle: "italic",
            }}
          >
            Cleared {cleared} older run{cleared === 1 ? "" : "s"}
          </span>
        ) : null}
      </header>

      {open ? (
        <div
          data-testid="replay-timeline-track"
          style={{
            display: "flex",
            gap: "var(--space-2, 8px)",
            padding: "var(--space-3, 12px)",
            overflowX: "auto",
          }}
        >
          {runs.map((run) => (
            <ReplayCell
              key={run.id}
              run={run}
              onRestore={() => restore(run)}
              onCompare={() => {
                // Stash the historical run on the navigation state so /diff
                // can pick it up. The diff page already supports a "two flow"
                // input — passing the historical flow as `state.flowB` lets
                // the user compare without re-fetching.
                navigate("/diff", {
                  state: { flowB: run.flow, runId: run.id },
                });
              }}
            />
          ))}
        </div>
      ) : null}
    </section>
  );
}

interface ReplayCellProps {
  run: ReplayRun;
  onRestore: () => void;
  onCompare: () => void;
}

function ReplayCell(props: ReplayCellProps): JSX.Element {
  const { run, onRestore, onCompare } = props;
  const ok = run.status === "success";
  return (
    <div
      data-testid={`replay-cell-${run.id}`}
      data-status={run.status}
      style={{
        minWidth: 160,
        maxWidth: 220,
        padding: "var(--space-2, 8px)",
        border: "1px solid var(--border, #eaecf0)",
        borderRadius: "var(--radius-sm, 4px)",
        background: ok
          ? "var(--success-bg, #ecfdf3)"
          : "var(--danger-bg, #fee4e2)",
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-1, 4px)",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          fontSize: "var(--text-xs, 12px)",
          color: ok ? "var(--success-fg, #027a48)" : "var(--danger-fg, #b42318)",
          fontWeight: 600,
        }}
      >
        <span>{ok ? "OK" : "ERR"}</span>
        <span>{formatRunTimestamp(run.timestamp)}</span>
      </div>
      <div style={{ fontSize: "var(--text-xs, 12px)", color: "var(--fg, #101828)" }}>
        {run.mode.toUpperCase()}
        {run.provider ? ` · ${run.provider}` : ""}
      </div>
      <div style={{ fontSize: "var(--text-xs, 12px)", color: "var(--fg-muted, #5b6470)" }}>
        {run.recipeCount} recipe{run.recipeCount === 1 ? "" : "s"} · cx {run.complexity.toFixed(1)}
      </div>
      {run.diffSummary && run.diffSummary.recipeDelta !== 0 ? (
        <div
          style={{
            fontSize: "var(--text-xs, 12px)",
            color: "var(--fg-subtle, #8a93a1)",
          }}
        >
          Δ recipes: {run.diffSummary.recipeDelta > 0 ? "+" : ""}
          {run.diffSummary.recipeDelta}
        </div>
      ) : null}
      <div style={{ display: "flex", gap: "var(--space-1, 4px)", marginTop: "var(--space-1, 4px)" }}>
        <button
          type="button"
          data-testid={`replay-restore-${run.id}`}
          onClick={onRestore}
          style={{
            flex: 1,
            padding: "2px 6px",
            border: "1px solid var(--border-strong, #d0d5dd)",
            background: "var(--surface, #ffffff)",
            color: "var(--fg, #101828)",
            borderRadius: "var(--radius-sm, 4px)",
            cursor: "pointer",
            fontSize: "var(--text-xs, 12px)",
          }}
        >
          Restore
        </button>
        <button
          type="button"
          data-testid={`replay-compare-${run.id}`}
          onClick={onCompare}
          disabled={!ok}
          style={{
            flex: 1,
            padding: "2px 6px",
            border: "1px solid var(--border-strong, #d0d5dd)",
            background: "var(--surface, #ffffff)",
            color: "var(--fg, #101828)",
            borderRadius: "var(--radius-sm, 4px)",
            cursor: ok ? "pointer" : "not-allowed",
            opacity: ok ? 1 : 0.5,
            fontSize: "var(--text-xs, 12px)",
          }}
        >
          Compare
        </button>
      </div>
    </div>
  );
}
