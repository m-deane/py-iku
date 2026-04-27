import { test, expect } from "@playwright/test";
import { prepare } from "./_helpers";

test("home page baseline", async ({ page }) => {
  await prepare(page);
  await page.goto("/");
  await expect(page.getByRole("link", { name: /py-iku-studio/i }).first()).toBeVisible();
  await expect(page).toHaveScreenshot("home.png", { maxDiffPixelRatio: 0.02 });
});
