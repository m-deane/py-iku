import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright configuration for apps/web e2e tests.
 *
 * baseURL defaults to http://localhost:5173 but can be overridden via
 * BASE_URL env var (useful in CI or docker).
 *
 * API_URL defaults to http://localhost:8000 and is used by tests that
 * need to verify the API is reachable.
 */
export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: [
    ["html", { outputFolder: "playwright-report", open: "never" }],
    ["list"],
  ],
  use: {
    baseURL: process.env.BASE_URL ?? "http://localhost:5173",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
    // Give Monaco time to load in real browser
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
  },
  outputDir: "test-results",
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "webkit",
      use: { ...devices["Desktop Safari"] },
    },
    // firefox is optional — uncomment to enable
    // {
    //   name: "firefox",
    //   use: { ...devices["Desktop Firefox"] },
    // },
  ],
  // webServer is used when running locally without a pre-started server.
  // In CI, the api+web are started by scripts/e2e.sh before playwright runs.
  webServer: process.env.CI
    ? undefined
    : {
        command: "pnpm dev",
        url: "http://localhost:5173",
        reuseExistingServer: true,
        timeout: 60_000,
      },
});
