import { test, expect } from "@playwright/test";
import { prepare } from "./_helpers";

test("diff page after compare with stubbed flows", async ({ page }) => {
  await prepare(page);
  // Block the WS so the diff page falls back to REST stubs for both calls.
  await page.route("**/convert/stream", (route) => route.abort("failed"));

  // Seed currentCode by navigating through the convert page first.
  await page.goto("/convert");
  await page.getByTestId("snippet-picker-trigger").click();
  await page.getByTestId("snippet-picker-first-item").click();

  await page.goto("/diff");
  await page.getByTestId("compare-button").click();
  await expect(page.getByTestId("diff-list")).toBeVisible({ timeout: 15_000 });
  await expect(page).toHaveScreenshot("diff.png", { maxDiffPixelRatio: 0.02 });
});
