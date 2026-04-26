/**
 * audit.spec.ts — perform a save+share, then visit /audit and assert at
 * least 2 events are visible. Hermetic — uses fixtures.
 */
import { test, expect } from "@playwright/test";
import { stubApi, stubWebSocketConvert } from "./_fixtures";

test.describe("Audit log", () => {
  test.beforeEach(async ({ page }) => {
    await stubApi(page, { withAuditEvent: true });
    await stubWebSocketConvert(page);
  });

  test("after save + share, /audit renders >= 2 events", async ({ page }) => {
    // Drive the save + share flow.
    await page.goto("/convert");
    await page.getByTestId("snippet-picker-trigger").click();
    await page.getByTestId("snippet-picker-first-item").click();
    await page.getByTestId("convert-submit").click();
    await expect(page.getByTestId("response-panel")).toBeVisible({ timeout: 30_000 });
    await page.getByTestId("share-flow-button").click();
    // Wait briefly for the share request to complete (fire-and-forget toast).
    await page.waitForTimeout(500);

    // Now visit /audit. The fixture returns 2 events.
    await page.goto("/audit");
    await expect(page.getByTestId("audit-table")).toBeVisible();

    const rows = page.locator('[data-testid^="audit-row-"]');
    await expect(rows).toHaveCount(2);
    await expect(page.getByTestId("audit-row-0")).toBeVisible();
    await expect(page.getByTestId("audit-row-1")).toBeVisible();
  });
});
