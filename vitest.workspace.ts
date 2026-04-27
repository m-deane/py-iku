/**
 * Vitest workspace configuration.
 *
 * This file anchors the workspace shape for IDE tooling and documents which
 * packages participate in the cross-package test suite.
 *
 * USAGE:
 *   pnpm -r --if-present test     # primary: runs each package's own vitest
 *                                 #   in its own directory with correct env
 *   pnpm test                     # alias for the above (see root package.json)
 *
 * NOTE: Running `pnpm vitest run` from the repo root with this workspace
 * config requires all packages to share the same vitest major version. The
 * packages currently use a mix of vitest ^1.x (apps/web, packages/types) and
 * ^2.x (packages/flow-viz). Until M8 unifies them, use `pnpm -r test`.
 *
 * packages included:
 *   - apps/web          (vite.config.ts, vitest 1.x, jsdom env)
 *   - packages/flow-viz (vitest.config.ts, vitest 2.x, jsdom env)
 *   - packages/types    (vitest.config.ts, vitest 1.x, node env)
 */
import { defineWorkspace } from "vitest/config";

export default defineWorkspace([
  "apps/web/vite.config.ts",
  "packages/flow-viz/vitest.config.ts",
  "packages/types/vitest.config.ts",
]);
