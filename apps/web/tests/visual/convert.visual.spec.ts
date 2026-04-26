import { test, expect } from "@playwright/test";
import { prepare } from "./_helpers";

test("convert page after a deterministic conversion", async ({ page }) => {
  await prepare(page);
  await page.goto("/convert");
  await page.getByTestId("snippet-picker-trigger").click();
  await page.getByTestId("snippet-picker-first-item").click();
  await page.getByTestId("convert-submit").click();
  await expect(page.getByTestId("response-panel")).toBeVisible({ timeout: 30_000 });
  // Wait for the score badge so the layout has stabilised.
  await expect(page.getByTestId("score-badge")).toBeVisible();
  await expect(page).toHaveScreenshot("convert.png", { maxDiffPixelRatio: 0.02 });
});
