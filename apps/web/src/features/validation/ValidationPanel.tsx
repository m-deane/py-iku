import { useEffect, useState } from "react";
import {
  client as defaultClient,
  type ScoreResponse,
} from "../../api/client";

export interface ValidationPanelProps {
  /** The current flow (post-conversion). */
  flow: Record<string, unknown> | null;
  /** Warnings emitted during conversion. */
  warnings: readonly string[];
  /** Optional client override for tests. */
  clientImpl?: { score: typeof defaultClient.score };
  /** Whether the panel starts open or collapsed. */
  defaultOpen?: boolean;
}

interface RecipeNode {
  type?: unknown;
}

function recipeTallies(flow: Record<string, unknown> | null): Map<string, number> {
  const tallies = new Map<string, number>();
  if (!flow) return tallies;
  const recipes = (flow.recipes ?? []) as RecipeNode[];
  for (const r of recipes) {
    const t = typeof r.type === "string" ? r.type : "unknown";
    tallies.set(t, (tallies.get(t) ?? 0) + 1);
  }
  return tallies;
}

export function ValidationPanel(props: ValidationPanelProps): JSX.Element {
  const { flow, warnings } = props;
  const [open, setOpen] = useState<boolean>(props.defaultOpen ?? false);
  const [score, setScore] = useState<ScoreResponse | null>(null);
  const [scoreError, setScoreError] = useState<string | null>(null);
  const [scoring, setScoring] = useState(false);

  useEffect(() => {
    setScore(null);
    setScoreError(null);
    if (!flow) return;
    const cli = props.clientImpl ?? defaultClient;
    let cancelled = false;
    setScoring(true);
    cli
      .score(flow)
      .then((res) => {
        if (!cancelled) setScore(res);
      })
      .catch((err) => {
        if (!cancelled) {
          setScoreError(err instanceof Error ? err.message : String(err));
        }
      })
      .finally(() => {
        if (!cancelled) setScoring(false);
      });
    return () => {
      cancelled = true;
    };
  }, [flow, props.clientImpl]);

  const tallies = recipeTallies(flow);

  return (
    <section
      data-testid="validation-panel"
      style={{
        border: "1px solid var(--color-grid, #e0e0e0)",
        borderRadius: 6,
        marginTop: "0.75rem",
      }}
    >
      <button
        type="button"
        data-testid="validation-panel-toggle"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        style={{
          width: "100%",
          padding: "0.6rem 0.8rem",
          textAlign: "left",
          background: "transparent",
          border: 0,
          color: "inherit",
          cursor: "pointer",
          fontSize: 14,
          fontWeight: 600,
          display: "flex",
          alignItems: "center",
          gap: "0.5rem",
        }}
      >
        <span aria-hidden>{open ? "▾" : "▸"}</span>
        <span>Validation</span>
        <span style={{ color: "var(--fg-muted, #5b6470)", fontWeight: 400, fontSize: 12 }}>
          {warnings.length} warning{warnings.length === 1 ? "" : "s"}
          {score ? ` · complexity ${score.complexity.toFixed(1)}` : ""}
        </span>
      </button>
      {open ? (
        <div
          data-testid="validation-panel-body"
          style={{
            padding: "0.5rem 0.8rem 0.8rem",
            borderTop: "1px solid var(--color-grid, #e0e0e0)",
            display: "flex",
            flexDirection: "column",
            gap: "0.75rem",
          }}
        >
          <Section title="Warnings" testId="validation-warnings">
            {warnings.length === 0 ? (
              <p style={{ margin: 0, color: "var(--fg-muted, #5b6470)", fontSize: 13 }}>
                No warnings.
              </p>
            ) : (
              <ul style={{ margin: 0, paddingLeft: "1.1rem", fontSize: 13 }}>
                {warnings.map((w, i) => (
                  <li key={i} data-testid={`validation-warning-${i}`}>
                    {w}
                  </li>
                ))}
              </ul>
            )}
          </Section>

          <Section title="Score breakdown" testId="validation-score">
            {scoring ? (
              <p style={{ margin: 0, color: "var(--fg-muted, #5b6470)", fontSize: 13 }}>
                Computing…
              </p>
            ) : scoreError ? (
              <p style={{ margin: 0, color: "#b71c1c", fontSize: 13 }}>{scoreError}</p>
            ) : score ? (
              <ScoreList score={score} />
            ) : (
              <p style={{ margin: 0, color: "var(--fg-muted, #5b6470)", fontSize: 13 }}>
                No score available.
              </p>
            )}
          </Section>

          <Section title="Recipe types" testId="validation-recipe-tally">
            {tallies.size === 0 ? (
              <p style={{ margin: 0, color: "var(--fg-muted, #5b6470)", fontSize: 13 }}>
                No recipes.
              </p>
            ) : (
              <ul style={{ margin: 0, paddingLeft: "1.1rem", fontSize: 13 }}>
                {[...tallies.entries()]
                  .sort(([, a], [, b]) => b - a)
                  .map(([t, n]) => (
                    <li key={t} data-testid={`validation-tally-${t}`}>
                      <strong>{t}</strong>: {n}
                    </li>
                  ))}
              </ul>
            )}
          </Section>
        </div>
      ) : null}
    </section>
  );
}

function Section(props: {
  title: string;
  testId: string;
  children: React.ReactNode;
}): JSX.Element {
  return (
    <div data-testid={props.testId}>
      <h3 style={{ margin: "0 0 0.3rem 0", fontSize: 13 }}>{props.title}</h3>
      {props.children}
    </div>
  );
}

function ScoreList(props: { score: ScoreResponse }): JSX.Element {
  const items: Array<[string, string | number]> = [
    ["complexity", props.score.complexity.toFixed(2)],
    ["recipes", props.score.recipe_count],
    ["processors", props.score.processor_count],
    ["max depth", props.score.max_depth],
    ["fan-out (max)", props.score.fan_out_max],
  ];
  if (typeof props.score.cost_estimate === "number") {
    items.push(["cost (USD est.)", props.score.cost_estimate.toFixed(4)]);
  }
  return (
    <ul style={{ margin: 0, paddingLeft: "1.1rem", fontSize: 13 }}>
      {items.map(([label, value]) => (
        <li key={label} data-testid={`validation-score-${label.replace(/\s+/g, "-")}`}>
          <strong>{label}:</strong> {value}
        </li>
      ))}
    </ul>
  );
}
