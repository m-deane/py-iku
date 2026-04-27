/**
 * Vitest setup. Stubs browser APIs that ReactFlow / ELK touch but jsdom does
 * not implement. Importing this file once per test run via vitest config.
 */

import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";

// jsdom lacks ResizeObserver; React Flow uses it for fit-to-viewport.
class StubResizeObserver {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
if (typeof globalThis.ResizeObserver === "undefined") {
  (globalThis as unknown as { ResizeObserver: typeof StubResizeObserver }).ResizeObserver =
    StubResizeObserver;
}

// jsdom lacks DOMMatrixReadOnly used by reactflow internals in some paths.
if (typeof (globalThis as { DOMMatrixReadOnly?: unknown }).DOMMatrixReadOnly === "undefined") {
  (globalThis as unknown as { DOMMatrixReadOnly: unknown }).DOMMatrixReadOnly = class {};
}

afterEach(() => {
  cleanup();
});
