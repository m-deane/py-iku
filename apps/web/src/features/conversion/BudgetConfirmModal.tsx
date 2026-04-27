/**
 * BudgetConfirmModal
 *
 * Surfaced when the API rejects a conversion / chat call with HTTP 402
 * because the projected cost would breach the configured budget. The user
 * can confirm to retry with `?force=true` (bypassing the pre-call gate)
 * or cancel to abort.
 *
 * Visual rules — all colors come from ui-tokens.css. No inline hex.
 */
import { useEffect } from "react";

export interface BudgetConfirmModalProps {
  /** Projected cost in USD for the rejected call. */
  projectedCostUsd: number;
  /**
   * Remaining budget for today in USD. The "today" framing matches the
   * spec copy ("Today's budget remaining: $Y.YY"). The cost meter exposes
   * monthly_cap minus month_to_date — callers compute the daily figure
   * (or pass through the same value) per their own UX preference.
   */
  todayRemainingUsd: number;
  /** Confirm callback — caller retries the API call with `?force=true`. */
  onConfirm: () => void;
  /** Dismiss callback — caller closes the modal without retrying. */
  onCancel: () => void;
}

function formatCurrency(usd: number): string {
  // Locale-stable two-decimal output so tests don't drift across machines.
  const sign = usd < 0 ? "-" : "";
  const abs = Math.abs(usd);
  return `${sign}$${abs.toFixed(2)}`;
}

export function BudgetConfirmModal(
  props: BudgetConfirmModalProps,
): JSX.Element {
  const { projectedCostUsd, todayRemainingUsd, onConfirm, onCancel } = props;

  // Esc to close.
  useEffect(() => {
    const onKey = (e: KeyboardEvent): void => {
      if (e.key === "Escape") {
        e.preventDefault();
        onCancel();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onCancel]);

  return (
    <div
      role="presentation"
      data-testid="budget-confirm-backdrop"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onCancel();
      }}
      style={{
        position: "fixed",
        inset: 0,
        background: "var(--scrim, rgba(0, 0, 0, 0.45))",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="budget-confirm-title"
        data-testid="budget-confirm-modal"
        style={{
          width: "min(440px, 90vw)",
          padding: "1rem 1.25rem",
          borderRadius: "var(--radius-md, 8px)",
          background: "var(--surface, #fff)",
          color: "var(--fg, inherit)",
          border: "1px solid var(--border, #eaecf0)",
          display: "flex",
          flexDirection: "column",
          gap: "0.75rem",
        }}
      >
        <h2
          id="budget-confirm-title"
          style={{ margin: 0, fontSize: "var(--text-md, 15px)" }}
        >
          Confirm budget breach
        </h2>
        <p
          data-testid="budget-confirm-message"
          style={{
            margin: 0,
            fontSize: "var(--text-sm, 13px)",
            color: "var(--fg-muted, #5b6470)",
          }}
        >
          This call costs ~
          <strong data-testid="budget-confirm-cost">
            {formatCurrency(projectedCostUsd)}
          </strong>
          . Today's budget remaining:{" "}
          <strong data-testid="budget-confirm-remaining">
            {formatCurrency(todayRemainingUsd)}
          </strong>
          . Proceed anyway?
        </p>
        <div
          style={{
            display: "flex",
            gap: "0.5rem",
            justifyContent: "flex-end",
            marginTop: "0.25rem",
          }}
        >
          <button
            type="button"
            data-testid="budget-confirm-cancel"
            onClick={onCancel}
            style={{
              padding: "0.4rem 0.8rem",
              borderRadius: "var(--radius-sm, 4px)",
              border: "1px solid var(--border-strong, #d0d5dd)",
              background: "transparent",
              color: "inherit",
              cursor: "pointer",
              fontSize: "var(--text-sm, 13px)",
            }}
          >
            Cancel
          </button>
          <button
            type="button"
            data-testid="budget-confirm-confirm"
            onClick={onConfirm}
            style={{
              padding: "0.4rem 0.8rem",
              borderRadius: "var(--radius-sm, 4px)",
              border: "1px solid var(--accent, #0d9488)",
              background: "var(--accent, #0d9488)",
              color: "var(--accent-fg, #fff)",
              cursor: "pointer",
              fontSize: "var(--text-sm, 13px)",
              fontWeight: 600,
            }}
          >
            Proceed anyway
          </button>
        </div>
      </div>
    </div>
  );
}
