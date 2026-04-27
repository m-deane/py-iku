/**
 * LintPanel
 *
 * Sits in the Inspector / next to it. Lists every Lint emitted by
 * `/flows/lint`. Clicking an entry sets the global selection to the
 * offending recipe (so the existing NodeInspector opens it). Fixable
 * rules surface an "Apply fix" button — currently wired for the
 * `merge-adjacent-prepares` rule via `/flows/lint/fix`.
 */
import { useCallback, useEffect, useState } from "react";
import {
  client as defaultClient,
  type Client,
  type LintEntry,
  type LintResponse,
} from "../../api/client";
import { useFlowStore } from "../../state/flowStore";

export interface LintPanelProps {
  /** Flow to lint. Re-runs whenever the reference changes. */
  flow: Record<string, unknown> | null;
  /** Test seam — pass a stub client. */
  clientImpl?: Client;
  /** Test seam — disable the auto-run on mount (controlled tests pass an explicit prop). */
  initialResult?: LintResponse;
  /** Called whenever an "Apply fix" succeeds with the new flow dict. */
  onFlowReplaced?: (flow: Record<string, unknown>) => void;
}

const SEVERITY_TO_COLOR: Record<string, string> = {
  blocker: "#b71c1c",
  warning: "var(--accent-hover, #0f766e)",
  info: "var(--fg-muted, #5b6470)",
};


export function LintPanel(props: LintPanelProps): JSX.Element {
  const { flow, onFlowReplaced } = props;
  const apiClient = props.clientImpl ?? defaultClient;
  const [result, setResult] = useState<LintResponse | null>(
    props.initialResult ?? null,
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const setSelectedNodeId = useFlowStore((s) => s.setSelectedNodeId);

  const refresh = useCallback(async (): Promise<void> => {
    if (!flow) return;
    setLoading(true);
    setError(null);
    try {
      const r = await apiClient.lint(flow);
      setResult(r);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, [apiClient, flow]);

  useEffect(() => {
    if (props.initialResult) return;
    void refresh();
  }, [refresh, props.initialResult]);

  const onClickEntry = (entry: LintEntry): void => {
    if (entry.recipe_id) {
      setSelectedNodeId(entry.recipe_id);
    }
  };

  const onApplyFix = async (entry: LintEntry): Promise<void> => {
    if (!flow || !entry.fix) return;
    setLoading(true);
    setError(null);
    try {
      const fix = entry.fix as Record<string, unknown>;
      const payload: Record<string, unknown> = {};
      // Map the rule's fix-payload onto the API's `payload` body.
      if (entry.rule_id === "merge-adjacent-prepares") {
        payload.left = fix.left;
        payload.right = fix.right;
      } else {
        Object.assign(payload, fix);
      }
      const out = await apiClient.lintFix(flow, entry.rule_id, payload);
      onFlowReplaced?.(out.flow);
      // After a fix, re-lint the new flow so the panel updates.
      try {
        const r = await apiClient.lint(out.flow);
        setResult(r);
      } catch {
        /* keep existing list — user can refresh manually */
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  const lints = result?.lints ?? [];
  const counts = lints.reduce(
    (acc, l) => {
      acc[l.severity] = (acc[l.severity] ?? 0) + 1;
      return acc;
    },
    {} as Record<string, number>,
  );

  return (
    <section
      aria-label="Lint findings"
      data-testid="lint-panel"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "0.5rem",
        padding: "0.6rem 0.8rem",
        border: "1px solid var(--border, #eaecf0)",
        borderRadius: "var(--radius-md, 6px)",
        background: "var(--surface, #fff)",
      }}
    >
      <header
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <strong style={{ fontSize: "var(--text-sm, 13px)" }}>
          Lint
          {lints.length > 0 ? (
            <span
              data-testid="lint-badge"
              style={{
                marginLeft: "0.5rem",
                padding: "0.05rem 0.4rem",
                borderRadius: "var(--radius-pill, 9999px)",
                background: counts.blocker
                  ? "rgba(183,28,28,0.12)"
                  : "var(--accent-bg-soft, #ccfbf1)",
                color: counts.blocker ? "#b71c1c" : "var(--accent-hover, #0f766e)",
                fontSize: "var(--text-xs, 12px)",
              }}
            >
              {lints.length} {lints.length === 1 ? "issue" : "issues"}
            </span>
          ) : null}
        </strong>
        <button
          type="button"
          onClick={() => void refresh()}
          disabled={!flow || loading}
          data-testid="lint-refresh"
          style={{
            padding: "0.15rem 0.5rem",
            borderRadius: "var(--radius-sm, 4px)",
            border: "1px solid var(--border-strong, #d0d5dd)",
            background: "transparent",
            color: "inherit",
            cursor: !flow || loading ? "not-allowed" : "pointer",
            fontSize: "var(--text-xs, 12px)",
          }}
        >
          Re-lint
        </button>
      </header>

      {error ? (
        <div
          role="alert"
          data-testid="lint-error"
          style={{ fontSize: "var(--text-xs, 12px)", color: "#b71c1c" }}
        >
          {error}
        </div>
      ) : null}

      {lints.length === 0 && !loading ? (
        <div
          data-testid="lint-empty"
          style={{ fontSize: "var(--text-xs, 12px)", color: "var(--fg-muted, #5b6470)" }}
        >
          {flow
            ? "No lint findings — flow looks healthy."
            : "Convert a flow first to run the linter."}
        </div>
      ) : null}

      <ul
        data-testid="lint-list"
        style={{
          listStyle: "none",
          margin: 0,
          padding: 0,
          display: "flex",
          flexDirection: "column",
          gap: "0.3rem",
        }}
      >
        {lints.map((l, i) => (
          <li
            key={`${l.rule_id}-${l.recipe_id ?? "global"}-${i}`}
            data-testid={`lint-entry-${l.rule_id}`}
          >
            <button
              type="button"
              onClick={() => onClickEntry(l)}
              style={{
                display: "flex",
                alignItems: "flex-start",
                gap: "0.5rem",
                padding: "0.4rem 0.6rem",
                width: "100%",
                textAlign: "left",
                borderRadius: "var(--radius-sm, 4px)",
                border: "1px solid var(--border, #eaecf0)",
                background: "var(--surface-raised, #f7f8fa)",
                cursor: "pointer",
              }}
            >
              <span
                aria-label={`Severity: ${l.severity}`}
                data-testid={`lint-severity-${l.severity}`}
                style={{
                  display: "inline-block",
                  marginTop: 4,
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  background: SEVERITY_TO_COLOR[l.severity] ?? "var(--fg-muted)",
                  flexShrink: 0,
                }}
              />
              <span style={{ flex: 1, fontSize: "var(--text-xs, 12px)" }}>
                <code style={{ color: "var(--fg-muted, #5b6470)" }}>{l.rule_id}</code>
                {l.recipe_id ? (
                  <>
                    {" · "}
                    <strong>{l.recipe_id}</strong>
                  </>
                ) : null}
                <div style={{ marginTop: 2 }}>{l.message}</div>
              </span>
              {l.fix ? (
                <button
                  type="button"
                  data-testid={`lint-apply-fix-${l.rule_id}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    void onApplyFix(l);
                  }}
                  style={{
                    padding: "0.2rem 0.5rem",
                    borderRadius: "var(--radius-sm, 4px)",
                    border: "1px solid var(--accent, #0d9488)",
                    background: "var(--accent, #0d9488)",
                    color: "var(--accent-fg, #fff)",
                    cursor: "pointer",
                    fontSize: "var(--text-xs, 12px)",
                  }}
                >
                  Apply fix
                </button>
              ) : null}
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}

/** Tiny inline badge — for surfacing "Lint: 2 warnings" near metric tiles. */
export function LintBadge(props: {
  result: LintResponse | null;
  onClick?: () => void;
}): JSX.Element | null {
  if (!props.result || props.result.lints.length === 0) return null;
  const counts = props.result.lints.reduce(
    (acc, l) => {
      acc[l.severity] = (acc[l.severity] ?? 0) + 1;
      return acc;
    },
    {} as Record<string, number>,
  );
  const tone = counts.blocker
    ? "blocker"
    : counts.warning
      ? "warning"
      : "info";
  const label = props.result.lints.length === 1 ? "issue" : "issues";
  return (
    <button
      type="button"
      data-testid="lint-summary-badge"
      data-tone={tone}
      onClick={props.onClick}
      style={{
        padding: "0.2rem 0.6rem",
        borderRadius: "var(--radius-pill, 9999px)",
        border: "1px solid var(--border-strong, #d0d5dd)",
        background:
          tone === "blocker"
            ? "rgba(183,28,28,0.12)"
            : "var(--accent-bg-soft, #ccfbf1)",
        color: tone === "blocker" ? "#b71c1c" : "var(--accent-hover, #0f766e)",
        cursor: "pointer",
        fontSize: "var(--text-xs, 12px)",
      }}
    >
      Lint: {props.result.lints.length} {label}
    </button>
  );
}
