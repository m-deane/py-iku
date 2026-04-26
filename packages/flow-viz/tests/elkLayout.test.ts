import { describe, expect, it } from "vitest";
import type { Edge, Node } from "reactflow";
import { layoutFlow } from "../src/layout/elkLayout";
import type { DatasetNodeData, RecipeNodeData } from "../src/types";

describe("layoutFlow (ELK)", () => {
  function fixture(): { nodes: Node<RecipeNodeData | DatasetNodeData>[]; edges: Edge[] } {
    const nodes: Node<RecipeNodeData | DatasetNodeData>[] = [
      {
        id: "ds_in",
        type: "dataset",
        position: { x: 0, y: 0 },
        data: { datasetType: "INPUT", connectionType: "SQL_POSTGRESQL", name: "in" },
      },
      {
        id: "rec_prep",
        type: "recipe",
        position: { x: 0, y: 0 },
        data: { type: "PREPARE", name: "prep", inputs: 1, outputs: 1 },
      },
      {
        id: "rec_group",
        type: "recipe",
        position: { x: 0, y: 0 },
        data: { type: "GROUPING", name: "agg", inputs: 1, outputs: 1 },
      },
      {
        id: "rec_split",
        type: "recipe",
        position: { x: 0, y: 0 },
        data: { type: "SPLIT", name: "split", inputs: 1, outputs: 2 },
      },
      {
        id: "ds_out",
        type: "dataset",
        position: { x: 0, y: 0 },
        data: { datasetType: "OUTPUT", connectionType: "SQL_BIGQUERY", name: "out" },
      },
    ];
    const edges: Edge[] = [
      { id: "e1", source: "ds_in", target: "rec_prep" },
      { id: "e2", source: "rec_prep", target: "rec_group" },
      { id: "e3", source: "rec_group", target: "rec_split" },
      { id: "e4", source: "rec_split", target: "ds_out" },
    ];
    return { nodes, edges };
  }

  it("assigns positions to every node", async () => {
    const { nodes, edges } = fixture();
    const result = await layoutFlow(nodes, edges);
    expect(result.nodes).toHaveLength(5);
    for (const n of result.nodes) {
      expect(n.position).toBeDefined();
      expect(typeof n.position!.x).toBe("number");
      expect(typeof n.position!.y).toBe("number");
    }
  });

  it("does not overlap nodes (bounding-box check)", async () => {
    const { nodes, edges } = fixture();
    const result = await layoutFlow(nodes, edges);
    type Box = { x: number; y: number; w: number; h: number; id: string };
    const boxes: Box[] = result.nodes.map((n) => ({
      id: n.id,
      x: n.position!.x,
      y: n.position!.y,
      w: n.type === "dataset" ? 160 : 70,
      h: n.type === "dataset" ? 50 : 70,
    }));
    for (let i = 0; i < boxes.length; i++) {
      for (let j = i + 1; j < boxes.length; j++) {
        const a = boxes[i];
        const b = boxes[j];
        const overlap =
          a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
        expect(overlap, `${a.id} overlaps ${b.id}`).toBe(false);
      }
    }
  });

  it("preserves edge identity (no edge loops added)", async () => {
    const { nodes, edges } = fixture();
    const result = await layoutFlow(nodes, edges);
    expect(result.edges).toHaveLength(4);
    for (const e of result.edges) {
      expect(e.source).not.toBe(e.target);
    }
  });

  it("returns empty arrays unchanged for an empty flow", async () => {
    const result = await layoutFlow([], []);
    expect(result.nodes).toEqual([]);
    expect(result.edges).toEqual([]);
  });
});
