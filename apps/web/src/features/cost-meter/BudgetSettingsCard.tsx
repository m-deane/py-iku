import { useEffect, useState } from "react";
import {
  client as defaultClient,
  type BudgetSettings,
} from "../../api/client";

export interface BudgetSettingsCardProps {
  /** Test seam — swap in stub fetcher. */
  clientImpl?: {
    getLlmBudget: typeof defaultClient.getLlmBudget;
    putLlmBudget: typeof defaultClient.putLlmBudget;
  };
}

/**
 * "LLM Budgets" section for SettingsPage. Mounts on demand and PUTs the
 * budget object back to the API on save. Validation: monthly_cap >=0,
 * per_call_cap >=0, alert_threshold in [0, 100].
 */
export function BudgetSettingsCard(props: BudgetSettingsCardProps): JSX.Element {
  const cli = props.clientImpl ?? defaultClient;
  const [budget, setBudget] = useState<BudgetSettings | null>(null);
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const b = await cli.getLlmBudget();
        if (!cancelled) setBudget(b);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err));
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [cli]);

  const update = (patch: Partial<BudgetSettings>): void => {
    if (!budget) return;
    setBudget({ ...budget, ...patch });
  };

  const save = async (): Promise<void> => {
    if (!budget) return;
    setSaving(true);
    setError(null);
    try {
      const next = await cli.putLlmBudget(budget);
      setBudget(next);
      setSavedAt(Date.now());
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <section
      data-testid="budget-settings-card"
      style={cardStyle}
    >
      <header>
        <h2 style={{ margin: 0, fontSize: "var(--text-md, 17px)" }}>LLM Budgets</h2>
        <p style={pStyle}>
          Caps applied to every LLM call across Studio. Daily/monthly totals
          come from the prompt-history log; over-budget calls are blocked
          server-side before the request reaches the provider.
        </p>
      </header>

      {!budget ? (
        <p style={{ color: "var(--fg-muted, #5b6470)" }}>Loading…</p>
      ) : (
        <>
          <Row label="Monthly cap (USD)">
            <input
              type="number"
              data-testid="budget-monthly"
              min={0}
              step={1}
              value={budget.monthly_cap_usd}
              onChange={(e) => update({ monthly_cap_usd: Number(e.target.value) || 0 })}
            />
          </Row>
          <Row label="Per-call cap (USD)">
            <input
              type="number"
              data-testid="budget-per-call"
              min={0}
              step={0.01}
              value={budget.per_call_cap_usd}
              onChange={(e) => update({ per_call_cap_usd: Number(e.target.value) || 0 })}
            />
          </Row>
          <Row label="Alert threshold (% of monthly)">
            <input
              type="number"
              data-testid="budget-threshold"
              min={0}
              max={100}
              step={1}
              value={budget.alert_threshold_pct}
              onChange={(e) =>
                update({
                  alert_threshold_pct: Math.max(0, Math.min(100, Number(e.target.value) || 0)),
                })
              }
            />
          </Row>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <button
              type="button"
              data-testid="budget-save"
              onClick={save}
              disabled={saving}
              style={{
                padding: "var(--space-2, 8px) var(--space-3, 14px)",
                background: "var(--accent, #0d9488)",
                color: "var(--accent-fg, #ffffff)",
                border: 0,
                borderRadius: "var(--radius-md, 6px)",
                fontWeight: 600,
                cursor: saving ? "wait" : "pointer",
              }}
            >
              {saving ? "Saving…" : "Save budget"}
            </button>
            {savedAt ? (
              <span style={{ color: "var(--ok, #15803d)", fontSize: "var(--text-xs, 12px)" }}>
                saved
              </span>
            ) : null}
            {error ? (
              <span
                role="alert"
                style={{ color: "var(--danger, #b91c1c)", fontSize: "var(--text-xs, 12px)" }}
              >
                {error}
              </span>
            ) : null}
          </div>
        </>
      )}
    </section>
  );
}

const cardStyle: React.CSSProperties = {
  border: "1px solid var(--border, #eaecf0)",
  borderRadius: "var(--radius-lg, 12px)",
  padding: "var(--space-5, 24px)",
  background: "var(--surface, #ffffff)",
  display: "flex",
  flexDirection: "column",
  gap: "var(--space-3, 12px)",
};

const pStyle: React.CSSProperties = {
  margin: "var(--space-1, 4px) 0 0",
  color: "var(--fg-muted, #5b6470)",
  fontSize: "var(--text-sm, 14px)",
};

function Row({ label, children }: { label: string; children: React.ReactNode }): JSX.Element {
  return (
    <label
      style={{
        display: "grid",
        gridTemplateColumns: "220px 1fr",
        alignItems: "center",
        gap: "var(--space-3, 12px)",
        fontSize: "var(--text-sm, 14px)",
      }}
    >
      <span style={{ color: "var(--fg-muted, #5b6470)" }}>{label}</span>
      <span>{children}</span>
    </label>
  );
}
