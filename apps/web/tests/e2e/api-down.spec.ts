/**
 * API-down resilience test.
 *
 * Routes the API calls to a non-existent port so network errors fire
 * immediately without needing to mock fetch. Asserts the UI surfaces
 * a sonner toast / error panel and does not crash.
 */
import { test, expect } from "@playwright/test";

test("Convert shows network error toast when API is unreachable", async ({ page, context }) => {
  // Block all requests to the default API origin so we get a network error.
  await context.route("**/api/convert", (route) => route.abort("failed"));
  // Also block the direct port in case the app calls it without the proxy.
  await context.route("http://localhost:8000/**", (route) => route.abort("failed"));

  await page.goto("/convert");

  // Wait for editor container (page must load even without API)
  await expect(page.getByTestId("monaco-editor")).toBeVisible({ timeout: 10_000 });

  // Click Convert — will attempt the (blocked) API call
  const convertBtn = page.getByTestId("convert-submit");
  await expect(convertBtn).toBeVisible();
  await convertBtn.click();

  // The error status panel should appear (no crash)
  const errorPanel = page.getByTestId("status-error");
  await expect(errorPanel).toBeVisible({ timeout: 15_000 });

  // Should mention a network/unexpected error (not a 5xx with body)
  await expect(errorPanel).toHaveText(/network error|unexpected error/i);

  // Page must still be functional — the Convert button should be re-enabled
  await expect(convertBtn).not.toBeDisabled({ timeout: 5_000 });
});
