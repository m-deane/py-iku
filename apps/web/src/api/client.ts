import { toast } from "sonner";
import { useSettingsStore } from "../state/settingsStore";
import type {
  ConvertRequest as GeneratedConvertRequest,
  ConvertResponse as GeneratedConvertResponse,
  HealthResponse as GeneratedHealthResponse,
  ProcessorCatalogEntry as GeneratedProcessorCatalogEntry,
  RecipeCatalogEntry as GeneratedRecipeCatalogEntry,
} from "@py-iku-studio/types";

/** RFC 7807 problem+json shape returned by the API. */
export interface ApiProblem {
  type: string;
  title: string;
  status: number;
  detail?: string;
  instance?: string;
  [extension: string]: unknown;
}

export class ApiError extends Error {
  readonly type: string;
  readonly title: string;
  readonly status: number;
  readonly detail?: string;
  readonly requestId?: string;
  /**
   * Full problem-detail body. Some endpoints attach structured payloads
   * under `detail`; callers that need those fields read them off `data`.
   */
  readonly data: Record<string, unknown>;

  constructor(problem: ApiProblem, requestId?: string) {
    const flat = typeof problem.detail === "string" ? problem.detail : problem.title;
    super(flat);
    this.name = "ApiError";
    this.type = problem.type;
    this.title = problem.title;
    this.status = problem.status;
    this.detail = typeof problem.detail === "string" ? problem.detail : undefined;
    this.requestId = requestId;
    this.data = { ...problem } as Record<string, unknown>;
  }
}

export interface HealthResponse {
  status: string;
  version: string;
  py_iku_version: string;
}

export interface ClientOptions {
  baseUrl?: string;
  authToken?: string | null;
  /** Overrides global `fetch` (used in tests). */
  fetchImpl?: typeof fetch;
}

function uuid(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  // RFC4122-ish fallback for very old environments
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

function getBaseUrl(opts: ClientOptions): string {
  if (opts.baseUrl) return opts.baseUrl;
  try {
    return useSettingsStore.getState().apiBaseUrl;
  } catch {
    return "http://localhost:8000";
  }
}

async function request<T>(
  path: string,
  init: RequestInit,
  opts: ClientOptions = {},
): Promise<T> {
  const baseUrl = getBaseUrl(opts).replace(/\/$/, "");
  const url = `${baseUrl}${path.startsWith("/") ? path : `/${path}`}`;
  const requestId = uuid();
  const fetchImpl = opts.fetchImpl ?? fetch;

  const headers = new Headers(init.headers);
  headers.set("X-Request-ID", requestId);
  if (!headers.has("Accept")) headers.set("Accept", "application/json");
  if (opts.authToken) headers.set("Authorization", `Bearer ${opts.authToken}`);
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  let response: Response;
  try {
    response = await fetchImpl(url, { ...init, headers });
  } catch (cause) {
    const message = cause instanceof Error ? cause.message : String(cause);
    throw new ApiError(
      {
        type: "about:blank",
        title: "Network error",
        status: 0,
        detail: message,
      },
      requestId,
    );
  }

  if (!response.ok) {
    let problem: ApiProblem;
    const contentType = response.headers.get("content-type") ?? "";
    if (contentType.includes("application/problem+json") || contentType.includes("application/json")) {
      try {
        const data = (await response.json()) as Partial<ApiProblem>;
        problem = {
          type: data.type ?? "about:blank",
          title: data.title ?? response.statusText,
          status: data.status ?? response.status,
          detail: data.detail,
          ...data,
        };
      } catch {
        problem = {
          type: "about:blank",
          title: response.statusText || "Request failed",
          status: response.status,
        };
      }
    } else {
      problem = {
        type: "about:blank",
        title: response.statusText || "Request failed",
        status: response.status,
        detail: await response.text().catch(() => undefined),
      };
    }

    if (response.status === 401) {
      tryToast("error", "Unauthorized", problem.detail ?? "Sign in or check your API key alias.");
    } else if (response.status === 429) {
      tryToast(
        "warning",
        "Rate limited",
        problem.detail ?? "Slow down — too many requests.",
      );
    }

    throw new ApiError(problem, requestId);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  // assume JSON response for typed methods
  return (await response.json()) as T;
}

function tryToast(level: "error" | "warning", title: string, description: string): void {
  try {
    if (level === "error") {
      toast.error(title, { description });
    } else {
      toast.warning(title, { description });
    }
  } catch {
    // toast harness not mounted (e.g. tests) — swallow.
  }
}

// ---------------------------------------------------------------------------
// Types sourced from @py-iku-studio/types codegen (GeneratedXxx aliases above).
// HealthResponse and RecipeCatalogEntry are swapped to generated types.
// ---------------------------------------------------------------------------

export type ConversionMode = "rule" | "llm";

export interface ConvertOptions {
  provider?: "anthropic" | "openai";
  model?: string;
  /** Free-form passthrough — server ignores unknown keys. */
  [key: string]: unknown;
}

export interface ConvertRequest {
  code: string;
  mode: ConversionMode;
  options?: ConvertOptions;
}

export interface FlowScore {
  complexity: number;
  recipe_count: number;
  dataset_count: number;
  cost_estimate?: number;
  breakdown?: Array<{ key: string; value: number }>;
}

export interface ConvertResponse {
  /** DataikuFlow payload (relaxed to Record for compat; can tighten later). */
  flow: Record<string, unknown>;
  score: FlowScore;
  warnings: string[];
}

/** RecipeCatalogEntry — now sourced from @py-iku-studio/types codegen. */
export type RecipeCatalogEntry = GeneratedRecipeCatalogEntry;

/** ProcessorCatalogEntry — sourced from @py-iku-studio/types codegen. */
export type ProcessorCatalogEntry = GeneratedProcessorCatalogEntry;

// Re-export generated types so downstream can import from one place.
export type {
  GeneratedConvertRequest,
  GeneratedConvertResponse,
  GeneratedHealthResponse,
  GeneratedProcessorCatalogEntry,
  GeneratedRecipeCatalogEntry,
};

export interface ScoreResponse {
  recipe_count: number;
  processor_count: number;
  max_depth: number;
  fan_out_max: number;
  complexity: number;
  cost_estimate?: number | null;
}

export interface ListProcessorsOptions extends ClientOptions {
  q?: string;
  category?: string;
}

/**
 * Server-side LLM provider/credential status. The key is **never** echoed —
 * the boolean `has_key` and `source` are the only signals the client gets.
 */
export interface LlmStatusResponse {
  provider: "anthropic" | "openai";
  model?: string | null;
  has_key: boolean;
  source: "file" | "env" | "none";
  supported_providers?: string[];
}

export interface SaveLlmKeyRequest {
  provider: "anthropic" | "openai";
  key: string;
}

export const client = {
  health(opts?: ClientOptions): Promise<HealthResponse> {
    return request<HealthResponse>("/health", { method: "GET" }, opts);
  },
  convert(
    req: ConvertRequest,
    opts?: ClientOptions & { force?: boolean },
  ): Promise<ConvertResponse> {
    const path = opts?.force ? "/convert?force=true" : "/convert";
    return request<ConvertResponse>(
      path,
      { method: "POST", body: JSON.stringify(req) },
      opts,
    );
  },
  listRecipes(opts?: ClientOptions): Promise<RecipeCatalogEntry[]> {
    return request<RecipeCatalogEntry[]>("/catalog/recipes", { method: "GET" }, opts);
  },
  /** @deprecated Use listRecipes instead. */
  getRecipes(opts?: ClientOptions): Promise<RecipeCatalogEntry[]> {
    return this.listRecipes(opts);
  },
  listProcessors(opts?: ListProcessorsOptions): Promise<ProcessorCatalogEntry[]> {
    const params = new URLSearchParams();
    if (opts?.q) params.set("q", opts.q);
    if (opts?.category) params.set("category", opts.category);
    const qs = params.toString();
    const path = qs ? `/catalog/processors?${qs}` : "/catalog/processors";
    return request<ProcessorCatalogEntry[]>(path, { method: "GET" }, opts);
  },
  getProcessor(type: string, opts?: ClientOptions): Promise<ProcessorCatalogEntry> {
    return request<ProcessorCatalogEntry>(
      `/catalog/processors/${encodeURIComponent(type)}`,
      { method: "GET" },
      opts,
    );
  },
  score(flow: Record<string, unknown>, opts?: ClientOptions): Promise<ScoreResponse> {
    return request<ScoreResponse>(
      "/score",
      { method: "POST", body: JSON.stringify(flow) },
      opts,
    );
  },
  // ----- LLM credential management ----------------------------------------
  getLlmStatus(opts?: ClientOptions): Promise<LlmStatusResponse> {
    return request<LlmStatusResponse>(
      "/api/settings/llm",
      { method: "GET" },
      opts,
    );
  },
  saveLlmKey(
    payload: SaveLlmKeyRequest,
    opts?: ClientOptions,
  ): Promise<LlmStatusResponse> {
    return request<LlmStatusResponse>(
      "/api/settings/llm/key",
      { method: "POST", body: JSON.stringify(payload) },
      opts,
    );
  },
  deleteLlmKey(
    provider: "anthropic" | "openai" = "anthropic",
    opts?: ClientOptions,
  ): Promise<{ removed: boolean }> {
    const qs = new URLSearchParams({ provider }).toString();
    return request<{ removed: boolean }>(
      `/api/settings/llm/key?${qs}`,
      { method: "DELETE" },
      opts,
    );
  },
};

export type Client = typeof client;
