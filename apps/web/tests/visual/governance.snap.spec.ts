/**
 * Sprint-4 governance UI screenshots.
 *
 * Loads the static reference HTML and captures one PNG per feature plus an
 * overview. Output lives in /tmp/py-iku-review/sprint4-after/governance/ so
 * the review tooling can pick them up regardless of where pnpm caches.
 */
import { test } from "@playwright/test";
import path from "node:path";
import fs from "node:fs";

const TARGET_DIR = "/tmp/py-iku-review/sprint4-after/governance";
const HTML_PATH = path.join(TARGET_DIR, "_mock_snapshots.html");
const HTML_URL = `file://${HTML_PATH}`;

test.describe("Sprint-4 governance — reference snapshots", () => {
  test.beforeAll(() => {
    fs.mkdirSync(TARGET_DIR, { recursive: true });
  });

  test("capture reference screenshots", async ({ page }) => {
    await page.setViewportSize({ width: 900, height: 1500 });
    await page.goto(HTML_URL);
    await page.waitForLoadState("domcontentloaded");

    await page.screenshot({
      path: path.join(TARGET_DIR, "00_overview.png"),
      fullPage: true,
    });

    const sections: Array<{ name: string; selector: string }> = [
      {
        name: "01_column_lineage_overlay.png",
        selector: "h2:nth-of-type(1) + .card",
      },
      {
        name: "02_schema_drift_banner.png",
        selector: "h2:nth-of-type(2) + .card",
      },
      {
        name: "03_schema_drift_panel.png",
        selector: "h2:nth-of-type(2) + .card + .card",
      },
      { name: "04_lint_panel.png", selector: "h2:nth-of-type(3) + .card" },
      {
        name: "05_export_integration_test.png",
        selector: "h2:nth-of-type(4) + .card",
      },
    ];
    for (const s of sections) {
      const el = await page.$(s.selector);
      if (!el) throw new Error(`Missing selector ${s.selector}`);
      await el.screenshot({ path: path.join(TARGET_DIR, s.name) });
    }
  });
});
