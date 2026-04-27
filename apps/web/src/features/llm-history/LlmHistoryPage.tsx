import { useEffect, useMemo, useState } from "react";
import {
  client as defaultClient,
  type LlmHistoryListResponse,
  type LlmHistoryRecord,
} from "../../api/client";
import { useSettingsStore } from "../../state/settingsStore";

export interface LlmHistoryPageProps {
  /** Test seam — swap in stub fetcher. */
  clientImpl?: {
    listLlmHistory: typeof defaultClient.listLlmHistory;
    exportUserData: typeof defaultClient.exportUserData;
    deleteUserData: typeof defaultClient.deleteUserData;
  };
  limit?: number;
  /** Test seam — supply a saveBlob to capture export downloads. */
  saveBlob?: (blob: Blob, filename: string) => void;
}

/**
 * Global view of every LLM call made through Studio. Lives under the Account
 * cluster (parallel to Settings) because the spend/audit semantics are
 * per-account rather than per-flow.
 *
 * Sprint 4D added prompt/response logging; Sprint 5 layers free-text search,
 * per-user filtering, severity chips, and the GDPR export / delete flow.
 */
export function LlmHistoryPage(props: LlmHistoryPageProps): JSX.Element {
  const limit = props.limit ?? 50;
  const cli = props.clientImpl ?? defaultClient;
  const baseUrl = useSettingsStore((s) => s.apiBaseUrl);

  const [records, setRecords] = useState<LlmHistoryRecord[]>([]);
  const [users, setUsers] = useState<string[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [provider, setProvider] = useState<"" | "anthropic" | "openai" | "mock" | "rule">("");
  const [status, setStatus] = useState<"" | "success" | "failure">("");
  const [severity, setSeverity] = useState<"" | "success" | "warning" | "error">("");
  const [user, setUser] = useState<string>("");
  const [q, setQ] = useState<string>("");
  const [since, setSince] = useState("");
  const [until, setUntil] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

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
        severity: severity || undefined,
        user: user || undefined,
        q: q || undefined,
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
      // Backend surfaces the user list so the dropdown is always fresh.
      const extended = res as LlmHistoryListResponse & { users?: string[] };
      if (extended.users) setUsers(extended.users);
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

  const targetUser = user || "you";

  const handleExport = async (): Promise<void> => {
    setActionMessage(null);
    setError(null);
    try {
      const result = await cli.exportUserData(targetUser);
      const save =
        props.saveBlob ??
        ((blob: Blob, filename: string) => {
          if (typeof window === "undefined" || typeof document === "undefined")
            return;
          const url = URL.createObjectURL(blob);
          try {
            const a = document.createElement("a");
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
          } finally {
            setTimeout(() => URL.revokeObjectURL(url), 0);
          }
        });
      save(result.blob, result.filename);
      setActionMessage(`Exported ${result.filename}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleDelete = async (): Promise<void> => {
    setActionMessage(null);
    setError(null);
    try {
      const res = await cli.deleteUserData(targetUser);
      setActionMessage(
        `Deleted ${res.removed} record${res.removed === 1 ? "" : "s"} for ${res.user}.`,
      );
      setConfirmDelete(false);
      await fetchPage({ reset: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setConfirmDelete(false);
    }
  };

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
        <span style={{ marginLeft: "auto", fontSize: "var(--text-xs, 12px)", color: "var(--fg-muted, #5b6470)" }}>
          Active user: <strong>{targetUser}</strong>
        </span>
      </div>

      {/* Sprint 4D — full-text search across prompt + response. */}
      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <input
          type="search"
          data-testid="llm-history-search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") onApply();
          }}
          placeholder="Search prompt + response (free text)…"
          style={{
            flex: 1,
            padding: "var(--space-2, 8px) var(--space-3, 12px)",
            border: "1px solid var(--border, #eaecf0)",
            borderRadius: "var(--radius-md, 6px)",
            fontSize: "var(--text-sm, 14px)",
          }}
        />
        <button
          type="button"
          data-testid="llm-history-search-go"
          onClick={onApply}
          style={primaryBtn}
        >
          Search
        </button>
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
        <Field label="Severity">
          <select
            data-testid="llm-history-severity"
            value={severity}
            onChange={(e) => setSeverity(e.target.value as typeof severity)}
          >
            <option value="">all</option>
            <option value="success">success</option>
            <option value="warning">warning ($&gt;1)</option>
            <option value="error">error</option>
          </select>
        </Field>
        <Field label="User">
          <select
            data-testid="llm-history-user"
            value={user}
            onChange={(e) => setUser(e.target.value)}
          >
            <option value="">all</option>
            {users.map((u) => (
              <option key={u} value={u}>
                {u}
              </option>
            ))}
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

      {/* Sprint 5 — GDPR controls. */}
      <div
        style={{
          display: "flex",
          gap: 8,
          alignItems: "center",
          padding: "var(--space-3, 12px) var(--space-4, 16px)",
          border: "1px dashed var(--border, #eaecf0)",
          borderRadius: "var(--radius-md, 8px)",
        }}
      >
        <strong style={{ fontSize: "var(--text-sm, 14px)" }}>GDPR</strong>
        <span style={{ color: "var(--fg-muted, #5b6470)", fontSize: "var(--text-sm, 14px)" }}>
          Manage data attributed to <code>{targetUser}</code>:
        </span>
        <button
          type="button"
          data-testid="llm-history-gdpr-export"
          onClick={() => void handleExport()}
          style={primaryBtn}
        >
          Export my data
        </button>
        <button
          type="button"
          data-testid="llm-history-gdpr-delete"
          onClick={() => setConfirmDelete(true)}
          style={{
            ...primaryBtn,
            background: "var(--danger, #b91c1c)",
            border: "1px solid var(--danger, #b91c1c)",
          }}
        >
          Delete my data
        </button>
        {actionMessage ? (
          <span
            data-testid="llm-history-action-message"
            style={{ color: "var(--ok, #15803d)", fontSize: "var(--text-sm, 14px)" }}
          >
            {actionMessage}
          </span>
        ) : null}
      </div>

      {confirmDelete ? (
        <ConfirmDialog
          user={targetUser}
          onCancel={() => setConfirmDelete(false)}
          onConfirm={() => void handleDelete()}
        />
      ) : null}

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
              <Th>User</Th>
              <Th>Mode</Th>
              <Th>Provider</Th>
              <Th>Model</Th>
              <Th>Severity</Th>
              <Th>In</Th>
              <Th>Out</Th>
              <Th>Cost USD</Th>
              <Th>Flow</Th>
            </tr>
          </thead>
          <tbody>
            {records.map((r, idx) => {
              const sev = (r as LlmHistoryRecord & { severity?: string }).severity ?? r.status;
              const u = (r as LlmHistoryRecord & { user?: string }).user ?? "you";
              return (
                <tr
                  key={`${r.ts}-${idx}`}
                  data-testid={`llm-history-row-${idx}`}
                  style={{ borderTop: "1px solid var(--border, #eaecf0)" }}
                >
                  <Td>{formatTs(r.ts)}</Td>
                  <Td>{u}</Td>
                  <Td>{r.mode}</Td>
                  <Td>{r.provider}</Td>
                  <Td title={r.model}>{r.model}</Td>
                  <Td>
                    <SeverityChip severity={sev} />
                  </Td>
                  <Td>{r.prompt_tokens}</Td>
                  <Td>{r.completion_tokens}</Td>
                  <Td>${r.cost_usd.toFixed(6)}</Td>
                  <Td>
                    {r.flow_id ? (
                      <a href={`/flow/${encodeURIComponent(r.flow_id)}`}>{r.flow_id}</a>
                    ) : (
                      "—"
                    )}
                  </Td>
                </tr>
              );
            })}
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

function SeverityChip({ severity }: { severity: string }): JSX.Element {
  const palette: Record<string, { bg: string; fg: string; label: string }> = {
    success: { bg: "rgba(21, 128, 61, 0.12)", fg: "var(--ok, #15803d)", label: "ok" },
    warning: { bg: "rgba(202, 138, 4, 0.14)", fg: "#a16207", label: "warning" },
    error: { bg: "rgba(185, 28, 28, 0.12)", fg: "var(--danger, #b91c1c)", label: "error" },
  };
  const p = palette[severity] ?? palette.success;
  return (
    <span
      data-testid={`severity-chip-${severity}`}
      style={{
        background: p.bg,
        color: p.fg,
        fontWeight: 600,
        padding: "2px 8px",
        borderRadius: 999,
        fontSize: "var(--text-xs, 11px)",
      }}
    >
      {p.label}
    </span>
  );
}

function ConfirmDialog({
  user,
  onCancel,
  onConfirm,
}: {
  user: string;
  onCancel: () => void;
  onConfirm: () => void;
}): JSX.Element {
  return (
    <>
      <div
        onClick={onCancel}
        data-testid="llm-history-delete-scrim"
        aria-hidden
        style={{
          position: "fixed",
          inset: 0,
          background: "rgba(0,0,0,0.4)",
          zIndex: 50,
        }}
      />
      <div
        role="dialog"
        aria-modal="true"
        data-testid="llm-history-delete-dialog"
        style={{
          position: "fixed",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          background: "var(--surface, #ffffff)",
          border: "1px solid var(--border, #eaecf0)",
          borderRadius: "var(--radius-md, 8px)",
          padding: "var(--space-5, 24px)",
          width: "min(480px, 92vw)",
          zIndex: 51,
          boxShadow: "0 24px 60px rgba(0,0,0,0.20)",
        }}
      >
        <h3 style={{ marginTop: 0, fontSize: "var(--text-lg, 18px)" }}>Delete all data?</h3>
        <p style={{ fontSize: "var(--text-sm, 14px)", color: "var(--fg-muted, #5b6470)" }}>
          This permanently removes every audit-log record attributed to{" "}
          <code>{user}</code>. This action cannot be undone. Comments and flow
          snapshots are not deleted (use a separate request for those).
        </p>
        <div style={{ display: "flex", justifyContent: "flex-end", gap: 8 }}>
          <button
            type="button"
            data-testid="llm-history-delete-cancel"
            onClick={onCancel}
            style={{ ...primaryBtn, background: "transparent", color: "var(--fg, #101828)" }}
          >
            Cancel
          </button>
          <button
            type="button"
            data-testid="llm-history-delete-confirm"
            onClick={onConfirm}
            style={{
              ...primaryBtn,
              background: "var(--danger, #b91c1c)",
              border: "1px solid var(--danger, #b91c1c)",
            }}
          >
            Yes, delete my data
          </button>
        </div>
      </div>
    </>
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
