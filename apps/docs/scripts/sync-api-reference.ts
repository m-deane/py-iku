/**
 * sync-api-reference.ts
 *
 * Reads packages/types/openapi.snapshot.json and can emit MDX files for each
 * API path family into apps/docs/docs/api-reference/.
 *
 * TODO(M9-followup): This script is a stub. Auto-generation from the snapshot
 * was deferred in M9 in favour of hand-authored pages (which are richer and
 * include usage examples). To enable auto-generation:
 *
 * 1. Install `openapi-to-md` or a similar tool.
 * 2. Iterate over snapshot.paths entries.
 * 3. Group by path prefix (e.g. /catalog/* → catalog.md).
 * 4. Emit MDX with frontmatter, request/response tables, and example cURL.
 * 5. Skip paths that have hand-authored pages (allow-list approach).
 *
 * Usage (once implemented):
 *   cd apps/docs
 *   npx ts-node scripts/sync-api-reference.ts
 */

import * as fs from "fs";
import * as path from "path";

const SNAPSHOT_PATH = path.resolve(
  __dirname,
  "../../../packages/types/openapi.snapshot.json"
);

function main() {
  if (!fs.existsSync(SNAPSHOT_PATH)) {
    console.error(`OpenAPI snapshot not found at: ${SNAPSHOT_PATH}`);
    process.exit(1);
  }

  const snapshot = JSON.parse(fs.readFileSync(SNAPSHOT_PATH, "utf-8"));
  const paths = Object.keys(snapshot.paths ?? {});

  console.log(`OpenAPI snapshot loaded: ${snapshot.info.title} v${snapshot.info.version}`);
  console.log(`Paths found: ${paths.length}`);
  console.log(paths.map((p) => `  ${p}`).join("\n"));

  console.log(
    "\nTODO(M9-followup): Auto-generation not yet implemented. " +
    "API reference pages in apps/docs/docs/api-reference/ are hand-authored."
  );
}

main();
