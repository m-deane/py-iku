/**
 * share.spec.ts — convert a flow, click Share, then visit the share URL in
 * a fresh context and assert the read-only viewer renders with editing
 * controls disabled.
 *
 * The share URL is captured via the stubbed /flows/{id}/share endpoint which
 * returns a deterministic token. We navigate the same page object to the
 * share URL afterwards (a fresh context isn't required for hermetic stubs).
 */
import { test, expect } from "@playwright/test";
import { stubApi, stubWebSocketConvert, STUB_SHARE_TOKEN } from "./_fixtures";

test.describe("Share flow", () => {
  test.beforeEach(async ({ page, context }) => {
    await stubApi(page);
    await stubWebSocketConvert(page);
    // Grant clipboard read/write permissions so the Share button doesn't
    // bail on `navigator.clipboard.writeText`.
    await context.grantPermissions(["clipboard-read", "clipboard-write"]).catch(() => {
      /* permissions API not available on webkit — fall through */
    });
  });

  test("Convert → Share → /share/:token renders read-only flow", async ({ page }) => {
    await page.goto("/convert");

    // Trigger a convert via the snippet picker → first snippet → Convert.
    await page.getByTestId("snippet-picker-trigger").click();
    await page.getByTestId("snippet-picker-first-item").click();
    const convertBtn = page.getByTestId("convert-submit");
    await convertBtn.click();
    await expect(page.getByTestId("response-panel")).toBeVisible({ timeout: 30_000 });

    // Click "Share this flow".
    const shareBtn = page.getByTestId("share-flow-button");
    await expect(shareBtn).toBeVisible();
    await shareBtn.click();

    // Sonner toast shows up with the URL — wait for the success toast text.
    // The toast container has role="status" / class "sonner-toast"; we
    // assert via the toast text content rather than internal selectors.
    await expect(page.getByText(/share link copied|sharing/i).first()).toBeVisible({
      timeout: 10_000,
    });

    // Visit the share URL — token comes from the stub.
    await page.goto(`/share/${STUB_SHARE_TOKEN}`);
    await expect(page.getByTestId("share-page")).toBeVisible();
    await expect(page.getByTestId("share-flow")).toBeVisible({ timeout: 10_000 });

    // Editing must be disabled.
    const editingDisabled = page.getByTestId("share-edit-disabled");
    await expect(editingDisabled).toBeVisible();
    await expect(editingDisabled).toBeDisabled();
  });
});
