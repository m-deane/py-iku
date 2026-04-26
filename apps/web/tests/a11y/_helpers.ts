/**
 * Helpers for the axe-core accessibility suite.
 *
 * Each route gets a small spec that scans for WCAG 2.0/2.1 A + AA violations.
 * We keep the rule set narrow so the suite is actionable: violations are
 * source-side bugs to fix, not noise to whitelist.
 */
import type { Page } from "@playwright/test";
import { AxeBuilder } from "@axe-core/playwright";
import {
  stubApi,
  stubWebSocketConvert,
  type StubOptions,
} from "../e2e/_fixtures";

/** Build an AxeBuilder configured with the rule set we hold ourselves to. */
export function axe(page: Page): AxeBuilder {
  return new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    // colour-contrast is environment-sensitive in headless chromium
    // (some fonts are missing → axe sees alpha-blended pixels). We assert
    // it separately on the visual suite via design-token review.
    .disableRules(["color-contrast"]);
}

export async function prepareA11y(
  page: Page,
  opts: StubOptions & { stubWs?: boolean } = {},
): Promise<void> {
  await stubApi(page, opts);
  if (opts.stubWs ?? true) await stubWebSocketConvert(page);
}
