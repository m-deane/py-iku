/**
 * wave2-flows.spec.ts — DSS-fidelity visual baselines for the post-Sprint-6
 * Studio canvas across 12 representative real-world flows.
 *
 * Each fixture mirrors a textbook example (or, for the synthetic wide/deep
 * cases, an extension of the V5 retail running example). The flow is
 * injected through the WebSocket-stub fixture so the Convert page renders
 * its inline canvas without hitting the FastAPI backend; the test then
 * screenshots the Convert response panel only — the canvas plus the score
 * cards above it — so the baseline doesn't drift on unrelated chrome.
 *
 * Theme axis = {light, dark} → 12 × 2 = 24 baselines.
 *
 * Update workflow:
 *   pnpm --filter apps-web exec playwright test --project=visual \
 *     tests/visual/wave2-flows.spec.ts --update-snapshots
 */
import { expect, test, type Page } from "@playwright/test";
import { prepare } from "./_helpers";
import { stubWebSocketConvert } from "../e2e/_fixtures";

type Theme = "light" | "dark";

interface DataikuRecipeStub {
  name: string;
  type: string;
  inputs: string[];
  outputs: string[];
  [key: string]: unknown;
}

interface DataikuDatasetStub {
  name: string;
  type: "input" | "intermediate" | "output";
  connection_type: string;
  schema?: Array<{ name: string; type?: string }>;
}

interface FlowFixture {
  id: string;
  description: string;
  flow: {
    flow_name: string;
    total_recipes: number;
    total_datasets: number;
    datasets: DataikuDatasetStub[];
    recipes: DataikuRecipeStub[];
  };
}

// ---------------------------------------------------------------------------
// Fixtures — DataikuFlow (recipes[] + datasets[]) shape, matching what the
// FastAPI backend emits. The Convert page's `dataikuFlowToMinimal` adapter
// converts these to the MinimalFlow shape FlowCanvas consumes.
// ---------------------------------------------------------------------------

function ds(
  name: string,
  type: DataikuDatasetStub["type"],
  connectionType: string,
): DataikuDatasetStub {
  return { name, type, connection_type: connectionType, schema: [] };
}

function recipe(
  name: string,
  type: string,
  inputs: string[],
  outputs: string[],
  extras: Record<string, unknown> = {},
): DataikuRecipeStub {
  return { name, type, inputs, outputs, ...extras };
}

const FIXTURES: FlowFixture[] = [
  {
    id: "v1-retail-smallest",
    description: "1 PREPARE + 2 datasets",
    flow: {
      flow_name: "v1_retail",
      total_recipes: 1,
      total_datasets: 2,
      datasets: [
        ds("customers", "input", "Filesystem"),
        ds("customers_clean", "output", "Filesystem"),
      ],
      recipes: [recipe("prepare_customers", "prepare", ["customers"], ["customers_clean"])],
    },
  },
  {
    id: "v2-retail-prepare-join",
    description: "PREPARE + JOIN + 3 datasets",
    flow: {
      flow_name: "v2_retail",
      total_recipes: 2,
      total_datasets: 4,
      datasets: [
        ds("customers", "input", "Filesystem"),
        ds("orders", "input", "PostgreSQL"),
        ds("customers_clean", "intermediate", "Filesystem"),
        ds("enriched", "output", "Filesystem"),
      ],
      recipes: [
        recipe("prepare_customers", "prepare", ["customers"], ["customers_clean"]),
        recipe("join_orders", "join", ["customers_clean", "orders"], ["enriched"]),
      ],
    },
  },
  {
    id: "v5-retail-full",
    description: "PREPARE + JOIN + GROUPING + SORT + SPLIT pipeline",
    flow: {
      flow_name: "v5_retail",
      total_recipes: 5,
      total_datasets: 7,
      datasets: [
        ds("customers", "input", "Filesystem"),
        ds("orders", "input", "PostgreSQL"),
        ds("customers_clean", "intermediate", "Filesystem"),
        ds("enriched", "intermediate", "Filesystem"),
        ds("region_totals", "intermediate", "Filesystem"),
        ds("top_regions", "output", "Snowflake"),
        ds("low_volume", "output", "Filesystem"),
      ],
      recipes: [
        recipe("prepare_customers", "prepare", ["customers"], ["customers_clean"]),
        recipe("join_orders", "join", ["customers_clean", "orders"], ["enriched"]),
        recipe("group_by_region", "grouping", ["enriched"], ["region_totals"]),
        recipe("sort_top_regions", "sort", ["region_totals"], ["top_regions"]),
        recipe("split_volume", "split", ["region_totals"], ["top_regions", "low_volume"]),
      ],
    },
  },
  {
    id: "trade-ingestion-validation",
    description: "PREPARE chain + PIVOT",
    flow: {
      flow_name: "trade_ingestion",
      total_recipes: 4,
      total_datasets: 5,
      datasets: [
        ds("trades", "input", "Filesystem"),
        ds("trades_prepared", "intermediate", "Filesystem"),
        ds("trades_dated", "intermediate", "Filesystem"),
        ds("trades_filtered", "intermediate", "Filesystem"),
        ds("trades_pivoted", "output", "Filesystem"),
      ],
      recipes: [
        recipe("prepare_dropna", "prepare", ["trades"], ["trades_prepared"]),
        recipe("prepare_dates", "prepare", ["trades_prepared"], ["trades_dated"]),
        recipe("split_filter", "split", ["trades_dated"], ["trades_filtered"]),
        recipe("pivot_exposure", "pivot", ["trades_filtered"], ["trades_pivoted"]),
      ],
    },
  },
  {
    id: "trade-dedup-multi-system",
    description: "STACK + DISTINCT + SORT (3 inputs)",
    flow: {
      flow_name: "trade_dedup",
      total_recipes: 3,
      total_datasets: 6,
      datasets: [
        ds("trades_a", "input", "PostgreSQL"),
        ds("trades_b", "input", "PostgreSQL"),
        ds("trades_c", "input", "S3"),
        ds("stacked", "intermediate", "Filesystem"),
        ds("dedup", "intermediate", "Filesystem"),
        ds("sorted", "output", "Snowflake"),
      ],
      recipes: [
        recipe("stack_systems", "stack", ["trades_a", "trades_b", "trades_c"], ["stacked"]),
        recipe("dedup_trades", "distinct", ["stacked"], ["dedup"]),
        recipe("sort_trades", "sort", ["dedup"], ["sorted"]),
      ],
    },
  },
  {
    id: "book-mtm-eod",
    description: "filter + JOIN + GROUPING + WINDOW + TOP_N",
    flow: {
      flow_name: "book_mtm_eod",
      total_recipes: 5,
      total_datasets: 7,
      datasets: [
        ds("positions", "input", "PostgreSQL"),
        ds("prices", "input", "Snowflake"),
        ds("positions_filtered", "intermediate", "PostgreSQL"),
        ds("positions_priced", "intermediate", "PostgreSQL"),
        ds("daily_mtm", "intermediate", "PostgreSQL"),
        ds("rolling_mtm", "intermediate", "PostgreSQL"),
        ds("top_books", "output", "S3"),
      ],
      recipes: [
        recipe("filter_open", "split", ["positions"], ["positions_filtered"]),
        recipe("join_prices", "join", ["positions_filtered", "prices"], ["positions_priced"]),
        recipe("group_by_book", "grouping", ["positions_priced"], ["daily_mtm"]),
        recipe("rolling_30d", "window", ["daily_mtm"], ["rolling_mtm"], {
          partition_columns: ["book_id"],
          order_by: ["business_date"],
        }),
        recipe("top_10_books", "topn", ["rolling_mtm"], ["top_books"]),
      ],
    },
  },
  {
    id: "forward-curve-scd",
    description: "consolidating ~cond SPLIT — single recipe with 2 outputs",
    flow: {
      flow_name: "forward_curve_scd",
      total_recipes: 1,
      total_datasets: 3,
      datasets: [
        ds("curve_history", "input", "Filesystem"),
        ds("curves_current", "output", "Filesystem"),
        ds("curves_archive", "output", "Filesystem"),
      ],
      recipes: [
        recipe("split_scd", "split", ["curve_history"], ["curves_current", "curves_archive"]),
      ],
    },
  },
  {
    id: "counterparty-features",
    description: "long PREPARE chain (8+ steps)",
    flow: {
      flow_name: "counterparty_features",
      total_recipes: 8,
      total_datasets: 9,
      datasets: [
        ds("cpty_raw", "input", "PostgreSQL"),
        ds("cpty_dropna", "intermediate", "PostgreSQL"),
        ds("cpty_typed", "intermediate", "PostgreSQL"),
        ds("cpty_lower", "intermediate", "PostgreSQL"),
        ds("cpty_renamed", "intermediate", "PostgreSQL"),
        ds("cpty_clipped", "intermediate", "PostgreSQL"),
        ds("cpty_logged", "intermediate", "PostgreSQL"),
        ds("cpty_normed", "intermediate", "PostgreSQL"),
        ds("cpty_features", "output", "Snowflake"),
      ],
      recipes: [
        recipe("prep_dropna", "prepare", ["cpty_raw"], ["cpty_dropna"]),
        recipe("prep_typing", "prepare", ["cpty_dropna"], ["cpty_typed"]),
        recipe("prep_lower", "prepare", ["cpty_typed"], ["cpty_lower"]),
        recipe("prep_rename", "prepare", ["cpty_lower"], ["cpty_renamed"]),
        recipe("prep_clip", "prepare", ["cpty_renamed"], ["cpty_clipped"]),
        recipe("prep_log", "prepare", ["cpty_clipped"], ["cpty_logged"]),
        recipe("prep_normalize", "prepare", ["cpty_logged"], ["cpty_normed"]),
        recipe("prep_finalize", "prepare", ["cpty_normed"], ["cpty_features"]),
      ],
    },
  },
  {
    id: "pjm-hub-locational-analysis",
    description: "JOIN + GREL + GROUPING",
    flow: {
      flow_name: "pjm_hub_locational",
      total_recipes: 3,
      total_datasets: 5,
      datasets: [
        ds("pjm_lmps", "input", "PostgreSQL"),
        ds("pjm_hubs", "input", "PostgreSQL"),
        ds("hub_lmps", "intermediate", "PostgreSQL"),
        ds("hub_lmps_basis", "intermediate", "PostgreSQL"),
        ds("basis_summary", "output", "S3"),
      ],
      recipes: [
        recipe("join_hub_lmps", "join", ["pjm_lmps", "pjm_hubs"], ["hub_lmps"]),
        recipe("grel_basis", "prepare", ["hub_lmps"], ["hub_lmps_basis"]),
        recipe("group_basis", "grouping", ["hub_lmps_basis"], ["basis_summary"]),
      ],
    },
  },
  {
    id: "pjm-lmp-tick-analytics",
    description: "WINDOW with partition_columns",
    flow: {
      flow_name: "pjm_lmp_ticks",
      total_recipes: 2,
      total_datasets: 3,
      datasets: [
        ds("pjm_ticks", "input", "BigQuery"),
        ds("pjm_ranked", "intermediate", "BigQuery"),
        ds("pjm_top", "output", "S3"),
      ],
      recipes: [
        recipe("window_rank", "window", ["pjm_ticks"], ["pjm_ranked"], {
          partition_columns: ["node_id"],
          order_by: ["timestamp"],
        }),
        recipe("topn_per_node", "topn", ["pjm_ranked"], ["pjm_top"]),
      ],
    },
  },
  {
    id: "wide-flow",
    description: "8 input datasets fed into one STACK — horizontal density stress",
    flow: {
      flow_name: "wide_stress",
      total_recipes: 1,
      total_datasets: 9,
      datasets: [
        ds("region_a", "input", "S3"),
        ds("region_b", "input", "S3"),
        ds("region_c", "input", "PostgreSQL"),
        ds("region_d", "input", "Snowflake"),
        ds("region_e", "input", "BigQuery"),
        ds("region_f", "input", "MySQL"),
        ds("region_g", "input", "Filesystem"),
        ds("region_h", "input", "Redshift"),
        ds("all_regions", "output", "Snowflake"),
      ],
      recipes: [
        recipe(
          "stack_regions",
          "stack",
          [
            "region_a",
            "region_b",
            "region_c",
            "region_d",
            "region_e",
            "region_f",
            "region_g",
            "region_h",
          ],
          ["all_regions"],
        ),
      ],
    },
  },
  {
    id: "deep-flow",
    description: "12-recipe linear chain — vertical depth stress",
    flow: (() => {
      const datasets: DataikuDatasetStub[] = [ds("step_0", "input", "Filesystem")];
      const recipes: DataikuRecipeStub[] = [];
      for (let i = 1; i <= 12; i += 1) {
        const isLast = i === 12;
        datasets.push(
          ds(
            `step_${i}`,
            isLast ? "output" : "intermediate",
            isLast ? "Snowflake" : "Filesystem",
          ),
        );
        const types = ["prepare", "grouping", "join", "sort", "distinct"];
        const t = types[(i - 1) % types.length];
        recipes.push(recipe(`r_${i}_${t}`, t, [`step_${i - 1}`], [`step_${i}`]));
      }
      return {
        flow_name: "deep_stress",
        total_recipes: 12,
        total_datasets: 13,
        datasets,
        recipes,
      };
    })(),
  },
];

const THEMES: Theme[] = ["light", "dark"];

async function pinTheme(page: Page, theme: Theme): Promise<void> {
  await page.addInitScript((t: Theme) => {
    document.documentElement.setAttribute("data-theme", t);
    try {
      window.localStorage.setItem("py-iku-theme", t);
    } catch {
      /* ignore */
    }
  }, theme);
}

test.describe("Wave-2 DSS canvas — 12-flow stress matrix", () => {
  for (const fixture of FIXTURES) {
    for (const theme of THEMES) {
      test(`${fixture.id} (${theme})`, async ({ page }) => {
        await pinTheme(page, theme);
        // Stub the WS so the convert click resolves to our fixture.
        await prepare(page, { stubWs: false });
        await stubWebSocketConvert(page, fixture.flow);

        await page.goto("/convert");
        // Type just enough Python so the Convert button activates.
        const editor = page.getByRole("textbox", { name: /Python code/i });
        await editor.fill(`# ${fixture.description}\nimport pandas as pd\n`);

        await page.getByTestId("convert-submit").click();
        await page.waitForSelector("[data-testid=\"convert-canvas\"]", {
          timeout: 8_000,
        });
        // Let ELK + double-rAF fitView settle.
        await page.waitForTimeout(500);

        const canvas = page.getByTestId("convert-canvas");
        await expect(canvas).toHaveScreenshot(
          `wave2-${fixture.id}-${theme}.png`,
          { maxDiffPixelRatio: 0.03 },
        );
      });
    }
  }
});
