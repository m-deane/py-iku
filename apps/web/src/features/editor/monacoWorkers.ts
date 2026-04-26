/// <reference types="vite/client" />
/**
 * monacoWorkers.ts — wires Monaco's worker URLs using Vite's `?worker` import.
 *
 * Imported as a side-effect from `main.tsx`; without this, Monaco falls back to
 * synchronous parsing on the main thread (sluggish) and logs a warning.
 *
 * We only ship the `editor.worker` because the studio currently exposes a single
 * Python file in the editor. JSON / TS / CSS / HTML workers would be wasted bytes.
 */

import EditorWorker from "monaco-editor/esm/vs/editor/editor.worker?worker";

if (typeof window !== "undefined" && !window.MonacoEnvironment) {
  window.MonacoEnvironment = {
    getWorker(_workerId: string, _label: string): Worker {
      return new EditorWorker();
    },
  };
}

export {};
