import { describe, expect, it } from "vitest";
import {
  getConnectionColor,
  getDatasetColor,
  getDatasetShape,
  getRecipeColor,
  loadTokens,
} from "../src/theme/tokens";
import { getRecipeGlyph } from "../src/theme/icons";

describe("token loaders", () => {
  it("returns the documented PREPARE light hex from tokens.json", () => {
    const c = getRecipeColor("PREPARE", "light");
    expect(c.bg).toBe("#FFF3E0");
    expect(c.border).toBe("#FF9800");
    expect(c.text).toBe("#E65100");
  });

  it("returns the documented PREPARE dark hex from tokens.json", () => {
    const c = getRecipeColor("PREPARE", "dark");
    expect(c.bg).toBe("#3E2723");
    expect(c.border).toBe("#FF9800");
    expect(c.text).toBe("#FFB74D");
  });

  it("returns dataset triplet for INPUT", () => {
    const c = getDatasetColor("INPUT", "light");
    expect(c.bg).toBe("#E3F2FD");
    expect(c.border).toBe("#4A90D9");
  });

  it("returns connection-type triplet for S3", () => {
    const c = getConnectionColor("S3", "light");
    expect(c.bg).toBe("#FFF3E0");
  });

  it("falls back to default triplet for TODO-marked PREDICTION_SCORING", () => {
    const c = getRecipeColor("PREDICTION_SCORING", "light");
    // Default fallback values from tokens.ts (matches recipe.default in tokens.json).
    expect(c.bg).toBe("#F5F5F5");
    expect(c.border).toBe("#9E9E9E");
    expect(c.text).toBe("#616161");
  });

  it("maps connection types to abstract shapes", () => {
    expect(getDatasetShape("SQL_POSTGRESQL")).toBe("cylinder");
    expect(getDatasetShape("FILESYSTEM")).toBe("folder");
    expect(getDatasetShape("S3")).toBe("document");
  });

  it("provides a glyph for representative recipe types", () => {
    expect(getRecipeGlyph("PREPARE")).toBe("⚙");
    expect(getRecipeGlyph("JOIN")).toBe("⋈");
    expect(getRecipeGlyph("GROUPING")).toBe("Σ");
    expect(getRecipeGlyph("SPLIT")).toBe("⑂");
    expect(getRecipeGlyph("WINDOW")).toBe("▦");
  });

  it("falls back to default glyph for unmapped types", () => {
    expect(getRecipeGlyph("DOWNLOAD")).toBe("■");
  });

  it("loadTokens exposes raw tokens", () => {
    const t = loadTokens();
    expect(t.raw.color.recipe.PREPARE).toBeDefined();
    expect(t.raw.space.layerSpacing).toBe(180);
  });
});
