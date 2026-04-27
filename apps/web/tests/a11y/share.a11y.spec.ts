import { test, expect } from "@playwright/test";
import { axe, prepareA11y } from "./_helpers";
import { STUB_SHARE_TOKEN } from "../e2e/_fixtures";

test("share viewer has no axe violations", async ({ page }) => {
  await prepareA11y(page);
  await page.goto(`/share/${STUB_SHARE_TOKEN}`);
  await page.getByTestId("share-flow").waitFor({ state: "visible", timeout: 10_000 });
  const results = await axe(page).analyze();
  expect(results.violations, JSON.stringify(results.violations, null, 2)).toEqual([]);
});
