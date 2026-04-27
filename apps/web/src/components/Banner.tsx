import type { ReactNode } from "react";

/**
 * Banner — inline alert for surfaceable error / warning / info messages.
 *
 * Sprint 2C polish: replaces console-only failures and bare red sentences
 * with a real recovery affordance. Colors come from the new design tokens
 * (`--danger-bg`, `--warn-bg`, `--info-bg`, etc.) added in Sprint 1A.
 *
 * Variants:
 *   - "danger" — convert failure (4xx/5xx, network, WS close)
 *   - "warn"   — soft errors / deprecations
 *   - "info"   — informational, low-stakes notifications
 *   - "success"— positive confirmation (rarely used inline)
 *
 * Always renders with `role="alert"` for danger/warn so AT users hear it.
 */

export type BannerVariant = "danger" | "warn" | "info" | "success";

export interface BannerProps {
  variant?: BannerVariant;
  /** Heading line — short, descriptive. */
  title: string;
  /** Optional secondary line of detail. */
  detail?: ReactNode;
  /** When provided, renders a Retry button on the right side. */
  onRetry?: () => void;
  /** Custom retry button label (defaults to "Retry"). */
  retryLabel?: string;
  /** When provided, renders a Dismiss button (×) on the right side. */
  onDismiss?: () => void;
  /** Test seam for assertions. */
  "data-testid"?: string;
}

const VARIANT_TOKENS: Record<BannerVariant, { bg: string; fg: string; border: string }> = {
  danger: {
    bg: "var(--danger-bg, #fee4e2)",
    fg: "var(--danger-fg, #b42318)",
    border: "var(--danger-border, #fecdca)",
  },
  warn: {
    bg: "var(--warn-bg, #fef3c7)",
    fg: "var(--warn-fg, #b54708)",
    border: "var(--warn-border, #fcd34d)",
  },
  info: {
    bg: "var(--info-bg, #eff6ff)",
    fg: "var(--info-fg, #1d4ed8)",
    border: "var(--info-border, #bfdbfe)",
  },
  success: {
    bg: "var(--success-bg, #ecfdf3)",
    fg: "var(--success-fg, #027a48)",
    border: "var(--success-border, #abefc6)",
  },
};

export function Banner(props: BannerProps): JSX.Element {
  const variant = props.variant ?? "danger";
  const tokens = VARIANT_TOKENS[variant];
  const liveRole = variant === "danger" || variant === "warn" ? "alert" : "status";

  return (
    <div
      role={liveRole}
      data-testid={props["data-testid"] ?? "banner"}
      data-variant={variant}
      style={{
        display: "flex",
        alignItems: "flex-start",
        gap: "0.75rem",
        padding: "0.75rem 1rem",
        borderRadius: "var(--radius-md, 8px)",
        background: tokens.bg,
        color: tokens.fg,
        border: `1px solid ${tokens.border}`,
        fontSize: "var(--text-sm, 14px)",
        lineHeight: "var(--lh-snug, 1.35)",
      }}
    >
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            fontWeight: "var(--font-weight-semibold, 600)",
            marginBottom: props.detail ? 2 : 0,
          }}
        >
          {props.title}
        </div>
        {props.detail ? (
          <div style={{ fontSize: "var(--text-xs, 12px)", opacity: 0.92 }}>
            {props.detail}
          </div>
        ) : null}
      </div>
      {props.onRetry ? (
        <button
          type="button"
          onClick={props.onRetry}
          data-testid={`${props["data-testid"] ?? "banner"}-retry`}
          style={{
            padding: "0.4rem 0.8rem",
            borderRadius: "var(--radius-sm, 4px)",
            border: 0,
            background: "var(--accent, #0d9488)",
            color: "var(--accent-fg, #ffffff)",
            cursor: "pointer",
            fontSize: "var(--text-xs, 12px)",
            fontWeight: "var(--font-weight-semibold, 600)",
            whiteSpace: "nowrap",
          }}
        >
          {props.retryLabel ?? "Retry"}
        </button>
      ) : null}
      {props.onDismiss ? (
        <button
          type="button"
          onClick={props.onDismiss}
          aria-label="Dismiss"
          data-testid={`${props["data-testid"] ?? "banner"}-dismiss`}
          style={{
            padding: "0.2rem 0.5rem",
            borderRadius: "var(--radius-sm, 4px)",
            border: `1px solid ${tokens.border}`,
            background: "transparent",
            color: "inherit",
            cursor: "pointer",
            fontSize: "var(--text-sm, 14px)",
            lineHeight: 1,
          }}
        >
          ×
        </button>
      ) : null}
    </div>
  );
}
