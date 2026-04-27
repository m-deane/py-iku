import {
  memo,
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
  type CSSProperties,
  type KeyboardEvent as ReactKeyboardEvent,
} from "react";
import { Handle, Position, type NodeProps } from "reactflow";
import clsx from "clsx";
import type { NodeStatus, RecipeNodeData, RecipeType, ThemeName } from "../types";
import { getRecipeColor } from "../theme/tokens";
import { getRecipeGlyph } from "../theme/icons";
import { categoryFor, subLabelFor, type RecipeCategory } from "./categories";
import { getSvgGlyph } from "./glyphs";
import styles from "./RecipeNode.module.css";

interface RecipeNodeProps extends NodeProps<RecipeNodeData> {
  /** Optional theme override; defaults to reading the closest `data-theme` attr. */
  theme?: ThemeName;
  /** Override the auto-derived category. Used by tests / stories. */
  category?: RecipeCategory;
  /**
   * Optional click handler for the "Lines X-Y of source ↗" link in the
   * popover. The Studio Convert page wires this to a function that calls
   * `monaco.editor.deltaDecorations` to highlight the source span; the
   * package itself stays Monaco-free.
   */
  onSourceLinesClick?: (range: [number, number]) => void;
  /**
   * Sprint-5 explain-this-recipe adapter. The host app (apps/web) wires this
   * to the AI explain popover so the package itself stays free of API/
   * provider concerns. When present, a small `(i)` icon renders on the card;
   * clicking it (or hovering for ~700ms) flips ``open`` and the host renders
   * its popover via ``renderPopover``.
   */
  explainAdapter?: ExplainAdapter;
}

export interface ExplainAdapter {
  /** Called the first time the popover should open (hover or click). */
  onExplainRequested: (recipeName: string, recipeType: RecipeType) => void;
  /**
   * Render-prop the host uses to mount its popover JSX inside the card. The
   * function is called with `{ open, close }` so the host can react to RecipeNode-
   * driven open/close transitions (Esc, outside-click).
   */
  renderPopover: (args: { open: boolean; close: () => void }) => React.ReactNode;
}

const EXPLAIN_HOVER_DELAY_MS = 700;

/** Confidence shading bands. */
type ConfidenceBand = "high" | "medium" | "low" | "rule-based";

function bandFor(confidence: number | null | undefined): ConfidenceBand {
  if (confidence === null || confidence === undefined) return "rule-based";
  if (confidence >= 0.85) return "high";
  if (confidence >= 0.6) return "medium";
  return "low";
}

function readTheme(): ThemeName {
  if (typeof document === "undefined") return "light";
  const attr = document.documentElement.getAttribute("data-theme");
  return attr === "dark" ? "dark" : "light";
}

/**
 * Base recipe node. Renders the rounded tile with category-color stripe,
 * SVG or Unicode glyph, label, optional sub-label badge (code recipes get a
 * monospace language tag), IO badges, status badge, and category-specific
 * decorations. Colors are read from `tokens.json` per RecipeType + theme;
 * no hard-coded hex.
 *
 * Sprint-3 additions:
 *   - LLM confidence shading via the medium/low CSS classes (no inline hex).
 *   - "R" rule-based badge in the bottom-left when `data.confidence == null`.
 *   - Keyboard-accessible popover (Enter/Space opens, Esc closes, Tab
 *     traps to the source-line link inside).
 */
function RecipeNodeImpl(props: RecipeNodeProps): JSX.Element {
  const {
    data,
    selected,
    theme: themeProp,
    category: categoryProp,
    onSourceLinesClick,
    explainAdapter,
  } = props;
  const theme: ThemeName = themeProp ?? readTheme();
  const colors = getRecipeColor(data.type, theme);
  const status: NodeStatus = data.status ?? "none";
  const category = categoryProp ?? categoryFor(data.type);
  const SvgGlyph = getSvgGlyph(data.type);
  const subLabel = subLabelFor(data.type);
  const dimmed = data.dimmed === true;

  const band = bandFor(data.confidence);
  const popoverId = useId();
  const [popoverOpen, setPopoverOpen] = useState(false);
  const cardRef = useRef<HTMLDivElement | null>(null);
  const popoverRef = useRef<HTMLDivElement | null>(null);
  const sourceLinkRef = useRef<HTMLButtonElement | null>(null);

  // Close on Esc anywhere; close on outside click. Both behaviours are
  // standard popover patterns and unblock Tab navigation past the card.
  useEffect(() => {
    if (!popoverOpen) return;
    const onDocKey = (e: globalThis.KeyboardEvent): void => {
      if (e.key === "Escape") {
        setPopoverOpen(false);
        cardRef.current?.focus();
      }
    };
    const onDocPointer = (e: MouseEvent): void => {
      const target = e.target as Node | null;
      if (!target) return;
      if (
        cardRef.current &&
        !cardRef.current.contains(target) &&
        popoverRef.current &&
        !popoverRef.current.contains(target)
      ) {
        setPopoverOpen(false);
      }
    };
    document.addEventListener("keydown", onDocKey);
    document.addEventListener("mousedown", onDocPointer);
    return () => {
      document.removeEventListener("keydown", onDocKey);
      document.removeEventListener("mousedown", onDocPointer);
    };
  }, [popoverOpen]);

  // Auto-focus the source-line link on open so Tab traps inside the popover.
  useEffect(() => {
    if (popoverOpen && sourceLinkRef.current) {
      sourceLinkRef.current.focus();
    }
  }, [popoverOpen]);

  const onCardKey = useCallback(
    (e: ReactKeyboardEvent<HTMLDivElement>): void => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        setPopoverOpen((v) => !v);
      }
    },
    [],
  );

  const onSourceLinesPress = useCallback((): void => {
    if (data.sourceLines && onSourceLinesClick) {
      onSourceLinesClick(data.sourceLines);
    }
  }, [data.sourceLines, onSourceLinesClick]);

  // ---------------------------------------------------------------------
  // Explain-this-recipe trigger (Sprint 5).  Hover for 700ms OR click the
  // (i) icon to flip ``explainOpen``. The host app renders the popover via
  // the ``explainAdapter.renderPopover`` render-prop.
  // ---------------------------------------------------------------------
  const [explainOpen, setExplainOpen] = useState(false);
  const explainTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const closeExplain = useCallback(() => setExplainOpen(false), []);

  const triggerExplain = useCallback((): void => {
    if (!explainAdapter) return;
    explainAdapter.onExplainRequested(data.name, data.type);
    setExplainOpen(true);
  }, [explainAdapter, data.name, data.type]);

  const onCardHoverEnter = useCallback((): void => {
    if (!explainAdapter) return;
    if (explainTimerRef.current) clearTimeout(explainTimerRef.current);
    explainTimerRef.current = setTimeout(() => {
      triggerExplain();
    }, EXPLAIN_HOVER_DELAY_MS);
  }, [explainAdapter, triggerExplain]);

  const onCardHoverLeave = useCallback((): void => {
    if (explainTimerRef.current) {
      clearTimeout(explainTimerRef.current);
      explainTimerRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => {
      if (explainTimerRef.current) clearTimeout(explainTimerRef.current);
    };
  }, []);

  const onExplainIconClick = useCallback(
    (e: React.MouseEvent): void => {
      e.stopPropagation();
      if (!explainAdapter) return;
      if (explainOpen) {
        setExplainOpen(false);
      } else {
        triggerExplain();
      }
    },
    [explainAdapter, explainOpen, triggerExplain],
  );

  // Close explain popover on outside click. Re-uses the existing card ref.
  useEffect(() => {
    if (!explainOpen) return;
    const onDocPointer = (e: MouseEvent): void => {
      const target = e.target as Node | null;
      if (!target) return;
      if (cardRef.current && !cardRef.current.contains(target)) {
        setExplainOpen(false);
      }
    };
    const onDocKey = (e: globalThis.KeyboardEvent): void => {
      if (e.key === "Escape") setExplainOpen(false);
    };
    document.addEventListener("mousedown", onDocPointer);
    document.addEventListener("keydown", onDocKey);
    return () => {
      document.removeEventListener("mousedown", onDocPointer);
      document.removeEventListener("keydown", onDocKey);
    };
  }, [explainOpen]);

  const styleVars: CSSProperties = {
    ["--node-bg" as string]: colors.bg,
    ["--node-border" as string]: colors.border,
    ["--node-text" as string]: colors.text,
  };

  const showWarn = band === "medium" || band === "low";
  const showRuleBadge = band === "rule-based";
  const confidencePct =
    typeof data.confidence === "number"
      ? Math.round(data.confidence * 100)
      : null;

  return (
    <div
      ref={cardRef}
      className={clsx(
        styles.recipeNode,
        styles[`category-${category}`],
        selected && styles.selected,
        status === "error" && styles.error,
        status === "executing" && styles.executing,
        status === "done" && styles.done,
        dimmed && styles.dimmed,
        band === "medium" && styles.confidenceMedium,
        band === "low" && styles.confidenceLow,
      )}
      style={styleVars}
      data-recipe-type={data.type}
      data-category={category}
      data-status={status}
      data-theme={theme}
      data-dimmed={dimmed ? "true" : undefined}
      data-confidence-band={band}
      data-confidence={
        typeof data.confidence === "number" ? data.confidence : undefined
      }
      data-testid={`recipe-node-${data.name}`}
      tabIndex={0}
      role="button"
      aria-label={`Recipe ${data.name}, type ${data.type}, ${band} confidence`}
      aria-expanded={popoverOpen}
      aria-haspopup="dialog"
      aria-controls={popoverOpen ? popoverId : undefined}
      onKeyDown={onCardKey}
      onMouseEnter={explainAdapter ? onCardHoverEnter : undefined}
      onMouseLeave={explainAdapter ? onCardHoverLeave : undefined}
    >
      <Handle type="target" position={Position.Left} />
      <span className={styles.icon} aria-hidden="true">
        {SvgGlyph ? <SvgGlyph color={colors.text} size={20} /> : getRecipeGlyph(data.type)}
      </span>
      <span className={styles.label}>{data.name}</span>
      {subLabel && (
        <span className={styles.subLabel} aria-hidden="true">
          {subLabel}
        </span>
      )}
      <span className={styles.ioRow}>
        <span className={styles.ioBadge} aria-label={`${data.inputs} inputs`}>
          ◀{data.inputs}
        </span>
        <span className={styles.ioBadge} aria-label={`${data.outputs} outputs`}>
          {data.outputs}▶
        </span>
      </span>
      {showWarn && (
        <span
          className={clsx(
            styles.confidenceWarn,
            band === "low" && styles.confidenceLowGlyph,
          )}
          aria-label={`${band} confidence`}
          data-testid={`confidence-warn-${data.name}`}
        >
          ⚠
        </span>
      )}
      {showRuleBadge && (
        <span
          className={styles.ruleBadge}
          aria-label="Rule-based recipe"
          data-testid={`rule-badge-${data.name}`}
        >
          R
        </span>
      )}
      {status !== "none" && !showWarn && (
        <span
          className={clsx(
            styles.statusBadge,
            status === "deployed" && styles.deployed,
            status === "deploying" && styles.deploying,
            status === "error" && styles.errorBadge,
            status === "done" && styles.doneBadge,
            status === "executing" && styles.executingBadge,
          )}
          aria-label={`status ${status}`}
        />
      )}
      {status === "executing" && <span className={styles.shimmer} aria-hidden="true" />}
      {explainAdapter && (
        <button
          type="button"
          data-testid={`explain-icon-${data.name}`}
          aria-label={`Explain recipe ${data.name}`}
          onClick={onExplainIconClick}
          style={{
            position: "absolute",
            top: 4,
            right: 4,
            width: 18,
            height: 18,
            borderRadius: "var(--radius-sm, 4px)",
            border: "1px solid var(--border, #e0e0e0)",
            background: "var(--surface, #ffffff)",
            color: "var(--fg-muted, #5b6470)",
            cursor: "pointer",
            fontSize: "var(--text-2xs, 10px)",
            lineHeight: 1,
            padding: 0,
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            fontWeight: 700,
          }}
        >
          i
        </button>
      )}
      {explainAdapter &&
        explainAdapter.renderPopover({ open: explainOpen, close: closeExplain })}
      <Handle type="source" position={Position.Right} />
      {popoverOpen && (
        <div
          ref={popoverRef}
          id={popoverId}
          role="dialog"
          aria-label={`Confidence details for ${data.name}`}
          data-testid={`recipe-popover-${data.name}`}
          style={{
            position: "absolute",
            top: "100%",
            left: 0,
            marginTop: 6,
            background: "var(--surface-raised, #ffffff)",
            color: "var(--fg, #111111)",
            border: "1px solid var(--border, #e0e0e0)",
            borderRadius: "var(--radius-md, 6px)",
            padding: "0.5rem 0.6rem",
            boxShadow: "0 6px 18px rgba(0,0,0,0.18)",
            minWidth: 220,
            fontSize: "var(--text-xs, 12px)",
            zIndex: 100,
          }}
          // Trap focus by handling Tab to keep within the popover.
          onKeyDown={(e) => {
            if (e.key === "Escape") {
              e.preventDefault();
              setPopoverOpen(false);
              cardRef.current?.focus();
            }
          }}
        >
          <div
            data-testid={`recipe-popover-confidence-${data.name}`}
            style={{ fontWeight: 600, marginBottom: 4 }}
          >
            {confidencePct !== null
              ? `${band.toUpperCase()} confidence — ${confidencePct}%`
              : "Rule-based mapping"}
          </div>
          {data.reasoning && (
            <div
              data-testid={`recipe-popover-reasoning-${data.name}`}
              style={{
                color: "var(--fg-muted, #5b6470)",
                marginBottom: 6,
                lineHeight: 1.4,
              }}
            >
              {data.reasoning}
            </div>
          )}
          {data.sourceLines && (
            <button
              ref={sourceLinkRef}
              type="button"
              data-testid={`recipe-popover-source-link-${data.name}`}
              onClick={onSourceLinesPress}
              style={{
                background: "transparent",
                border: 0,
                padding: 0,
                color: "var(--accent, #0d9488)",
                cursor: onSourceLinesClick ? "pointer" : "default",
                textDecoration: "underline",
                font: "inherit",
              }}
            >
              Lines {data.sourceLines[0]}–{data.sourceLines[1]} of source ↗
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export const RecipeNode = memo(RecipeNodeImpl);
RecipeNode.displayName = "RecipeNode";

/** Helper used by `nodeTypes` map below to bind a fixed RecipeType. */
export function makeRecipeNodeForType(
  type: RecipeType,
): (props: NodeProps<RecipeNodeData>) => JSX.Element {
  const Bound = (props: NodeProps<RecipeNodeData>): JSX.Element => {
    const data: RecipeNodeData = { ...props.data, type };
    return <RecipeNode {...props} data={data} />;
  };
  Bound.displayName = `RecipeNode(${type})`;
  return Bound;
}

export { bandFor };
export type { ConfidenceBand };
