import { test, expect } from "@playwright/test";
import { axe, prepareA11y } from "./_helpers";

test("audit page has no axe violations (with events)", async ({ page }) => {
  await prepareA11y(page, { withAuditEvent: true });
  await page.goto("/audit");
  await page.getByTestId("audit-table").waitFor({ state: "visible" });
  const results = await axe(page).analyze();
  expect(results.violations, JSON.stringify(results.violations, null, 2)).toEqual([]);
});
