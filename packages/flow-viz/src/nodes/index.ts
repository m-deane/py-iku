/**
 * React Flow `nodeTypes` registry.
 *
 * M3a wires interactive renderers for the 5 representative RecipeType members
 * (PREPARE, GROUPING, JOIN, SPLIT, WINDOW) plus the generic recipe / dataset
 * nodes. The remaining 32 RecipeType members render via the generic `recipe`
 * type (which still resolves correct color + glyph + label from tokens, but
 * does not have a dedicated story or icon yet).
 */

import type { NodeTypes } from "reactflow";
import { RecipeNode, makeRecipeNodeForType } from "./RecipeNode";
import { DatasetNode } from "./DatasetNode";
import type { RecipeType } from "../types";

/** Representative recipe types interactive in M3a. */
export const REPRESENTATIVE_RECIPE_TYPES: readonly RecipeType[] = [
  "PREPARE",
  "GROUPING",
  "JOIN",
  "SPLIT",
  "WINDOW",
] as const;

/**
 * TODO:M3b — register dedicated nodes for the remaining 32 RecipeType members:
 * SYNC, FUZZY_JOIN, GEO_JOIN, STACK, SORT, DISTINCT, TOP_N, PIVOT, SAMPLING,
 * DOWNLOAD, GENERATE_FEATURES, GENERATE_STATISTICS, PUSH_TO_EDITABLE,
 * LIST_FOLDER_CONTENTS, DYNAMIC_REPEAT, EXTRACT_FAILED_ROWS, UPSERT,
 * LIST_ACCESS, PYTHON, R, SQL, HIVE, IMPALA, SPARKSQL, PYSPARK, SPARK_SCALA,
 * SPARKR, SHELL, PREDICTION_SCORING, CLUSTERING_SCORING, EVALUATION,
 * AI_ASSISTANT_GENERATE.
 */
export const nodeTypes: NodeTypes = {
  recipe: RecipeNode,
  dataset: DatasetNode,
  // Representative bound types: each renders a RecipeNode with its type fixed.
  "recipe.PREPARE": makeRecipeNodeForType("PREPARE"),
  "recipe.GROUPING": makeRecipeNodeForType("GROUPING"),
  "recipe.JOIN": makeRecipeNodeForType("JOIN"),
  "recipe.SPLIT": makeRecipeNodeForType("SPLIT"),
  "recipe.WINDOW": makeRecipeNodeForType("WINDOW"),
};

export { RecipeNode, DatasetNode };
