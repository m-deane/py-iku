/**
 * catalog.spec.ts — visits /catalog, asserts 37 recipe cards on the recipes
 * tab, switches to processors, types in the search box and confirms the list
 * shrinks, then clicks a card to open the detail drawer.
 */
import { test, expect } from "@playwright/test";
import { stubApi } from "./_fixtures";

test.describe("Catalog page", () => {
  test.beforeEach(async ({ page }) => {
    await stubApi(page);
  });

  test("renders 37 recipe cards, supports search + drawer on processors tab", async ({
    page,
  }) => {
    await page.goto("/catalog");

    // Recipe cards — exact 37 from the catalog stub.
    await expect(page.getByTestId("recipes-list")).toBeVisible({ timeout: 15_000 });
    const recipeCards = page.locator('[data-testid^="recipe-card-"]');
    await expect(recipeCards).toHaveCount(37);

    // Switch to processors tab.
    await page.getByTestId("catalog-tab-processors").click();
    await expect(page.getByTestId("processors-list")).toBeVisible();

    // Pre-search count.
    const processorCards = page.locator('[data-testid^="processor-card-"]');
    const initialCount = await processorCards.count();
    expect(initialCount).toBeGreaterThan(1);

    // Type in the search box → the visible list should shrink.
    const search = page.getByTestId("processors-search");
    await search.fill("formula");
    await expect.poll(async () => processorCards.count(), { timeout: 5_000 }).toBeLessThan(
      initialCount,
    );
    // Specifically the FORMULA card must remain.
    await expect(page.getByTestId("processor-card-FORMULA")).toBeVisible();

    // Click the FORMULA card → drawer opens with detail.
    await page.getByTestId("processor-card-FORMULA").click();
    const drawer = page.getByTestId("catalog-detail-drawer");
    await expect(drawer).toBeVisible();
    await expect(page.getByTestId("catalog-processor-detail")).toBeVisible();
    await expect(page.getByTestId("processor-detail-type")).toContainText("FORMULA");

    // Close the drawer.
    await page.getByTestId("catalog-detail-close").click();
    await expect(drawer).not.toBeVisible();
  });
});
