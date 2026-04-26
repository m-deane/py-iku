/**
 * sync-api-reference.ts
 *
 * Drift check between packages/types/openapi.snapshot.json and the
 * hand-authored API reference MDX pages under apps/docs/docs/api-reference/.
 *
 * Why a drift check rather than a generator? The MDX pages include curated
 * examples, narrative, and cross-links that a generic generator can't
 * produce well. Drift between the routes and the docs is the real risk —
 * this script catches it.
 *
 * Exits non-zero if any documented path is missing from the snapshot or
 * any snapshot path is undocumented.
 *
 * Usage:
 *   cd apps/docs
 *   pnpm tsx scripts/sync-api-reference.ts            # report-only
 *   pnpm tsx scripts/sync-api-reference.ts --quiet    # exit code only
 */

import * as fs from "fs";
import * as path from "path";

const SNAPSHOT_PATH = path.resolve(
  __dirname,
  "../../../packages/types/openapi.snapshot.json",
);
const API_REF_DIR = path.resolve(__dirname, "../docs/api-reference");

interface OpenApiSnapshot {
  info: { title: string; version: string };
  paths: Record<string, Record<string, unknown>>;
}

function loadSnapshot(): OpenApiSnapshot {
  if (!fs.existsSync(SNAPSHOT_PATH)) {
    console.error(`OpenAPI snapshot not found at: ${SNAPSHOT_PATH}`);
    process.exit(2);
  }
  return JSON.parse(fs.readFileSync(SNAPSHOT_PATH, "utf-8")) as OpenApiSnapshot;
}

// FastAPI's auto-mounted routes are documented elsewhere; not first-party.
const FASTAPI_DEFAULTS = new Set(["/openapi.json", "/docs", "/redoc"]);

function loadDocPaths(): Map<string, string> {
  const out = new Map<string, string>();
  if (!fs.existsSync(API_REF_DIR)) return out;
  const files = fs
    .readdirSync(API_REF_DIR)
    .filter((f) => f.endsWith(".md") || f.endsWith(".mdx"));
  for (const file of files) {
    const full = path.join(API_REF_DIR, file);
    // Strip MDX-escape backslashes before regex so /flows/\{id\} → /flows/{id}.
    const text = fs.readFileSync(full, "utf-8").replace(/\\([{}])/g, "$1");
    const matches = text.matchAll(
      /(?:GET|POST|PATCH|DELETE|PUT|WS)\s+(\/[\w/{}.-]*)/g,
    );
    for (const m of matches) {
      const docPath = m[1].replace(/\/+$/, "");
      if (!docPath || FASTAPI_DEFAULTS.has(docPath)) continue;
      // Skip /convert/stream — it's a WebSocket endpoint, not in the OpenAPI snapshot.
      if (docPath === "/convert/stream") continue;
      if (!out.has(docPath)) out.set(docPath, file);
    }
  }
  return out;
}

function normalizePathParams(p: string): string {
  return p.replace(/\{[^/}]+\}/g, "{X}");
}

function main(): void {
  const quiet = process.argv.includes("--quiet");
  const snapshot = loadSnapshot();
  const docPaths = loadDocPaths();

  const snapshotKeys = new Set(
    Object.keys(snapshot.paths).map(normalizePathParams),
  );
  const docKeys = new Set(
    Array.from(docPaths.keys()).map(normalizePathParams),
  );

  const missingFromDocs: string[] = [];
  for (const key of snapshotKeys) {
    if (!docKeys.has(key)) missingFromDocs.push(key);
  }
  const missingFromSnapshot: string[] = [];
  for (const key of docKeys) {
    if (!snapshotKeys.has(key)) missingFromSnapshot.push(key);
  }

  if (!quiet) {
    console.log(
      `Snapshot: ${snapshot.info.title} v${snapshot.info.version} (${snapshotKeys.size} paths)`,
    );
    console.log(`Docs:     ${docKeys.size} paths across ${new Set(docPaths.values()).size} MDX files`);
    if (missingFromDocs.length > 0) {
      console.error(
        `\nMissing from docs (${missingFromDocs.length}):`,
      );
      for (const p of missingFromDocs) console.error(`  - ${p}`);
    }
    if (missingFromSnapshot.length > 0) {
      console.error(
        `\nDocumented but not in snapshot (${missingFromSnapshot.length}):`,
      );
      for (const p of missingFromSnapshot) console.error(`  - ${p}`);
    }
  }

  const drift = missingFromDocs.length + missingFromSnapshot.length;
  if (drift > 0) {
    console.error(`\nDRIFT: ${drift} path${drift === 1 ? "" : "s"} mismatched.`);
    process.exit(1);
  }
  if (!quiet) console.log("\nNo drift.");
}

main();
