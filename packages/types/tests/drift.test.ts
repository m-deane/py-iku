import { describe, it, expect } from "vitest";
import * as fs from "node:fs";
import * as path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const APPS_API_DIR = path.resolve(__dirname, "../../../apps/api");
const SNAPSHOT_PATH = path.join(ROOT, "openapi.snapshot.json");

/**
 * Generate the OpenAPI schema via Python in-process.
 * This mirrors the codegen script's fallback path exactly.
 */
function generateOpenAPIFromPython(): object {
  const result = spawnSync(
    "python",
    ["-c", `from app.main import app; import json; print(json.dumps(app.openapi()))`],
    { cwd: APPS_API_DIR, encoding: "utf8", timeout: 30_000 }
  );

  if (result.status !== 0) {
    throw new Error(`Python generation failed:\n${result.stderr}\n${result.stdout}`);
  }
  return JSON.parse(result.stdout.trim()) as object;
}

describe("drift detection", () => {
  it("openapi.snapshot.json exists and is valid JSON", () => {
    expect(fs.existsSync(SNAPSHOT_PATH)).toBe(true);
    const raw = fs.readFileSync(SNAPSHOT_PATH, "utf8");
    const parsed = JSON.parse(raw);
    expect(parsed).toHaveProperty("openapi");
    expect(parsed).toHaveProperty("components");
    expect(parsed).toHaveProperty("paths");
  });

  it("the committed snapshot matches what the live FastAPI app emits (no drift)", () => {
    const committed = JSON.parse(fs.readFileSync(SNAPSHOT_PATH, "utf8")) as object;
    const live = generateOpenAPIFromPython();

    // Normalise: stringify both with sorted keys for deterministic comparison
    const normalise = (obj: object): string =>
      JSON.stringify(obj, Object.keys(JSON.stringify(obj) ? JSON.parse(JSON.stringify(obj)) : {}).sort());

    // Deep-equality comparison
    expect(JSON.stringify(committed)).toEqual(JSON.stringify(live));
  });

  it("snapshot has all 12 RecipeSettings subclass schemas", () => {
    const snapshot = JSON.parse(fs.readFileSync(SNAPSHOT_PATH, "utf8")) as {
      components: { schemas: Record<string, unknown> };
    };
    const schemas = snapshot.components.schemas;

    const expected = [
      "PrepareSettingsModel",
      "GroupingSettingsModel",
      "JoinSettingsModel",
      "WindowSettingsModel",
      "SamplingSettingsModel",
      "SplitSettingsModel",
      "SortSettingsModel",
      "TopNSettingsModel",
      "DistinctSettingsModel",
      "StackSettingsModel",
      "PythonSettingsModel",
      "PivotSettingsModel",
    ];

    for (const name of expected) {
      expect(schemas, `Missing schema: ${name}`).toHaveProperty(name);
    }
  });

  it("snapshot has exactly 40 component schemas", () => {
    const snapshot = JSON.parse(fs.readFileSync(SNAPSHOT_PATH, "utf8")) as {
      components: { schemas: Record<string, unknown> };
    };
    const count = Object.keys(snapshot.components.schemas).length;
    expect(count).toBe(40);
  });

  it("snapshot has the 9 trimmed-Studio API paths", () => {
    const snapshot = JSON.parse(fs.readFileSync(SNAPSHOT_PATH, "utf8")) as {
      paths: Record<string, unknown>;
    };
    const paths = Object.keys(snapshot.paths);
    expect(paths).toContain("/health");
    expect(paths).toContain("/api/version");
    expect(paths).toContain("/convert");
    expect(paths).toContain("/catalog/recipes");
    expect(paths).toContain("/catalog/processors");
    expect(paths).toContain("/catalog/processors/{processor_type}");
    expect(paths).toContain("/score");
    expect(paths).toContain("/flows");
    expect(paths).toContain("/flows/{flow_id}");
    expect(paths.length).toBe(9);
  });
});
