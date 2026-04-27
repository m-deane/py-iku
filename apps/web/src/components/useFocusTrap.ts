import { useEffect, useRef, type RefObject } from "react";

/**
 * useFocusTrap — keyboard focus trap for modal-like surfaces.
 *
 * Sprint 2C polish: SettingsDrawer (and any future modal/drawer) needs to
 * confine Tab / Shift+Tab focus inside the dialog while open, focus the first
 * focusable child on mount, and restore focus to the previously-focused
 * element (the trigger) when the trap deactivates.
 *
 * No external dependency: a small sentinel + keydown approach. Tested via the
 * SettingsDrawer test (`tab cycles inside the drawer`).
 *
 * Usage:
 *   const ref = useFocusTrap<HTMLDivElement>(open);
 *   return open ? <aside ref={ref}>…</aside> : null;
 *
 * Notes:
 * - We query focusable elements every keydown rather than once on mount —
 *   form fields appear/disappear (e.g. error messages with focusable links).
 * - Esc closes via the consumer's own onClose: this hook only handles Tab.
 */

const FOCUSABLE_SELECTOR = [
  "a[href]",
  "area[href]",
  "input:not([disabled]):not([type='hidden'])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  'button:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
  "audio[controls]",
  "video[controls]",
  "iframe",
  "[contenteditable]:not([contenteditable='false'])",
].join(",");

export function useFocusTrap<T extends HTMLElement>(
  active: boolean,
): RefObject<T> {
  const containerRef = useRef<T>(null);
  const previouslyFocused = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!active) return;
    const container = containerRef.current;
    if (!container) return;

    // Stash the element that had focus before the trap activated so we can
    // restore it on deactivation. Tests assert this restores to the trigger
    // (the gear icon for SettingsDrawer).
    previouslyFocused.current =
      typeof document !== "undefined"
        ? (document.activeElement as HTMLElement | null)
        : null;

    // Focus the first focusable child. If none are focusable, fall back to
    // the container itself (with tabindex=-1 set inline by the consumer).
    const focusables = container.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR);
    const first = focusables[0];
    if (first) {
      // requestAnimationFrame so the browser has painted the modal first; jsdom
      // ignores rAF timing but synchronous focus is also fine there.
      first.focus();
    } else if (typeof container.focus === "function") {
      container.focus();
    }

    const onKeyDown = (e: KeyboardEvent): void => {
      if (e.key !== "Tab") return;
      const list = Array.from(
        container.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR),
      ).filter((el) => !el.hasAttribute("data-focus-trap-sentinel"));
      if (list.length === 0) {
        e.preventDefault();
        container.focus?.();
        return;
      }
      const firstEl = list[0];
      const lastEl = list[list.length - 1];
      const active = document.activeElement as HTMLElement | null;

      // If focus has somehow escaped the container, pull it back to the first
      // element (defensive: external scripts can steal focus).
      if (!active || !container.contains(active)) {
        e.preventDefault();
        firstEl.focus();
        return;
      }

      if (e.shiftKey) {
        if (active === firstEl) {
          e.preventDefault();
          lastEl.focus();
        }
      } else {
        if (active === lastEl) {
          e.preventDefault();
          firstEl.focus();
        }
      }
    };

    document.addEventListener("keydown", onKeyDown, true);
    return (): void => {
      document.removeEventListener("keydown", onKeyDown, true);
      // Restore focus to the trigger on deactivation. Skipped if the
      // previously-focused node has been removed from the DOM.
      const prev = previouslyFocused.current;
      if (prev && typeof prev.focus === "function" && document.contains(prev)) {
        prev.focus();
      }
      previouslyFocused.current = null;
    };
  }, [active]);

  return containerRef;
}
