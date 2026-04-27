/**
 * Sprint-6 — recipe icon library coverage + render shape.
 */
import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import {
  recipeIconFor,
  RECIPE_ICON_TYPES,
  listIconCoverage,
} from "../src/icons/recipeIcons";
import { ALL_RECIPE_TYPES } from "../src/nodes";

describe("recipeIconFor", () => {
  it("renders an inline <svg> for the new DSS-style types", () => {
    const { container } = render(
      <>{recipeIconFor("PREPARE", { color: "#000", size: 22 })}</>,
    );
    const svg = container.querySelector("svg");
    expect(svg).not.toBeNull();
    expect(svg?.getAttribute("width")).toBe("22");
  });

  it("falls back to the legacy glyph library when no new icon exists", () => {
    const { container } = render(
      <>{recipeIconFor("FUZZY_JOIN", { color: "#000", size: 20 })}</>,
    );
    const svg = container.querySelector("svg");
    expect(svg).not.toBeNull();
  });

  it("falls back to a default square for unknown recipe types", () => {
    const { container } = render(
      <>
        {recipeIconFor("definitely-not-a-recipe", {
          color: "#000",
          size: 22,
        })}
      </>,
    );
    const svg = container.querySelector("svg");
    expect(svg).not.toBeNull();
  });

  it("ships ≥ 6 dedicated DSS-style icons", () => {
    // 6 unique recipe types are covered by the new layer (PREPARE / JOIN /
    // GROUPING / WINDOW / SPLIT / PYTHON); the rest reuse the legacy lib.
    // Allow either 6 (unique types) or 12 (uppercase + lowercase aliases).
    expect(RECIPE_ICON_TYPES.length).toBeGreaterThanOrEqual(6);
  });

  it("covers ≥ 30 of the 37 RecipeType members across NEW + legacy", () => {
    const cov = listIconCoverage(ALL_RECIPE_TYPES);
    expect(cov.total).toBe(37);
    expect(cov.covered.length).toBeGreaterThanOrEqual(30);
  });

  it("covers all members of the structure family", () => {
    const structure = [
      "JOIN",
      "FUZZY_JOIN",
      "GEO_JOIN",
      "GROUPING",
      "WINDOW",
      "SPLIT",
      "SORT",
      "TOP_N",
      "PIVOT",
    ];
    const cov = listIconCoverage(structure);
    expect(cov.uncovered).toEqual([]);
  });
});
