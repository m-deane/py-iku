import { describe, it, expect } from "vitest";
import {
  DataikuFlowModelSchema,
  ConvertResponseSchema,
  HealthResponseSchema,
  HTTPValidationErrorSchema,
} from "../src/zod.js";

// ---------------------------------------------------------------------------
// Fixture 1: A rule-converted PREPARE flow (string-transform)
// ---------------------------------------------------------------------------
const prepareFlow = {
  flow_name: "converted_flow",
  generated_from: null,
  total_recipes: 1,
  total_datasets: 2,
  datasets: [
    {
      name: "df",
      type: "output",
      connection_type: "Filesystem",
      schema: [],
      source_variable: "df",
      source_line: 2,
      notes: [],
    },
    {
      name: "df_prepared",
      type: "intermediate",
      connection_type: "Filesystem",
      schema: [],
      source_variable: null,
      source_line: null,
      notes: [],
    },
  ],
  recipes: [
    {
      name: "prepare_1",
      type: "prepare",
      inputs: ["df"],
      outputs: ["df_prepared"],
      source_lines: [],
      notes: [],
      steps: [
        {
          metaType: "PROCESSOR",
          type: "StringTransformer",
          disabled: false,
          params: { column: "col1", mode: "TO_UPPER" },
        },
      ],
      step_count: 1,
    },
  ],
  optimization_notes: ["prepare: 1 recipe(s)"],
  recommendations: [],
  generation_timestamp: "2026-04-26T11:57:30.997225",
};

// ---------------------------------------------------------------------------
// Fixture 2: An empty flow (zero recipes, zero datasets)
// ---------------------------------------------------------------------------
const emptyFlow = {
  flow_name: "empty_flow",
  generated_from: null,
  total_recipes: 0,
  total_datasets: 0,
  datasets: [],
  recipes: [],
  optimization_notes: [],
  recommendations: [],
};

// ---------------------------------------------------------------------------
// Fixture 3: An invalid payload (missing required fields)
// ---------------------------------------------------------------------------
const invalidFlow = {
  // Missing flow_name, total_recipes, total_datasets
  recipes: "not-an-array",
};

// ---------------------------------------------------------------------------
// Fixture 4: A problem+json error envelope (as HTTPValidationError)
// ---------------------------------------------------------------------------
const validationError = {
  detail: [
    {
      loc: ["body", "code"],
      msg: "Field required",
      type: "missing",
    },
  ],
};

// ---------------------------------------------------------------------------
// Fixture 5: A ConvertResponse wrapper
// ---------------------------------------------------------------------------
const convertResponse = {
  flow: prepareFlow,
  score: {
    recipe_count: 1,
    processor_count: 1,
    max_depth: 2,
    fan_out_max: 1,
    complexity: 3.5,
    cost_estimate: null,
  },
  warnings: [],
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("DataikuFlowModelSchema", () => {
  it("parses a valid PREPARE flow", () => {
    const result = DataikuFlowModelSchema.safeParse(prepareFlow);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.flow_name).toBe("converted_flow");
      expect(result.data.total_recipes).toBe(1);
      expect(result.data.datasets).toHaveLength(2);
      expect(result.data.recipes).toHaveLength(1);
    }
  });

  it("parses an empty flow (zero recipes/datasets)", () => {
    const result = DataikuFlowModelSchema.safeParse(emptyFlow);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.total_recipes).toBe(0);
      // Empty arrays are valid — either [] or undefined depending on what was passed
      const recipes = result.data.recipes;
      expect(recipes === undefined || (Array.isArray(recipes) && recipes.length === 0)).toBe(true);
    }
  });

  it("rejects an invalid payload (wrong types, missing fields)", () => {
    const result = DataikuFlowModelSchema.safeParse(invalidFlow);
    expect(result.success).toBe(false);
    if (!result.success) {
      // Should contain errors about missing required fields
      const paths = result.error.issues.map((i) => i.path.join("."));
      expect(paths.some((p) => p.includes("flow_name") || p.includes("total_recipes"))).toBe(true);
    }
  });

  it("allows passthrough of extra fields (additionalProperties=true)", () => {
    const withExtra = { ...prepareFlow, custom_field: "extra_value", nested: { x: 1 } };
    const result = DataikuFlowModelSchema.safeParse(withExtra);
    expect(result.success).toBe(true);
    if (result.success) {
      expect((result.data as Record<string, unknown>)["custom_field"]).toBe("extra_value");
    }
  });
});

describe("HTTPValidationErrorSchema (problem+json envelope)", () => {
  it("parses a FastAPI validation error envelope", () => {
    const result = HTTPValidationErrorSchema.safeParse(validationError);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.detail).toHaveLength(1);
      expect(result.data.detail![0]!.type).toBe("missing");
    }
  });

  it("parses an empty validation error (no detail)", () => {
    const result = HTTPValidationErrorSchema.safeParse({});
    expect(result.success).toBe(true);
  });
});

describe("ConvertResponseSchema", () => {
  it("parses a full ConvertResponse", () => {
    const result = ConvertResponseSchema.safeParse(convertResponse);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.score.recipe_count).toBe(1);
      expect(result.data.score.complexity).toBe(3.5);
      expect(result.data.flow.flow_name).toBe("converted_flow");
    }
  });

  it("rejects a ConvertResponse missing the flow field", () => {
    const result = ConvertResponseSchema.safeParse({ score: convertResponse.score, warnings: [] });
    expect(result.success).toBe(false);
  });
});

describe("HealthResponseSchema", () => {
  it("parses a valid health response", () => {
    const result = HealthResponseSchema.safeParse({
      status: "ok",
      version: "0.0.0",
      py_iku_version: "0.3.0",
    });
    expect(result.success).toBe(true);
  });

  it("rejects a health response missing py_iku_version", () => {
    const result = HealthResponseSchema.safeParse({ status: "ok", version: "0.0.0" });
    expect(result.success).toBe(false);
  });
});
