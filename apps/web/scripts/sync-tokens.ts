/**
 * sync-tokens.ts — reads docs/design/tokens.json and emits src/styles/tokens.css.
 *
 * Emits a `:root` block (light theme) and a `[data-theme="dark"]` block (dark theme).
 * Variables are flattened from the nested tokens JSON using a `--<segment>-<segment>` naming
 * convention. Values that contain "TODO" markers are emitted as comments so that downstream
 * CSS is still valid.
 *
 * If tokens.json is missing (M2 not yet shipped), a stub file is emitted with a single TODO
 * comment so that `import "./styles/tokens.css"` still resolves.
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const TOKENS_PATH = resolve(__dirname, "../../../docs/design/tokens.json");
const OUT_PATH = resolve(__dirname, "../src/styles/tokens.css");

type Json = string | number | boolean | null | Json[] | { [k: string]: Json };

function flatten(prefix: string, node: Json, out: Map<string, string>): void {
  if (node === null) return;
  if (typeof node === "string" || typeof node === "number" || typeof node === "boolean") {
    out.set(prefix, String(node));
    return;
  }
  if (Array.isArray(node)) {
    node.forEach((child, i) => flatten(`${prefix}-${i}`, child, out));
    return;
  }
  for (const [key, value] of Object.entries(node)) {
    if (key === "note" || key.startsWith("_")) continue; // skip documentation notes
    const slug = key.toLowerCase().replace(/[^a-z0-9]+/g, "-");
    flatten(prefix ? `${prefix}-${slug}` : `--${slug}`, value, out);
  }
}

function renderBlock(selector: string, vars: Map<string, string>): string {
  const lines: string[] = [`${selector} {`];
  for (const [name, value] of vars) {
    if (value.includes("TODO")) {
      lines.push(`  /* ${name}: ${value}; */`);
    } else {
      lines.push(`  ${name}: ${value};`);
    }
  }
  lines.push("}");
  return lines.join("\n");
}

function main(): void {
  mkdirSync(dirname(OUT_PATH), { recursive: true });

  if (!existsSync(TOKENS_PATH)) {
    const stub = [
      "/* tokens.css — STUB */",
      "/* TODO: docs/design/tokens.json not found yet (M2 in flight). */",
      "/* This file will be regenerated once tokens land. */",
      ":root {",
      "  --color-bg: #FAFAFA;",
      "  --color-fg: #212121;",
      "  --color-accent: #1976D2;",
      "}",
      '[data-theme="dark"] {',
      "  --color-bg: #1E1E1E;",
      "  --color-fg: #EEEEEE;",
      "  --color-accent: #64B5F6;",
      "}",
      "",
    ].join("\n");
    writeFileSync(OUT_PATH, stub, "utf8");
    console.log(`[sync-tokens] tokens.json missing — wrote stub to ${OUT_PATH}`);
    return;
  }

  const raw = readFileSync(TOKENS_PATH, "utf8");
  const tokens = JSON.parse(raw) as Json;

  // Split light vs dark by walking color.theme.{light,dark} into separate buckets,
  // and emit non-color tokens once into :root.
  const light = new Map<string, string>();
  const dark = new Map<string, string>();
  const shared = new Map<string, string>();

  if (typeof tokens === "object" && tokens !== null && !Array.isArray(tokens)) {
    for (const [topKey, topValue] of Object.entries(tokens)) {
      if (topKey === "color") {
        if (typeof topValue === "object" && topValue !== null && !Array.isArray(topValue)) {
          for (const [colorKey, colorValue] of Object.entries(topValue)) {
            if (colorKey === "theme") {
              if (
                typeof colorValue === "object" &&
                colorValue !== null &&
                !Array.isArray(colorValue)
              ) {
                if ("light" in colorValue) flatten("--color", colorValue.light as Json, light);
                if ("dark" in colorValue) flatten("--color", colorValue.dark as Json, dark);
              }
            } else {
              // recipe / dataset / connection groups — emit per theme variants
              flatten(`--color-${colorKey.toLowerCase()}`, colorValue, shared);
            }
          }
        }
      } else {
        flatten(`--${topKey.toLowerCase()}`, topValue, shared);
      }
    }
  }

  // Emit backward-compat aliases consumed by datasetStripe.tsx and the
  // recipe-family CSS in ui-tokens.css. The flow.* block in tokens.json is
  // canonical; these aliases preserve the names used by Sprint-1 / Sprint-6
  // consumers without a hard rename.
  emitFlowAliases(tokens, shared);
  emitFlowAliasesDark(tokens, dark);

  const root = new Map<string, string>([...shared, ...light]);
  const out = `${renderBlock(":root", root)}\n\n${renderBlock('[data-theme="dark"]', dark)}\n`;
  writeFileSync(OUT_PATH, out, "utf8");
  console.log(`[sync-tokens] wrote ${root.size + dark.size} variables to ${OUT_PATH}`);
}

/**
 * Emit `--dataset-stripe-<family>` and `--recipe-<type>` aliases sourced from
 * the canonical `flow.*` block. Keeps existing CSS variable names stable for
 * datasetStripe.tsx (`var(--dataset-stripe-filesystem)`) and the recipe-family
 * tokens that ui-tokens.css used to define manually.
 */
function emitFlowAliases(tokens: Json, out: Map<string, string>): void {
  if (typeof tokens !== "object" || tokens === null || Array.isArray(tokens)) return;
  const flow = (tokens as { flow?: Json }).flow;
  if (typeof flow !== "object" || flow === null || Array.isArray(flow)) return;

  const dataset = (flow as { dataset?: Json }).dataset;
  if (typeof dataset === "object" && dataset !== null && !Array.isArray(dataset)) {
    const stripe = (dataset as { stripe?: Json }).stripe;
    if (typeof stripe === "object" && stripe !== null && !Array.isArray(stripe)) {
      for (const [family, hex] of Object.entries(stripe)) {
        if (typeof hex === "string" && !hex.includes("TODO")) {
          out.set(`--dataset-stripe-${family.toLowerCase().replace(/_/g, "-")}`, hex);
        }
      }
    }
  }

  const recipe = (flow as { recipe?: Json }).recipe;
  if (typeof recipe === "object" && recipe !== null && !Array.isArray(recipe)) {
    for (const [name, triplet] of Object.entries(recipe)) {
      if (
        typeof triplet === "object" &&
        triplet !== null &&
        !Array.isArray(triplet) &&
        typeof (triplet as { bg?: unknown }).bg === "string"
      ) {
        out.set(
          `--recipe-${name.toLowerCase().replace(/_/g, "-")}`,
          (triplet as { bg: string }).bg,
        );
      }
    }
  }

  const edge = (flow as { edge?: Json }).edge;
  if (typeof edge === "object" && edge !== null && !Array.isArray(edge)) {
    const stroke = (edge as { stroke?: unknown }).stroke;
    if (typeof stroke === "string" && !stroke.includes("TODO")) {
      out.set("--edge-stroke", stroke);
    }
  }
}

/**
 * Emit dark-mode overrides for `--dataset-stripe-<family>`, `--recipe-<type>`
 * and `--edge-stroke` from the canonical `flow.*_dark` blocks. These end up
 * in the `[data-theme="dark"]` selector in tokens.css.
 */
function emitFlowAliasesDark(tokens: Json, out: Map<string, string>): void {
  if (typeof tokens !== "object" || tokens === null || Array.isArray(tokens)) return;
  const flow = (tokens as { flow?: Json }).flow;
  if (typeof flow !== "object" || flow === null || Array.isArray(flow)) return;

  const dataset = (flow as { dataset?: Json }).dataset;
  if (typeof dataset === "object" && dataset !== null && !Array.isArray(dataset)) {
    const stripeDark = (dataset as { stripe_dark?: Json }).stripe_dark;
    if (typeof stripeDark === "object" && stripeDark !== null && !Array.isArray(stripeDark)) {
      for (const [family, hex] of Object.entries(stripeDark)) {
        if (typeof hex === "string" && !hex.includes("TODO")) {
          out.set(`--dataset-stripe-${family.toLowerCase().replace(/_/g, "-")}`, hex);
        }
      }
    }
  }

  const recipeDark = (flow as { recipe_dark_alias?: Json }).recipe_dark_alias;
  if (typeof recipeDark === "object" && recipeDark !== null && !Array.isArray(recipeDark)) {
    for (const [name, hex] of Object.entries(recipeDark)) {
      if (
        typeof hex === "string" &&
        !hex.includes("TODO") &&
        name !== "note" &&
        !name.startsWith("_")
      ) {
        out.set(`--recipe-${name.toLowerCase().replace(/_/g, "-")}`, hex);
      }
    }
  }

  const edgeDark = (flow as { edge_dark?: Json }).edge_dark;
  if (typeof edgeDark === "object" && edgeDark !== null && !Array.isArray(edgeDark)) {
    const stroke = (edgeDark as { stroke?: unknown }).stroke;
    if (typeof stroke === "string" && !stroke.includes("TODO")) {
      out.set("--edge-stroke", stroke);
    }
  }
}

main();
