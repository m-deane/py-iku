/**
 * convert.spec.ts — paste a snippet via the picker, run a conversion, assert
 * the response panel renders with the expected nodes and that the export
 * buttons appear.
 *
 * Hermetic: all network + WebSocket traffic is intercepted by the fixtures.
 */
import { test, expect } from "@playwright/test";
import { stubApi, stubFlowDict, stubWebSocketConvert } from "./_fixtures";

test.describe("Convert page — happy path", () => {
  test.beforeEach(async ({ page }) => {
    await stubApi(page);
    await stubWebSocketConvert(page);
  });

  test("paste snippet via picker, convert, and see flow nodes + export buttons", async ({
    page,
  }) => {
    await page.goto("/convert");

    // Open the snippet picker and select the first entry.
    await page.getByTestId("snippet-picker-trigger").click();
    const firstItem = page.getByTestId("snippet-picker-first-item");
    await expect(firstItem).toBeVisible();
    await firstItem.click();

    // Click Convert (rule-mode default).
    const convertBtn = page.getByTestId("convert-submit");
    await expect(convertBtn).toBeVisible();
    await expect(convertBtn).not.toBeDisabled({ timeout: 10_000 });
    await convertBtn.click();

    // The response panel must render with the stubbed flow.
    const responsePanel = page.getByTestId("response-panel");
    await expect(responsePanel).toBeVisible({ timeout: 30_000 });

    // The flow has at least one recipe node — its name appears in the JSON view.
    const stub = stubFlowDict();
    const recipeName = (stub.recipes as Array<{ name: string }>)[0].name;
    await expect(responsePanel).toContainText(recipeName);

    // Export buttons appear next to the response.
    await expect(page.getByTestId("export-buttons")).toBeVisible();
    await expect(page.getByTestId("export-zip")).toBeVisible();

    // Score badge appears with a numeric complexity.
    await expect(page.getByTestId("score-badge")).toContainText(/complexity:\s*\d/);
  });
});
