import { describe, expect, it } from "vitest";
import { topologicalSort } from "../src/sim/useExecutionSim";
import type { FlowEdge, FlowNode } from "../src/types";

describe("topologicalSort", () => {
  it("orders a linear chain in source-to-sink order", () => {
    const nodes: FlowNode[] = [
      { id: "a", type: "dataset", data: { datasetType: "INPUT", connectionType: "S3", name: "a" } },
      { id: "b", type: "recipe", data: { type: "PREPARE", name: "b", inputs: 1, outputs: 1 } },
      { id: "c", type: "dataset", data: { datasetType: "OUTPUT", connectionType: "S3", name: "c" } },
    ];
    const edges: FlowEdge[] = [
      { id: "e1", source: "a", target: "b" },
      { id: "e2", source: "b", target: "c" },
    ];
    expect(topologicalSort(nodes, edges)).toEqual(["a", "b", "c"]);
  });

  it("places sources before downstream nodes for diamond DAGs", () => {
    const nodes: FlowNode[] = [
      { id: "a", type: "dataset", data: { datasetType: "INPUT", connectionType: "S3", name: "a" } },
      { id: "b", type: "recipe", data: { type: "PREPARE", name: "b", inputs: 1, outputs: 1 } },
      { id: "c", type: "recipe", data: { type: "GROUPING", name: "c", inputs: 1, outputs: 1 } },
      { id: "d", type: "recipe", data: { type: "JOIN", name: "d", inputs: 2, outputs: 1 } },
    ];
    const edges: FlowEdge[] = [
      { id: "e1", source: "a", target: "b" },
      { id: "e2", source: "a", target: "c" },
      { id: "e3", source: "b", target: "d" },
      { id: "e4", source: "c", target: "d" },
    ];
    const order = topologicalSort(nodes, edges);
    expect(order[0]).toBe("a");
    expect(order.indexOf("d")).toBeGreaterThan(order.indexOf("b"));
    expect(order.indexOf("d")).toBeGreaterThan(order.indexOf("c"));
  });

  it("returns every node even when a cycle is present", () => {
    const nodes: FlowNode[] = [
      { id: "a", type: "recipe", data: { type: "PREPARE", name: "a", inputs: 1, outputs: 1 } },
      { id: "b", type: "recipe", data: { type: "PREPARE", name: "b", inputs: 1, outputs: 1 } },
    ];
    const edges: FlowEdge[] = [
      { id: "e1", source: "a", target: "b" },
      { id: "e2", source: "b", target: "a" },
    ];
    const order = topologicalSort(nodes, edges);
    expect(order).toContain("a");
    expect(order).toContain("b");
    expect(order).toHaveLength(2);
  });
});
