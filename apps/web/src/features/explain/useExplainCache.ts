import { useCallback, useState } from "react";
import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";
import {
  client as defaultClient,
  type ExplainRecipeRequest,
  type ExplainRecipeResponse,
} from "../../api/client";

/**
 * Client-side mirror of the server-side explain-cache. The server cache lives
 * in `apps/api/.py-iku-flows/explain-cache.jsonl` and survives restarts; this
 * client-side cache lets the popover hydrate instantly when a recipe was
 * already explained earlier in the session — the network call is skipped
 * outright if we have a fresh entry.
 *
 * Cache key matches the server: `<RECIPE_TYPE>:<sha256-of-normalised-settings>`.
 * That means the server returns ``cache_key`` and we use it as our local key,
 * so a server cache hit and a client cache hit are interchangeable.
 */
interface CacheEntry {
  value: ExplainRecipeResponse;
  ts: number;
}

interface ExplainCacheState {
  byKey: Record<string, CacheEntry>;
  put: (key: string, value: ExplainRecipeResponse) => void;
  clear: () => void;
}

const ONE_DAY_MS = 24 * 60 * 60 * 1000;

export const useExplainCacheStore = create<ExplainCacheState>()(
  persist(
    (set) => ({
      byKey: {},
      put: (key, value) =>
        set((s) => ({
          byKey: { ...s.byKey, [key]: { value, ts: Date.now() } },
        })),
      clear: () => set({ byKey: {} }),
    }),
    {
      name: "py-iku-studio-explain-cache",
      version: 1,
      storage: createJSONStorage(() => localStorage),
    },
  ),
);

/**
 * Stable client-side hash mirroring `services/explain.recipe_cache_key`. Used
 * for the *pre-call* lookup so we can short-circuit before hitting the wire.
 * Drops the same noise fields as the server (name, confidence, reasoning,
 * source_lines, IO names) so a rename or confidence wobble doesn't bust it.
 */
const DROPPED = new Set([
  "name",
  "confidence",
  "reasoning",
  "source_lines",
  "inputs",
  "outputs",
]);

function normalise(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(normalise);
  if (value && typeof value === "object") {
    const obj = value as Record<string, unknown>;
    const sorted = Object.keys(obj).sort();
    const out: Record<string, unknown> = {};
    for (const k of sorted) {
      if (DROPPED.has(k)) continue;
      out[k] = normalise(obj[k]);
    }
    return out;
  }
  return value;
}

/** djb2 string hash — small, fast, identical across runs in a single tab. */
function hash(str: string): string {
  let h = 5381;
  for (let i = 0; i < str.length; i += 1) {
    h = ((h << 5) + h + str.charCodeAt(i)) | 0;
  }
  return (h >>> 0).toString(36);
}

export function clientCacheKey(recipe: Record<string, unknown>): string {
  const recipeType = String(recipe.type ?? "UNKNOWN").toUpperCase();
  const blob = JSON.stringify(normalise(recipe));
  return `${recipeType}:${hash(blob)}`;
}

export type ExplainStatus = "idle" | "loading" | "ready" | "error";

export interface UseExplainOptions {
  /** Test seam — swap in a stub `client.explainRecipe`. */
  clientImpl?: { explainRecipe: typeof defaultClient.explainRecipe };
  /** Disable the localStorage layer (tests). */
  disableCache?: boolean;
}

export interface UseExplainResult {
  status: ExplainStatus;
  data: ExplainRecipeResponse | null;
  error: { title: string; detail?: string } | null;
  /** Was the most recent response served from the client-side cache? */
  clientCacheHit: boolean;
  request: (req: ExplainRecipeRequest) => Promise<void>;
  reset: () => void;
}

/**
 * Hook that fetches an explain-recipe response with two layers of caching:
 *
 * 1. ``useExplainCacheStore`` — a Zustand store persisted to localStorage,
 *    fast-path that skips the network entirely on repeat hovers.
 * 2. The server's on-disk cache — surfaced via the response's ``cache_hit``
 *    flag so the popover can hint at zero-cost.
 */
export function useExplainRecipe(
  options: UseExplainOptions = {},
): UseExplainResult {
  const client = options.clientImpl ?? { explainRecipe: defaultClient.explainRecipe };
  const byKey = useExplainCacheStore((s) => s.byKey);
  const put = useExplainCacheStore((s) => s.put);

  const [status, setStatus] = useState<ExplainStatus>("idle");
  const [data, setData] = useState<ExplainRecipeResponse | null>(null);
  const [error, setError] = useState<{ title: string; detail?: string } | null>(null);
  const [clientCacheHit, setClientCacheHit] = useState(false);

  const request = useCallback(
    async (req: ExplainRecipeRequest): Promise<void> => {
      setError(null);
      const key = clientCacheKey(req.recipe);
      if (!options.disableCache) {
        const entry = byKey[key];
        if (entry && Date.now() - entry.ts < ONE_DAY_MS) {
          setData(entry.value);
          setClientCacheHit(true);
          setStatus("ready");
          return;
        }
      }

      setStatus("loading");
      setClientCacheHit(false);
      try {
        const resp = await client.explainRecipe(req);
        setData(resp);
        setStatus("ready");
        if (!options.disableCache) {
          // Store under the client-computed key so subsequent lookups (which
          // use the same djb2 hash) hit reliably. We also mirror under the
          // server-returned cache_key when present, so a future feature that
          // reads the server's cache key directly stays consistent.
          put(key, resp);
          if (resp.cache_key && resp.cache_key !== key) {
            put(resp.cache_key, resp);
          }
        }
      } catch (e) {
        const err = e as { title?: string; detail?: string; message?: string };
        setError({
          title: err.title ?? "Explain failed",
          detail: err.detail ?? err.message,
        });
        setStatus("error");
      }
    },
    [byKey, put, client, options.disableCache],
  );

  const reset = useCallback(() => {
    setStatus("idle");
    setData(null);
    setError(null);
    setClientCacheHit(false);
  }, []);

  return { status, data, error, clientCacheHit, request, reset };
}
