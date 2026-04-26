import { toast } from "sonner";
import { useSettingsStore } from "../state/settingsStore";

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

  constructor(problem: ApiProblem, requestId?: string) {
    super(problem.detail ?? problem.title);
    this.name = "ApiError";
    this.type = problem.type;
    this.title = problem.title;
    this.status = problem.status;
    this.detail = problem.detail;
    this.requestId = requestId;
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

export const client = {
  health(opts?: ClientOptions): Promise<HealthResponse> {
    return request<HealthResponse>("/health", { method: "GET" }, opts);
  },
  /** Generic escape hatch for not-yet-typed endpoints (M5+ will expand). */
  request,
};

export type Client = typeof client;
