/**
 * Sprint 5 — responsive screenshot harness for the most-used routes.
 *
 * For each viewport × route, navigates and takes a screenshot to
 * /tmp/py-iku-review/sprint5-after/responsive/. The Sprint 5 plan calls out
 * 4 viewports (phone / tablet / small laptop / desktop) and 5 priority
 * routes (Convert / Templates / Catalog / GREL / LMP).
 *
 * Run with:
 *   cd apps/web
 *   BASE_URL=http://localhost:5173 npx playwright test tests/e2e/sprint5-responsive.spec.ts \
 *     --project=chromium
 */
import { test, expect } from "@playwright/test";

const VIEWPORTS = [
  { name: "phone-360x800", width: 360, height: 800 },
  { name: "tablet-768x1024", width: 768, height: 1024 },
  { name: "small-laptop-1024x768", width: 1024, height: 768 },
  { name: "desktop-1440x900", width: 1440, height: 900 },
];

const ROUTES: Array<{ name: string; path: string; testId?: string }> = [
  { name: "convert", path: "/convert", testId: "convert-page" },
  { name: "templates", path: "/templates", testId: "templates-page" },
  { name: "catalog", path: "/catalog", testId: "catalog-page" },
  { name: "grel", path: "/grel", testId: "grel-library-page" },
  { name: "lmp", path: "/lmp", testId: "lmp-browser-page" },
];

const SCREENSHOT_DIR = "/tmp/py-iku-review/sprint5-after/responsive";

for (const vp of VIEWPORTS) {
  for (const route of ROUTES) {
    test(`${route.name} @ ${vp.name}`, async ({ page }) => {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.goto(route.path);
      // Wait for the route content to mount (best-effort — fall back to a small timeout).
      if (route.testId) {
        await page
          .waitForSelector(`[data-testid="${route.testId}"]`, { timeout: 10_000 })
          .catch(() => undefined);
      }
      // Settle any in-progress animations.
      await page.waitForTimeout(300);
      await page.screenshot({
        path: `${SCREENSHOT_DIR}/${route.name}-${vp.name}.png`,
        fullPage: true,
      });
      // Soft assertion that the page rendered _something_.
      const body = await page.locator("body").innerText();
      expect(body.length).toBeGreaterThan(0);
    });
  }
}
