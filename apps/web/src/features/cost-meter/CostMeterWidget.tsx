import { useEffect, useState } from "react";
import {
  client as defaultClient,
  type CostSummary,
} from "../../api/client";

export interface CostMeterWidgetProps {
  /** Test seam — swap in stub fetcher. */
  clientImpl?: { getLlmCostSummary: typeof defaultClient.getLlmCostSummary };
  /** Polling interval in ms. Default 30s. Set to 0 to disable. */
  pollMs?: number;
}

/**
 * Always-visible spend widget shown in the gear-bar. Polls
 * /llm-cost-summary at a configurable cadence. When the user crosses the
 * alert threshold (default 80% of monthly cap) the widget colours itself
 * yellow; over-budget switches to red.
 */
export function CostMeterWidget(props: CostMeterWidgetProps): JSX.Element {
  const cli = props.clientImpl ?? defaultClient;
  const pollMs = props.pollMs ?? 30_000;
  const [summary, setSummary] = useState<CostSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function tick(): Promise<void> {
      try {
        const s = await cli.getLlmCostSummary();
        if (!cancelled) {
          setSummary(s);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
        }
      }
    }
    void tick();
    if (pollMs > 0) {
      const handle = setInterval(tick, pollMs);
      return () => {
        cancelled = true;
        clearInterval(handle);
      };
    }
    return () => {
      cancelled = true;
    };
  }, [cli, pollMs]);

  if (!summary) {
    return (
      <div
        data-testid="cost-meter-widget"
        data-state="loading"
        style={baseStyle}
        title={error ?? "Loading cost summary…"}
      >
        <span style={{ opacity: 0.6 }}>$—</span>
      </div>
    );
  }

  const tone: "ok" | "warn" | "danger" = summary.over_budget
    ? "danger"
    : summary.over_threshold
      ? "warn"
      : "ok";
  const fgColor = TONE_COLORS[tone];

  const tooltip =
    `Today: $${summary.today_usd.toFixed(2)}\n` +
    `Month: $${summary.month_usd.toFixed(2)} / $${summary.budget.monthly_cap_usd.toFixed(2)} ` +
    `(${summary.pct_of_monthly_cap.toFixed(0)}% of cap)\n` +
    `Per-call cap: $${summary.budget.per_call_cap_usd.toFixed(2)}`;

  return (
    <a
      href="/llm-history"
      data-testid="cost-meter-widget"
      data-state={tone}
      data-over-budget={summary.over_budget}
      data-over-threshold={summary.over_threshold}
      style={{
        ...baseStyle,
        color: fgColor,
        borderColor: fgColor,
        textDecoration: "none",
      }}
      title={tooltip}
      aria-label={`LLM spend: ${tooltip.replace(/\n/g, "; ")}`}
    >
      <span style={{ fontWeight: 600 }} data-testid="cost-meter-today">
        ${summary.today_usd.toFixed(2)} today
      </span>
      <span style={{ opacity: 0.6, margin: "0 6px" }}>·</span>
      <span data-testid="cost-meter-month">
        ${summary.month_usd.toFixed(2)} / ${summary.budget.monthly_cap_usd.toFixed(0)} mo
      </span>
    </a>
  );
}

const baseStyle: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  padding: "var(--space-1, 4px) var(--space-3, 12px)",
  border: "1px solid var(--border, #eaecf0)",
  borderRadius: "var(--radius-md, 6px)",
  fontSize: "var(--text-xs, 12px)",
  color: "var(--fg, #101828)",
  background: "var(--surface, #ffffff)",
  whiteSpace: "nowrap",
};

const TONE_COLORS = {
  ok: "var(--fg, #101828)",
  warn: "var(--warning, #b45309)",
  danger: "var(--danger, #b91c1c)",
} as const;
