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

// ---------------------------------------------------------------------------
// Types sourced from @py-iku-studio/types codegen (GeneratedXxx aliases above).
// HealthResponse and RecipeCatalogEntry are swapped to generated types.
// ConvertRequest / ConvertResponse keep local shapes for call-signature stability
// (the generated ConvertResponse.flow is DataikuFlowModel; M5 will complete the swap).
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
  /** DataikuFlow payload (relaxed to Record for M4 compatibility; M5 tightens to DataikuFlow). */
  flow: Record<string, unknown>;
  score: FlowScore;
  warnings: string[];
}

/** RecipeCatalogEntry — now sourced from @py-iku-studio/types codegen. */
export type RecipeCatalogEntry = GeneratedRecipeCatalogEntry;

/** ProcessorCatalogEntry — sourced from @py-iku-studio/types codegen. */
export type ProcessorCatalogEntry = GeneratedProcessorCatalogEntry;

// Re-export generated HealthResponse so downstream can import from one place.
// Local HealthResponse interface above is superseded but kept for backward compat.
export type {
  GeneratedConvertRequest,
  GeneratedConvertResponse,
  GeneratedHealthResponse,
  GeneratedProcessorCatalogEntry,
  GeneratedRecipeCatalogEntry,
};

export interface NodeDiff {
  id: string;
  recipe_type_a: string | null;
  recipe_type_b: string | null;
  diff: Record<string, unknown> | null;
}

export interface DiffResponse {
  added: NodeDiff[];
  removed: NodeDiff[];
  changed: NodeDiff[];
}

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

// ---------------------------------------------------------------------------
// Market calendar — settle-window guard for the Deploy page
// ---------------------------------------------------------------------------

export interface MarketSession {
  venue: string;
  venue_name: string;
  product: string;
  timezone: string;
  /** HH:MM venue-local close. */
  close_time: string;
  /** Half-window — Deploy is gated within +/- this many minutes of close. */
  settle_window_minutes: number;
  note: string;
}

export interface MarketCalendarResponse {
  schedule_kind: "static-v1";
  note: string;
  sessions: MarketSession[];
}

// ---------------------------------------------------------------------------
// Persistence + sharing + audit (M7)
// ---------------------------------------------------------------------------

export interface SaveFlowRequest {
  flow: Record<string, unknown>;
  name: string;
  tags?: string[];
}

export interface CreatedFlowResponse {
  id: string;
  created_at: string;
}

export interface SavedFlowResponse {
  id: string;
  name: string;
  flow: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  tags: string[];
}

export interface ShareFlowRequest {
  ttl_seconds?: number;
  scopes?: string[];
}

export interface ShareFlowResponse {
  token: string;
  url: string;
  expires_at: string;
}

export interface AuditEvent {
  actor: string;
  action: string;
  resource_type: string;
  resource_id: string;
  details: Record<string, unknown>;
  ts: string;
}

export interface AuditListResponse {
  events: AuditEvent[];
  next_cursor: string | null;
}

export interface ListAuditOptions extends ClientOptions {
  since?: string;
  actor?: string;
  limit?: number;
  cursor?: string;
}

// ---------------------------------------------------------------------------
// Chat-with-flow + LLM history + budget (Sprint 4)
// ---------------------------------------------------------------------------

export interface ChatMessageWire {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface ChatCitation {
  recipe_id: string;
  source_lines?: number[] | null;
}

export interface ChatRequest {
  flow_json: Record<string, unknown>;
  question: string;
  history?: ChatMessageWire[];
  pandas_source?: string;
  flow_id?: string;
  provider?: "anthropic" | "openai" | "mock";
  model?: string;
  stream?: boolean;
}

export interface ChatResponse {
  answer: string;
  citations: ChatCitation[];
  model: string;
  usage: { input_tokens?: number; output_tokens?: number };
  cost_usd: number;
}

export interface LlmHistoryRecord {
  ts: string;
  mode: "rule" | "llm";
  provider: string;
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  cost_usd: number;
  status: "success" | "failure";
  flow_id?: string | null;
  error?: string | null;
  feature: string;
  request_id?: string | null;
  extra?: Record<string, unknown>;
}

export interface LlmHistoryListResponse {
  records: LlmHistoryRecord[];
  next_cursor: string | null;
}

export interface ListLlmHistoryOptions extends ClientOptions {
  provider?: string;
  status?: "success" | "failure";
  since?: string;
  until?: string;
  limit?: number;
  cursor?: string;
}

export interface CostSummary {
  today_usd: number;
  month_usd: number;
  budget: BudgetSettings;
  over_threshold: boolean;
  over_budget: boolean;
  pct_of_monthly_cap: number;
}

export interface BudgetSettings {
  monthly_cap_usd: number;
  per_call_cap_usd: number;
  alert_threshold_pct: number;
}

export type ExportFormat = "zip" | "json" | "yaml" | "svg" | "png" | "pdf";

export interface ExportResult {
  blob: Blob;
  filename: string;
  contentType: string;
}

function parseFilename(disposition: string | null, fallback: string): string {
  if (!disposition) return fallback;
  // Prefer filename*=UTF-8'' if present.
  const utf8 = /filename\*=UTF-8''([^;]+)/i.exec(disposition);
  if (utf8?.[1]) {
    try {
      return decodeURIComponent(utf8[1].trim());
    } catch {
      /* fall through */
    }
  }
  const ascii = /filename="?([^";]+)"?/i.exec(disposition);
  if (ascii?.[1]) return ascii[1].trim();
  return fallback;
}

export const client = {
  health(opts?: ClientOptions): Promise<HealthResponse> {
    return request<HealthResponse>("/health", { method: "GET" }, opts);
  },
  convert(req: ConvertRequest, opts?: ClientOptions): Promise<ConvertResponse> {
    return request<ConvertResponse>(
      "/convert",
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
  diff(
    a: Record<string, unknown>,
    b: Record<string, unknown>,
    opts?: ClientOptions,
  ): Promise<DiffResponse> {
    return request<DiffResponse>(
      "/diff",
      { method: "POST", body: JSON.stringify({ a, b }) },
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
  async export(
    format: ExportFormat,
    flow: Record<string, unknown>,
    opts?: ClientOptions & { exportOpts?: Record<string, unknown> },
  ): Promise<ExportResult> {
    const baseUrl = (opts?.baseUrl ?? getBaseUrl(opts ?? {})).replace(/\/$/, "");
    const url = `${baseUrl}/export/${encodeURIComponent(format)}`;
    const fetchImpl = opts?.fetchImpl ?? fetch;
    const requestId = uuid();
    const headers = new Headers({
      "X-Request-ID": requestId,
      "Content-Type": "application/json",
      Accept: "*/*",
    });
    if (opts?.authToken) headers.set("Authorization", `Bearer ${opts.authToken}`);

    const body = JSON.stringify({ flow, opts: opts?.exportOpts });
    let response: Response;
    try {
      response = await fetchImpl(url, { method: "POST", headers, body });
    } catch (cause) {
      const message = cause instanceof Error ? cause.message : String(cause);
      throw new ApiError(
        { type: "about:blank", title: "Network error", status: 0, detail: message },
        requestId,
      );
    }
    if (!response.ok) {
      let problem: ApiProblem = {
        type: "about:blank",
        title: response.statusText || "Request failed",
        status: response.status,
      };
      try {
        const data = (await response.json()) as Partial<ApiProblem>;
        problem = {
          type: data.type ?? problem.type,
          title: data.title ?? problem.title,
          status: data.status ?? response.status,
          detail: data.detail,
          ...data,
        };
      } catch {
        /* keep default problem */
      }
      throw new ApiError(problem, requestId);
    }

    const blob = await response.blob();
    const contentType = response.headers.get("content-type") ?? "application/octet-stream";
    const filename = parseFilename(
      response.headers.get("content-disposition"),
      `flow.${format}`,
    );
    return { blob, filename, contentType };
  },
  saveFlow(payload: SaveFlowRequest, opts?: ClientOptions): Promise<CreatedFlowResponse> {
    return request<CreatedFlowResponse>(
      "/flows",
      { method: "POST", body: JSON.stringify(payload) },
      opts,
    );
  },
  getFlow(id: string, opts?: ClientOptions): Promise<SavedFlowResponse> {
    return request<SavedFlowResponse>(
      `/flows/${encodeURIComponent(id)}`,
      { method: "GET" },
      opts,
    );
  },
  shareFlow(
    id: string,
    body?: ShareFlowRequest,
    opts?: ClientOptions,
  ): Promise<ShareFlowResponse> {
    return request<ShareFlowResponse>(
      `/flows/${encodeURIComponent(id)}/share`,
      { method: "POST", body: JSON.stringify(body ?? {}) },
      opts,
    );
  },
  getShared(token: string, opts?: ClientOptions): Promise<SavedFlowResponse> {
    return request<SavedFlowResponse>(
      `/share/${encodeURIComponent(token)}`,
      { method: "GET" },
      opts,
    );
  },
  listAuditEvents(opts?: ListAuditOptions): Promise<AuditListResponse> {
    const params = new URLSearchParams();
    if (opts?.since) params.set("since", opts.since);
    if (opts?.actor) params.set("actor", opts.actor);
    if (typeof opts?.limit === "number") params.set("limit", String(opts.limit));
    if (opts?.cursor) params.set("cursor", opts.cursor);
    const qs = params.toString();
    const path = qs ? `/audit?${qs}` : "/audit";
    return request<AuditListResponse>(path, { method: "GET" }, opts);
  },

  // -------------------------------------------------------------------
  // Chat-with-flow + LLM history (Sprint 4)
  // -------------------------------------------------------------------
  chat(req: ChatRequest, opts?: ClientOptions): Promise<ChatResponse> {
    return request<ChatResponse>(
      "/chat",
      { method: "POST", body: JSON.stringify({ ...req, stream: false }) },
      opts,
    );
  },
  listLlmHistory(opts?: ListLlmHistoryOptions): Promise<LlmHistoryListResponse> {
    const params = new URLSearchParams();
    if (opts?.provider) params.set("provider", opts.provider);
    if (opts?.status) params.set("status", opts.status);
    if (opts?.since) params.set("since", opts.since);
    if (opts?.until) params.set("until", opts.until);
    if (typeof opts?.limit === "number") params.set("limit", String(opts.limit));
    if (opts?.cursor) params.set("cursor", opts.cursor);
    const qs = params.toString();
    const path = qs ? `/llm-history?${qs}` : "/llm-history";
    return request<LlmHistoryListResponse>(path, { method: "GET" }, opts);
  },
  getLlmCostSummary(opts?: ClientOptions): Promise<CostSummary> {
    return request<CostSummary>("/llm-cost-summary", { method: "GET" }, opts);
  },
  getLlmBudget(opts?: ClientOptions): Promise<BudgetSettings> {
    return request<BudgetSettings>("/llm-budget", { method: "GET" }, opts);
  },
  putLlmBudget(
    body: BudgetSettings,
    opts?: ClientOptions,
  ): Promise<BudgetSettings> {
    return request<BudgetSettings>(
      "/llm-budget",
      { method: "PUT", body: JSON.stringify(body) },
      opts,
    );
  },
  /** Sprint 4 — market calendar feeds the Deploy settle-window guard. */
  getMarketCalendar(opts?: ClientOptions): Promise<MarketCalendarResponse> {
    return request<MarketCalendarResponse>(
      "/market-calendar",
      { method: "GET" },
      opts,
    );
  },
  /**
   * Sprint-4 governance: column-level lineage on an inline flow.
   *
   * Returns aliases (rename history), recipe edges that operate on / derive
   * the column, and the leaf input/output datasets.
   */
  lineage(
    flow: Record<string, unknown>,
    column: string,
    opts?: ClientOptions,
  ): Promise<LineageResponse> {
    return request<LineageResponse>(
      "/flows/lineage",
      { method: "POST", body: JSON.stringify({ flow, column }) },
      opts,
    );
  },
  /** Sprint-4 governance: lint a flow. */
  lint(
    flow: Record<string, unknown>,
    opts?: ClientOptions,
  ): Promise<LintResponse> {
    return request<LintResponse>(
      "/flows/lint",
      { method: "POST", body: JSON.stringify({ flow }) },
      opts,
    );
  },
  /** Sprint-4 governance: apply a fixable lint rule. */
  lintFix(
    flow: Record<string, unknown>,
    rule_id: string,
    payload: Record<string, unknown>,
    opts?: ClientOptions,
  ): Promise<{ flow: Record<string, unknown> }> {
    return request<{ flow: Record<string, unknown> }>(
      "/flows/lint/fix",
      { method: "POST", body: JSON.stringify({ flow, rule_id, payload }) },
      opts,
    );
  },
  /** Sprint-4 governance: schema-drift between two flow snapshots. */
  schemaDrift(
    prior: Record<string, unknown>,
    next_: Record<string, unknown>,
    opts?: ClientOptions,
  ): Promise<SchemaDriftResponse> {
    return request<SchemaDriftResponse>(
      "/flows/schema-drift",
      { method: "POST", body: JSON.stringify({ prior, next: next_ }) },
      opts,
    );
  },
  /**
   * Sprint-4 governance: scaffold a pytest integration test from a flow.
   * Returns a downloadable .py blob and filename.
   */
  async scaffoldTest(
    body: ScaffoldTestRequest,
    opts?: ClientOptions,
  ): Promise<ExportResult> {
    const baseUrl = (opts?.baseUrl ?? getBaseUrl(opts ?? {})).replace(/\/$/, "");
    const url = `${baseUrl}/flows/scaffold-test`;
    const fetchImpl = opts?.fetchImpl ?? fetch;
    const requestId = uuid();
    const headers = new Headers({
      "X-Request-ID": requestId,
      "Content-Type": "application/json",
      Accept: "*/*",
    });
    if (opts?.authToken) headers.set("Authorization", `Bearer ${opts.authToken}`);

    let response: Response;
    try {
      response = await fetchImpl(url, {
        method: "POST",
        headers,
        body: JSON.stringify(body),
      });
    } catch (cause) {
      const message = cause instanceof Error ? cause.message : String(cause);
      throw new ApiError(
        { type: "about:blank", title: "Network error", status: 0, detail: message },
        requestId,
      );
    }
    if (!response.ok) {
      let problem: ApiProblem = {
        type: "about:blank",
        title: response.statusText || "Request failed",
        status: response.status,
      };
      try {
        const data = (await response.json()) as Partial<ApiProblem>;
        problem = {
          type: data.type ?? problem.type,
          title: data.title ?? problem.title,
          status: data.status ?? response.status,
          detail: data.detail,
          ...data,
        };
      } catch {
        /* keep default */
      }
      throw new ApiError(problem, requestId);
    }
    const blob = await response.blob();
    const contentType = response.headers.get("content-type") ?? "text/x-python";
    const filename = parseFilename(
      response.headers.get("content-disposition"),
      `test_flow_integration.py`,
    );
    return { blob, filename, contentType };
  },
  /** Generic escape hatch for not-yet-typed endpoints (M5+ will expand). */
  request,
};

export type Client = typeof client;

// ---------------------------------------------------------------------------
// Sprint-4 governance types
// ---------------------------------------------------------------------------

export interface LineageEdge {
  recipe_id: string;
  input_dataset: string;
  output_dataset: string;
  kind: string;
  details?: Record<string, unknown>;
}

export interface LineageResponse {
  column: string;
  aliases: string[];
  input_datasets: string[];
  output_datasets: string[];
  edges: LineageEdge[];
  recipes: string[];
  available_columns: string[];
}

export interface LintEntry {
  rule_id: string;
  severity: "blocker" | "warning" | "info";
  recipe_id: string | null;
  message: string;
  fix?: Record<string, unknown> | null;
}

export interface LintResponse {
  lints: LintEntry[];
  rule_catalog: { rule_id: string; severity: string; title: string }[];
}

export interface SchemaDriftRenamed {
  from: string;
  to: string;
  type: string;
}
export interface SchemaDriftTypeChanged {
  name: string;
  from_type: string;
  to_type: string;
}
export interface SchemaDriftPerDataset {
  dataset: string;
  added: { name: string; type: string }[];
  removed: { name: string; type: string }[];
  renamed: SchemaDriftRenamed[];
  type_changed: SchemaDriftTypeChanged[];
}

export interface SchemaDriftResponse {
  summary: {
    datasets_added: number;
    datasets_removed: number;
    columns_added: number;
    columns_removed: number;
    columns_renamed: number;
    columns_type_changed: number;
    has_drift: boolean;
  };
  headline: string;
  datasets_added: string[];
  datasets_removed: string[];
  per_dataset: SchemaDriftPerDataset[];
}

export interface ScaffoldTestRequest {
  flow: Record<string, unknown>;
  source: string;
  flow_name?: string;
  track_columns?: string[];
}

// ---------------------------------------------------------------------------
// Wave 4D — Collaboration & lifecycle types
// ---------------------------------------------------------------------------

export interface Comment {
  id: string;
  flow_id: string;
  recipe_id: string;
  author: string;
  body: string;
  timestamp: string;
  edited_at?: string | null;
}

export interface CommentListResponse {
  comments: Comment[];
}

export interface CreateCommentRequest {
  body: string;
  author?: string;
}

export interface FixturePreviewDataset {
  name: string;
  columns: string[];
  sample_rows: Array<Record<string, unknown>>;
}

export interface FixturePreviewResponse {
  n_rows: number;
  datasets: FixturePreviewDataset[];
}

export interface FixtureBundleResponse {
  n_rows: number;
  datasets: Record<string, Array<Record<string, unknown>>>;
}

export interface GithubPublishRequest {
  pat: string;
  repo: string;
  base?: string;
  branch: string;
  flow_name: string;
  pr_title: string;
  pr_body?: string;
  commit_message?: string;
  flow_json: Record<string, unknown>;
  flow_svg: string;
}

export interface GithubPublishResponse {
  pr_url: string;
  pr_number: number;
  branch: string;
  commit_sha: string;
}

export const collabClient = {
  listComments(flowId: string, opts?: ClientOptions): Promise<CommentListResponse> {
    return request<CommentListResponse>(
      `/flows/${encodeURIComponent(flowId)}/comments`,
      { method: "GET" },
      opts,
    );
  },
  postComment(
    flowId: string,
    recipeId: string,
    body: CreateCommentRequest,
    opts?: ClientOptions,
  ): Promise<Comment> {
    return request<Comment>(
      `/flows/${encodeURIComponent(flowId)}/recipes/${encodeURIComponent(recipeId)}/comments`,
      { method: "POST", body: JSON.stringify(body) },
      opts,
    );
  },
  deleteComment(
    flowId: string,
    commentId: string,
    opts?: ClientOptions,
  ): Promise<void> {
    return request<void>(
      `/flows/${encodeURIComponent(flowId)}/comments/${encodeURIComponent(commentId)}`,
      { method: "DELETE" },
      opts,
    );
  },
  previewFixtures(
    flow: Record<string, unknown>,
    nRows = 5,
    opts?: ClientOptions,
  ): Promise<FixturePreviewResponse> {
    return request<FixturePreviewResponse>(
      "/share/fixtures/preview",
      { method: "POST", body: JSON.stringify({ flow, n_rows: nRows }) },
      opts,
    );
  },
  bundleFixtures(
    flow: Record<string, unknown>,
    nRows = 100,
    opts?: ClientOptions,
  ): Promise<FixtureBundleResponse> {
    return request<FixtureBundleResponse>(
      "/share/fixtures/bundle",
      { method: "POST", body: JSON.stringify({ flow, n_rows: nRows }) },
      opts,
    );
  },
  githubPublish(
    body: GithubPublishRequest,
    opts?: ClientOptions,
  ): Promise<GithubPublishResponse> {
    return request<GithubPublishResponse>(
      "/github/publish",
      { method: "POST", body: JSON.stringify(body) },
      opts,
    );
  },
};

export type CollabClient = typeof collabClient;
