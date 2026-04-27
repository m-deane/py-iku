import { useEffect, useMemo, useState } from "react";
import {
  client as defaultClient,
  collabClient as defaultCollab,
  type CollabClient,
  type Client,
  type FixturePreviewResponse,
  type ShareFlowResponse,
} from "../../api/client";

export interface ShareModalProps {
  /** The flow being shared — modal closes when null. */
  flow: Record<string, unknown> | null;
  /** Existing saved-flow id, if any. */
  savedFlowId: string | null;
  /** Close + cancel. */
  onClose: () => void;
  /** Called once the share is complete with the freshly-minted token. */
  onShared: (response: ShareFlowResponse) => void;
  /** Test seam — main API client. */
  clientImpl?: Client;
  /** Test seam — Wave 4D collab client. */
  collabImpl?: CollabClient;
}

const MAX_BUNDLE_ROWS = 100;

/**
 * Share-as-link modal with optional fixture-data embedding.
 *
 * Steps the user through:
 *   1. Pick TTL + scopes (defaults sane).
 *   2. Optionally tick "Include fixture data" — preview pane on the right
 *      then renders a sample of synthetic rows generated from the flow's
 *      input dataset schemas.
 *   3. Click "Create link" — saves the flow if needed, mints a share
 *      token, and (if fixtures are on) attaches the bundle as a
 *      base64-encoded blob the recipient can replay.
 */
export function ShareModal(props: ShareModalProps): JSX.Element | null {
  const { flow, savedFlowId, onClose, onShared } = props;
  const cli = props.clientImpl ?? defaultClient;
  const collab = props.collabImpl ?? defaultCollab;

  const [includeFixtures, setIncludeFixtures] = useState(false);
  const [preview, setPreview] = useState<FixturePreviewResponse | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!flow || !includeFixtures) {
      setPreview(null);
      setPreviewError(null);
      return;
    }
    let cancelled = false;
    setPreviewLoading(true);
    setPreviewError(null);
    collab
      .previewFixtures(flow, 5)
      .then((res) => {
        if (!cancelled) setPreview(res);
      })
      .catch((err) => {
        if (!cancelled) {
          setPreviewError(err instanceof Error ? err.message : String(err));
        }
      })
      .finally(() => {
        if (!cancelled) setPreviewLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [flow, includeFixtures, collab]);

  const inputDatasetCount = preview?.datasets.length ?? 0;

  const onCreate = async (): Promise<void> => {
    if (!flow) return;
    setBusy(true);
    setError(null);
    try {
      let flowId = savedFlowId;
      if (!flowId) {
        const saved = await cli.saveFlow({
          flow,
          name: (flow.flow_name as string | undefined) ?? "shared-flow",
        });
        flowId = saved.id;
      }
      // Generate the bundle on the server when requested. For v1 we
      // surface it as a downloadable blob alongside the share URL — the
      // recipient gets a link plus the fixture file.
      if (includeFixtures) {
        const bundle = await collab.bundleFixtures(flow, MAX_BUNDLE_ROWS);
        // Trigger a download — the share URL itself stays small.
        triggerJsonDownload(
          {
            flow_id: flowId,
            ...bundle,
          },
          `${(flow.flow_name as string) ?? "flow"}-fixtures.json`,
        );
      }
      const shared = await cli.shareFlow(flowId, {
        ttl_seconds: 24 * 60 * 60,
        scopes: ["read"],
      });
      onShared(shared);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  const flowName = useMemo(
    () => (flow?.flow_name as string | undefined) ?? "(unnamed flow)",
    [flow],
  );

  if (!flow) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Share flow"
      data-testid="share-modal"
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(16,24,40,0.5)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 60,
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        style={{
          background: "var(--surface)",
          color: "var(--fg)",
          borderRadius: "var(--radius-lg)",
          boxShadow: "var(--shadow-lg)",
          width: "min(720px, 92vw)",
          maxHeight: "92vh",
          overflow: "hidden",
          display: "grid",
          gridTemplateRows: "auto 1fr auto",
          fontFamily: "var(--font-sans)",
        }}
      >
        <header
          style={{
            padding: "var(--space-4) var(--space-5)",
            borderBottom: "1px solid var(--border)",
            display: "flex",
            alignItems: "center",
            gap: "var(--space-3)",
          }}
        >
          <h2
            style={{
              margin: 0,
              fontSize: "var(--text-md)",
              fontWeight: "var(--font-weight-semibold)",
              flex: 1,
            }}
          >
            Share flow
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            data-testid="share-modal-close"
            style={{
              border: 0,
              background: "transparent",
              cursor: "pointer",
              fontSize: "1.2rem",
              color: "var(--fg-muted)",
            }}
          >
            ×
          </button>
        </header>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "minmax(220px, 280px) 1fr",
            minHeight: 0,
          }}
        >
          <section
            style={{
              padding: "var(--space-5)",
              borderRight: "1px solid var(--border)",
              display: "flex",
              flexDirection: "column",
              gap: "var(--space-4)",
              overflow: "auto",
            }}
          >
            <div>
              <label
                style={{
                  display: "block",
                  fontSize: "var(--text-sm)",
                  color: "var(--fg-muted)",
                  marginBottom: "var(--space-1)",
                }}
              >
                Flow
              </label>
              <div
                style={{
                  fontSize: "var(--text-sm)",
                  fontWeight: "var(--font-weight-medium)",
                }}
              >
                {flowName}
              </div>
            </div>
            <label
              style={{
                display: "flex",
                alignItems: "flex-start",
                gap: "var(--space-2)",
                fontSize: "var(--text-sm)",
                lineHeight: "var(--lh-snug)",
                cursor: "pointer",
              }}
              data-testid="include-fixtures-label"
            >
              <input
                type="checkbox"
                checked={includeFixtures}
                onChange={(e) => setIncludeFixtures(e.target.checked)}
                data-testid="include-fixtures-checkbox"
                style={{ marginTop: 3 }}
              />
              <span>
                <strong>Include fixture data</strong>
                <br />
                <span
                  style={{ color: "var(--fg-muted)", fontSize: "var(--text-xs)" }}
                >
                  Up to {MAX_BUNDLE_ROWS} synthetic rows per input dataset.
                  Recipient can replay without sourcing live data.
                </span>
              </span>
            </label>
            {error ? (
              <div
                role="alert"
                data-testid="share-modal-error"
                style={{
                  padding: "var(--space-2) var(--space-3)",
                  borderRadius: "var(--radius-md)",
                  background: "var(--danger-bg)",
                  border: "1px solid var(--danger-border)",
                  color: "var(--danger-fg)",
                  fontSize: "var(--text-xs)",
                }}
              >
                {error}
              </div>
            ) : null}
          </section>

          <section
            data-testid="fixture-preview"
            aria-live="polite"
            style={{
              padding: "var(--space-5)",
              overflow: "auto",
              display: "flex",
              flexDirection: "column",
              gap: "var(--space-3)",
            }}
          >
            <h3
              style={{
                margin: 0,
                fontSize: "var(--text-sm)",
                color: "var(--fg-muted)",
                fontWeight: "var(--font-weight-medium)",
                textTransform: "uppercase",
                letterSpacing: 0.4,
              }}
            >
              Fixture preview
            </h3>
            {!includeFixtures ? (
              <p
                data-testid="fixture-preview-disabled"
                style={{
                  fontSize: "var(--text-sm)",
                  color: "var(--fg-subtle)",
                  margin: 0,
                }}
              >
                Tick "Include fixture data" to see a sample of the rows that
                will be embedded.
              </p>
            ) : previewLoading ? (
              <p style={{ color: "var(--fg-muted)", fontSize: "var(--text-sm)" }}>
                Generating sample rows…
              </p>
            ) : previewError ? (
              <p
                role="alert"
                data-testid="fixture-preview-error"
                style={{
                  color: "var(--danger-fg)",
                  fontSize: "var(--text-sm)",
                }}
              >
                Could not generate preview: {previewError}
              </p>
            ) : preview && preview.datasets.length > 0 ? (
              preview.datasets.map((d) => (
                <div
                  key={d.name}
                  data-testid={`fixture-dataset-${d.name}`}
                  style={{
                    border: "1px solid var(--border)",
                    borderRadius: "var(--radius-md)",
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      padding: "var(--space-2) var(--space-3)",
                      background: "var(--surface-sunken)",
                      fontSize: "var(--text-xs)",
                      color: "var(--fg-muted)",
                      display: "flex",
                      gap: "var(--space-2)",
                    }}
                  >
                    <strong style={{ color: "var(--fg)" }}>{d.name}</strong>
                    <span>{d.columns.length} columns</span>
                  </div>
                  <FixtureTable rows={d.sample_rows} columns={d.columns} />
                </div>
              ))
            ) : (
              <p
                data-testid="fixture-preview-empty"
                style={{
                  color: "var(--fg-subtle)",
                  fontSize: "var(--text-sm)",
                }}
              >
                No input datasets detected — nothing will be embedded.
              </p>
            )}
          </section>
        </div>

        <footer
          style={{
            padding: "var(--space-3) var(--space-5)",
            borderTop: "1px solid var(--border)",
            display: "flex",
            alignItems: "center",
            gap: "var(--space-3)",
            justifyContent: "flex-end",
          }}
        >
          {includeFixtures ? (
            <span
              style={{ fontSize: "var(--text-xs)", color: "var(--fg-muted)" }}
              data-testid="include-fixtures-summary"
            >
              {inputDatasetCount} input dataset
              {inputDatasetCount === 1 ? "" : "s"} · ≤ {MAX_BUNDLE_ROWS} rows
              each
            </span>
          ) : null}
          <button
            type="button"
            onClick={onClose}
            data-testid="share-modal-cancel"
            style={{
              padding: "var(--space-2) var(--space-4)",
              border: "1px solid var(--border-strong)",
              borderRadius: "var(--radius-md)",
              background: "transparent",
              color: "inherit",
              cursor: "pointer",
              fontSize: "var(--text-sm)",
            }}
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={() => void onCreate()}
            disabled={busy}
            data-testid="share-modal-submit"
            style={{
              padding: "var(--space-2) var(--space-4)",
              border: 0,
              borderRadius: "var(--radius-md)",
              background: "var(--accent)",
              color: "var(--accent-fg)",
              cursor: busy ? "not-allowed" : "pointer",
              fontSize: "var(--text-sm)",
              fontWeight: "var(--font-weight-semibold)",
              opacity: busy ? 0.6 : 1,
            }}
          >
            {busy ? "Creating link…" : "Create link"}
          </button>
        </footer>
      </div>
    </div>
  );
}

function FixtureTable(props: {
  rows: Array<Record<string, unknown>>;
  columns: string[];
}): JSX.Element {
  const { rows, columns } = props;
  if (rows.length === 0) {
    return (
      <div
        style={{
          padding: "var(--space-3)",
          fontSize: "var(--text-xs)",
          color: "var(--fg-subtle)",
        }}
      >
        No sample rows available for this dataset.
      </div>
    );
  }
  return (
    <div style={{ overflowX: "auto", maxHeight: 200 }}>
      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          fontSize: "var(--text-xs)",
          fontFamily: "var(--font-mono)",
        }}
      >
        <thead>
          <tr>
            {columns.slice(0, 6).map((c) => (
              <th
                key={c}
                style={{
                  padding: "4px 8px",
                  textAlign: "left",
                  color: "var(--fg-muted)",
                  borderBottom: "1px solid var(--border)",
                }}
              >
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} style={{ borderBottom: "1px solid var(--border)" }}>
              {columns.slice(0, 6).map((c) => (
                <td
                  key={c}
                  style={{
                    padding: "4px 8px",
                    color: "var(--fg)",
                    whiteSpace: "nowrap",
                  }}
                >
                  {String(row[c] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function triggerJsonDownload(
  payload: Record<string, unknown>,
  filename: string,
): void {
  if (typeof window === "undefined" || typeof document === "undefined") return;
  const blob = new Blob([JSON.stringify(payload, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  try {
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
  } finally {
    setTimeout(() => URL.revokeObjectURL(url), 0);
  }
}
