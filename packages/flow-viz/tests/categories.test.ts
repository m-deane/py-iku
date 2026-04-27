import { describe, expect, it } from "vitest";
import { categoryFor, subLabelFor } from "../src/nodes/categories";
import { ALL_RECIPE_TYPES } from "../src/nodes";
import type { RecipeType } from "../src/types";

describe("categoryFor", () => {
  it("returns 'prep' for visual prep family members", () => {
    expect(categoryFor("PREPARE")).toBe("prep");
    expect(categoryFor("SAMPLING")).toBe("prep");
    expect(categoryFor("DISTINCT")).toBe("prep");
    expect(categoryFor("STACK")).toBe("prep");
  });
  it("returns 'structure' for join / group / split / sort / pivot", () => {
    expect(categoryFor("JOIN")).toBe("structure");
    expect(categoryFor("FUZZY_JOIN")).toBe("structure");
    expect(categoryFor("GEO_JOIN")).toBe("structure");
    expect(categoryFor("GROUPING")).toBe("structure");
    expect(categoryFor("SPLIT")).toBe("structure");
    expect(categoryFor("SORT")).toBe("structure");
    expect(categoryFor("TOP_N")).toBe("structure");
    expect(categoryFor("PIVOT")).toBe("structure");
    expect(categoryFor("WINDOW")).toBe("structure");
  });
  it("returns 'code' for the 10 code recipes", () => {
    const codeTypes: RecipeType[] = [
      "PYTHON", "R", "SQL", "HIVE", "IMPALA", "SPARKSQL",
      "PYSPARK", "SPARK_SCALA", "SPARKR", "SHELL",
    ];
    for (const t of codeTypes) {
      expect(categoryFor(t), t).toBe("code");
    }
  });
  it("returns 'ml' for the 4 ML recipes", () => {
    expect(categoryFor("PREDICTION_SCORING")).toBe("ml");
    expect(categoryFor("CLUSTERING_SCORING")).toBe("ml");
    expect(categoryFor("EVALUATION")).toBe("ml");
    expect(categoryFor("AI_ASSISTANT_GENERATE")).toBe("ml");
  });
  it("returns 'io' for connector recipes", () => {
    expect(categoryFor("SYNC")).toBe("io");
    expect(categoryFor("DOWNLOAD")).toBe("io");
    expect(categoryFor("PUSH_TO_EDITABLE")).toBe("io");
    expect(categoryFor("UPSERT")).toBe("io");
    expect(categoryFor("LIST_FOLDER_CONTENTS")).toBe("io");
    expect(categoryFor("LIST_ACCESS")).toBe("io");
  });
  it("classifies every one of the 37 RecipeType members", () => {
    expect(ALL_RECIPE_TYPES).toHaveLength(37);
    for (const t of ALL_RECIPE_TYPES) {
      const c = categoryFor(t);
      expect(["prep", "structure", "code", "ml", "io"]).toContain(c);
    }
  });
});

describe("subLabelFor", () => {
  it("returns a monospace badge for code recipes", () => {
    expect(subLabelFor("PYTHON")).toBe("py");
    expect(subLabelFor("R")).toBe("R");
    expect(subLabelFor("SQL")).toBe("SQL");
    expect(subLabelFor("PYSPARK")).toBe("pySp");
  });
  it("returns null for non-code recipes", () => {
    expect(subLabelFor("PREPARE")).toBeNull();
    expect(subLabelFor("JOIN")).toBeNull();
    expect(subLabelFor("PREDICTION_SCORING")).toBeNull();
    expect(subLabelFor("SYNC")).toBeNull();
  });
});
