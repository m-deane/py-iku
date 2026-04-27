/**
 * inspector.spec.ts — convert a flow, click a recipe in the node list to
 * open the inspector, assert recipe fields are shown, then close the
 * inspector and confirm the selection is cleared.
 */
import { test, expect } from "@playwright/test";
import { stubApi, stubFlowDict, stubWebSocketConvert } from "./_fixtures";

test.describe("Node inspector", () => {
  test.beforeEach(async ({ page }) => {
    await stubApi(page);
    await stubWebSocketConvert(page);
  });

  test("opens with recipe fields and closes via the close button", async ({
    page,
  }) => {
    await page.goto("/convert");

    // Trigger convert.
    await page.getByTestId("snippet-picker-trigger").click();
    await page.getByTestId("snippet-picker-first-item").click();
    await page.getByTestId("convert-submit").click();
    await expect(page.getByTestId("response-panel")).toBeVisible({ timeout: 30_000 });

    // Click the first recipe node in the post-convert node list.
    const stub = stubFlowDict();
    const recipeName = (stub.recipes as Array<{ name: string }>)[0].name;
    const nodeBtn = page.getByTestId(`node-list-item-${recipeName}`);
    await expect(nodeBtn).toBeVisible();
    await nodeBtn.click();

    // Inspector renders with the recipe fields.
    const inspector = page.getByTestId("node-inspector");
    await expect(inspector).toBeVisible();
    await expect(page.getByTestId("recipe-inspector")).toBeVisible();
    await expect(page.getByTestId("recipe-type")).toContainText(/grouping/i);

    // Close button clears the selection (inspector unmounts).
    await page.getByTestId("inspector-close").click();
    await expect(inspector).not.toBeVisible();
  });
});
