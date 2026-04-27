import { test, expect } from "@playwright/test";
import { prepare } from "./_helpers";

test("audit empty-state baseline", async ({ page }) => {
  await prepare(page, { withAuditEvent: false });
  await page.goto("/audit");
  await expect(page.getByTestId("audit-table")).toBeVisible();
  await expect(page.getByTestId("audit-empty")).toBeVisible();
  await expect(page).toHaveScreenshot("audit-empty.png", { maxDiffPixelRatio: 0.02 });
});

test("audit with one event baseline", async ({ page }) => {
  await prepare(page, { withAuditEvent: true });
  await page.goto("/audit");
  await expect(page.getByTestId("audit-table")).toBeVisible();
  await expect(page.getByTestId("audit-row-0")).toBeVisible();
  await expect(page).toHaveScreenshot("audit-event.png", { maxDiffPixelRatio: 0.02 });
});
