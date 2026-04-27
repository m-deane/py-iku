/**
 * Shared fixtures + helpers for the e2e suite.
 *
 * - `LLM_AVAILABLE` flag — read from the PY_IKU_LLM_AVAILABLE env var. Tests
 *   that require a live LLM provider should `test.skip(!LLM_AVAILABLE, ...)`.
 *
 * - `stubApi(page)` — installs network routes that return canned, deterministic
 *   API responses. Avoids any dependency on the FastAPI backend, which keeps
 *   the suite hermetic and fast. Each spec calls this once at the top of the
 *   test if it doesn't otherwise depend on a live API.
 *
 * - `apiUp(url)` — async helper that probes the live API health endpoint.
 *   Used by tests that prefer the live API but tolerate it being absent.
 */
import type { Page, Route } from "@playwright/test";

export const LLM_AVAILABLE = (process.env.PY_IKU_LLM_AVAILABLE ?? "") === "1";

export async function apiUp(apiUrl: string): Promise<boolean> {
  try {
    const resp = await fetch(`${apiUrl.replace(/\/$/, "")}/health`);
    return resp.ok;
  } catch {
    return false;
  }
}

export interface StubFlowOptions {
  flowName?: string;
  recipeName?: string;
  recipeType?: string;
}

/** A minimal, deterministic DataikuFlow.to_dict() shape. */
export function stubFlowDict(opts: StubFlowOptions = {}): Record<string, unknown> {
  const flowName = opts.flowName ?? "stub_flow";
  const recipeName = opts.recipeName ?? "agg_summary";
  const recipeType = opts.recipeType ?? "GROUPING";
  return {
    flow_name: flowName,
    total_recipes: 1,
    total_datasets: 2,
    datasets: [
      {
        name: "input_data",
        type: "Filesystem",
        connection_type: "filesystem",
        schema: [{ name: "id", type: "bigint" }],
      },
      {
        name: "output_data",
        type: "Filesystem",
        connection_type: "filesystem",
        schema: [{ name: "category", type: "string" }],
      },
    ],
    recipes: [
      {
        name: recipeName,
        type: recipeType,
        inputs: ["input_data"],
        outputs: ["output_data"],
        keys: ["category"],
        aggregations: [{ column: "amount", op: "sum" }],
      },
    ],
  };
}

/** Canned shared-flow payload (for /share/{token}). */
export const STUB_SHARE_TOKEN = "stub-token-abc123";
export function stubSharedResponse(): Record<string, unknown> {
  return {
    id: "stub-flow-id",
    name: "stub-flow",
    flow: stubFlowDict(),
    created_at: "2026-04-26T00:00:00Z",
    updated_at: "2026-04-26T00:00:00Z",
    tags: [],
  };
}

/**
 * Stubs the WebSocket /convert/stream endpoint so it sends a deterministic
 * `started` → `completed` sequence (matching `WSEvent` in the API). Call this
 * before the page navigates so the WebSocket constructor is overridden in
 * the page context.
 */
export async function stubWebSocketConvert(
  page: Page,
  flow: Record<string, unknown> = stubFlowDict(),
): Promise<void> {
  const flowJson = JSON.stringify(flow);
  await page.addInitScript((args: { flowJson: string }) => {
      const flowObj = JSON.parse(args.flowJson);
      const score = { complexity: 1.0, recipe_count: 1, dataset_count: 2 };

      // Replace the global WebSocket with a stub that immediately fires
      // open + a deterministic event sequence on send().
      class FakeWebSocket implements EventTarget {
        readyState = 0;
        url: string;
        protocol = "py-iku-studio.v1";
        binaryType: BinaryType = "blob";
        bufferedAmount = 0;
        extensions = "";
        onopen: ((ev: Event) => void) | null = null;
        onclose: ((ev: CloseEvent) => void) | null = null;
        onerror: ((ev: Event) => void) | null = null;
        onmessage: ((ev: MessageEvent) => void) | null = null;
        // Constants required by the WebSocket spec.
        CONNECTING = 0;
        OPEN = 1;
        CLOSING = 2;
        CLOSED = 3;
        static CONNECTING = 0;
        static OPEN = 1;
        static CLOSING = 2;
        static CLOSED = 3;

        constructor(url: string, _protocols?: string | string[]) {
          this.url = url;
          // Open asynchronously so callers can attach handlers.
          setTimeout(() => {
            this.readyState = 1;
            this.onopen?.(new Event("open"));
          }, 0);
        }

        send(_data: string): void {
          // Drive the canned event sequence after the request is "received".
          let seq = 0;
          const emit = (event: string, payload: Record<string, unknown> = {}): void => {
            seq += 1;
            this.onmessage?.(
              new MessageEvent("message", {
                data: JSON.stringify({
                  event,
                  seq,
                  ts: new Date().toISOString(),
                  payload,
                }),
              }),
            );
          };
          setTimeout(() => emit("started", { mode: "rule" }), 0);
          setTimeout(() => emit("ast_parsed", {}), 5);
          setTimeout(
            () =>
              emit("completed", {
                flow: flowObj,
                score,
                warnings: [],
              }),
            10,
          );
          setTimeout(() => {
            this.readyState = 3;
            this.onclose?.(
              new CloseEvent("close", { code: 1000, reason: "normal" }),
            );
          }, 15);
        }

        close(_code?: number, _reason?: string): void {
          this.readyState = 3;
          this.onclose?.(new CloseEvent("close", { code: _code ?? 1000 }));
        }

        addEventListener(): void {
          /* no-op for our handlers — we only use on{event} */
        }
        removeEventListener(): void {
          /* no-op */
        }
        dispatchEvent(_e: Event): boolean {
          return true;
        }
      }

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (window as any).WebSocket = FakeWebSocket as any;
    },
    { flowJson },
  );
}

/** Single, fixed audit event for empty-vs-populated visuals. */
export function stubAuditEvent(): Record<string, unknown> {
  return {
    actor: "anonymous",
    action: "convert.run",
    resource_type: "flow",
    resource_id: "stub-flow-id",
    details: { mode: "rule" },
    ts: "2026-04-26T00:00:00Z",
  };
}

/**
 * Installs deterministic API stubs for every endpoint touched by the e2e
 * suite. Call near the top of each test (after navigating, before clicking).
 */
export interface StubOptions {
  /** Whether to include a single pre-seeded audit event. Default: true. */
  withAuditEvent?: boolean;
  /** Optional flow override — when set, /convert returns this instead of stubFlowDict(). */
  flow?: Record<string, unknown>;
}

export async function stubApi(page: Page, opts: StubOptions = {}): Promise<void> {
  const flow = opts.flow ?? stubFlowDict();
  const withAuditEvent = opts.withAuditEvent ?? true;

  // /health
  await page.route(/\/health(?:$|\?)/, (route: Route) => {
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ status: "ok", version: "0.0.0", py_iku_version: "0.3.0" }),
    });
  });

  // /convert (rule + llm both go through this in the REST path; stream path
  // tests stub the WS separately or fall back to REST via prop seam).
  await page.route(/\/convert(?:$|\?)/, (route: Route) => {
    if (route.request().method() !== "POST") return route.continue();
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        flow,
        score: { complexity: 1.0, recipe_count: 1, dataset_count: 2 },
        warnings: [],
      }),
    });
  });

  // /diff
  await page.route(/\/diff(?:$|\?)/, (route: Route) => {
    if (route.request().method() !== "POST") return route.continue();
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        added: [
          { id: "added_node", recipe_type_a: null, recipe_type_b: "sort", diff: null },
        ],
        removed: [],
        changed: [
          {
            id: "agg_summary",
            recipe_type_a: "GROUPING",
            recipe_type_b: "GROUPING",
            diff: { keys: { a: ["category"], b: ["category", "type"] } },
          },
        ],
      }),
    });
  });

  // /flows (save) → returns a canned id.
  await page.route(/\/flows$/, (route: Route) => {
    if (route.request().method() === "POST") {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ id: "stub-flow-id", created_at: "2026-04-26T00:00:00Z" }),
      });
    }
    return route.continue();
  });

  // /flows/{id} (read after save)
  await page.route(/\/flows\/[^/?]+$/, (route: Route) => {
    if (route.request().method() === "GET") {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(stubSharedResponse()),
      });
    }
    return route.continue();
  });

  // /flows/{id}/share
  await page.route(/\/flows\/[^/]+\/share$/, (route: Route) => {
    if (route.request().method() === "POST") {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          token: STUB_SHARE_TOKEN,
          url: `${new URL(page.url()).origin}/share/${STUB_SHARE_TOKEN}`,
          expires_at: "2026-04-27T00:00:00Z",
        }),
      });
    }
    return route.continue();
  });

  // /share/{token}
  await page.route(/\/share\/[^/?]+(?:$|\?)/, (route: Route) => {
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(stubSharedResponse()),
    });
  });

  // /audit
  await page.route(/\/audit(?:$|\?)/, (route: Route) => {
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        events: withAuditEvent
          ? [
              stubAuditEvent(),
              {
                ...(stubAuditEvent() as Record<string, unknown>),
                action: "share.create",
              },
            ]
          : [],
        next_cursor: null,
      }),
    });
  });

  // /catalog/recipes — 37 entries with deterministic types.
  await page.route(/\/catalog\/recipes(?:$|\?)/, (route: Route) => {
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(buildRecipeCatalog37()),
    });
  });

  // /catalog/processors
  await page.route(/\/catalog\/processors(?:$|\?)/, (route: Route) => {
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(buildProcessorCatalog()),
    });
  });

  // /catalog/processors/{type}
  await page.route(/\/catalog\/processors\/[^/?]+/, (route: Route) => {
    const match = /\/catalog\/processors\/([^/?]+)/.exec(new URL(route.request().url()).pathname);
    const type = match?.[1] ?? "COLUMN_RENAMER";
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        name: type,
        type,
        category: "Cleansing",
        description: `Stub processor: ${type}`,
        tags: ["stub"],
      }),
    });
  });
}

/** Mirror of the 37 RecipeType values (order doesn't matter for assertions). */
const RECIPE_TYPES_37 = [
  "PYTHON",
  "SQL",
  "R",
  "SHELL",
  "PREPARE",
  "GROUPING",
  "JOIN",
  "SPLIT",
  "STACK",
  "SORT",
  "TOP_N",
  "DISTINCT",
  "WINDOW",
  "FILTER",
  "PIVOT",
  "SAMPLING",
  "DOWNLOAD",
  "EXPORT",
  "VSTACK",
  "SYNC",
  "TRAIN",
  "PREDICT",
  "CLUSTERING",
  "EVALUATION",
  "STANDALONE_EVALUATION",
  "SCORING",
  "FUZZY_JOIN",
  "GEO_JOIN",
  "MERGE_FOLDER",
  "VIRTUAL",
  "PIPELINE",
  "VIRTUAL_SUB_PIPELINE",
  "STREAMING",
  "CONTINUOUS_SYNC",
  "UPDATE",
  "PUSH_TO_EDITOR",
  "VISUAL_ANALYSIS",
];

function buildRecipeCatalog37(): Record<string, unknown>[] {
  return RECIPE_TYPES_37.map((t) => ({
    type: t,
    name: t.replace(/_/g, " ").toLowerCase(),
    category: "structural",
    icon: "◆",
    description: `Stub catalog entry for ${t}`,
  }));
}

function buildProcessorCatalog(): Record<string, unknown>[] {
  // 5 deterministic entries are enough for the e2e search/select assertions.
  return [
    "COLUMN_RENAMER",
    "FILL_EMPTY_WITH_VALUE",
    "FOLD_MULTIPLE_COLUMNS",
    "REGEXP_EXTRACT",
    "FORMULA",
  ].map((t) => ({
    name: t,
    type: t,
    category: "Cleansing",
    description: `Stub processor: ${t}`,
    tags: ["stub"],
  }));
}
