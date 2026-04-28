// AUTO-GENERATED — do not edit. Run `pnpm codegen`
// Public API for @py-iku-studio/types

export type { components, paths, operations } from "./openapi.js";

export * from "./zod.js";

// Convenience type aliases from generated components
import type { components } from "./openapi.js";

export type DataikuFlow = components["schemas"]["DataikuFlowModel-Output"];
export type DataikuRecipe = components["schemas"]["DataikuRecipeModel-Output"];
export type DataikuDataset = components["schemas"]["DataikuDatasetModel"];
export type PrepareStep = components["schemas"]["PrepareStepModel"];
export type ConvertRequest = components["schemas"]["ConvertRequest"];
export type ConvertResponse = components["schemas"]["ConvertResponse"];
export type ComplexityScore = components["schemas"]["ComplexityScore"];
export type RecipeCatalogEntry = components["schemas"]["RecipeCatalogEntry"];
export type ProcessorCatalogEntry = components["schemas"]["ProcessorCatalogEntry"];
export type HealthResponse = components["schemas"]["HealthResponse"];

// Re-export Zod schema parse helpers
import {
  DataikuFlowModelSchema,
  ConvertResponseSchema,
  ConvertRequestSchema,
} from "./zod.js";

/** Parse an unknown payload as DataikuFlowModel; throws ZodError on failure. */
export function parseFlow(x: unknown): DataikuFlow {
  return DataikuFlowModelSchema.parse(x) as DataikuFlow;
}

/** Safely parse a ConvertResponse; returns { success, data, error }. */
export function safeParseConvertResponse(x: unknown) {
  return ConvertResponseSchema.safeParse(x);
}

/** Safely parse a ConvertRequest. */
export function safeParseConvertRequest(x: unknown) {
  return ConvertRequestSchema.safeParse(x);
}
