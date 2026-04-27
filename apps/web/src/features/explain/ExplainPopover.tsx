import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type CSSProperties,
} from "react";
import {
  useExplainRecipe,
  type UseExplainOptions,
} from "./useExplainCache";
import { useChatStore, flowIdFromCode } from "../chat/chatStore";

export interface ExplainPopoverProps {
  /** The recipe being explained. Whole serialized DataikuRecipe is passed. */
  recipe: Record<string, unknown>;
  /** Optional extra context — upstream/downstream recipes, code snippet, etc. */
  context?: Record<string, unknown>;
  /** Open state controlled by the parent (RecipeNode owns hover/click). */
  open: boolean;
  /** Provider override — defaults to "anthropic". */
  provider?: "anthropic" | "openai" | "mock";
  /** Optional flow id for audit correlation. */
  flowId?: string;
  /** Test seam — swap in a stub `client.explainRecipe`. */
  options?: UseExplainOptions;
  /** Called when the popover requests close (Esc, "More" CTA). */
  onClose?: () => void;
  /**
   * Called when the user clicks "More". Defaults to opening the chat drawer
   * and seeding the first message with the explanation, but the parent can
   * override (e.g. to also pop the chat focus).
   */
  onMore?: (recipeName: string, summary: string) => void;
}

const HOVER_DELAY_MS = 700;

/**
 * AI explain-this-recipe popover. Three single-sentence bullets framed for
 * front-office trading vocabulary:
 *   - "What this does"
 *   - "Trading context"
 *   - "What to watch out for"
 *
 * Click "More" to escalate into the chat drawer with the explanation
 * pre-loaded as the first assistant turn — the trader can then ask
 * follow-ups against the same flow.
 */
export function ExplainPopover(props: ExplainPopoverProps): JSX.Element | null {
  const { recipe, context, open, provider, flowId, options, onClose } = props;
  const explain = useExplainRecipe(options);
  const lastKeyRef = useRef<string | null>(null);

  // Trigger fetch on open. The hook's own client-cache short-circuits hot paths.
  useEffect(() => {
    if (!open) return;
    const recipeName = String(recipe.name ?? "(unnamed)");
    if (lastKeyRef.current === recipeName && explain.status !== "idle") return;
    lastKeyRef.current = recipeName;
    void explain.request({
      recipe,
      context: context ?? null,
      flow_id: flowId ?? null,
      provider: provider ?? "anthropic",
    });
    // We intentionally only re-trigger on `open` toggling so re-renders of
    // the parent don't double-fetch.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const onMoreClick = useCallback(() => {
    if (!explain.data) return;
    const summary = formatChatPrefill(
      String(recipe.name ?? "(unnamed)"),
      explain.data,
    );
    if (props.onMore) {
      props.onMore(String(recipe.name ?? ""), summary);
    } else {
      // Default: open the chat drawer + seed the assistant turn.
      const code = ""; // ChatDrawer reads its own flow code
      const flowKey = flowId ?? flowIdFromCode(code);
      const store = useChatStore.getState();
      store.appendTurn(flowKey, {
        id: `t-explain-${Date.now()}`,
        role: "assistant",
        content: summary,
        ts: Date.now(),
      });
      store.setOpen(true);
    }
    onClose?.();
  }, [explain.data, recipe, flowId, props, onClose]);

  if (!open) return null;

  return (
    <div
      data-testid={`explain-popover-${recipe.name ?? "unnamed"}`}
      role="dialog"
      aria-label={`Explanation for recipe ${recipe.name}`}
      style={popoverStyle}
    >
      <div style={titleStyle}>
        Explain · {String(recipe.type ?? "?")}
        {explain.data?.cache_hit || explain.clientCacheHit ? (
          <span
            data-testid="explain-cache-badge"
            style={badgeStyle}
            title="Served from cache — no LLM cost"
          >
            cached
          </span>
        ) : null}
      </div>

      {explain.status === "loading" && (
        <div data-testid="explain-loading" style={mutedStyle}>
          Asking the assistant…
        </div>
      )}

      {explain.status === "error" && explain.error && (
        <div data-testid="explain-error" style={errorStyle}>
          {explain.error.title}
          {explain.error.detail ? `: ${explain.error.detail}` : null}
        </div>
      )}

      {explain.status === "ready" && explain.data && (
        <div>
          <Section
            label="What this does"
            text={explain.data.what_this_does}
            testid="explain-what"
          />
          <Section
            label="Trading context"
            text={explain.data.trading_context}
            testid="explain-trading"
          />
          <Section
            label="Watch out for"
            text={explain.data.watch_out_for}
            testid="explain-watch"
          />
          <div style={ctaRowStyle}>
            <button
              type="button"
              data-testid="explain-more"
              onClick={onMoreClick}
              style={moreBtnStyle}
            >
              More →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function Section(props: { label: string; text: string; testid: string }): JSX.Element {
  return (
    <div style={{ marginBottom: 6 }}>
      <div style={sectionLabelStyle}>{props.label}</div>
      <div data-testid={props.testid} style={sectionBodyStyle}>
        {props.text}
      </div>
    </div>
  );
}

function formatChatPrefill(
  name: string,
  data: { what_this_does: string; trading_context: string; watch_out_for: string },
): string {
  return [
    `Recipe explanation for [recipe:${name}]:`,
    `• What this does — ${data.what_this_does}`,
    `• Trading context — ${data.trading_context}`,
    `• Watch out for — ${data.watch_out_for}`,
  ].join("\n");
}

// ---------------------------------------------------------------------------
// Tiny hook used by RecipeNode to reproduce the documented hover/click UX.
// 700ms hover delay; click toggles open immediately. Keeping this here lets
// RecipeNode stay agnostic of the popover's internal API surface.
// ---------------------------------------------------------------------------

export interface UseExplainTriggerResult {
  open: boolean;
  setOpen: (v: boolean) => void;
  hoverProps: {
    onMouseEnter: () => void;
    onMouseLeave: () => void;
  };
  clickProps: {
    onClick: (e: React.MouseEvent) => void;
  };
}

export function useExplainTrigger(): UseExplainTriggerResult {
  const [open, setOpen] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const onMouseEnter = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => setOpen(true), HOVER_DELAY_MS);
  }, []);
  const onMouseLeave = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);
  const onClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    setOpen((v) => !v);
  }, []);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  return {
    open,
    setOpen,
    hoverProps: { onMouseEnter, onMouseLeave },
    clickProps: { onClick },
  };
}

// ---------------------------------------------------------------------------
// Styles — all driven off ui-tokens.css custom props. No hard-coded hex.
// ---------------------------------------------------------------------------

const popoverStyle: CSSProperties = {
  position: "absolute",
  top: "100%",
  left: 0,
  marginTop: 6,
  background: "var(--surface-raised, #ffffff)",
  color: "var(--fg, #111111)",
  border: "1px solid var(--border, #e0e0e0)",
  borderRadius: "var(--radius-md, 6px)",
  padding: "var(--space-3, 10px) var(--space-3, 12px)",
  boxShadow: "var(--shadow-lg, 0 6px 18px rgba(0,0,0,0.18))",
  minWidth: 260,
  maxWidth: 320,
  fontSize: "var(--text-xs, 12px)",
  lineHeight: 1.45,
  zIndex: 110,
};

const titleStyle: CSSProperties = {
  fontWeight: 600,
  marginBottom: 6,
  display: "flex",
  alignItems: "center",
  gap: "var(--space-2, 6px)",
  color: "var(--fg, #111111)",
};

const badgeStyle: CSSProperties = {
  marginLeft: "auto",
  padding: "1px 6px",
  fontSize: "var(--text-2xs, 10px)",
  background: "var(--surface, #f3f4f6)",
  color: "var(--fg-muted, #5b6470)",
  borderRadius: "var(--radius-sm, 4px)",
  border: "1px solid var(--border, #eaecf0)",
};

const mutedStyle: CSSProperties = {
  color: "var(--fg-muted, #5b6470)",
  fontStyle: "italic",
};

const errorStyle: CSSProperties = {
  color: "var(--danger, #b42318)",
};

const sectionLabelStyle: CSSProperties = {
  fontWeight: 600,
  fontSize: "var(--text-2xs, 10px)",
  textTransform: "uppercase",
  letterSpacing: "0.04em",
  color: "var(--fg-muted, #5b6470)",
  marginBottom: 2,
};

const sectionBodyStyle: CSSProperties = {
  color: "var(--fg, #111111)",
};

const ctaRowStyle: CSSProperties = {
  display: "flex",
  justifyContent: "flex-end",
  marginTop: "var(--space-2, 6px)",
};

const moreBtnStyle: CSSProperties = {
  background: "transparent",
  border: 0,
  padding: 0,
  color: "var(--accent, #0d9488)",
  cursor: "pointer",
  textDecoration: "underline",
  font: "inherit",
};
