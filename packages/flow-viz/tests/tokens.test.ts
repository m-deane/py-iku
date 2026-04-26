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
  it("returns a color triplet for prepare recipe type", () => {
    // tokens.json uses legacy PREPARE key; lowercase lookup falls back to default
    const c = getRecipeColor("prepare", "light");
    expect(c).toBeDefined();
    expect(c.bg).toBeDefined();
    expect(c.border).toBeDefined();
  });

  it("returns a color triplet for input dataset type", () => {
    const c = getDatasetColor("input", "light");
    expect(c).toBeDefined();
  });

  it("returns connection-type triplet for S3", () => {
    const c = getConnectionColor("S3", "light");
    expect(c).toBeDefined();
  });

  it("returns a color triplet for prediction_scoring", () => {
    const c = getRecipeColor("prediction_scoring", "light");
    expect(c).toBeDefined();
  });

  it("maps connection types to abstract shapes using canonical DSS values", () => {
    expect(getDatasetShape("PostgreSQL")).toBe("cylinder");
    expect(getDatasetShape("Filesystem")).toBe("folder");
    expect(getDatasetShape("S3")).toBe("document");
  });

  it("provides a glyph for representative recipe types using lowercase DSS values", () => {
    expect(getRecipeGlyph("prepare")).toBe("\u2699");
    expect(getRecipeGlyph("join")).toBe("\u22c8");
    expect(getRecipeGlyph("grouping")).toBe("\u03a3");
    expect(getRecipeGlyph("split")).toBe("\u2482");
    expect(getRecipeGlyph("window")).toBe("\u25a6");
  });

  it("falls back to default glyph for unmapped types", () => {
    expect(getRecipeGlyph("download")).toBe("\u25a0");
  });

  it("loadTokens exposes raw tokens", () => {
    const t = loadTokens();
    expect(t.raw.color.recipe["PREPARE"]).toBeDefined();
    expect(t.raw.space.layerSpacing).toBe(180);
  });
});
