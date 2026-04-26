/**
 * Recipe icon glyphs. Mirrors `py2dataiku/visualizers/icons.py` UNICODE map.
 *
 * M3a covers the 5 representative types (PREPARE, GROUPING, JOIN, SPLIT,
 * WINDOW) plus the partials Unicode-only glyphs already defined in the Python
 * source; the 23 fall-back-only types resolve to the default square. Dedicated
 * SVG paths and the ML/AI/code-recipe glyphs are TODO:M3b per icon-inventory.md.
 */

import type { RecipeType } from "../types";

const UNICODE: Partial<Record<RecipeType, string>> = {
  PREPARE: "⚙", // ⚙ gear
  JOIN: "⋈", // ⋈ bowtie
  STACK: "☰", // ☰ trigram
  GROUPING: "Σ", // Σ sigma
  WINDOW: "▦", // ▦ grid square
  SPLIT: "⑂", // ⑂ fork
  SORT: "⇅", // ⇅ up-down
  DISTINCT: "◎", // ◎ bullseye
  PYTHON: "λ", // λ lambda
  PYSPARK: "λ",
  SYNC: "⇄", // ⇄ left-right
  SAMPLING: "◔", // ◔ circle quarter
  PIVOT: "⊞", // ⊞ squared plus
  TOP_N: "↑", // ↑ up arrow
  EXTRACT_FAILED_ROWS: "▼", // ▼ filter
  FUZZY_JOIN: "⋈",
  GEO_JOIN: "⋈",
};

const DEFAULT_GLYPH = "■"; // ■

export function getRecipeGlyph(type: RecipeType): string {
  return UNICODE[type] ?? DEFAULT_GLYPH;
}
