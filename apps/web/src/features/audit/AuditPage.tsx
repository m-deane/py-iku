import { useEffect, useState } from "react";
import {
  client as defaultClient,
  type AuditEvent,
  type AuditListResponse,
} from "../../api/client";

export interface AuditPageProps {
  /** Optional client override (test seam). */
  clientImpl?: { listAuditEvents: typeof defaultClient.listAuditEvents };
  /** Page size override. */
  limit?: number;
}

export function AuditPage(props: AuditPageProps): JSX.Element {
  const limit = props.limit ?? 25;
  const cli = props.clientImpl ?? defaultClient;
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [actor, setActor] = useState("");
  const [since, setSince] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPage = async (
    opts: { reset?: boolean; cursor?: string | null } = {},
  ): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      const res: AuditListResponse = await cli.listAuditEvents({
        limit,
        actor: actor.trim() || undefined,
        since: since.trim() || undefined,
        cursor: opts.cursor ?? undefined,
      });
      if (opts.reset) {
        setEvents(res.events);
      } else {
        setEvents((prev) => [...prev, ...res.events]);
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

  const onApplyFilters = (): void => {
    setCursor(null);
    void fetchPage({ reset: true });
  };

  const onLoadMore = (): void => {
    if (!nextCursor) return;
    setCursor(nextCursor);
    void fetchPage({ cursor: nextCursor });
  };

  return (
    <section
      style={{
        padding: "1.25rem",
        maxWidth: 1100,
        margin: "0 auto",
        display: "flex",
        flexDirection: "column",
        gap: "1rem",
      }}
    >
      <header>
        <h1 style={{ margin: 0, fontSize: "1.4rem" }}>Audit log</h1>
        <p style={{ margin: "0.25rem 0 0", color: "var(--fg-muted, #5b6470)", fontSize: 13 }}>
          Every Convert, Save, Share, and Patch action is recorded with
          timestamp, actor, and resource. Filter by actor or by ISO timestamp
          to scope the view.
        </p>
      </header>

      <div
        data-testid="audit-filters"
        style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}
      >
        <input
          type="text"
          placeholder="actor"
          value={actor}
          onChange={(e) => setActor(e.target.value)}
          aria-label="Filter by actor"
          data-testid="audit-filter-actor"
          style={inputStyle}
        />
        <input
          type="text"
          placeholder="ISO timestamp (since)"
          value={since}
          onChange={(e) => setSince(e.target.value)}
          aria-label="Filter by since timestamp"
          data-testid="audit-filter-since"
          style={inputStyle}
        />
        <button
          type="button"
          onClick={onApplyFilters}
          data-testid="audit-apply-filters"
          style={btnStyle}
        >
          Apply
        </button>
      </div>

      {error ? (
        <p data-testid="audit-error" style={{ color: "#b71c1c" }}>
          {error}
        </p>
      ) : null}

      <table
        data-testid="audit-table"
        style={{
          width: "100%",
          borderCollapse: "collapse",
          fontSize: 13,
        }}
      >
        <thead>
          <tr>
            <Th>Timestamp</Th>
            <Th>Actor</Th>
            <Th>Action</Th>
            <Th>Resource</Th>
            <Th>Details</Th>
          </tr>
        </thead>
        <tbody>
          {events.length === 0 && !loading ? (
            <tr>
              <td
                colSpan={5}
                data-testid="audit-empty"
                style={{ padding: "1.25rem 1rem", color: "var(--fg-muted, #5b6470)" }}
              >
                <div style={{ fontWeight: 600, color: "inherit", marginBottom: 4 }}>
                  No audit events match the current filter.
                </div>
                <div style={{ fontSize: 13 }}>
                  Each Convert, Save, Share, and Patch action lands here with
                  a timestamp, actor, and the resulting flow id.{" "}
                  <a href="/convert" style={{ color: "var(--accent-hover, #0f766e)" }}>
                    Run a conversion
                  </a>{" "}
                  to populate the log.
                </div>
              </td>
            </tr>
          ) : (
            events.map((ev, i) => (
              <tr key={`${ev.ts}-${i}`} data-testid={`audit-row-${i}`}>
                <Td>{ev.ts}</Td>
                <Td>{ev.actor}</Td>
                <Td>{ev.action}</Td>
                <Td>
                  {ev.resource_type}/{ev.resource_id}
                </Td>
                <Td>
                  <code style={{ fontSize: 12 }}>
                    {summarise(ev.details)}
                  </code>
                </Td>
              </tr>
            ))
          )}
        </tbody>
      </table>

      <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
        {nextCursor || loading ? (
          <button
            type="button"
            onClick={onLoadMore}
            disabled={!nextCursor || loading}
            data-testid="audit-load-more"
            style={btnStyle}
          >
            {loading ? "Loading…" : "Load more"}
          </button>
        ) : events.length > 0 ? (
          <span
            data-testid="audit-end-of-log"
            style={{ fontSize: 12, color: "var(--fg-muted, #5b6470)" }}
          >
            End of log.
          </span>
        ) : null}
        {cursor ? (
          <span style={{ fontSize: 12, color: "var(--fg-muted, #5b6470)" }}>
            cursor: {cursor}
          </span>
        ) : null}
      </div>
    </section>
  );
}

function summarise(details: Record<string, unknown>): string {
  try {
    const json = JSON.stringify(details);
    return json.length > 80 ? `${json.slice(0, 77)}…` : json;
  } catch {
    return "[unserializable]";
  }
}

const inputStyle: React.CSSProperties = {
  padding: "0.4rem 0.6rem",
  borderRadius: 6,
  border: "1px solid var(--color-grid, #e0e0e0)",
  background: "transparent",
  color: "inherit",
  fontSize: 13,
};

const btnStyle: React.CSSProperties = {
  padding: "0.4rem 0.8rem",
  borderRadius: 6,
  border: "1px solid var(--color-grid, #e0e0e0)",
  background: "transparent",
  color: "inherit",
  cursor: "pointer",
  fontSize: 13,
};

function Th({ children }: { children: React.ReactNode }): JSX.Element {
  return (
    <th
      style={{
        textAlign: "left",
        padding: "0.4rem 0.6rem",
        borderBottom: "1px solid var(--color-grid, #e0e0e0)",
        fontWeight: 600,
        fontSize: 12,
        textTransform: "uppercase",
        letterSpacing: 0.4,
        color: "var(--fg-muted, #5b6470)",
      }}
    >
      {children}
    </th>
  );
}

function Td({ children }: { children: React.ReactNode }): JSX.Element {
  return (
    <td
      style={{
        padding: "0.4rem 0.6rem",
        borderBottom: "1px solid var(--color-grid, #f0f0f0)",
        verticalAlign: "top",
      }}
    >
      {children}
    </td>
  );
}
