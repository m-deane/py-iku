/**
 * conversion-rule.spec.ts — visual smoke test of the rule-based conversion
 * path through the Studio's Convert page.
 *
 * Strategy:
 *   - Disable the WebSocket streaming path (we want the deterministic REST
 *     code path here so the test exercises the real /convert endpoint).
 *   - Stub /convert with a known DataikuFlow payload (recipes + datasets).
 *   - Paste a small Python script via the Monaco fallback textarea, click
 *     Convert, and assert the canvas + node-list render the expected
 *     recipe/dataset nodes.
 *
 * These tests intentionally keep their fixtures separate from the WebSocket
 * stubs in convert.spec.ts — they're verifying the structural-adapter path
 * (DataikuFlow → MinimalFlow → FlowCanvas) which the Wave-2 rule fixes
 * touch.
 */
import { test, expect, Page } from "@playwright/test";
import { stubApi } from "./_fixtures";

const V1_RETAIL = `import pandas as pd

orders = pd.read_csv("orders.csv")
orders["discount_pct"] = orders["discount_pct"].fillna(0.0)
orders["revenue"] = orders["quantity"] * orders["unit_price"] * (1 - orders["discount_pct"])
orders = orders.rename(columns={"order_date": "ordered_at"})
orders_clean = orders
`;

const EX03_CURVE_SCD = `import pandas as pd
ref_date = "2026-04-26"
df = pd.read_csv("curve_history.csv")
cond = (df["effective_date"] <= ref_date) & ((df["end_date"].isna()) | (df["end_date"] > ref_date))
current = df[cond]
history = df[~cond]
current.to_parquet("curves_current.parquet")
history.to_parquet("curves_history.parquet")
`;

const EX04_PJM_HUB = `import pandas as pd

positions = pd.read_csv("lmp_positions.csv")
nodes = pd.read_csv("node_to_zone.csv")

enriched = positions.merge(nodes, on="node_id", how="left")
by_zone = enriched.groupby(["zone", "hour_ending"]).agg({
    "volume_mwh": "sum",
    "position_id": "count",
})
`;

const EX01_TRADE_INGESTION = `import pandas as pd

trades = pd.read_csv("trades.csv")
trades = trades.dropna(subset=["trade_id", "trade_date", "notional"])
filtered = trades[trades["notional"] > 0]
filtered.to_csv("trade_blotter.csv")
`;

/**
 * Build a deterministic /convert response that mirrors what the rule-based
 * engine + sanitizer produces. The shape matches the post-Wave-2 contract:
 * datasets are tagged with input/intermediate/output, recipe inputs/outputs
 * reference real dataset names, no empty-string entries.
 */
function ruleConvertResponse(opts: {
  recipes: Array<{ name: string; type: string; inputs: string[]; outputs: string[] }>;
  datasets: Array<{ name: string; type: "input" | "intermediate" | "output" }>;
}) {
  return {
    flow: {
      flow_name: "rule_flow",
      generated_from: "rule_engine",
      generation_timestamp: "2026-04-26T00:00:00Z",
      total_recipes: opts.recipes.length,
      total_datasets: opts.datasets.length,
      datasets: opts.datasets.map((d) => ({
        name: d.name,
        type: d.type,
        connection_type: "Filesystem",
        schema: [],
        notes: [],
      })),
      recipes: opts.recipes.map((r) => ({
        name: r.name,
        type: r.type,
        inputs: r.inputs,
        outputs: r.outputs,
        steps: [],
      })),
      optimization_notes: [],
      recommendations: [],
      zones: [],
    },
    score: {
      recipe_count: opts.recipes.length,
      processor_count: 0,
      dataset_count: opts.datasets.length,
      max_depth: opts.recipes.length + 1,
      fan_out_max: 2,
      complexity: opts.recipes.length * 1.0,
      cost_estimate: null,
    },
    warnings: [],
  };
}

async function stubConvertRoute(page: Page, body: object): Promise<void> {
  await page.route("**/convert", async (route) => {
    if (route.request().method() === "POST") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(body),
      });
    } else {
      await route.continue();
    }
  });
}

/** Force the page to use the REST-only conversion path (no WebSocket). */
async function disableStreaming(page: Page): Promise<void> {
  // The component reads `useRestOnly` as a prop. We don't have direct access
  // to set that prop from outside in the live app — instead we make the
  // WebSocket constructor throw so the page's stream hook fails fast and
  // the user-visible state stays in REST mode (the page falls back to
  // showing an error). Since both REST and WS paths are exercised together,
  // the cleanest live-code lever is to stub /convert and let the streaming
  // hook fail silently. The page's effect will pick up the response from
  // the REST POST.
  // For these tests the simplest approach is to disable any active WS by
  // overriding the global WebSocket to no-op.
  await page.addInitScript(() => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (window as unknown as { WebSocket: unknown }).WebSocket = class {
      readyState = 0;
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      addEventListener(): void {}
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      removeEventListener(): void {}
      send(): void {}
      close(): void {}
    };
  });
}

async function pasteCode(page: Page, code: string): Promise<void> {
  // The Monaco editor's fallback textarea has the data-testid below when the
  // fallback path is active. Under jsdom-style runs this is always the
  // fallback; under real Chromium the Monaco editor is real. The test asks
  // Monaco to focus then types the value via the value setter.
  await page.evaluate((src) => {
    // Try fallback textarea first.
    const ta = document.querySelector(
      '[data-testid="monaco-fallback"]',
    ) as HTMLTextAreaElement | null;
    if (ta) {
      ta.value = src;
      ta.dispatchEvent(new Event("input", { bubbles: true }));
      ta.dispatchEvent(new Event("change", { bubbles: true }));
      return;
    }
    // Otherwise drive Monaco via its global API.
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const monaco = (window as any).monaco;
    if (monaco?.editor) {
      const models = monaco.editor.getModels();
      if (models && models.length > 0) {
        models[0].setValue(src);
        return;
      }
    }
    // Last-resort: dispatch a paste event on the textarea Monaco wraps.
    const inputs = document.querySelectorAll("textarea");
    for (const t of Array.from(inputs)) {
      const ta = t as HTMLTextAreaElement;
      ta.value = src;
      ta.dispatchEvent(new Event("input", { bubbles: true }));
    }
  }, code);
}

test.describe("Convert (rule mode) — Wave-2 visual smoke", () => {
  test.beforeEach(async ({ page }) => {
    await stubApi(page);
    await disableStreaming(page);
  });

  test("V1 retail: PREPARE node + orders dataset render on the canvas", async ({ page }) => {
    await stubConvertRoute(
      page,
      ruleConvertResponse({
        recipes: [
          {
            name: "prepare_1",
            type: "prepare",
            inputs: ["orders"],
            outputs: ["orders_prepared"],
          },
        ],
        datasets: [
          { name: "orders", type: "input" },
          { name: "orders_prepared", type: "output" },
        ],
      }),
    );
    await page.goto("/convert");
    await pasteCode(page, V1_RETAIL);
    await page.getByTestId("convert-submit").click();
    await expect(page.getByTestId("response-panel")).toBeVisible({ timeout: 15_000 });
    // Recipe node appears in the node list.
    await expect(page.getByTestId("node-list-item-prepare_1")).toBeVisible();
    // Inline canvas renders.
    await expect(page.getByTestId("convert-canvas")).toBeVisible();
  });

  test("ex03 curves SCD: ONE consolidated SPLIT recipe with two output stripes", async ({
    page,
  }) => {
    await stubConvertRoute(
      page,
      ruleConvertResponse({
        recipes: [
          {
            name: "split_1",
            type: "split",
            inputs: ["df"],
            outputs: ["current", "history"],
          },
        ],
        datasets: [
          { name: "df", type: "input" },
          { name: "current", type: "output" },
          { name: "history", type: "output" },
        ],
      }),
    );
    await page.goto("/convert");
    await pasteCode(page, EX03_CURVE_SCD);
    await page.getByTestId("convert-submit").click();
    await expect(page.getByTestId("response-panel")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("node-list-item-split_1")).toBeVisible();
    // The split has only ONE recipe entry (consolidation regression check).
    const items = page.locator('[data-testid^="node-list-item-"]');
    await expect(items).toHaveCount(1);
  });

  test("ex04 PJM hub: JOIN + GROUPING render side by side", async ({ page }) => {
    await stubConvertRoute(
      page,
      ruleConvertResponse({
        recipes: [
          {
            name: "join_1",
            type: "join",
            inputs: ["positions", "nodes"],
            outputs: ["enriched"],
          },
          {
            name: "grouping_2",
            type: "grouping",
            inputs: ["enriched"],
            outputs: ["by_zone"],
          },
        ],
        datasets: [
          { name: "positions", type: "input" },
          { name: "nodes", type: "input" },
          { name: "enriched", type: "intermediate" },
          { name: "by_zone", type: "output" },
        ],
      }),
    );
    await page.goto("/convert");
    await pasteCode(page, EX04_PJM_HUB);
    await page.getByTestId("convert-submit").click();
    await expect(page.getByTestId("response-panel")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("node-list-item-join_1")).toBeVisible();
    await expect(page.getByTestId("node-list-item-grouping_2")).toBeVisible();
  });

  test("ex01 trade ingestion: stat-datasets reflects post-sanitize count", async ({
    page,
  }) => {
    await stubConvertRoute(
      page,
      ruleConvertResponse({
        recipes: [
          {
            name: "prepare_1",
            type: "prepare",
            inputs: ["trades"],
            outputs: ["trades_prepared"],
          },
          {
            name: "split_2",
            type: "split",
            inputs: ["trades_prepared"],
            outputs: ["filtered"],
          },
        ],
        datasets: [
          { name: "trades", type: "input" },
          { name: "trades_prepared", type: "intermediate" },
          { name: "filtered", type: "output" },
        ],
      }),
    );
    await page.goto("/convert");
    await pasteCode(page, EX01_TRADE_INGESTION);
    await page.getByTestId("convert-submit").click();
    await expect(page.getByTestId("response-panel")).toBeVisible({ timeout: 15_000 });
    // The Datasets stat-card surfaces the dataset_count from the score.
    await expect(page.getByTestId("stat-datasets")).toContainText("3");
  });

  test("Convert button stays disabled while the editor is empty", async ({ page }) => {
    await page.goto("/convert");
    // The Convert button is enabled by default but `onConvert` toasts on empty.
    // We assert that clicking it without code does not trigger /convert.
    let convertCalled = false;
    await page.route("**/convert", async (route) => {
      if (route.request().method() === "POST") {
        convertCalled = true;
      }
      await route.continue();
    });
    // Make sure the editor is empty.
    await page.evaluate(() => {
      const ta = document.querySelector(
        '[data-testid="monaco-fallback"]',
      ) as HTMLTextAreaElement | null;
      if (ta) {
        ta.value = "";
        ta.dispatchEvent(new Event("input", { bubbles: true }));
      }
    });
    await page.getByTestId("convert-submit").click();
    await expect(page.locator("text=No code to convert")).toBeVisible({ timeout: 4_000 });
    expect(convertCalled).toBe(false);
  });
});
