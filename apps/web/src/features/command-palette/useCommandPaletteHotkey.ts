import { useEffect } from "react";
import { useCommandPaletteStore } from "../../store/commandPalette";

/**
 * Detect whether the active element is a text input where Cmd+K should NOT
 * be intercepted (e.g. inside Monaco). We DO intercept inside <input>/<textarea>
 * because Cmd+K is the canonical "open palette" gesture and overrides editing.
 *
 * Returning `true` means: still allow the toggle. The exception is a
 * `data-disable-command-palette` attribute on the active element, which
 * editor wrappers can set when they need exclusive Cmd+K handling.
 */
function shouldHandle(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return true;
  if (target.closest("[data-disable-command-palette]")) return false;
  return true;
}

/**
 * Wires the global Cmd+K (Mac) / Ctrl+K (other) shortcut to the command
 * palette store. Mounts a single `keydown` listener on `document`.
 *
 * Esc-to-close is handled inside the palette itself (focus-trap aware)
 * so that pressing Esc anywhere else on the page doesn't accidentally
 * close other modals.
 */
export function useCommandPaletteHotkey(): void {
  const toggle = useCommandPaletteStore((s) => s.toggle);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent): void => {
      // Cmd+K on Mac, Ctrl+K elsewhere. Match either modifier so a Mac user
      // hitting Ctrl+K (e.g. via an external keyboard) still works.
      const isModifier = e.metaKey || e.ctrlKey;
      if (!isModifier) return;
      if (e.key !== "k" && e.key !== "K") return;
      if (!shouldHandle(e.target)) return;

      // Prevent Chrome/Firefox's default "focus address bar" behaviour.
      e.preventDefault();
      e.stopPropagation();
      toggle();
    };

    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [toggle]);
}
