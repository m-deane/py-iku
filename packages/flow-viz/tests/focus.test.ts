import { describe, expect, it } from "vitest";
import { computeFocus } from "../src/focus/useFocusMode";
import type { FlowEdge } from "../src/types";

describe("computeFocus", () => {
  const edges: FlowEdge[] = [
    { id: "e1", source: "a", target: "b" },
    { id: "e2", source: "b", target: "c" },
    { id: "e3", source: "c", target: "d" },
    { id: "e4", source: "x", target: "b" }, // alt parent
    { id: "e5", source: "c", target: "y" }, // alt child
  ];

  it("returns no focus when no node is selected", () => {
    const r = computeFocus(null, edges);
    expect(r.isFocusActive).toBe(false);
    expect(r.focusedIds.size).toBe(0);
  });

  it("includes the selected node and its ancestors + descendants", () => {
    const r = computeFocus("c", edges);
    expect(r.isFocusActive).toBe(true);
    // Ancestors of c: a, b, x. Descendants: d, y. Plus c itself.
    expect(r.focusedIds.has("a")).toBe(true);
    expect(r.focusedIds.has("b")).toBe(true);
    expect(r.focusedIds.has("c")).toBe(true);
    expect(r.focusedIds.has("d")).toBe(true);
    expect(r.focusedIds.has("x")).toBe(true);
    expect(r.focusedIds.has("y")).toBe(true);
  });

  it("excludes unrelated nodes", () => {
    const isolated: FlowEdge[] = [
      { id: "e1", source: "a", target: "b" },
      { id: "e2", source: "x", target: "y" },
    ];
    const r = computeFocus("a", isolated);
    expect(r.focusedIds.has("a")).toBe(true);
    expect(r.focusedIds.has("b")).toBe(true);
    expect(r.focusedIds.has("x")).toBe(false);
    expect(r.focusedIds.has("y")).toBe(false);
  });
});
