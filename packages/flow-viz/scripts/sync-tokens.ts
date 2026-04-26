/**
 * sync-tokens.ts — flow-viz local copy of the tokens-CSS generator.
 *
 * Reads `docs/design/tokens.json` and emits `src/theme/tokens.css` containing a
 * `:root` block (light theme + non-color shared tokens) and a
 * `[data-theme="dark"]` block (dark-theme color overrides).
 *
 * This is intentionally duplicated from `apps/web/scripts/sync-tokens.ts` so
 * that the package is self-contained and can be published independently. M4b
 * may switch `apps/web` to import this module from `@py-iku-studio/flow-viz`
 * once the package builds an exported `tokens.css`. Both scripts MUST stay in
 * sync until that consolidation lands; the flatten/render logic is identical.
 *
 * Values that contain "TODO" markers (designer-decision gaps) are emitted as
 * CSS comments so that downstream stylesheets remain valid and the gap is
 * still visible in the generated artifact.
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const TOKENS_PATH = resolve(__dirname, "../../../docs/design/tokens.json");
const OUT_PATH = resolve(__dirname, "../src/theme/tokens.css");

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
    if (key === "note") continue;
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
      "/* TODO: docs/design/tokens.json not found. */",
      ":root { --color-bg: #FAFAFA; --color-fg: #212121; }",
      '[data-theme="dark"] { --color-bg: #1E1E1E; --color-fg: #EEEEEE; }',
      "",
    ].join("\n");
    writeFileSync(OUT_PATH, stub, "utf8");
    console.log(`[flow-viz/sync-tokens] tokens.json missing — wrote stub to ${OUT_PATH}`);
    return;
  }

  const raw = readFileSync(TOKENS_PATH, "utf8");
  const tokens = JSON.parse(raw) as Json;

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
              flatten(`--color-${colorKey.toLowerCase()}`, colorValue, shared);
            }
          }
        }
      } else {
        flatten(`--${topKey.toLowerCase()}`, topValue, shared);
      }
    }
  }

  const root = new Map<string, string>([...shared, ...light]);
  const out = `${renderBlock(":root", root)}\n\n${renderBlock('[data-theme="dark"]', dark)}\n`;
  writeFileSync(OUT_PATH, out, "utf8");
  console.log(
    `[flow-viz/sync-tokens] wrote ${root.size + dark.size} variables to ${OUT_PATH}`,
  );
}

main();
