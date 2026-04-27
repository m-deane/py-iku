import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import { getSvgGlyph, SVG_GLYPH_TYPES } from "../src/nodes/glyphs";
import { ALL_RECIPE_TYPES } from "../src/nodes";

describe("getSvgGlyph", () => {
  it("provides at least 23 dedicated SVG glyphs", () => {
    // Per icon-inventory.md the 23 RecipeType members that resolved to the
    // default square in M3a should now have dedicated SVGs.
    expect(SVG_GLYPH_TYPES.length).toBeGreaterThanOrEqual(23);
  });

  it("the glyphs render an inline <svg>", () => {
    const Comp = getSvgGlyph("FUZZY_JOIN");
    expect(Comp).toBeTruthy();
    if (!Comp) return;
    const { container } = render(<Comp color="#000" size={20} />);
    const svg = container.querySelector("svg");
    expect(svg).not.toBeNull();
    expect(svg?.getAttribute("width")).toBe("20");
  });

  it("returns undefined for types without a custom glyph", () => {
    // PREPARE keeps its Unicode glyph in M3b; no SVG override.
    expect(getSvgGlyph("PREPARE")).toBeUndefined();
    expect(getSvgGlyph("JOIN")).toBeUndefined();
  });

  it("covers the entire ML category", () => {
    expect(getSvgGlyph("PREDICTION_SCORING")).toBeTruthy();
    expect(getSvgGlyph("CLUSTERING_SCORING")).toBeTruthy();
    expect(getSvgGlyph("EVALUATION")).toBeTruthy();
    expect(getSvgGlyph("AI_ASSISTANT_GENERATE")).toBeTruthy();
  });

  it("covers every code recipe", () => {
    for (const t of ["R", "SQL", "HIVE", "IMPALA", "SPARKSQL", "PYSPARK", "SPARK_SCALA", "SPARKR", "SHELL"] as const) {
      expect(getSvgGlyph(t), t).toBeTruthy();
    }
  });

  it("registers all 37 RecipeTypes in nodeTypes via ALL_RECIPE_TYPES", () => {
    expect(ALL_RECIPE_TYPES.length).toBe(37);
  });
});
