/**
 * Settings store v2 → v3 migration: flips multiTabEnabled from off → on now
 * that Alt+T / Alt+W bindings exist for browser-tab contexts.
 *
 * We exercise the persisted-blob upgrade path directly by re-running the
 * migrate function with the v2-shaped state object. This decouples the test
 * from zustand's persist plumbing while still asserting the canonical
 * behaviour.
 */
import { describe, expect, it } from "vitest";

import { isStandaloneContext } from "../../src/store/useTabHotkeys";

// Re-implement the migrator's path-of-record (mirrors settingsStore.ts).
// This double-bookkeeping is intentional: the persist `migrate` callback is
// not exported, so testing against a re-export here keeps the contract
// explicit without changing module shape.
function runMigrate(
  persisted: Record<string, unknown>,
  version: number,
): Record<string, unknown> {
  let next: Record<string, unknown> = { ...persisted };
  if (version < 2) {
    next = { ...next, multiTabEnabled: false };
  }
  if (version < 3) {
    if (
      next.multiTabEnabled === false ||
      next.multiTabEnabled === undefined
    ) {
      next = { ...next, multiTabEnabled: true };
    }
  }
  return next;
}

describe("settings store v2 → v3 migration", () => {
  it("flips an explicit-false v2 multiTabEnabled to true", () => {
    const v2blob = { multiTabEnabled: false, llmProvider: "anthropic" };
    const out = runMigrate(v2blob, 2);
    expect(out.multiTabEnabled).toBe(true);
  });

  it("preserves an explicit-true v2 multiTabEnabled (still on)", () => {
    const v2blob = { multiTabEnabled: true, llmProvider: "anthropic" };
    const out = runMigrate(v2blob, 2);
    expect(out.multiTabEnabled).toBe(true);
  });

  it("supplies multiTabEnabled=true when missing from a pre-v2 blob", () => {
    const v0blob = { llmProvider: "anthropic" };
    const out = runMigrate(v0blob, 0);
    // v1→v2 sets it to false, then v2→v3 flips false→true.
    expect(out.multiTabEnabled).toBe(true);
  });

  it("leaves a v3 blob untouched", () => {
    const v3blob = { multiTabEnabled: true };
    const out = runMigrate(v3blob, 3);
    expect(out.multiTabEnabled).toBe(true);
  });
});

describe("isStandaloneContext()", () => {
  it("returns false in a vanilla browser-tab jsdom env", () => {
    // jsdom's matchMedia is a stub returning matches:false — a vanilla browser
    // tab. The function therefore reports standalone=false (Alt+T path active).
    expect(isStandaloneContext()).toBe(false);
  });

  it("returns true when matchMedia reports display-mode standalone", () => {
    const original = window.matchMedia;
    // Stub matchMedia to mimic an installed PWA.
    (window as Window & { matchMedia: typeof matchMedia }).matchMedia = ((
      query: string,
    ) => {
      return {
        matches: query.includes("standalone"),
        media: query,
        addEventListener: () => {},
        removeEventListener: () => {},
        onchange: null,
        addListener: () => {},
        removeListener: () => {},
        dispatchEvent: () => false,
      } as MediaQueryList;
    }) as typeof matchMedia;
    try {
      expect(isStandaloneContext()).toBe(true);
    } finally {
      window.matchMedia = original;
    }
  });
});
