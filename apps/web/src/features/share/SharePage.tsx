import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { JsonView } from "../../components/JsonView";
import {
  client as defaultClient,
  type SavedFlowResponse,
} from "../../api/client";

export interface SharePageProps {
  /** Optional client override (test seam). */
  clientImpl?: { getShared: typeof defaultClient.getShared };
  /** Test seam — bypass the URL-derived token. */
  tokenOverride?: string;
}

export function SharePage(props: SharePageProps): JSX.Element {
  const params = useParams<{ token?: string }>();
  const token = props.tokenOverride ?? params.token ?? "";
  const cli = props.clientImpl ?? defaultClient;
  const [data, setData] = useState<SavedFlowResponse | null>(null);
  const [error, setError] = useState<{ status?: number; message: string } | null>(
    null,
  );
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!token) {
      setError({ message: "No token provided." });
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    cli
      .getShared(token)
      .then((res) => {
        if (!cancelled) setData(res);
      })
      .catch((err) => {
        if (!cancelled) {
          const status = (err as { status?: number }).status;
          const message =
            err instanceof Error ? err.message : "Failed to load shared flow.";
          setError({ status, message });
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [token, cli]);

  return (
    <section
      data-testid="share-page"
      style={{
        padding: "1.25rem",
        maxWidth: 1200,
        margin: "0 auto",
        display: "flex",
        flexDirection: "column",
        gap: "1rem",
      }}
    >
      <header>
        <h1 style={{ margin: 0, fontSize: "1.4rem" }}>Shared flow (read-only)</h1>
        <p
          style={{
            margin: "0.25rem 0 0",
            color: "var(--color-grid, #888)",
            fontSize: 13,
          }}
        >
          This is a read-only view of a flow shared via a signed link.
          Editing controls are disabled.
        </p>
      </header>

      {loading ? (
        <p data-testid="share-loading">Loading…</p>
      ) : error ? (
        <ShareError error={error} />
      ) : data ? (
        <SharedFlowReadOnly data={data} />
      ) : null}
    </section>
  );
}

function ShareError(props: {
  error: { status?: number; message: string };
}): JSX.Element {
  const { status, message } = props.error;
  let label = "Could not load shared flow.";
  if (status === 401) label = "This share link is invalid or its signature failed.";
  else if (status === 404) label = "The flow this link points to no longer exists.";
  else if (status === 410) label = "This share link has expired.";
  else if (status === 429) label = "Too many requests. Please slow down and try again.";
  return (
    <div
      data-testid="share-error"
      role="alert"
      style={{
        padding: "0.75rem 1rem",
        borderRadius: 6,
        border: "1px solid #d32f2f",
        background: "rgba(211,47,47,0.08)",
        color: "#b71c1c",
      }}
    >
      <div style={{ fontWeight: 600 }}>
        {status ? `HTTP ${status}` : "Error"} — {label}
      </div>
      <div style={{ fontSize: 13 }}>{message}</div>
    </div>
  );
}

function SharedFlowReadOnly(props: { data: SavedFlowResponse }): JSX.Element {
  const { data } = props;
  return (
    <div data-testid="share-flow" style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
      <div
        style={{
          padding: "0.5rem 0.75rem",
          borderRadius: 6,
          background: "var(--color-grid, #e0e0e0)",
          fontSize: 12,
          color: "var(--color-fg, #212121)",
        }}
      >
        <strong>{data.name}</strong> · saved {data.created_at}
      </div>
      <button
        type="button"
        disabled
        aria-disabled="true"
        data-testid="share-edit-disabled"
        style={{
          padding: "0.4rem 0.8rem",
          borderRadius: 6,
          border: "1px solid var(--color-grid, #e0e0e0)",
          background: "transparent",
          color: "var(--color-grid, #888)",
          cursor: "not-allowed",
          width: "fit-content",
        }}
      >
        Editing disabled
      </button>
      <JsonView value={data.flow as Record<string, unknown>} />
    </div>
  );
}
