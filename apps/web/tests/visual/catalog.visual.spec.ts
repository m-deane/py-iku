import { test, expect } from "@playwright/test";
import { prepare } from "./_helpers";

test("catalog recipes tab baseline", async ({ page }) => {
  await prepare(page);
  await page.goto("/catalog");
  await expect(page.getByTestId("recipes-list")).toBeVisible();
  // Wait for all 37 cards to render so the grid has stabilised.
  await expect(page.locator('[data-testid^="recipe-card-"]')).toHaveCount(37);
  await expect(page).toHaveScreenshot("catalog.png", { maxDiffPixelRatio: 0.02 });
});
