import { useCallback, useState, type CSSProperties } from "react";
import {
  useSuggestMapping,
  applySuggestionToEditor,
  APPLY_CONFIDENCE_THRESHOLD,
  type UseSuggestOptions,
  type MonacoLikeEditor,
} from "./useSuggestMapping";

export interface SuggestMappingBannerProps {
  /** Original Python source for the PYTHON recipe. */
  pythonSource: string;
  /** Recipe being analysed — used for audit/history correlation. */
  recipeName?: string;
  /** Optional flow id for audit correlation. */
  flowId?: string;
  /** Provider override — defaults to "anthropic". */
  provider?: "anthropic" | "openai" | "mock";
  /**
   * Editor handle. The banner calls ``editor.executeEdits()`` to apply the
   * suggested rewrite. When undefined the Apply CTA is hidden — useful in
   * read-only contexts (Diff, Share view).
   */
  editor?: MonacoLikeEditor | null;
  /** Test seam for the suggest hook. */
  options?: UseSuggestOptions;
  /** Called when the user dismisses the banner. */
  onDismiss?: () => void;
  /**
   * Called after a successful apply. The host can refresh its conversion
   * pipeline so the canvas re-renders with the visual recipe in place.
   */
  onApplied?: (info: { mode: "exact" | "full-replace" }) => void;
}

/**
 * Yellow banner surfaced on PYTHON recipe nodes. Click "Show suggestion" →
 * fetches a visual-recipe equivalent. If confidence ≥ 0.7 the "Apply" CTA
 * replaces the original source in the Monaco editor via ``executeEdits``.
 */
export function SuggestMappingBanner(
  props: SuggestMappingBannerProps,
): JSX.Element {
  const {
    pythonSource,
    recipeName,
    flowId,
    provider,
    editor,
    options,
    onDismiss,
    onApplied,
  } = props;

  const suggest = useSuggestMapping(options);
  const [applyMode, setApplyMode] = useState<
    "exact" | "full-replace" | "noop" | null
  >(null);

  const onShowClick = useCallback(() => {
    void suggest.request({
      python_source: pythonSource,
      flow_id: flowId ?? null,
      provider: provider ?? "anthropic",
    });
  }, [suggest, pythonSource, flowId, provider]);

  const onApplyClick = useCallback(() => {
    if (!editor || !suggest.data) return;
    const result = applySuggestionToEditor(
      editor,
      pythonSource,
      suggest.data.transformed_pandas,
    );
    setApplyMode(result.mode);
    if (result.applied && onApplied) {
      onApplied({ mode: result.mode === "noop" ? "exact" : result.mode });
    }
  }, [editor, suggest.data, pythonSource, onApplied]);

  const isHigh =
    suggest.data !== null && suggest.data.confidence >= APPLY_CONFIDENCE_THRESHOLD;

  return (
    <div
      role="status"
      data-testid={`suggest-banner-${recipeName ?? "default"}`}
      style={bannerStyle}
    >
      <span style={iconStyle} aria-hidden>
        ▲
      </span>
      <div style={{ flex: 1, minWidth: 0 }}>
        {suggest.status === "idle" && (
          <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
            <span>Visual recipe equivalent available — show suggestion?</span>
            <button
              type="button"
              data-testid="suggest-show"
              onClick={onShowClick}
              style={primaryBtnStyle}
            >
              Show suggestion
            </button>
            {onDismiss && (
              <button
                type="button"
                data-testid="suggest-dismiss"
                onClick={onDismiss}
                style={ghostBtnStyle}
              >
                Dismiss
              </button>
            )}
          </div>
        )}

        {suggest.status === "loading" && (
          <span data-testid="suggest-loading" style={mutedStyle}>
            Asking the assistant…
          </span>
        )}

        {suggest.status === "error" && suggest.error && (
          <span data-testid="suggest-error" style={errorStyle}>
            {suggest.error.title}
            {suggest.error.detail ? `: ${suggest.error.detail}` : ""}
          </span>
        )}

        {suggest.status === "ready" && suggest.data && (
          <div>
            <div style={summaryRowStyle}>
              <strong data-testid="suggest-type">
                {suggest.data.suggested_recipe_type}
              </strong>
              <span style={confidenceStyle} data-testid="suggest-confidence">
                {Math.round(suggest.data.confidence * 100)}% confidence
              </span>
            </div>
            <div style={reasoningStyle} data-testid="suggest-reasoning">
              {suggest.data.reasoning}
            </div>
            {applyMode && (
              <div data-testid="suggest-applied" style={appliedStyle}>
                Applied ({applyMode}).
              </div>
            )}
            <div style={{ display: "flex", gap: 6, marginTop: 6 }}>
              {isHigh && editor ? (
                <button
                  type="button"
                  data-testid="suggest-apply"
                  onClick={onApplyClick}
                  style={primaryBtnStyle}
                >
                  Apply suggestion
                </button>
              ) : (
                <span style={mutedStyle} data-testid="suggest-info-only">
                  {isHigh
                    ? "Editor not ready — open the Convert page to apply."
                    : "Below 70% confidence — informational only."}
                </span>
              )}
              {onDismiss && (
                <button
                  type="button"
                  data-testid="suggest-dismiss"
                  onClick={onDismiss}
                  style={ghostBtnStyle}
                >
                  Dismiss
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Styles — driven entirely off ui-tokens.css custom props with safe fallbacks.
// ---------------------------------------------------------------------------

const bannerStyle: CSSProperties = {
  display: "flex",
  alignItems: "flex-start",
  gap: "var(--space-2, 8px)",
  background: "var(--warn-surface, #fff8db)",
  color: "var(--fg, #111111)",
  border: "1px solid var(--warn-border, #ead65b)",
  borderRadius: "var(--radius-md, 6px)",
  padding: "var(--space-2, 8px) var(--space-3, 12px)",
  fontSize: "var(--text-xs, 12px)",
  lineHeight: 1.4,
};

const iconStyle: CSSProperties = {
  color: "var(--warn-fg, #92670d)",
  fontWeight: 700,
};

const primaryBtnStyle: CSSProperties = {
  background: "var(--accent, #0d9488)",
  color: "var(--accent-fg, #ffffff)",
  border: 0,
  borderRadius: "var(--radius-sm, 4px)",
  padding: "var(--space-1, 3px) var(--space-2, 8px)",
  fontSize: "var(--text-xs, 12px)",
  cursor: "pointer",
  fontWeight: 600,
};

const ghostBtnStyle: CSSProperties = {
  background: "transparent",
  color: "var(--fg-muted, #5b6470)",
  border: "1px solid var(--border, #eaecf0)",
  borderRadius: "var(--radius-sm, 4px)",
  padding: "var(--space-1, 3px) var(--space-2, 8px)",
  fontSize: "var(--text-xs, 12px)",
  cursor: "pointer",
};

const mutedStyle: CSSProperties = {
  color: "var(--fg-muted, #5b6470)",
  fontStyle: "italic",
};

const errorStyle: CSSProperties = {
  color: "var(--danger, #b42318)",
};

const summaryRowStyle: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "var(--space-2, 8px)",
};

const confidenceStyle: CSSProperties = {
  color: "var(--fg-muted, #5b6470)",
  fontSize: "var(--text-2xs, 10px)",
};

const reasoningStyle: CSSProperties = {
  color: "var(--fg-muted, #5b6470)",
  marginTop: 2,
};

const appliedStyle: CSSProperties = {
  marginTop: 4,
  color: "var(--success, #027a48)",
  fontSize: "var(--text-2xs, 10px)",
};
