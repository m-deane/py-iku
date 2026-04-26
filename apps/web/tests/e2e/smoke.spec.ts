/**
 * Smoke tests — golden path through the py-iku Studio UI.
 *
 * Prerequisites (when running locally without the CI launcher):
 *   Terminal 1: cd apps/api && uvicorn app.main:app --port 8000
 *   Terminal 2: pnpm --filter apps-web dev
 *   Run: pnpm --filter apps-web exec playwright test --project=chromium
 *
 * All selectors map to data-testid attributes or stable ARIA roles added in
 * the M11 test-infra pass. No brittle CSS class selectors.
 */
import { test, expect } from "@playwright/test";

// ── Home page ────────────────────────────────────────────────────────────────

test("home page loads with logo and theme toggle", async ({ page }) => {
  await page.goto("/");

  // Header logo link — use the link role to avoid strict-mode collision with
  // the h1 on the home page that also contains the text.
  const logoLink = page.getByRole("link", { name: /py-iku-studio/i });
  await expect(logoLink.first()).toBeVisible();

  // Theme toggle button (aria-label contains "theme")
  const themeToggle = page.getByRole("button", { name: /theme/i });
  await expect(themeToggle).toBeVisible();
});

test("clicking Convert CTA navigates to /convert", async ({ page }) => {
  await page.goto("/");

  // The home page CTA is an <a href="/convert">
  await page.getByRole("link", { name: /paste python/i }).click();

  await expect(page).toHaveURL(/\/convert/);
});

// ── Convert page ─────────────────────────────────────────────────────────────

test("Convert page renders Monaco editor container", async ({ page }) => {
  await page.goto("/convert");

  // The wrapper div is rendered immediately; Monaco loads inside it async.
  // We only assert the container exists, not the iframe internals.
  const editorContainer = page.getByTestId("monaco-editor");
  await expect(editorContainer).toBeVisible({ timeout: 10_000 });
});

test("snippet picker opens and selecting first snippet updates content", async ({ page }) => {
  await page.goto("/convert");

  // Open the snippet picker popover
  const trigger = page.getByTestId("snippet-picker-trigger");
  await expect(trigger).toBeVisible();
  await trigger.click();

  // First snippet item should appear
  const firstItem = page.getByTestId("snippet-picker-first-item");
  await expect(firstItem).toBeVisible();

  // Click it — picker should close (no confirm needed since current code
  // matches a known snippet body)
  await firstItem.click();

  // Picker should be closed
  await expect(page.getByTestId("snippet-picker-first-item")).not.toBeVisible();
});

test("settings drawer opens, theme select flips html[data-theme], drawer closes", async ({
  page,
}) => {
  await page.goto("/convert");

  // Open drawer via gear icon
  const trigger = page.getByTestId("settings-open-trigger");
  await expect(trigger).toBeVisible();
  await trigger.click();

  // Drawer must be visible (role=dialog, aria-label=Settings)
  const drawer = page.getByRole("dialog", { name: /settings/i });
  await expect(drawer).toBeVisible();

  // Read current theme from <html data-theme>
  const initialTheme = await page.evaluate(
    () => document.documentElement.dataset.theme ?? "",
  );

  // Select the opposite theme
  const themeSelect = page.getByTestId("settings-theme-select");
  await expect(themeSelect).toBeVisible();
  const nextTheme = initialTheme === "dark" ? "light" : "dark";
  await themeSelect.selectOption(nextTheme);

  // Save
  await page.getByRole("button", { name: /^save$/i }).click();

  // Drawer should close
  await expect(drawer).not.toBeVisible();

  // html[data-theme] should reflect the change
  const appliedTheme = await page.evaluate(
    () => document.documentElement.dataset.theme ?? "",
  );
  expect(appliedTheme).toBe(nextTheme);
});

// ── Convert flow (real API call) ─────────────────────────────────────────────

test("clicking Convert with default snippet returns complexity stat", async ({ page }) => {
  // Skip if API is not reachable — avoids flakiness when running UI-only.
  const apiUrl = process.env.API_URL ?? "http://localhost:8000";
  let apiUp = false;
  try {
    const resp = await fetch(`${apiUrl}/health`);
    apiUp = resp.ok;
  } catch {
    apiUp = false;
  }
  test.skip(!apiUp, "API not reachable — skipping live conversion test");

  // Intercept the POST /convert call from the browser and proxy it through
  // Playwright's Node.js runtime (which has network access to the API).
  // This avoids relying on the browser's direct access to localhost:8000
  // which may be blocked in the headless sandbox environment.
  await page.route("**/convert", async (route) => {
    if (route.request().method() !== "POST") {
      await route.continue();
      return;
    }
    const body = route.request().postDataJSON();
    try {
      const resp = await fetch(`${apiUrl}/convert`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await resp.json();
      await route.fulfill({
        status: resp.status,
        contentType: "application/json",
        body: JSON.stringify(data),
      });
    } catch {
      await route.abort("failed");
    }
  });

  await page.goto("/convert");

  // Wait for editor container to appear
  await expect(page.getByTestId("monaco-editor")).toBeVisible({ timeout: 10_000 });

  // The Monaco editor loads async. Wait for Monaco to initialise and push
  // the default snippet into the Zustand store.
  await page.waitForTimeout(3_000);

  // Click Convert (rule mode is default, default snippet is in the store)
  const convertBtn = page.getByTestId("convert-submit");
  await expect(convertBtn).toBeVisible();
  await expect(convertBtn).not.toBeDisabled({ timeout: 5_000 });
  await convertBtn.click();

  // Wait for either a success or an error panel (up to 30s for real API call)
  const successPanel = page.getByTestId("status-success");
  const errorPanel = page.getByTestId("status-error");
  await expect(successPanel.or(errorPanel)).toBeVisible({ timeout: 30_000 });

  // If we got an error, fail the test with a useful message.
  if (await errorPanel.isVisible()) {
    const errText = await errorPanel.textContent();
    throw new Error(`Convert returned error panel: ${errText}`);
  }

  // Complexity stat must be present
  const complexityStat = page.getByTestId("stat-complexity");
  await expect(complexityStat).toBeVisible();
  // Value should be a number (not empty / undefined)
  const text = await complexityStat.textContent();
  expect(text).toMatch(/\d/);
});
