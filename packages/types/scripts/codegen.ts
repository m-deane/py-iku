#!/usr/bin/env tsx
// AUTO-GENERATED script — generates src/openapi.ts and src/zod.ts from /openapi.json.
// Run: pnpm codegen

import { execSync, spawnSync } from "node:child_process";
import * as fs from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const APPS_API_DIR = path.resolve(__dirname, "../../../apps/api");
const SNAPSHOT_PATH = path.join(ROOT, "openapi.snapshot.json");
const SRC_DIR = path.join(ROOT, "src");

// ---------------------------------------------------------------------------
// Step 1: Fetch or generate the OpenAPI JSON
// ---------------------------------------------------------------------------

async function fetchOpenAPI(): Promise<object> {
  // Try live API first
  try {
    const res = await fetch("http://localhost:8000/openapi.json", {
      signal: AbortSignal.timeout(3000),
    });
    if (res.ok) {
      const data = await res.json();
      console.log("  [codegen] OpenAPI fetched from live API at localhost:8000");
      return data as object;
    }
  } catch {
    // fall through to in-process generation
  }

  // In-process extraction via Python
  console.log("  [codegen] No live API — generating via Python in-process...");
  const result = spawnSync(
    "python",
    ["-c", `from app.main import app; import json; print(json.dumps(app.openapi()))`],
    { cwd: APPS_API_DIR, encoding: "utf8", timeout: 30_000 }
  );

  if (result.status !== 0) {
    const cached = loadSnapshot();
    if (cached) {
      console.warn("  [codegen] Python generation failed; using cached snapshot.");
      return cached;
    }
    throw new Error(
      `Python in-process extraction failed:\n${result.stderr}\n${result.stdout}`
    );
  }

  const raw = result.stdout.trim();
  return JSON.parse(raw) as object;
}

function loadSnapshot(): object | null {
  try {
    return JSON.parse(fs.readFileSync(SNAPSHOT_PATH, "utf8")) as object;
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Step 2: Pipe through openapi-typescript
// ---------------------------------------------------------------------------

async function generateOpenAPITypes(schema: object): Promise<string> {
  // openapi-typescript v7 accepts a URL or parsed object; returns AST nodes
  const ot = await import("openapi-typescript");
  const openapiTS = ot.default;
  const astToString = ot.astToString;
  const nodes = await openapiTS(schema as Parameters<typeof openapiTS>[0]);
  if (Array.isArray(nodes)) {
    return astToString(nodes);
  }
  return String(nodes);
}

// ---------------------------------------------------------------------------
// Step 3: Generate Zod schemas by walking components.schemas
// ---------------------------------------------------------------------------

type OpenAPISchema = {
  type?: string;
  enum?: unknown[];
  properties?: Record<string, OpenAPISchema>;
  required?: string[];
  $ref?: string;
  anyOf?: OpenAPISchema[];
  oneOf?: OpenAPISchema[];
  items?: OpenAPISchema;
  additionalProperties?: boolean | OpenAPISchema;
  discriminator?: { propertyName: string; mapping: Record<string, string> };
  default?: unknown;
  description?: string;
  title?: string;
  [key: string]: unknown;
};

type OpenAPIDocument = {
  components?: {
    schemas?: Record<string, OpenAPISchema>;
  };
  paths?: Record<string, unknown>;
};

function refToName(ref: string): string {
  // "#/components/schemas/Foo" -> "Foo"
  return ref.split("/").pop() ?? ref;
}

/**
 * Convert an OpenAPI component name (which may contain hyphens for FastAPI's
 * Input/Output split — e.g. "DataikuRecipeModel-Input") into a valid JS
 * identifier (`DataikuRecipeModelInput`). Same transform applied to both the
 * declaration and every reference.
 */
function safeIdent(name: string): string {
  return name.replace(/[^A-Za-z0-9_]/g, "");
}

function schemaToZod(schema: OpenAPISchema, allSchemas: Record<string, OpenAPISchema>, indent: number): string {
  const pad = "  ".repeat(indent);

  if (schema.$ref) {
    const name = safeIdent(refToName(schema.$ref));
    return `${name}Schema`;
  }

  // anyOf / oneOf without discriminator -> z.union
  if (schema.anyOf || schema.oneOf) {
    const variants = (schema.anyOf ?? schema.oneOf)!;
    // Filter null variants out; handle nullable separately
    const nonNull = variants.filter(
      (v) => !(v.type === "null")
    );
    const hasNull = variants.some((v) => v.type === "null");

    if (nonNull.length === 0) return "z.null()";

    let inner: string;
    if (nonNull.length === 1) {
      inner = schemaToZod(nonNull[0]!, allSchemas, indent);
    } else if (
      schema.discriminator?.propertyName &&
      nonNull.every((v) => v.$ref)
    ) {
      // Discriminated union
      const disc = JSON.stringify(schema.discriminator.propertyName);
      const members = nonNull
        .map((v) => `${pad}    ${schemaToZod(v, allSchemas, indent + 2)}`)
        .join(",\n");
      inner = `z.discriminatedUnion(${disc}, [\n${members}\n${pad}  ])`;
    } else {
      const members = nonNull
        .map((v) => `${pad}    ${schemaToZod(v, allSchemas, indent + 2)}`)
        .join(",\n");
      inner = `z.union([\n${members}\n${pad}  ])`;
    }

    return hasNull ? `${inner}.nullable()` : inner;
  }

  if (schema.enum !== undefined) {
    const values = schema.enum.map((v) => JSON.stringify(v)).join(", ");
    return `z.enum([${values}])`;
  }

  switch (schema.type) {
    case "string":
      return "z.string()";
    case "integer":
    case "number":
      return "z.number()";
    case "boolean":
      return "z.boolean()";
    case "null":
      return "z.null()";
    case "array": {
      const items = schema.items
        ? schemaToZod(schema.items, allSchemas, indent)
        : "z.unknown()";
      return `z.array(${items})`;
    }
    case "object": {
      if (!schema.properties || Object.keys(schema.properties).length === 0) {
        if (schema.additionalProperties === true || schema.additionalProperties !== false) {
          return "z.record(z.string(), z.unknown())";
        }
        return "z.object({})";
      }

      const requiredSet = new Set(schema.required ?? []);
      const props = Object.entries(schema.properties)
        .map(([key, propSchema]) => {
          const zodType = schemaToZod(propSchema, allSchemas, indent + 1);
          const optional = !requiredSet.has(key);
          // Add default if present
          const hasDefault = propSchema.default !== undefined;
          let field = zodType;
          if (optional && !hasDefault) field = `${zodType}.optional()`;
          return `${pad}  ${JSON.stringify(key)}: ${field}`;
        })
        .join(",\n");

      let obj = `z.object({\n${props}\n${pad}})`;
      // If additionalProperties is not false, allow passthrough
      if (schema.additionalProperties !== false) {
        obj = `${obj}.passthrough()`;
      }
      return obj;
    }
    default:
      return "z.unknown()";
  }
}

function generateZodSchemas(openapi: OpenAPIDocument): string {
  const schemas = openapi.components?.schemas ?? {};
  const lines: string[] = [
    '// AUTO-GENERATED — do not edit. Run `pnpm codegen`',
    "// Zod runtime schemas generated from /openapi.json components.schemas",
    "",
    'import { z } from "zod";',
    "",
  ];

  // Separate enums from objects; enums are self-contained and come first
  const enumNames: string[] = [];
  const objectNames: string[] = [];

  for (const [name, schema] of Object.entries(schemas)) {
    if (schema.enum !== undefined) {
      enumNames.push(name);
    } else {
      objectNames.push(name);
    }
  }

  // Emit enums first
  for (const name of enumNames) {
    const schema = schemas[name]!;
    const ident = safeIdent(name);
    const values = schema.enum!.map((v) => JSON.stringify(v)).join(", ");
    lines.push(`export const ${ident}Schema = z.enum([${values}]);`);
    lines.push(`export type ${ident} = z.infer<typeof ${ident}Schema>;`);
    lines.push("");
  }

  // Discriminated-union schema for RecipeSettings
  // Emitted before DataikuRecipeModel so the reference resolves
  const settingsKinds = [
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

  // Topologically sort object schemas so dependencies come first
  const emitted = new Set<string>(enumNames);

  function emitSchema(name: string, visitStack: Set<string> = new Set()): void {
    if (emitted.has(name)) return;
    if (visitStack.has(name)) return; // cycle guard

    const schema = schemas[name];
    if (!schema) return;

    visitStack.add(name);

    // Emit dependencies first
    if (schema.properties) {
      for (const propSchema of Object.values(schema.properties)) {
        collectRefs(propSchema).forEach((dep) => emitSchema(dep, visitStack));
      }
    }
    collectRefs(schema).forEach((dep) => {
      if (dep !== name) emitSchema(dep, visitStack);
    });

    visitStack.delete(name);
    if (emitted.has(name)) return;

    emitted.add(name);

    const zodExpr = schemaToZod(schema, schemas, 0);
    const ident = safeIdent(name);
    lines.push(`export const ${ident}Schema = ${zodExpr};`);
    lines.push(`export type ${ident} = z.infer<typeof ${ident}Schema>;`);
    lines.push("");
  }

  function collectRefs(schema: OpenAPISchema): string[] {
    const refs: string[] = [];
    if (schema.$ref) refs.push(refToName(schema.$ref));
    if (schema.properties) {
      for (const v of Object.values(schema.properties)) {
        refs.push(...collectRefs(v));
      }
    }
    (schema.anyOf ?? []).forEach((v) => refs.push(...collectRefs(v)));
    (schema.oneOf ?? []).forEach((v) => refs.push(...collectRefs(v)));
    if (schema.items) refs.push(...collectRefs(schema.items));
    return refs;
  }

  // Emit settings subclasses first
  for (const name of settingsKinds) {
    emitSchema(name);
  }

  // Emit RecipeSettingsModel discriminated union
  if (!emitted.has("RecipeSettingsModel") && settingsKinds.every((n) => emitted.has(n))) {
    emitted.add("RecipeSettingsModel");
    const members = settingsKinds
      .map((n) => `  ${n}Schema`)
      .join(",\n");
    lines.push(`export const RecipeSettingsModelSchema = z.discriminatedUnion("kind", [`);
    lines.push(members);
    lines.push(`]);`);
    lines.push(`export type RecipeSettingsModel = z.infer<typeof RecipeSettingsModelSchema>;`);
    lines.push("");
  }

  // Emit remaining object schemas in dependency order
  for (const name of objectNames) {
    emitSchema(name);
  }

  // FastAPI sometimes splits a single Pydantic model into "<Name>-Input" and
  // "<Name>-Output" variants when the model is consumed in both request and
  // response bodies (and `extra="allow"` further forces the split). Tests and
  // the public API surface refer to the bare name, so alias the Output variant
  // under the bare identifier when both are present. We pick Output because
  // that's what `/convert` returns and what the bulk of consumers care about.
  const allNames = new Set(objectNames);
  for (const name of objectNames) {
    if (!name.endsWith("-Output")) continue;
    const base = name.slice(0, -"-Output".length);
    // Skip if a bare schema already exists (no split happened).
    if (allNames.has(base)) continue;
    const baseIdent = safeIdent(base);
    const outputIdent = safeIdent(name);
    lines.push(`export const ${baseIdent}Schema = ${outputIdent}Schema;`);
    lines.push(`export type ${baseIdent} = z.infer<typeof ${baseIdent}Schema>;`);
    lines.push("");
  }

  return lines.join("\n");
}

// ---------------------------------------------------------------------------
// Step 4: Emit src/index.ts
// ---------------------------------------------------------------------------

function generateIndex(openapi: OpenAPIDocument): string {
  // FastAPI may split a model into <Name>-Input/-Output variants when it's
  // used in both request and response bodies (especially with
  // `model_config = {"extra": "allow"}`). For convenience-aliased types we
  // pick the Output variant when both exist, falling back to the bare name.
  const schemas = openapi.components?.schemas ?? {};
  const pickKey = (base: string): string =>
    schemas[base] ? base : `${base}-Output`;
  const flowKey = pickKey("DataikuFlowModel");
  const recipeKey = pickKey("DataikuRecipeModel");
  const datasetKey = pickKey("DataikuDatasetModel");

  return `// AUTO-GENERATED — do not edit. Run \`pnpm codegen\`
// Public API for @py-iku-studio/types

export type { components, paths, operations } from "./openapi.js";

export * from "./zod.js";

// Convenience type aliases from generated components
import type { components } from "./openapi.js";

export type DataikuFlow = components["schemas"]["${flowKey}"];
export type DataikuRecipe = components["schemas"]["${recipeKey}"];
export type DataikuDataset = components["schemas"]["${datasetKey}"];
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
`;
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main(): Promise<void> {
  console.log("[codegen] Starting types codegen...");

  // 1. Get OpenAPI JSON
  const openapi = await fetchOpenAPI();

  // 2. Save snapshot
  const snapshotJson = JSON.stringify(openapi, null, 2);
  fs.writeFileSync(SNAPSHOT_PATH, snapshotJson, "utf8");
  console.log(`  [codegen] Snapshot saved to openapi.snapshot.json`);

  // 3. Generate openapi.ts via openapi-typescript
  fs.mkdirSync(SRC_DIR, { recursive: true });
  const openapiTS = await generateOpenAPITypes(openapi);
  const openapiTSWithHeader =
    `// AUTO-GENERATED — do not edit. Run \`pnpm codegen\`\n` +
    `// Generated by openapi-typescript from /openapi.json\n\n` +
    openapiTS;
  fs.writeFileSync(path.join(SRC_DIR, "openapi.ts"), openapiTSWithHeader, "utf8");
  console.log("  [codegen] src/openapi.ts written");

  // 4. Generate zod.ts
  const zodTS = generateZodSchemas(openapi as OpenAPIDocument);
  fs.writeFileSync(path.join(SRC_DIR, "zod.ts"), zodTS, "utf8");
  console.log("  [codegen] src/zod.ts written");

  // 5. Write index.ts
  fs.writeFileSync(
    path.join(SRC_DIR, "index.ts"),
    generateIndex(openapi as OpenAPIDocument),
    "utf8",
  );
  console.log("  [codegen] src/index.ts written");

  // 6. Summary
  const doc = openapi as OpenAPIDocument;
  const schemas = doc.components?.schemas ?? {};
  const enumCount = Object.values(schemas).filter((s) => s.enum !== undefined).length;
  const schemaCount = Object.keys(schemas).length;
  const pathCount = Object.keys(doc.paths ?? {}).length;

  const openapiLines = openapiTSWithHeader.split("\n").length;
  const zodLines = zodTS.split("\n").length;

  console.log(`
[codegen] Summary
  schemas generated : ${schemaCount}
  enums             : ${enumCount}
  object schemas    : ${schemaCount - enumCount}
  paths covered     : ${pathCount}
  src/openapi.ts    : ${openapiLines} lines
  src/zod.ts        : ${zodLines} lines
`);
}

main().catch((err) => {
  console.error("[codegen] FATAL:", err);
  process.exit(1);
});
