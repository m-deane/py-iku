/**
 * Helpers shared by the visual regression suite.
 *
 * Visual tests need a deterministic page. This module:
 *   1. Re-exports the e2e fixtures (`stubApi`, `stubWebSocketConvert`, …) so
 *      visual specs don't go through the FastAPI backend.
 *   2. Adds an init script that freezes Date/Math.random so any time-stamped
 *      strings in the UI (e.g. audit timestamps) render the same value.
 *   3. Provides a `prepare(page, opts)` helper that consolidates the bootstrap
 *      sequence used by every spec.
 */
import type { Page } from "@playwright/test";
import {
  stubApi,
  stubWebSocketConvert,
  type StubOptions,
} from "../e2e/_fixtures";

export interface PrepareOptions extends StubOptions {
  /** Whether to also stub the WebSocket. Default: true. */
  stubWs?: boolean;
}

export async function prepare(page: Page, opts: PrepareOptions = {}): Promise<void> {
  // Freeze time so timestamps render deterministically.
  await page.addInitScript(() => {
    const FIXED = Date.parse("2026-04-26T12:00:00.000Z");
    // Patch Date.now() — sufficient for the audit page timestamps without
    // breaking Date construction in third-party libraries.
    Date.now = (): number => FIXED;

    // Disable animations + transitions globally for screenshot stability.
    const css = document.createElement("style");
    css.textContent =
      "*, *::before, *::after { animation: none !important; transition: none !important; caret-color: transparent !important; }";
    document.documentElement.appendChild(css);
  });

  await stubApi(page, opts);
  if (opts.stubWs ?? true) await stubWebSocketConvert(page);
}
