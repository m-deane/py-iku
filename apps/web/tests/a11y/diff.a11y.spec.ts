import { test, expect } from "@playwright/test";
import { axe, prepareA11y } from "./_helpers";

test("diff page has no axe violations (empty state)", async ({ page }) => {
  await prepareA11y(page);
  await page.goto("/diff");
  await page.getByTestId("compare-button").waitFor({ state: "visible" });
  const results = await axe(page).analyze();
  expect(results.violations, JSON.stringify(results.violations, null, 2)).toEqual([]);
});
