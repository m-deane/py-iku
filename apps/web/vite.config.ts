import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// https://vite.dev/config/
//
// Monaco editor workers: we use the recommended `?worker` import pattern wired
// through `window.MonacoEnvironment.getWorker` (set up at the entry point in
// `src/main.tsx`). That keeps the bundle deterministic without pulling in
// `vite-plugin-monaco-editor`, which still depends on the deprecated
// monaco-editor-webpack-plugin shim. See `src/features/editor/monacoWorkers.ts`.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
      "@flow-viz": path.resolve(__dirname, "../../packages/flow-viz/src"),
      "@types": path.resolve(__dirname, "../../packages/types/src"),
    },
  },
  // Pre-bundle monaco for fast cold starts; without this Vite traverses every
  // monaco-editor language definition at startup and the dev server stalls.
  optimizeDeps: {
    include: ["monaco-editor/esm/vs/editor/editor.api"],
  },
  server: {
    port: 5173,
    proxy: {
      // Route API calls through the Vite proxy. The /api prefix is used as
      // a namespace to avoid conflicts with SPA client-side routes.
      "/api": "http://localhost:8000",
      // Also proxy /health so the e2e wait-for-port check can use the web port.
      "/health": "http://localhost:8000",
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    include: ["tests/**/*.test.{ts,tsx}"],
    setupFiles: ["./tests/setup.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text", "html", "lcov", "json-summary"],
      reportsDirectory: "coverage",
      // Only measure the production app, not tooling scripts.
      include: ["src/**/*.{ts,tsx}"],
      exclude: [
        "src/**/*.d.ts",
        "src/main.tsx",
        // Boot/wire-up shells: trivial JSX with no logic to assert against.
        "src/app/router.tsx",
        "src/app/providers.tsx",
        "src/components/AppLayout.tsx",
        "src/components/ThemeToggle.tsx",
        // Monaco workers are environment-only setup.
        "src/features/editor/monacoWorkers.ts",
        // WebSocket client is exercised end-to-end (see useConvertStream).
        "src/api/ws.ts",
      ],
      thresholds: {
        lines: 80,
        statements: 80,
      },
    },
  },
});
