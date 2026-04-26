import { test, expect } from "@playwright/test";
import { prepare } from "./_helpers";

test("snippets gallery baseline", async ({ page }) => {
  await prepare(page);
  await page.goto("/snippets");
  await expect(page.getByTestId("snippet-gallery-grid")).toBeVisible();
  await expect(page).toHaveScreenshot("snippets.png", { maxDiffPixelRatio: 0.02 });
});
