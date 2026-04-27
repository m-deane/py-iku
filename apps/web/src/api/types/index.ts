/**
 * Local type extensions on top of the openapi-codegen `@py-iku-studio/types`.
 *
 * The /convert response schema is `extra="allow"` server-side and the
 * generated `DataikuRecipeModel` reflects that as a Record passthrough.
 * For Sprint-3 LLM-confidence shading we surface the three optional
 * fields explicitly so the canvas/inspector code can read them without
 * casting through `unknown`.
 *
 * These three fields are populated only on the LLM path (and only for
 * recipes that originated from a `DataStep` with confidence/reasoning
 * set). On the rule-based path all three are `null`/`undefined` and
 * the UI renders an "R" rule-based badge.
 */

import type { DataikuRecipe as GeneratedDataikuRecipe } from "@py-iku-studio/types";

/**
 * Per-recipe confidence shading metadata produced by the LLM path.
 *
 * Bands rendered by `<RecipeNode>`:
 *   confidence == null OR >= 0.85 -> no shading (high or rule-based)
 *   0.60 <= confidence < 0.85    -> 2px var(--warn-border) + ⚠
 *   confidence < 0.60            -> 2px var(--danger-border) + ⚠ + pulse
 *   confidence == null           -> "R" rule-based badge bottom-left
 */
export interface RecipeConfidenceFields {
  /**
   * LLM self-reported mapping confidence in [0.0, 1.0]. `null` means
   * rule-based or unspecified — the UI treats both identically except
   * the rule-based path tags a small "R" badge in the bottom-left.
   */
  confidence?: number | null;
  /**
   * 1-indexed [start, end] inclusive line span of the originating
   * Python source. Used by the popover's "Lines X-Y of source ↗" link
   * to drive `monaco.editor.deltaDecorations`.
   */
  sourceLines?: [number, number] | null;
  /**
   * One-sentence rationale for the mapping. Rendered inside the
   * popover above the source-link.
   */
  reasoning?: string | null;
}

/**
 * Recipe with confidence-shading fields baked in. Use this on the UI
 * side wherever a recipe object is passed to `<RecipeNode>` or the
 * confidence panel. The codegen counterpart (`DataikuRecipe`) is
 * passthrough via `extra="allow"`, so consumers reading from the
 * `/convert` response payload should narrow with this type.
 */
export type Recipe = GeneratedDataikuRecipe &
  RecipeConfidenceFields & {
    /**
     * snake_case mirror surfaced by the API (Pydantic v2 + extras).
     * Codegen uses snake_case; TS components prefer camelCase, so we
     * expose both and a small adapter (`adoptRecipe`) below.
     */
    source_lines?: number[];
  };

/** Confidence band for shading + panel buckets. */
export type ConfidenceBand = "high" | "medium" | "low" | "rule-based";

/**
 * Pure helper: derive the confidence band from a recipe's confidence
 * value. Used by both the recipe-card shading and the summary panel.
 *
 * Rules (from sprint-3 spec):
 *   confidence == null -> "rule-based"
 *   confidence >= 0.85 -> "high"
 *   0.60 <= confidence < 0.85 -> "medium"
 *   confidence < 0.60 -> "low"
 */
export function bandFor(confidence: number | null | undefined): ConfidenceBand {
  if (confidence === null || confidence === undefined) return "rule-based";
  if (confidence >= 0.85) return "high";
  if (confidence >= 0.60) return "medium";
  return "low";
}

/**
 * Adapter: snap a `/convert`-shape recipe (snake_case `source_lines`,
 * raw confidence/reasoning) into the camelCase `Recipe` shape used by
 * the UI components.
 *
 * The API may emit `source_lines` as a free-form `number[]` (the legacy
 * py-iku field) OR as a `[start, end]` 2-tuple specifically for the
 * LLM path. We coerce to a 2-tuple here.
 */
export function adoptRecipe(raw: Record<string, unknown>): Recipe {
  const sourceLinesRaw = raw["source_lines"];
  let sourceLines: [number, number] | null = null;
  if (Array.isArray(sourceLinesRaw) && sourceLinesRaw.length > 0) {
    const nums = sourceLinesRaw.filter(
      (n): n is number => typeof n === "number",
    );
    if (nums.length > 0) {
      const start = Math.min(...nums);
      const end = Math.max(...nums);
      sourceLines = [start, end];
    }
  }
  const confidence =
    typeof raw["confidence"] === "number"
      ? (raw["confidence"] as number)
      : null;
  const reasoning =
    typeof raw["reasoning"] === "string" ? (raw["reasoning"] as string) : null;
  return {
    ...(raw as GeneratedDataikuRecipe),
    confidence,
    reasoning,
    sourceLines,
  } as Recipe;
}
