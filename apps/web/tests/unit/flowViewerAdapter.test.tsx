/**
 * flowViewerAdapter.test.tsx — verifies the DataikuFlow → MinimalFlow
 * adapter used by both <FlowViewer> (route-level) and the inline canvas
 * on the Convert page.
 *
 * The previous implementation cast the persisted flow directly to
 * MinimalFlow, which lied to TypeScript and produced an empty canvas at
 * runtime because the two shapes have different field names
 * (`recipes`/`datasets` vs `nodes`/`edges`). This test pins the new
 * structural conversion.
 */
import { describe, expect, it } from "vitest";
import { dataikuFlowToMinimal } from "../../src/features/conversion/FlowViewer";
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyFlow = any;

describe("dataikuFlowToMinimal", () => {
  it("turns datasets[] + recipes[] into nodes[] + edges[]", () => {
    const flow: AnyFlow = {
      flow_name: "f",
      total_recipes: 1,
      total_datasets: 2,
      datasets: [
        { name: "a", type: "input", connection_type: "Filesystem", schema: [] },
        { name: "b", type: "output", connection_type: "Snowflake", schema: [] },
      ],
      recipes: [
        { name: "r1", type: "prepare", inputs: ["a"], outputs: ["b"] },
      ],
    };
    const min = dataikuFlowToMinimal(flow);
    // 2 datasets + 1 recipe = 3 nodes
    expect(min.nodes.length).toBe(3);
    expect(min.nodes.find((n) => n.id === "a")?.type).toBe("dataset");
    expect(min.nodes.find((n) => n.id === "r1")?.type).toBe("recipe");
    // Edges: a→r1 and r1→b
    expect(min.edges.length).toBe(2);
    expect(min.edges.find((e) => e.source === "a" && e.target === "r1")).toBeTruthy();
    expect(min.edges.find((e) => e.source === "r1" && e.target === "b")).toBeTruthy();
  });

  it("emits a SPLIT recipe with both outputs as separate edges", () => {
    const flow: AnyFlow = {
      flow_name: "scd",
      total_recipes: 1,
      total_datasets: 3,
      datasets: [
        { name: "src", type: "input", connection_type: "Filesystem", schema: [] },
        { name: "current", type: "output", connection_type: "Filesystem", schema: [] },
        { name: "archive", type: "output", connection_type: "Filesystem", schema: [] },
      ],
      recipes: [
        { name: "split_scd", type: "split", inputs: ["src"], outputs: ["current", "archive"] },
      ],
    };
    const min = dataikuFlowToMinimal(flow);
    expect(min.edges.length).toBe(3); // src→split, split→current, split→archive
    const splitOutEdges = min.edges.filter((e) => e.source === "split_scd");
    expect(splitOutEdges.length).toBe(2);
  });

  it("synthesizes a stub dataset node when an output is referenced but missing", () => {
    const flow: AnyFlow = {
      flow_name: "x",
      total_recipes: 1,
      total_datasets: 1,
      datasets: [{ name: "a", type: "input", connection_type: "Filesystem", schema: [] }],
      recipes: [
        // Outputs "missing_b" but datasets[] doesn't include it.
        { name: "r1", type: "prepare", inputs: ["a"], outputs: ["missing_b"] },
      ],
    };
    const min = dataikuFlowToMinimal(flow);
    expect(min.nodes.find((n) => n.id === "missing_b")?.type).toBe("dataset");
    expect(min.edges.length).toBe(2);
  });

  it("preserves recipe confidence + sourceLines from LLM payloads", () => {
    const flow: AnyFlow = {
      flow_name: "x",
      total_recipes: 1,
      total_datasets: 2,
      datasets: [
        { name: "a", type: "input", connection_type: "Filesystem", schema: [] },
        { name: "b", type: "output", connection_type: "Filesystem", schema: [] },
      ],
      recipes: [
        {
          name: "r1",
          type: "prepare",
          inputs: ["a"],
          outputs: ["b"],
          confidence: 0.72,
          source_lines: [10, 18],
          reasoning: "GROUPING with two columns aggregated by sum.",
        },
      ],
    };
    const min = dataikuFlowToMinimal(flow);
    const recipeNode = min.nodes.find((n) => n.id === "r1");
    expect(recipeNode).toBeTruthy();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const data = recipeNode!.data as any;
    expect(data.confidence).toBe(0.72);
    expect(data.sourceLines).toEqual([10, 18]);
    expect(data.reasoning).toBe("GROUPING with two columns aggregated by sum.");
  });

  it("handles a 12-recipe deep chain without losing edges", () => {
    const datasets = [{ name: "step_0", type: "input", connection_type: "Filesystem", schema: [] }];
    const recipes: Array<Record<string, unknown>> = [];
    for (let i = 1; i <= 12; i += 1) {
      datasets.push({
        name: `step_${i}`,
        type: i === 12 ? "output" : "intermediate",
        connection_type: "Filesystem",
        schema: [],
      });
      recipes.push({
        name: `r_${i}`,
        type: "prepare",
        inputs: [`step_${i - 1}`],
        outputs: [`step_${i}`],
      });
    }
    const flow: AnyFlow = {
      flow_name: "deep",
      total_recipes: 12,
      total_datasets: 13,
      datasets,
      recipes,
    };
    const min = dataikuFlowToMinimal(flow);
    expect(min.nodes.length).toBe(13 + 12); // 13 datasets + 12 recipes
    expect(min.edges.length).toBe(12 * 2); // each recipe = 2 edges
  });

  it("collects 8 inputs into a single STACK recipe with 8 incoming edges", () => {
    const datasets = [];
    const inputNames: string[] = [];
    for (let i = 0; i < 8; i += 1) {
      const name = `in_${i}`;
      inputNames.push(name);
      datasets.push({ name, type: "input", connection_type: "Filesystem", schema: [] });
    }
    datasets.push({ name: "out", type: "output", connection_type: "Filesystem", schema: [] });
    const flow: AnyFlow = {
      flow_name: "wide",
      total_recipes: 1,
      total_datasets: 9,
      datasets,
      recipes: [
        { name: "stack_all", type: "stack", inputs: inputNames, outputs: ["out"] },
      ],
    };
    const min = dataikuFlowToMinimal(flow);
    const incoming = min.edges.filter((e) => e.target === "stack_all");
    expect(incoming.length).toBe(8);
  });
});
