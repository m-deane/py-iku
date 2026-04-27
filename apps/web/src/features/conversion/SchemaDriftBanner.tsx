/**
 * SchemaDriftBanner — surfaces above the editor on a re-conversion.
 *
 * Compares the freshly-converted flow against the prior snapshot keyed by
 * source-hash and shows a one-line summary plus a "Review →" button that
 * opens the side panel.
 */
import { useEffect, useState } from "react";
import {
  client as defaultClient,
  type Client,
  type SchemaDriftResponse,
} from "../../api/client";
import {
  hashSource,
  projectForSnapshot,
  useSchemaSnapshots,
} from "../../store/schemaSnapshots";

export interface SchemaDriftBannerProps {
  /** The Python source we just converted. */
  source: string;
  /** The freshly-converted flow. */
  flow: Record<string, unknown> | null;
  /** Test seam — pass an explicit snapshot store. */
  clientImpl?: Client;
  /** Test seam — skip auto-capture (only test diff). */
  noAutoCapture?: boolean;
  /** Called when the user opens the panel. */
  onReview?: (drift: SchemaDriftResponse) => void;
}

export function SchemaDriftBanner(props: SchemaDriftBannerProps): JSX.Element | null {
  const { source, flow, onReview } = props;
  const apiClient = props.clientImpl ?? defaultClient;
  const put = useSchemaSnapshots((s) => s.put);
  const get = useSchemaSnapshots((s) => s.get);

  const [drift, setDrift] = useState<SchemaDriftResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    if (!flow || !source) return;
    let cancelled = false;
    const sourceHash = hashSource(source);
    const prior = get(sourceHash);

    const compare = async (): Promise<void> => {
      if (!prior) {
        // No prior snapshot — capture and we're done.
        if (!props.noAutoCapture) {
          put(sourceHash, {
            flow: projectForSnapshot(flow),
            capturedAt: new Date().toISOString(),
          });
        }
        return;
      }
      try {
        const result = await apiClient.schemaDrift(prior.flow, projectForSnapshot(flow));
        if (cancelled) return;
        setDrift(result);
        // Refresh the snapshot for next time.
        if (!props.noAutoCapture) {
          put(sourceHash, {
            flow: projectForSnapshot(flow),
            capturedAt: new Date().toISOString(),
          });
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
        }
      }
    };

    void compare();
    return () => {
      cancelled = true;
    };
  }, [apiClient, flow, source, put, get, props.noAutoCapture]);

  if (dismissed) return null;
  if (error) {
    return (
      <div
        role="alert"
        data-testid="schema-drift-banner-error"
        style={{
          padding: "0.6rem 0.8rem",
          borderRadius: "var(--radius-md, 6px)",
          background: "rgba(183,28,28,0.08)",
          color: "#b71c1c",
          fontSize: "var(--text-xs, 12px)",
        }}
      >
        Schema-drift check failed: {error}
      </div>
    );
  }

  if (!drift?.summary?.has_drift) return null;

  return (
    <div
      role="status"
      data-testid="schema-drift-banner"
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "0.75rem",
        padding: "0.6rem 0.8rem",
        borderRadius: "var(--radius-md, 6px)",
        border: "1px solid var(--border-strong, #d0d5dd)",
        background: "var(--accent-bg-soft, #ccfbf1)",
        color: "var(--accent-hover, #0f766e)",
        fontSize: "var(--text-sm, 13px)",
      }}
    >
      <span>
        <strong>Schema drift detected.</strong>{" "}
        <span data-testid="schema-drift-headline">{drift.headline}</span>
      </span>
      <span style={{ display: "flex", gap: "0.4rem" }}>
        <button
          type="button"
          data-testid="schema-drift-review"
          onClick={() => onReview?.(drift)}
          style={{
            padding: "0.25rem 0.7rem",
            borderRadius: "var(--radius-sm, 4px)",
            border: "1px solid var(--accent-hover, #0f766e)",
            background: "var(--accent, #0d9488)",
            color: "var(--accent-fg, #fff)",
            cursor: "pointer",
            fontSize: "var(--text-xs, 12px)",
          }}
        >
          Review →
        </button>
        <button
          type="button"
          aria-label="Dismiss schema-drift banner"
          data-testid="schema-drift-dismiss"
          onClick={() => setDismissed(true)}
          style={{
            padding: "0.25rem 0.5rem",
            borderRadius: "var(--radius-sm, 4px)",
            border: "1px solid var(--border-strong, #d0d5dd)",
            background: "transparent",
            color: "inherit",
            cursor: "pointer",
            fontSize: "var(--text-xs, 12px)",
          }}
        >
          ×
        </button>
      </span>
    </div>
  );
}
