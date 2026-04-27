import { describe, it, expect } from "vitest";
import {
  RecipeSettingsModelSchema,
  DataikuRecipeModelSchema,
  DataikuFlowModelSchema,
} from "../src/zod.js";

// ---------------------------------------------------------------------------
// One representative shape per RecipeSettings subclass
// ---------------------------------------------------------------------------

const prepareSettings = {
  kind: "prepare",
  steps: [{ metaType: "PROCESSOR", type: "ColumnRenamer", disabled: false, params: { from: "a", to: "b" } }],
  step_count: 1,
};

const groupingSettings = {
  kind: "grouping",
  keys: ["region"],
  aggregations: [{ column: "sales", type: "SUM" }],
};

const joinSettings = {
  kind: "join",
  join_type: "LEFT",
  join_keys: [{ left: "id", right: "id" }],
  selected_columns: null,
};

const windowSettings = {
  kind: "window",
  partitionColumns: [{ column: "user_id" }],
  orderColumns: [{ column: "date", order: "ASC" }],
  aggregations: [{ type: "SUM", column: "value" }],
};

const samplingSettings = {
  kind: "sampling",
  samplingMethod: "RANDOM_FIXED_NB",
  sampleSize: 1000,
};

const splitSettings = {
  kind: "split",
  splitMode: "FILTER",
  condition: "age > 18",
};

const sortSettings = {
  kind: "sort",
  sortColumns: [{ column: "created_at", order: "DESC" }],
};

const topNSettings = {
  kind: "topn",
  topN: 10,
  rankingColumn: "score",
};

const distinctSettings = {
  kind: "distinct",
  computeCount: true,
};

const stackSettings = {
  kind: "stack",
  mode: "UNION",
};

const pythonSettings = {
  kind: "python",
  code: "# custom python script\ndf = dataiku.Dataset('input').get_dataframe()",
};

const pivotSettings = {
  kind: "pivot",
  rowColumns: ["region"],
  columnColumn: "quarter",
  valueColumn: "revenue",
  aggregation: "SUM",
};

// All 12 settings shapes
const allSettingsFixtures = [
  { name: "prepare", settings: prepareSettings },
  { name: "grouping", settings: groupingSettings },
  { name: "join", settings: joinSettings },
  { name: "window", settings: windowSettings },
  { name: "sampling", settings: samplingSettings },
  { name: "split", settings: splitSettings },
  { name: "sort", settings: sortSettings },
  { name: "topn", settings: topNSettings },
  { name: "distinct", settings: distinctSettings },
  { name: "stack", settings: stackSettings },
  { name: "python", settings: pythonSettings },
  { name: "pivot", settings: pivotSettings },
] as const;

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("RecipeSettingsModelSchema (discriminatedUnion on 'kind')", () => {
  for (const { name, settings } of allSettingsFixtures) {
    it(`parses ${name} settings and narrows to correct kind`, () => {
      const result = RecipeSettingsModelSchema.safeParse(settings);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.kind).toBe(name);
      }
    });
  }

  it("rejects an unknown kind value", () => {
    const result = RecipeSettingsModelSchema.safeParse({ kind: "unknown_recipe_type", steps: [] });
    expect(result.success).toBe(false);
  });

  it("rejects settings missing the kind discriminator", () => {
    const result = RecipeSettingsModelSchema.safeParse({ steps: [], step_count: 0 });
    expect(result.success).toBe(false);
  });
});

describe("DataikuRecipeModelSchema with embedded settings", () => {
  it("parses a recipe with prepare settings", () => {
    const recipe = {
      name: "prepare_1",
      type: "prepare",
      inputs: ["input_ds"],
      outputs: ["output_ds"],
      settings: prepareSettings,
    };
    const result = DataikuRecipeModelSchema.safeParse(recipe);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.settings?.kind).toBe("prepare");
    }
  });

  it("parses a recipe with null settings (py-iku to_dict() default)", () => {
    const recipe = {
      name: "grouping_1",
      type: "grouping",
      inputs: ["df"],
      outputs: ["grouped"],
      settings: null,
      // Inlined fields from to_display_dict() pass through via additionalProperties
      keys: ["region"],
      aggregations: [{ column: "sales", type: "SUM" }],
    };
    const result = DataikuRecipeModelSchema.safeParse(recipe);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.settings).toBeNull();
      expect((result.data as Record<string, unknown>)["keys"]).toEqual(["region"]);
    }
  });
});

describe("Round-trip: a flow with each of the 12 settings subclasses", () => {
  const datasets = [
    { name: "input_ds", type: "input", connection_type: "Filesystem", notes: [], schema: [] },
    { name: "output_ds", type: "output", connection_type: "Filesystem", notes: [], schema: [] },
  ];

  for (const { name, settings } of allSettingsFixtures) {
    it(`round-trips a flow containing a ${name} recipe with composed settings`, () => {
      const flow = {
        flow_name: `${name}_flow`,
        total_recipes: 1,
        total_datasets: 2,
        datasets,
        recipes: [
          {
            name: `${name}_recipe`,
            type: name === "topn" ? "topn" : name,
            inputs: ["input_ds"],
            outputs: ["output_ds"],
            settings,
          },
        ],
        optimization_notes: [],
        recommendations: [],
      };

      const result = DataikuFlowModelSchema.safeParse(flow);
      expect(result.success).toBe(true);
      if (result.success) {
        const recipe = result.data.recipes?.[0];
        expect(recipe).toBeDefined();
        expect(recipe?.settings?.kind).toBe(name);
      }
    });
  }
});
