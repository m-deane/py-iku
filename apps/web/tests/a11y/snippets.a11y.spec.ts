import { test, expect } from "@playwright/test";
import { axe, prepareA11y } from "./_helpers";

test("snippets page has no axe violations", async ({ page }) => {
  await prepareA11y(page);
  await page.goto("/snippets");
  await page.getByTestId("snippet-gallery-grid").waitFor({ state: "visible" });
  const results = await axe(page).analyze();
  expect(results.violations, JSON.stringify(results.violations, null, 2)).toEqual([]);
});
