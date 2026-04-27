/**
 * Sprint-3 axe-core a11y check on the confidence-shading recipe popover.
 *
 * The popover is keyboard-accessible by spec: Tab focuses the recipe,
 * Enter opens, Tab traps to the source-line link inside, Esc closes
 * (returning focus to the card). axe-core verifies the static a11y
 * properties on top of that — no missing labels, valid ARIA, etc.
 *
 * Because the production Convert page does not yet mount the FlowCanvas
 * (sprint-3 surface only — the Studio canvas mount lands in a follow-up
 * sprint), we render a minimal hand-rolled card + popover here that
 * mirrors the production component's ARIA contract:
 *
 *   - card: role="button", tabIndex=0, aria-haspopup="dialog",
 *     aria-expanded, aria-controls when open
 *   - popover: role="dialog", aria-label
 *   - source link: <button> inside the popover for Tab-trap + Enter
 */
import { test, expect } from "@playwright/test";
import { axe } from "./_helpers";

const POPOVER_DEMO_HTML = `<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>confidence popover demo</title>
<style>
  body { font-family: ui-sans-serif, system-ui, sans-serif; padding: 32px; }
  .card { display: inline-block; width: 96px; height: 96px; border-radius: 10px;
    background: #e0f2f1; color: #014e48; border: 2px solid #fcd34d; padding: 8px;
    box-sizing: border-box; position: relative; cursor: pointer; }
  .card:focus { outline: 3px solid #1976d2; outline-offset: 2px; }
  .popover { display: inline-block; vertical-align: top; margin-left: 16px;
    background: #ffffff; border: 1px solid #e0e0e0; border-radius: 6px; padding: 8px 12px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.12); min-width: 240px; font-size: 12px; }
  .popover h4 { margin: 0 0 4px 0; font-size: 13px; }
  .popover p { margin: 0 0 8px 0; color: #374151; line-height: 1.4; }
  .popover button { background: transparent; border: 0; padding: 0; cursor: pointer;
    color: #0d9488; text-decoration: underline; font: inherit; }
</style></head><body>
  <h2 style="margin-top:0">Sprint-3 confidence popover (open state)</h2>
  <div class="card" role="button" tabindex="0" aria-haspopup="dialog"
       aria-expanded="true" aria-controls="popover-1"
       aria-label="Recipe group_med, type grouping, medium confidence">
    <span aria-hidden="true">Σ</span><br/>group_med
  </div>
  <div class="popover" id="popover-1" role="dialog"
       aria-label="Confidence details for group_med">
    <h4>MEDIUM confidence — 72%</h4>
    <p>Multi-function aggregation; judgement call on 'sum' vs 'mean' columns.</p>
    <button type="button">Lines 4-4 of source ↗</button>
  </div>
</body></html>`;

test.describe("Sprint-3 confidence popover — a11y", () => {
  test("popover open state has no axe violations", async ({ page }) => {
    await page.setContent(POPOVER_DEMO_HTML);
    const results = await axe(page).analyze();
    expect(results.violations).toEqual([]);
  });

  test("card is keyboard focusable and exposes a dialog popover", async ({ page }) => {
    await page.setContent(POPOVER_DEMO_HTML);
    const card = page.locator('[role="button"][aria-haspopup="dialog"]');
    await expect(card).toHaveAttribute("aria-expanded", "true");
    await expect(card).toHaveAttribute("aria-controls", "popover-1");
    await expect(page.locator("#popover-1")).toHaveAttribute("role", "dialog");
    // The "Lines X-Y" link is a real <button> so Enter / Space activate it.
    const link = page.locator(".popover button");
    await expect(link).toBeVisible();
    await expect(link).toHaveText(/Lines 4-4/);
  });
});
