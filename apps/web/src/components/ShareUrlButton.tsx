import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { useTabsStore } from "../store/tabs";
import { useSettingsStore } from "../state/settingsStore";
import {
  encodeShareUrl,
  decodeShareUrl,
  sharedToTab,
  tabToShared,
  SHARE_HASH_KEY,
  type SharedAppState,
} from "../store/shareState";

/**
 * "Copy share URL" button (Sprint 4 — power user feature 3).
 *
 * Sits next to the gear icon in the AppLayout header. Encodes the current
 * tabs + theme + a few panel flags into the URL hash, copies the resulting
 * URL to the clipboard, and toasts the result. If the encoded URL exceeds
 * the 32KB Chrome ceiling, we fall through to a friendly hint pointing the
 * user at the existing /share/:token server-side share flow.
 */
export interface ShareUrlButtonProps {
  /** Test seam — override clipboard write. */
  writeClipboard?: (text: string) => Promise<void>;
  /** Test seam — override `window.location.href`. */
  baseUrl?: string;
}

export function ShareUrlButton(props: ShareUrlButtonProps): JSX.Element {
  const tabs = useTabsStore((s) => s.tabs);
  const activeTabId = useTabsStore((s) => s.activeTabId);
  const theme = useSettingsStore((s) => s.theme);

  const onCopy = useCallback(async () => {
    const state: SharedAppState = {
      v: 1,
      tabs: tabs.map(tabToShared),
      activeTabId,
      theme,
      panels: {},
    };
    const baseUrl =
      props.baseUrl ??
      (typeof window !== "undefined" ? window.location.href : "");
    const encoded = encodeShareUrl(state, baseUrl);
    if (encoded.tooLarge) {
      toast.error("Share URL exceeds 32KB", {
        description:
          "Your workspace is too large for a URL share. Use the per-flow share button on the convert panel instead — it stores the flow server-side and gives you a /share/:token link.",
      });
      return;
    }
    try {
      const writer =
        props.writeClipboard ??
        (typeof navigator !== "undefined" && navigator.clipboard
          ? (txt: string) => navigator.clipboard.writeText(txt)
          : null);
      if (writer) {
        await writer(encoded.url);
        toast.success("Share URL copied", {
          description: `${encoded.bytes.toLocaleString()} bytes`,
        });
      } else {
        toast.message("Share URL ready", { description: encoded.url });
      }
    } catch (err) {
      toast.error("Could not copy share URL", {
        description: err instanceof Error ? err.message : String(err),
      });
    }
  }, [tabs, activeTabId, theme, props.writeClipboard, props.baseUrl]);

  return (
    <button
      type="button"
      data-testid="share-url-button"
      onClick={onCopy}
      aria-label="Copy share URL"
      title="Copy URL with full workspace state"
      style={{
        background: "transparent",
        border: 0,
        color: "var(--fg-muted, #5b6470)",
        cursor: "pointer",
        fontSize: "var(--text-base, 16px)",
        padding: "var(--space-1, 4px) var(--space-2, 8px)",
        borderRadius: "var(--radius-sm, 4px)",
      }}
    >
      ↗
    </button>
  );
}

/**
 * Boot-time hook — checks the URL hash for an encoded `?state=` payload and
 * hydrates the tabs + theme stores from it. Runs once on mount and clears
 * the hash so subsequent reloads don't keep replaying the same state.
 */
export function useShareUrlBoot(enabled: boolean = true): void {
  const hydrate = useTabsStore((s) => s.hydrateFromState);
  const setTheme = useSettingsStore((s) => s.setTheme);

  useEffect(() => {
    if (!enabled) return;
    if (typeof window === "undefined") return;
    const decoded = decodeShareUrl(window.location.href);
    if (!decoded) return;
    if (Array.isArray(decoded.tabs) && decoded.tabs.length > 0) {
      hydrate(decoded.tabs.map(sharedToTab), decoded.activeTabId);
    }
    if (decoded.theme === "light" || decoded.theme === "dark") {
      setTheme(decoded.theme);
    }
    // Clear the hash so reloading doesn't keep restoring (otherwise the user
    // can't escape the shared state). We preserve the rest of the URL.
    try {
      const url = new URL(window.location.href);
      // Strip our key but leave any others.
      const params = new URLSearchParams(url.hash.replace(/^#/, ""));
      params.delete(SHARE_HASH_KEY);
      const remaining = params.toString();
      url.hash = remaining ? `#${remaining}` : "";
      window.history.replaceState({}, document.title, url.toString());
    } catch {
      /* ignore — best effort */
    }
  }, [enabled, hydrate, setTheme]);
}

/**
 * Tiny hook helper used by the command palette: returns a function that
 * encodes-and-copies the share URL. Mirrors the button's onClick.
 */
export function useCopyShareUrl(): () => Promise<void> {
  const tabs = useTabsStore((s) => s.tabs);
  const activeTabId = useTabsStore((s) => s.activeTabId);
  const theme = useSettingsStore((s) => s.theme);
  const [, force] = useState(0);
  void force;
  return useCallback(async () => {
    const state: SharedAppState = {
      v: 1,
      tabs: tabs.map(tabToShared),
      activeTabId,
      theme,
      panels: {},
    };
    const baseUrl = typeof window !== "undefined" ? window.location.href : "";
    const encoded = encodeShareUrl(state, baseUrl);
    if (encoded.tooLarge) {
      toast.error("Share URL exceeds 32KB", {
        description: "Use the per-flow share button instead.",
      });
      return;
    }
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard) {
        await navigator.clipboard.writeText(encoded.url);
      }
      toast.success("Share URL copied");
    } catch (err) {
      toast.error("Could not copy share URL", {
        description: err instanceof Error ? err.message : String(err),
      });
    }
  }, [tabs, activeTabId, theme]);
}
