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
      "/api": "http://localhost:8000",
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    include: ["tests/**/*.test.{ts,tsx}"],
    setupFiles: ["./tests/setup.ts"],
  },
});
