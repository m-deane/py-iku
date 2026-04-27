/**
 * URL-as-state codec (Sprint 4 — power user).
 *
 * Encodes a slice of app state into a URL-safe string so a colleague can paste
 * the link and land in the exact same view. The state is JSON-serialised then
 * base64url-encoded, and lives in the URL **hash** rather than a query param:
 *
 *   - hash never hits the server, so a long encoded blob doesn't show up in
 *     access logs.
 *   - hash sidesteps the Vite-managed search params and the React Router
 *     query parser entirely.
 *   - 32KB is the practical Chrome URL ceiling — we enforce 32_000 bytes as
 *     `MAX_URL_BYTES` and surface a `tooLarge` signal so the caller can fall
 *     back to the existing server-side share token at /share/:token.
 *
 * Hash format: `#state=<base64url-json>`. We pick `state` rather than just `=`
 * to leave room for additional hash params later (e.g. `#state=...&panel=...`)
 * without a breaking change.
 */
import type { WorkspaceTab } from "./tabs";

export const SHARE_HASH_KEY = "state";
/** 32KB practical ceiling for Chrome URLs. */
export const MAX_URL_BYTES = 32_000;

/** App-level state we want round-trippable through the URL. */
export interface SharedAppState {
  /** Schema version — bump on breaking changes so we can migrate. */
  v: 1;
  /** Tabs payload (subset of WorkspaceTab — we drop transient `updatedAt`). */
  tabs: SharedTab[];
  /** Active tab id. May be null if `tabs` is empty. */
  activeTabId: string | null;
  /** Theme preference at share time ("light" | "dark" | null = system). */
  theme: "light" | "dark" | null;
  /** Open/closed state of named panels (replay timeline, validation, etc.). */
  panels: Record<string, boolean>;
}

export interface SharedTab {
  id: string;
  title: string;
  code: string;
  lastFlow: Record<string, unknown> | null;
  mode: "rule" | "llm";
  provider: "anthropic" | "openai";
  model?: string;
  scrollTop: number;
}

/**
 * Reduce a `WorkspaceTab` to its serialisable shape — drops `updatedAt` and
 * any future runtime-only fields.
 */
export function tabToShared(tab: WorkspaceTab): SharedTab {
  return {
    id: tab.id,
    title: tab.title,
    code: tab.code,
    lastFlow: tab.lastFlow,
    mode: tab.mode,
    provider: tab.provider,
    model: tab.model,
    scrollTop: tab.scrollTop,
  };
}

/**
 * Inflate a `SharedTab` back into a `WorkspaceTab`. `updatedAt` is reset to
 * "now" since the tab was just rehydrated.
 */
export function sharedToTab(shared: SharedTab): WorkspaceTab {
  return {
    id: shared.id,
    title: shared.title,
    code: shared.code,
    lastFlow: shared.lastFlow,
    mode: shared.mode,
    provider: shared.provider,
    model: shared.model,
    scrollTop: shared.scrollTop,
    updatedAt: Date.now(),
  };
}

/** base64url — RFC 4648 §5. */
function base64UrlEncode(input: string): string {
  // btoa doesn't handle multi-byte chars; encode the UTF-8 bytes first.
  const bytes = new TextEncoder().encode(input);
  let bin = "";
  for (let i = 0; i < bytes.length; i += 1) {
    bin += String.fromCharCode(bytes[i]);
  }
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const b64 = (typeof btoa !== "undefined" ? btoa : (globalThis as any).btoa)(bin);
  return b64.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function base64UrlDecode(input: string): string {
  const padded =
    input.replace(/-/g, "+").replace(/_/g, "/") +
    "=".repeat((4 - (input.length % 4)) % 4);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const bin = (typeof atob !== "undefined" ? atob : (globalThis as any).atob)(padded);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i += 1) {
    bytes[i] = bin.charCodeAt(i);
  }
  return new TextDecoder().decode(bytes);
}

export interface EncodeShareUrlResult {
  /** Full URL with the hash applied. Empty when `tooLarge` is true. */
  url: string;
  /** Encoded state string (without the `state=` prefix). */
  encoded: string;
  /** Byte length of the produced URL (for budget checks/UX hints). */
  bytes: number;
  /**
   * True when the encoded URL would breach `MAX_URL_BYTES`. The caller should
   * fall back to the server-side share token in that case.
   */
  tooLarge: boolean;
}

/**
 * Build a share URL by pasting the encoded state into the hash of the current
 * `baseUrl`. The base URL is stripped of any pre-existing hash so we never
 * concatenate two `#`s.
 */
export function encodeShareUrl(
  state: SharedAppState,
  baseUrl: string,
): EncodeShareUrlResult {
  const json = JSON.stringify(state);
  const encoded = base64UrlEncode(json);
  // Strip an existing hash from baseUrl if present.
  const hashIdx = baseUrl.indexOf("#");
  const cleanBase = hashIdx >= 0 ? baseUrl.slice(0, hashIdx) : baseUrl;
  const url = `${cleanBase}#${SHARE_HASH_KEY}=${encoded}`;
  const bytes = url.length;
  return {
    url,
    encoded,
    bytes,
    tooLarge: bytes > MAX_URL_BYTES,
  };
}

/**
 * Pull encoded state out of a URL hash, returning the parsed `SharedAppState`
 * or null if the hash isn't present / can't be parsed. Never throws — bad
 * input simply yields null so the caller can fall through to defaults.
 */
export function decodeShareUrl(href: string): SharedAppState | null {
  try {
    const hashIdx = href.indexOf("#");
    if (hashIdx < 0) return null;
    const hash = href.slice(hashIdx + 1);
    if (!hash) return null;
    const params = new URLSearchParams(hash);
    const encoded = params.get(SHARE_HASH_KEY);
    if (!encoded) return null;
    const json = base64UrlDecode(encoded);
    const parsed = JSON.parse(json) as SharedAppState;
    if (!parsed || typeof parsed !== "object") return null;
    if (parsed.v !== 1) return null;
    if (!Array.isArray(parsed.tabs)) return null;
    return parsed;
  } catch {
    return null;
  }
}
