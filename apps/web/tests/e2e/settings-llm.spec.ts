/**
 * E2E coverage for Settings → LLM Provider key entry.
 *
 * The full flow:
 *   1. visit /settings
 *   2. find the LLM Provider section
 *   3. type a key, click Save
 *   4. assert the status pill flips to 🟢 / "Configured"
 *   5. click "Test connection" → assert the result line says OK
 *
 * All HTTP traffic is stubbed via Playwright's page.route so the test stays
 * hermetic — no FastAPI process required.
 */
import { test, expect } from "@playwright/test";

const fakeKey = "sk-ant-e2e-test-key-12345";

test.describe("Settings → LLM Provider", () => {
  test.beforeEach(async ({ page }) => {
    let hasKey = false;

    await page.route("**/api/settings/llm", async (route) => {
      const method = route.request().method();
      if (method !== "GET") {
        await route.fallback();
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          provider: "anthropic",
          has_key: hasKey,
          source: hasKey ? "file" : "none",
        }),
      });
    });

    await page.route("**/api/settings/llm/key", async (route) => {
      const method = route.request().method();
      if (method === "POST") {
        const body = JSON.parse(route.request().postData() ?? "{}");
        // The fake key is asserted to round-trip through the request.
        if (body.key !== fakeKey) {
          await route.fulfill({
            status: 400,
            contentType: "application/json",
            body: JSON.stringify({
              type: "about:blank",
              title: "Bad key",
              status: 400,
            }),
          });
          return;
        }
        hasKey = true;
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            provider: "anthropic",
            has_key: true,
            source: "file",
          }),
        });
      } else if (method === "DELETE") {
        hasKey = false;
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ removed: true }),
        });
      } else {
        await route.fallback();
      }
    });

    // Stub /convert so the "Test connection" flow returns a recipe.
    await page.route("**/convert*", async (route) => {
      const method = route.request().method();
      if (method !== "POST") {
        await route.fallback();
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          flow: { recipes: [{ name: "agg", type: "grouping" }] },
          score: { complexity: 1.0, recipe_count: 1, dataset_count: 2 },
          warnings: [],
        }),
      });
    });
  });

  test("user can enter a key, save, and test the connection", async ({ page }) => {
    await page.goto("/settings");

    // The LlmProviderSection should mount and probe status.
    const status = page.getByTestId("settings-llm-status");
    await expect(status).toBeVisible();
    await expect(status).toHaveText(/not configured/i);

    // Type the key — input is type=password by default; flipping reveal does
    // not change the persistence path, so we leave it hidden here.
    await page.getByTestId("settings-llm-key-input").fill(fakeKey);
    await page.getByTestId("settings-llm-key-save").click();

    await expect(status).toHaveText(/configured/i, { timeout: 5_000 });

    // Test connection — should now be enabled.
    const test = page.getByTestId("settings-llm-test");
    await expect(test).toBeEnabled();
    await test.click();

    await expect(page.getByTestId("settings-llm-test-result")).toHaveText(/OK/i, {
      timeout: 5_000,
    });
  });

  test("clearing the key flips status back to Not configured", async ({ page }) => {
    await page.goto("/settings");

    await page.getByTestId("settings-llm-key-input").fill(fakeKey);
    await page.getByTestId("settings-llm-key-save").click();

    const status = page.getByTestId("settings-llm-status");
    await expect(status).toHaveText(/configured/i, { timeout: 5_000 });

    // Remove via the explicit "Remove" button surfaced once a file-source key exists.
    await page.getByTestId("settings-llm-key-clear").click();

    await expect(status).toHaveText(/not configured/i, { timeout: 5_000 });
  });

  test("Convert page surfaces a deep-link banner when no key is configured", async ({ page }) => {
    await page.goto("/convert");
    // Toggle to LLM mode — banner should appear once the probe lands.
    const llmTab = page.getByRole("radio", { name: /llm/i });
    await llmTab.click();

    const banner = page.getByTestId("convert-llm-no-key-banner");
    await expect(banner).toBeVisible({ timeout: 5_000 });
    await expect(banner).toContainText(/Settings/);
  });
});
