import { useEffect, useMemo, useState } from "react";
import {
  client as defaultClient,
  type LlmHistoryListResponse,
  type LlmHistoryRecord,
} from "../../api/client";
import { useSettingsStore } from "../../state/settingsStore";

export interface LlmHistoryPageProps {
  /** Test seam — swap in stub fetcher. */
  clientImpl?: { listLlmHistory: typeof defaultClient.listLlmHistory };
  limit?: number;
}

/**
 * Global view of every LLM call made through Studio. Lives under the Account
 * cluster (parallel to Settings) because the spend/audit semantics are
 * per-account rather than per-flow. Filters: provider, status, date range.
 * Each row is clickable — clicking opens the related flow via /flow/:id when
 * a flow_id was recorded.
 */
export function LlmHistoryPage(props: LlmHistoryPageProps): JSX.Element {
  const limit = props.limit ?? 50;
  const cli = props.clientImpl ?? defaultClient;
  const baseUrl = useSettingsStore((s) => s.apiBaseUrl);

  const [records, setRecords] = useState<LlmHistoryRecord[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [provider, setProvider] = useState<"" | "anthropic" | "openai" | "mock" | "rule">("");
  const [status, setStatus] = useState<"" | "success" | "failure">("");
  const [since, setSince] = useState("");
  const [until, setUntil] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPage = async (
    opts: { reset?: boolean; cursor?: string | null } = {},
  ): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      const res: LlmHistoryListResponse = await cli.listLlmHistory({
        limit,
        provider: provider || undefined,
        status: status || undefined,
        since: since || undefined,
        until: until || undefined,
        cursor: opts.cursor ?? undefined,
      });
      if (opts.reset) {
        setRecords(res.records);
      } else {
        setRecords((prev) => [...prev, ...res.records]);
      }
      setNextCursor(res.next_cursor);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchPage({ reset: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const totals = useMemo(() => {
    const total = records.reduce((acc, r) => acc + r.cost_usd, 0);
    const success = records.filter((r) => r.status === "success").length;
    const fail = records.filter((r) => r.status === "failure").length;
    return { total, success, fail };
  }, [records]);

  const onApply = (): void => {
    void fetchPage({ reset: true });
  };

  const csvUrl = useMemo(() => {
    const u = new URL(`${baseUrl.replace(/\/$/, "")}/llm-history.csv`);
    if (provider) u.searchParams.set("provider", provider);
    if (status) u.searchParams.set("status", status);
    if (since) u.searchParams.set("since", since);
    if (until) u.searchParams.set("until", until);
    return u.toString();
  }, [baseUrl, provider, status, since, until]);

  return (
    <section
      style={{
        padding: "var(--space-6, 32px)",
        maxWidth: 1200,
        margin: "0 auto",
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-4, 16px)",
      }}
    >
      <header style={{ display: "flex", alignItems: "baseline", gap: 12 }}>
        <h1 style={{ margin: 0, fontSize: "var(--text-2xl, 28px)" }}>LLM history</h1>
        <span style={{ color: "var(--fg-muted, #5b6470)", fontSize: "var(--text-sm, 14px)" }}>
          Every Anthropic / OpenAI / mock call made through Studio.
        </span>
      </header>

      <div
        data-testid="llm-history-summary"
        style={{
          display: "flex",
          gap: 16,
          padding: "var(--space-3, 12px) var(--space-4, 16px)",
          border: "1px solid var(--border, #eaecf0)",
          borderRadius: "var(--radius-md, 8px)",
        }}
      >
        <span>
          <strong>{records.length}</strong> calls loaded
        </span>
        <span>
          <strong>${totals.total.toFixed(4)}</strong> total cost
        </span>
        <span>
          <strong style={{ color: "var(--ok, #15803d)" }}>{totals.success}</strong> ok
        </span>
        <span>
          <strong style={{ color: "var(--danger, #b91c1c)" }}>{totals.fail}</strong> failed
        </span>
      </div>

      <div
        style={{
          display: "flex",
          gap: 8,
          flexWrap: "wrap",
          alignItems: "flex-end",
        }}
      >
        <Field label="Provider">
          <select
            data-testid="llm-history-provider"
            value={provider}
            onChange={(e) => setProvider(e.target.value as typeof provider)}
          >
            <option value="">all</option>
            <option value="anthropic">anthropic</option>
            <option value="openai">openai</option>
            <option value="mock">mock</option>
            <option value="rule">rule</option>
          </select>
        </Field>
        <Field label="Status">
          <select
            data-testid="llm-history-status"
            value={status}
            onChange={(e) => setStatus(e.target.value as typeof status)}
          >
            <option value="">all</option>
            <option value="success">success</option>
            <option value="failure">failure</option>
          </select>
        </Field>
        <Field label="Since">
          <input
            type="datetime-local"
            value={since}
            onChange={(e) => setSince(e.target.value)}
          />
        </Field>
        <Field label="Until">
          <input
            type="datetime-local"
            value={until}
            onChange={(e) => setUntil(e.target.value)}
          />
        </Field>
        <button
          type="button"
          data-testid="llm-history-apply"
          onClick={onApply}
          style={primaryBtn}
        >
          Apply filters
        </button>
        <a
          href={csvUrl}
          data-testid="llm-history-csv"
          style={{
            ...primaryBtn,
            background: "var(--surface-raised, #f7f8fa)",
            color: "var(--fg, #101828)",
            textDecoration: "none",
          }}
        >
          Export CSV
        </a>
      </div>

      {error ? (
        <div
          role="alert"
          style={{
            color: "var(--danger, #b91c1c)",
            padding: "var(--space-2, 8px) var(--space-3, 12px)",
            border: "1px solid var(--danger, #b91c1c)",
            borderRadius: "var(--radius-md, 6px)",
          }}
        >
          {error}
        </div>
      ) : null}

      <div
        style={{
          border: "1px solid var(--border, #eaecf0)",
          borderRadius: "var(--radius-md, 8px)",
          overflow: "auto",
        }}
      >
        <table
          data-testid="llm-history-table"
          style={{ width: "100%", borderCollapse: "collapse", fontSize: "var(--text-sm, 14px)" }}
        >
          <thead>
            <tr style={{ background: "var(--surface-raised, #f7f8fa)" }}>
              <Th>Timestamp</Th>
              <Th>Mode</Th>
              <Th>Provider</Th>
              <Th>Model</Th>
              <Th>In</Th>
              <Th>Out</Th>
              <Th>Cost USD</Th>
              <Th>Status</Th>
              <Th>Flow</Th>
            </tr>
          </thead>
          <tbody>
            {records.map((r, idx) => (
              <tr
                key={`${r.ts}-${idx}`}
                data-testid={`llm-history-row-${idx}`}
                style={{ borderTop: "1px solid var(--border, #eaecf0)" }}
              >
                <Td>{formatTs(r.ts)}</Td>
                <Td>{r.mode}</Td>
                <Td>{r.provider}</Td>
                <Td title={r.model}>{r.model}</Td>
                <Td>{r.prompt_tokens}</Td>
                <Td>{r.completion_tokens}</Td>
                <Td>${r.cost_usd.toFixed(6)}</Td>
                <Td>
                  <span
                    style={{
                      color:
                        r.status === "success"
                          ? "var(--ok, #15803d)"
                          : "var(--danger, #b91c1c)",
                      fontWeight: 600,
                    }}
                  >
                    {r.status}
                  </span>
                </Td>
                <Td>
                  {r.flow_id ? (
                    <a href={`/flow/${encodeURIComponent(r.flow_id)}`}>{r.flow_id}</a>
                  ) : (
                    "—"
                  )}
                </Td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={{ display: "flex", justifyContent: "center" }}>
        {nextCursor ? (
          <button
            type="button"
            data-testid="llm-history-load-more"
            onClick={() => fetchPage({ cursor: nextCursor })}
            disabled={loading}
            style={primaryBtn}
          >
            {loading ? "Loading…" : "Load more"}
          </button>
        ) : (
          <span style={{ color: "var(--fg-muted, #5b6470)", fontSize: "var(--text-sm, 14px)" }}>
            {loading ? "Loading…" : records.length === 0 ? "No calls recorded yet." : "End of history."}
          </span>
        )}
      </div>
    </section>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }): JSX.Element {
  return (
    <label style={{ display: "flex", flexDirection: "column", fontSize: "var(--text-xs, 12px)", gap: 4 }}>
      <span style={{ color: "var(--fg-muted, #5b6470)" }}>{label}</span>
      {children}
    </label>
  );
}

function Th({ children }: { children: React.ReactNode }): JSX.Element {
  return (
    <th
      style={{
        textAlign: "left",
        padding: "var(--space-2, 8px) var(--space-3, 12px)",
        fontWeight: 600,
        fontSize: "var(--text-xs, 12px)",
        textTransform: "uppercase",
        color: "var(--fg-muted, #5b6470)",
      }}
    >
      {children}
    </th>
  );
}

function Td({ children, title }: { children: React.ReactNode; title?: string }): JSX.Element {
  return (
    <td
      title={title}
      style={{
        padding: "var(--space-2, 8px) var(--space-3, 12px)",
        verticalAlign: "top",
        whiteSpace: "nowrap",
      }}
    >
      {children}
    </td>
  );
}

function formatTs(ts: string): string {
  try {
    return new Date(ts).toLocaleString();
  } catch {
    return ts;
  }
}

const primaryBtn: React.CSSProperties = {
  padding: "var(--space-2, 6px) var(--space-3, 12px)",
  border: "1px solid var(--border, #eaecf0)",
  borderRadius: "var(--radius-md, 6px)",
  background: "var(--accent, #0d9488)",
  color: "var(--accent-fg, #ffffff)",
  fontSize: "var(--text-sm, 14px)",
  cursor: "pointer",
  fontWeight: 600,
};
