/**
 * React Flow `nodeTypes` registry.
 *
 * M3a wired interactive renderers for the 5 representative RecipeType
 * members (prepare, grouping, join, split, window). M3b extends coverage to
 * all 37 RecipeType members via category-based visual treatment driven by
 * `categories.ts` + `glyphs.tsx`. Each `recipe.<TYPE>` entry is generated
 * from `makeRecipeNodeForType(type)`.
 *
 * NOTE: RecipeType values are lowercase DSS values (e.g. "prepare", not "PREPARE")
 * sourced from @py-iku-studio/types codegen.
 */

import type { NodeTypes } from "reactflow";
import { RecipeNode, makeRecipeNodeForType } from "./RecipeNode";
import { DatasetNode } from "./DatasetNode";
import type { RecipeType } from "../types";

/** Representative recipe types from M3a — kept for backwards compatibility. */
export const REPRESENTATIVE_RECIPE_TYPES: readonly RecipeType[] = [
  "prepare",
  "grouping",
  "join",
  "split",
  "window",
] as const;

/** All 37 RecipeType members (lowercase DSS values) — M3b registers a bound RecipeNode for each. */
export const ALL_RECIPE_TYPES: readonly RecipeType[] = [
  "prepare",
  "sync",
  "grouping",
  "window",
  "join",
  "fuzzyjoin",
  "geojoin",
  "stack",
  "split",
  "sort",
  "distinct",
  "topn",
  "pivot",
  "sampling",
  "download",
  "generate_features",
  "generate_statistics",
  "push_to_editable",
  "list_folder_contents",
  "dynamic_repeat",
  "extract_failed_rows",
  "upsert",
  "list_access",
  "python",
  "r",
  "sql_script",
  "hive",
  "impala",
  "spark_sql_query",
  "pyspark",
  "spark_scala",
  "sparkr",
  "shell",
  "prediction_scoring",
  "clustering_scoring",
  "standalone_evaluation",
  "ai_assistant_generate",
] as const;

function buildBoundRecipeTypes(): Record<string, ReturnType<typeof makeRecipeNodeForType>> {
  const out: Record<string, ReturnType<typeof makeRecipeNodeForType>> = {};
  for (const t of ALL_RECIPE_TYPES) {
    out[`recipe.${t}`] = makeRecipeNodeForType(t);
  }
  return out;
}

export const nodeTypes: NodeTypes = {
  recipe: RecipeNode,
  dataset: DatasetNode,
  ...buildBoundRecipeTypes(),
};

export { RecipeNode, DatasetNode };
export { categoryFor, subLabelFor } from "./categories";
export type { RecipeCategory } from "./categories";
export { getSvgGlyph, SVG_GLYPH_TYPES } from "./glyphs";
