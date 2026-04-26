import { test, expect } from "@playwright/test";
import { axe, prepareA11y } from "./_helpers";

test("convert page has no axe violations (idle)", async ({ page }) => {
  await prepareA11y(page);
  await page.goto("/convert");
  // Wait for the editor container so the layout is stable.
  await page.getByTestId("monaco-editor").waitFor({ state: "visible" });
  const results = await axe(page).analyze();
  expect(results.violations, JSON.stringify(results.violations, null, 2)).toEqual([]);
});
