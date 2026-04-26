import { test, expect } from "@playwright/test";
import { axe, prepareA11y } from "./_helpers";

test("catalog page has no axe violations", async ({ page }) => {
  await prepareA11y(page);
  await page.goto("/catalog");
  await page.getByTestId("recipes-list").waitFor({ state: "visible" });
  const results = await axe(page).analyze();
  expect(results.violations, JSON.stringify(results.violations, null, 2)).toEqual([]);
});
