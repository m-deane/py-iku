import { test, expect } from "@playwright/test";
import { axe, prepareA11y } from "./_helpers";

test("home page has no axe violations", async ({ page }) => {
  await prepareA11y(page);
  await page.goto("/");
  const results = await axe(page).analyze();
  expect(results.violations, JSON.stringify(results.violations, null, 2)).toEqual([]);
});
