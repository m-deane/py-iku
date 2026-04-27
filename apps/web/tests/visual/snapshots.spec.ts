/**
 * snapshots.spec.ts — comprehensive visual baseline coverage.
 *
 * Sweeps every navigable route in the studio router × {light, dark} theme.
 * One test per (route, theme) pair so a regression in any single page in
 * either theme is reported in isolation rather than as a fan-out failure.
 *
 * ── Update workflow ──
 *   pnpm --filter apps-web test:visual              # run + diff
 *   pnpm --filter apps-web test:visual:update       # regenerate baselines
 *
 * Routes that need a token are passed `share/example-token`. The route list
 * here mirrors `src/app/router.tsx` 1:1 — when a route is added there, also
 * add it here so the baseline grid stays exhaustive.
 *
 * The default theme is light; dark is set by writing `data-theme="dark"`
 * onto the html element via init script BEFORE the React app boots, so the
 * theme is honoured on first paint (no flicker → stable screenshot).
 */
import { test, expect, type Page } from "@playwright/test";
import { prepare } from "./_helpers";

interface RouteSpec {
  /** Identifier used in the snapshot filename (kebab-case). */
  id: string;
  /** Path to navigate to. May include a sentinel param like `:token`. */
  path: string;
  /** Optional locator the test waits on before snapshotting. */
  waitForTestId?: string;
  /** Optional locator (text/role) the test waits on before snapshotting. */
  waitForText?: RegExp;
}

// Mirrors apps/web/src/app/router.tsx — keep in sync when routes change.
const ROUTES: RouteSpec[] = [
  { id: "home", path: "/", waitForText: /py-iku-studio/i },
  { id: "convert", path: "/convert" },
  { id: "catalog", path: "/catalog" },
  { id: "snippets", path: "/snippets" },
  { id: "diff", path: "/diff" },
  { id: "audit", path: "/audit" },
  { id: "settings", path: "/settings" },
  { id: "flow-id", path: "/flow/example-id" },
  { id: "editor", path: "/editor" },
  { id: "inspector", path: "/inspector" },
  { id: "validation", path: "/validation" },
  { id: "export", path: "/export" },
  { id: "deploy", path: "/deploy" },
  { id: "share-token", path: "/share/example-token" },
  { id: "templates", path: "/templates" },
  { id: "grel", path: "/grel" },
  { id: "lmp", path: "/lmp" },
  { id: "diff-curves", path: "/diff/curves" },
  { id: "llm-history", path: "/llm-history" },
];

const THEMES = ["light", "dark"] as const;
type Theme = (typeof THEMES)[number];

/**
 * Inject the theme attribute onto <html> BEFORE the React bundle boots.
 * If we waited until after navigation, the first frames would render in the
 * default light theme and flash to dark — which would diff against the
 * baseline on first capture and be flaky on every subsequent run.
 */
async function pinTheme(page: Page, theme: Theme): Promise<void> {
  await page.addInitScript((t: Theme) => {
    document.documentElement.setAttribute("data-theme", t);
    // Persist via localStorage so any in-app `useTheme` hook sees it.
    try {
      window.localStorage.setItem("py-iku-theme", t);
    } catch {
      /* ignore */
    }
  }, theme);
}

/**
 * Settle a page to a snapshot-stable state.
 *
 * Visual specs are notorious for flake when async work (lazy chunks, fonts,
 * suspense boundaries) hasn't finished. This helper lets the optional
 * route-specific anchor settle before we hit the screenshot button.
 */
async function settle(page: Page, spec: RouteSpec): Promise<void> {
  if (spec.waitForTestId) {
    await page.getByTestId(spec.waitForTestId).first().waitFor({ state: "visible" });
  }
  if (spec.waitForText) {
    // Some routes render multiple matches; first() avoids strict-mode errors.
    await expect(page.getByText(spec.waitForText).first()).toBeVisible();
  }
  // Give web fonts + lazy chunks a tick to land. 250ms is enough — animations
  // are already disabled by `prepare()`'s init script.
  await page.waitForTimeout(250);
}

for (const theme of THEMES) {
  for (const spec of ROUTES) {
    test(`${spec.id} (${theme}) baseline`, async ({ page }) => {
      await pinTheme(page, theme);
      await prepare(page);
      const resp = await page.goto(spec.path);
      // Soft-tolerate 4xx — share/:token & flow/:id may 404 with an empty
      // state on stub fixtures. The test still asserts the rendered page
      // doesn't crash, by snapshotting whatever the router fell back to.
      if (resp && resp.status() >= 500) {
        throw new Error(
          `unexpected ${resp.status()} on ${spec.path}: ${await resp.text()}`,
        );
      }
      await settle(page, spec);
      await expect(page).toHaveScreenshot(`${spec.id}-${theme}.png`, {
        maxDiffPixelRatio: 0.02,
        fullPage: true,
      });
    });
  }
}
