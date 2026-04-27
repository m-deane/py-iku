import { describe, expect, it } from "vitest";
import {
  autoAssignZones,
  ZONE_LABELS,
  ZONE_PALETTE_INDEX,
  ZONE_ORDER,
  getZoneColor,
  ZONE_PALETTE_SIZE,
  ZONE_RADIUS,
  ZONE_PADDING,
} from "../src/zones";
import type { FlowEdge, FlowNode } from "../src/types";

describe("autoAssignZones", () => {
  function fixture(): { nodes: FlowNode[]; edges: FlowEdge[] } {
    return {
      nodes: [
        { id: "in", type: "dataset", data: { datasetType: "INPUT", connectionType: "S3", name: "src" } },
        { id: "prep", type: "recipe", data: { type: "PREPARE", name: "p", inputs: 1, outputs: 1 } },
        { id: "score", type: "recipe", data: { type: "PREDICTION_SCORING", name: "ps", inputs: 1, outputs: 1 } },
        { id: "out", type: "dataset", data: { datasetType: "OUTPUT", connectionType: "S3", name: "dst" } },
      ],
      edges: [
        { id: "e1", source: "in", target: "prep" },
        { id: "e2", source: "prep", target: "score" },
        { id: "e3", source: "score", target: "out" },
      ],
    };
  }

  it("assigns inputs to 'input' zone", () => {
    const { nodes, edges } = fixture();
    const m = autoAssignZones(nodes, edges);
    expect(m.get("in")).toBe("input");
  });

  it("assigns outputs to 'output' zone", () => {
    const { nodes, edges } = fixture();
    const m = autoAssignZones(nodes, edges);
    expect(m.get("out")).toBe("output");
  });

  it("assigns ML recipes to 'ml' zone", () => {
    const { nodes, edges } = fixture();
    const m = autoAssignZones(nodes, edges);
    expect(m.get("score")).toBe("ml");
  });

  it("assigns prep recipes to 'prep' zone", () => {
    const { nodes, edges } = fixture();
    const m = autoAssignZones(nodes, edges);
    expect(m.get("prep")).toBe("prep");
  });
});

describe("zone tokens", () => {
  it("exposes 8 palette entries", () => {
    expect(ZONE_PALETTE_SIZE).toBe(8);
  });

  it("returns the M2 light fill for index 0", () => {
    expect(getZoneColor(0, "light").fill).toBe("#E3F2FD");
    expect(getZoneColor(0, "light").border).toBe("#90CAF9");
  });

  it("returns the M2 dark fill for index 0", () => {
    expect(getZoneColor(0, "dark").fill).toBe("#1A2744");
    expect(getZoneColor(0, "dark").border).toBe("#3F51B5");
  });

  it("wraps indices modulo palette size", () => {
    const at0 = getZoneColor(0, "light");
    const at8 = getZoneColor(8, "light");
    expect(at0.fill).toBe(at8.fill);
  });

  it("exposes constant defaults", () => {
    expect(ZONE_RADIUS).toBe(12);
    expect(ZONE_PADDING).toBe(24);
  });
});

describe("zone labels & order", () => {
  it("exposes 4 predefined zones in order", () => {
    expect(ZONE_ORDER).toEqual(["input", "prep", "ml", "output"]);
  });
  it("maps every predefined zone to a label and palette index", () => {
    for (const z of ZONE_ORDER) {
      expect(ZONE_LABELS[z]).toBeTruthy();
      expect(ZONE_PALETTE_INDEX[z]).toBeGreaterThanOrEqual(0);
    }
  });
});
