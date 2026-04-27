/**
 * Recipe icon glyphs. Uses lowercase DSS enum values from @py-iku-studio/types codegen.
 */

import type { RecipeType } from "../types";

const UNICODE: Partial<Record<RecipeType, string>> = {
  "prepare": "\u2699",
  "join": "\u22c8",
  "stack": "\u2630",
  "grouping": "\u03a3",
  "window": "\u25a6",
  "split": "\u2482",
  "sort": "\u21c5",
  "distinct": "\u25ce",
  "python": "\u03bb",
  "pyspark": "\u03bb",
  "sync": "\u21c4",
  "sampling": "\u25d4",
  "pivot": "\u229e",
  "topn": "\u2191",
  "extract_failed_rows": "\u25bc",
  "fuzzyjoin": "\u22c8",
  "geojoin": "\u22c8",
};

const DEFAULT_GLYPH = "\u25a0";

export function getRecipeGlyph(type: RecipeType): string {
  return UNICODE[type] ?? DEFAULT_GLYPH;
}
