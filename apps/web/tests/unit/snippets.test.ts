import { describe, it, expect } from "vitest";
import { SNIPPETS, getSnippet, getDefaultCode, DEFAULT_SNIPPET_ID } from "../../src/features/editor/snippets";

describe("snippets gallery", () => {
  it("ships at least 6 snippets", () => {
    expect(SNIPPETS.length).toBeGreaterThanOrEqual(6);
  });

  it("every snippet has the required fields populated", () => {
    for (const s of SNIPPETS) {
      expect(s.id).toMatch(/^[a-z0-9-]+$/);
      expect(s.name.trim().length).toBeGreaterThan(0);
      expect(s.description.trim().length).toBeGreaterThan(0);
      expect(s.code.trim().length).toBeGreaterThan(0);
      expect(Array.isArray(s.tags)).toBe(true);
      expect(s.tags.length).toBeGreaterThan(0);
      for (const tag of s.tags) {
        expect(tag.trim().length).toBeGreaterThan(0);
      }
    }
  });

  it("ids are unique", () => {
    const ids = SNIPPETS.map((s) => s.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("names are unique", () => {
    const names = SNIPPETS.map((s) => s.name);
    expect(new Set(names).size).toBe(names.length);
  });

  it("covers the headline pandas/sklearn shapes from the plan", () => {
    const idsLower = new Set(SNIPPETS.map((s) => s.id.toLowerCase()));
    expect(idsLower.has("groupby-agg")).toBe(true);
    expect(idsLower.has("merge-two-dataframes")).toBe(true);
    expect(idsLower.has("sort-top-n")).toBe(true);
    expect(idsLower.has("pivot-melt")).toBe(true);
    expect(idsLower.has("window-rolling")).toBe(true);
    expect(idsLower.has("sklearn-train-test-logistic")).toBe(true);
  });

  it("getSnippet() returns the matching snippet and undefined for misses", () => {
    expect(getSnippet("merge-two-dataframes")?.name).toMatch(/merge/i);
    expect(getSnippet("does-not-exist")).toBeUndefined();
  });

  it("getDefaultCode() returns the default snippet's code", () => {
    const expected = getSnippet(DEFAULT_SNIPPET_ID)?.code;
    expect(expected).toBeDefined();
    expect(getDefaultCode()).toBe(expected);
  });

  it("snippets reference real py-iku patterns (smoke check)", () => {
    const all = SNIPPETS.map((s) => s.code).join("\n");
    expect(all).toMatch(/import pandas as pd/);
    expect(all).toMatch(/groupby/);
    expect(all).toMatch(/pd\.merge/);
    expect(all).toMatch(/nlargest/);
    expect(all).toMatch(/pd\.melt/);
    expect(all).toMatch(/rolling/);
    expect(all).toMatch(/train_test_split/);
    expect(all).toMatch(/LogisticRegression/);
  });
});
