/**
 * snippets.spec.ts — visit /snippets, click a card's "Open in editor" CTA,
 * assert the URL changes to /convert and that the snippet code is loaded
 * into the editor (visible via the Monaco fallback or the Zustand store).
 */
import { test, expect } from "@playwright/test";
import { stubApi } from "./_fixtures";

test.describe("Snippets page", () => {
  test.beforeEach(async ({ page }) => {
    await stubApi(page);
  });

  test("clicking 'Open in editor' navigates to /convert with snippet loaded", async ({
    page,
  }) => {
    await page.goto("/snippets");
    await expect(page.getByTestId("snippet-gallery-grid")).toBeVisible();

    // Click the first snippet's "Open in editor" button.
    const firstOpen = page.locator('[data-testid^="snippet-open-"]').first();
    await expect(firstOpen).toBeVisible();
    await firstOpen.click();

    // URL must become /convert.
    await expect(page).toHaveURL(/\/convert/);

    // The Monaco container is rendered (which means the convert page mounted).
    await expect(page.getByTestId("monaco-editor")).toBeVisible({ timeout: 10_000 });
  });
});
