import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright configuration for apps/web e2e + visual + a11y tests.
 *
 * baseURL defaults to http://localhost:5173 but can be overridden via
 * BASE_URL env var (useful in CI or docker).
 *
 * API_URL defaults to http://localhost:8000 and is used by tests that
 * need to verify the API is reachable.
 *
 * Projects:
 *   - chromium / webkit: full e2e suite (tests/e2e/)
 *   - visual: deterministic full-page screenshots (tests/visual/)
 *     baselines committed for chromium only — see __screenshots__/.
 *   - a11y: axe-core scans (tests/a11y/) — chromium only, fast.
 *
 * The visual + a11y projects also run inside the chromium browser but use
 * separate test directories so they can be filtered with --project=visual
 * (or --project=a11y) from the CLI / CI.
 */
export default defineConfig({
  testDir: "./tests",
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
  // Visual baselines are stored co-located with each spec at
  // tests/visual/__screenshots__/ — chromium-only to avoid cross-browser drift.
  snapshotPathTemplate:
    "{testDir}/{testFileDir}/__screenshots__/{testFileName}-{arg}{ext}",
  expect: {
    toHaveScreenshot: {
      maxDiffPixelRatio: 0.02,
      animations: "disabled",
    },
  },
  projects: [
    // ── E2E ────────────────────────────────────────────────────────────────
    {
      name: "chromium",
      testDir: "./tests/e2e",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "webkit",
      testDir: "./tests/e2e",
      use: { ...devices["Desktop Safari"] },
    },
    // ── Visual regression ──────────────────────────────────────────────────
    {
      name: "visual",
      testDir: "./tests/visual",
      use: {
        ...devices["Desktop Chrome"],
        // Lock viewport for deterministic screenshots.
        viewport: { width: 1280, height: 800 },
        // Tells the page to honour prefers-reduced-motion to disable
        // CSS-driven animation/transitions during baseline captures.
        reducedMotion: "reduce",
      },
    },
    // ── Accessibility (axe) ────────────────────────────────────────────────
    {
      name: "a11y",
      testDir: "./tests/a11y",
      use: { ...devices["Desktop Chrome"] },
    },
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
