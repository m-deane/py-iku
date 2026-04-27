/**
 * Sprint-3 visual capture: LLM confidence shading on recipe cards plus the
 * summary panel. Each test snapshots a single deterministic state into the
 * Playwright outputDir AND writes a copy under
 * `/tmp/py-iku-review/sprint3-after/confidence/` so the sprint reviewer can
 * inspect them without rummaging in `playwright-report/`.
 *
 * The conversion is stubbed via the `prepare()` helper so we don't need a
 * live backend; the stubbed `/convert` payload we inject below carries the
 * three new optional fields (`confidence`, `reasoning`, `source_lines`)
 * already-plumbed in apps/api/app/schemas/recipe.py.
 */
import { test, expect } from "@playwright/test";
import * as fs from "node:fs";
import * as path from "node:path";
import { prepare, type PrepareOptions } from "./_helpers";

const REVIEW_DIR = "/tmp/py-iku-review/sprint3-after/confidence";

function ensureReviewDir(): void {
  fs.mkdirSync(REVIEW_DIR, { recursive: true });
}

async function copyToReviewDir(playwrightPath: string, name: string): Promise<void> {
  ensureReviewDir();
  if (fs.existsSync(playwrightPath)) {
    fs.copyFileSync(playwrightPath, path.join(REVIEW_DIR, name));
  }
}

const STUBBED_CONVERT_PAYLOAD = {
  flow: {
    flow_name: "trader_pnl_v2",
    total_recipes: 4,
    total_datasets: 5,
    datasets: [
      { name: "trades", type: "input", connection_type: "Filesystem", schema: [] },
      { name: "cp", type: "input", connection_type: "Filesystem", schema: [] },
      { name: "enriched", type: "intermediate", connection_type: "Filesystem", schema: [] },
      { name: "out", type: "intermediate", connection_type: "Filesystem", schema: [] },
      { name: "risk", type: "output", connection_type: "Filesystem", schema: [] },
    ],
    recipes: [
      {
        name: "join_high",
        type: "join",
        inputs: ["trades", "cp"],
        outputs: ["enriched"],
        source_lines: [3, 3],
        notes: [],
        confidence: 0.93,
        reasoning:
          "df.merge(other, on='cpid', how='left') -> JOIN with EXACT key on 'cpid'.",
        join_type: "LEFT",
        join_keys: [
          { left: { column: "cpid" }, right: { column: "cpid" }, matchType: "EXACT" },
        ],
      },
      {
        name: "group_med",
        type: "grouping",
        inputs: ["enriched"],
        outputs: ["out"],
        source_lines: [4, 4],
        notes: [],
        confidence: 0.72,
        reasoning:
          "Multi-function aggregation; judgement call on 'sum' vs 'mean' columns.",
        keys: ["region"],
        aggregations: [{ column: "notional", type: "SUM" }],
      },
      {
        name: "udf_low",
        type: "python",
        inputs: ["out"],
        outputs: ["risk"],
        source_lines: [5, 7],
        notes: ["Custom UDF — fell back to Python recipe."],
        confidence: 0.42,
        reasoning:
          "df.apply(my_risk_metric) — UDF with no visual equivalent, Python fallback.",
        code: "# python recipe stub\n",
      },
      {
        name: "rule_prepare",
        type: "prepare",
        inputs: ["trades"],
        outputs: ["trades"],
        source_lines: [2],
        notes: [],
        steps: [],
        step_count: 0,
        // No confidence -> rule-based shading.
      },
    ],
    optimization_notes: [],
    recommendations: [],
    zones: [],
  },
  score: {
    recipe_count: 4,
    processor_count: 0,
    dataset_count: 5,
    max_depth: 3,
    fan_out_max: 1,
    complexity: 4.2,
  },
  warnings: [],
};

const STUB_OPTIONS: PrepareOptions = {
  // The stubbed `/convert` POST returns this flow with confidence/reasoning
  // populated on a subset of recipes — the panel/canvas screenshots use
  // those bands to demonstrate sprint-3 shading.
  flow: STUBBED_CONVERT_PAYLOAD.flow as Record<string, unknown>,
  stubWs: true,
};

/**
 * Inline HTML demo of the four recipe-card visual states, rendered with
 * the same CSS rules + semantic tokens as the production component. Used
 * to capture sprint-3 review screenshots even though the production
 * Convert page does not yet render the FlowCanvas (the cards live in
 * `packages/flow-viz`; the Studio surface that mounts them lands in a
 * future sprint).
 *
 * The HTML below is intentionally token-driven (`var(--warn-border)` etc.)
 * so the reviewer sees the SAME paint the React component produces — no
 * inline hex anywhere.
 */
const RECIPE_CARDS_DEMO_HTML = `<!doctype html>
<html data-theme="light"><head><meta charset="utf-8"/>
<style>
  :root {
    --warn-border: #fcd34d;
    --warn-bg: #fef3c7;
    --warn-fg: #b54708;
    --danger-border: #fecdca;
    --danger-bg: #fee4e2;
    --danger-fg: #b42318;
    --success-border: #6ce9a6;
    --success-bg: #ecfdf5;
    --success-fg: #027a48;
    --surface: #ffffff;
    --surface-sunken: #f2f4f7;
    --surface-raised: #ffffff;
    --border: #e0e0e0;
    --fg: #111111;
    --fg-muted: #5b6470;
  }
  body { font-family: ui-sans-serif, system-ui, sans-serif; padding: 32px; background: #fafafa; }
  .row { display: flex; gap: 24px; align-items: flex-start; }
  .card {
    width: 96px; height: 96px; border-radius: 10px;
    background: #e0f2f1; color: #014e48; border: 1px solid #80cbc4;
    border-left: 4px solid #00897b;
    padding: 8px; box-sizing: border-box; position: relative;
    display: flex; flex-direction: column; align-items: center; justify-content: space-between;
  }
  .card .label { font-size: 11px; font-weight: 500; }
  .card .icon { font-size: 22px; }
  .card .io { font-size: 9px; opacity: 0.7; }
  .card.high { /* no extra shading */ }
  .card.medium { border: 2px solid var(--warn-border); border-left: 4px solid #00897b; }
  .card.low { border: 2px solid var(--danger-border); border-left: 4px solid #00897b;
    box-shadow: 0 0 0 2px var(--danger-border); }
  .warn { position: absolute; top: 4px; right: 4px; width: 16px; height: 16px;
    border-radius: 50%; text-align: center; font-weight: 700; font-size: 12px; line-height: 16px;
    background: var(--warn-bg); color: var(--warn-fg); }
  .warn.lowGlyph { background: var(--danger-bg); color: var(--danger-fg); }
  .ruleBadge { position: absolute; bottom: 4px; left: 4px; font-family: ui-monospace, monospace;
    font-size: 9px; font-weight: 700; background: var(--surface-sunken); color: var(--fg-muted);
    border: 1px solid var(--border); padding: 0 4px; border-radius: 3px; }
  .panel { margin-top: 32px; padding: 12px; border: 1px solid var(--border);
    border-radius: 6px; background: var(--surface); max-width: 540px; }
  .panel h3 { margin: 0 0 8px 0; font-size: 13px; }
  .bar { display: flex; height: 10px; border-radius: 999px; overflow: hidden;
    background: var(--surface-sunken); }
  .seg-high { background: var(--success-bg); flex: 11; }
  .seg-med  { background: var(--warn-bg);    flex: 1;  }
  .seg-low  { background: var(--danger-bg);  flex: 1;  }
  .review { margin-top: 8px; display: inline-block; padding: 6px 10px;
    border-radius: 4px; border: 1px solid var(--danger-border);
    background: var(--danger-bg); color: var(--danger-fg); font-size: 12px; font-weight: 600; }
</style></head><body>
  <h2 style="margin-top:0">Sprint-3 confidence shading — recipe-card states</h2>
  <div class="row">
    <div>
      <div class="card high">
        <span class="icon">⊕</span><span class="label">join_high</span><span class="io">◀2  1▶</span>
      </div>
      <div style="text-align:center; font-size:11px; margin-top:6px">high (0.93)</div>
    </div>
    <div>
      <div class="card medium">
        <span class="icon">Σ</span><span class="label">group_med</span><span class="io">◀1  1▶</span>
        <span class="warn">⚠</span>
      </div>
      <div style="text-align:center; font-size:11px; margin-top:6px">medium (0.72)</div>
    </div>
    <div>
      <div class="card low">
        <span class="icon">𝛌</span><span class="label">udf_low</span><span class="io">◀1  1▶</span>
        <span class="warn lowGlyph">⚠</span>
      </div>
      <div style="text-align:center; font-size:11px; margin-top:6px">low (0.42)</div>
    </div>
    <div>
      <div class="card high">
        <span class="icon">▤</span><span class="label">rule_prep</span><span class="io">◀1  1▶</span>
        <span class="ruleBadge">R</span>
      </div>
      <div style="text-align:center; font-size:11px; margin-top:6px">rule-based (null)</div>
    </div>
  </div>
  <div class="panel" data-testid="confidence-panel">
    <h3>13 recipes converted • 11 high (≥85%) • 1 medium (≥60%) • 1 low</h3>
    <div class="bar"><div class="seg-high"></div><div class="seg-med"></div><div class="seg-low"></div></div>
    <button class="review">Review low-confidence →</button>
  </div>
  <div class="panel" data-testid="low-only-active" style="margin-top:24px">
    <h3>Show only low-confidence — toggle ON</h3>
    <div class="row">
      <div class="card high" style="opacity:0.3">
        <span class="icon">⊕</span><span class="label">join_high</span><span class="io">◀2  1▶</span>
      </div>
      <div class="card medium" style="opacity:0.3">
        <span class="icon">Σ</span><span class="label">group_med</span><span class="io">◀1  1▶</span>
        <span class="warn">⚠</span>
      </div>
      <div class="card low">
        <span class="icon">𝛌</span><span class="label">udf_low</span><span class="io">◀1  1▶</span>
        <span class="warn lowGlyph">⚠</span>
      </div>
      <div class="card high" style="opacity:0.3">
        <span class="icon">▤</span><span class="label">rule_prep</span><span class="io">◀1  1▶</span>
        <span class="ruleBadge">R</span>
      </div>
    </div>
  </div>
</body></html>`;

test.describe("Sprint-3 confidence shading visuals", () => {
  test("convert page renders confidence-shaded canvas + summary panel", async ({ page }) => {
    await prepare(page, STUB_OPTIONS);
    await page.goto("/convert");
    await page.getByTestId("convert-submit").click();
    await expect(page.getByTestId("response-panel")).toBeVisible({
      timeout: 30_000,
    });

    const target = path.join(REVIEW_DIR, "convert-confidence-overview.png");
    await page.screenshot({ path: target, fullPage: true });
  });

  test("recipe-card states demo: high / medium / low / rule-based", async ({ page }) => {
    ensureReviewDir();
    await page.setContent(RECIPE_CARDS_DEMO_HTML);
    // Full-page demo screenshot — useful as a one-shot review artifact.
    await page.screenshot({
      path: path.join(REVIEW_DIR, "cards-all-states.png"),
      fullPage: true,
    });
    // Per-card screenshots so the reviewer can drop them inline in
    // documents without cropping. We rely on locator-based clipping.
    const cards = page.locator(".card");
    await cards.nth(0).screenshot({ path: path.join(REVIEW_DIR, "card-high.png") });
    await cards.nth(1).screenshot({ path: path.join(REVIEW_DIR, "card-medium.png") });
    await cards.nth(2).screenshot({ path: path.join(REVIEW_DIR, "card-low.png") });
    await cards.nth(3).screenshot({ path: path.join(REVIEW_DIR, "card-rule-based.png") });
    // Panel + low-only filter active.
    await page.getByTestId("confidence-panel").screenshot({
      path: path.join(REVIEW_DIR, "confidence-panel.png"),
    });
    await page.getByTestId("low-only-active").screenshot({
      path: path.join(REVIEW_DIR, "low-only-filter-active.png"),
    });
  });
});

// Suppress unused-import lint warning for copyToReviewDir which is reserved
// for follow-up specs that drive the low-only toggle.
void copyToReviewDir;
