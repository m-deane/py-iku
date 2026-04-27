/**
 * sprint6-canvas.test.tsx — unit tests asserting that the new RecipeNode +
 * DatasetNode visuals comply with the design-tokens contract.
 *
 * Renders each component standalone (i.e. NOT through the FlowCanvas /
 * ReactFlow stack — we don't want the canvas's SVG-geometry nondeterminism
 * polluting these assertions) and inspects:
 *   - RecipeNode: an inline <svg> icon is present, the
 *     `data-recipe-type` and `data-category` attributes match the design
 *     tokens contract, and the rendered label matches the bound name.
 *   - DatasetNode: the `data-connection-family` and `data-dataset-type`
 *     attributes match the design tokens, and the inline CSS exposes
 *     `--ds-stripe` resolving to the right per-family token.
 *
 * Because the components depend on the ReactFlow `Handle` primitive, each
 * test wraps them in a minimal `<ReactFlowProvider>` — the provider is the
 * cheapest way to satisfy the `useStoreApi` lookup inside `Handle` without
 * mounting a full canvas.
 */
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { ReactFlowProvider } from "reactflow";
import "reactflow/dist/style.css";

import { RecipeNode } from "../src/nodes/RecipeNode";
import { DatasetNode } from "../src/nodes/DatasetNode";
import type { RecipeNodeData, DatasetNodeData } from "../src/types";

// ----------------------------------------------------------------------------
// Helpers — wrap a node component in the bits ReactFlow's Handle expects.
// ----------------------------------------------------------------------------

function renderRecipe(data: RecipeNodeData) {
  // The bare RecipeNode receives NodeProps from ReactFlow at runtime; in a
  // unit test we provide just the fields the implementation reads.
  const props = {
    id: data.name,
    data,
    selected: false,
    type: "recipe",
    xPos: 0,
    yPos: 0,
    isConnectable: false,
    zIndex: 0,
    dragging: false,
    targetPosition: undefined,
    sourcePosition: undefined,
    dragHandle: undefined,
  } as unknown as Parameters<typeof RecipeNode>[0];
  return render(
    <ReactFlowProvider>
      <RecipeNode {...props} />
    </ReactFlowProvider>,
  );
}

function renderDataset(data: DatasetNodeData) {
  const props = {
    id: data.name,
    data,
    selected: false,
    type: "dataset",
    xPos: 0,
    yPos: 0,
    isConnectable: false,
    zIndex: 0,
    dragging: false,
  } as unknown as Parameters<typeof DatasetNode>[0];
  return render(
    <ReactFlowProvider>
      <DatasetNode {...props} />
    </ReactFlowProvider>,
  );
}

// ----------------------------------------------------------------------------
// RecipeNode — 5 most common DSS-fidelity types.
// ----------------------------------------------------------------------------

describe("Sprint-6 RecipeNode visuals", () => {
  const cases: Array<{
    type: RecipeNodeData["type"];
    expectedCategory: string;
    name: string;
  }> = [
    { type: "PREPARE",  expectedCategory: "prep",      name: "clean_customers" },
    { type: "JOIN",     expectedCategory: "structure", name: "join_orders" },
    { type: "GROUPING", expectedCategory: "structure", name: "agg_by_region" },
    { type: "WINDOW",   expectedCategory: "structure", name: "rolling_30d" },
    { type: "SPLIT",    expectedCategory: "structure", name: "split_scd" },
  ];

  for (const c of cases) {
    it(`${c.type} renders icon + label + correct data-category`, () => {
      renderRecipe({
        type: c.type,
        name: c.name,
        inputs: 1,
        outputs: 1,
      });
      const card = screen.getByTestId(`recipe-node-${c.name}`);
      // The bound recipe-type attribute is the contract for tests + lineage.
      expect(card.getAttribute("data-recipe-type")).toBe(c.type);
      // The category drives a CSS class — must match the design tokens.
      expect(card.getAttribute("data-category")).toBe(c.expectedCategory);
      // Inline <svg> icon is mandatory — falls through to recipeIconFor's
      // default when no glyph is available, but never empty.
      const svg = card.querySelector("svg");
      expect(svg).not.toBeNull();
      // The recipe NAME shows up as a below-label.
      expect(card.textContent).toContain(c.name);
      // Inline style vars expose the family tokens (set in JSX). The DOM
      // CSSStyleDeclaration in jsdom exposes the literal value with quotes.
      const style = card.getAttribute("style") ?? "";
      expect(style).toMatch(/--node-bg/);
      expect(style).toMatch(/--node-border/);
      expect(style).toMatch(/--node-text/);
    });
  }

  it("each of the 5 types yields a distinct icon SVG signature", () => {
    // Render all 5 in sequence and snapshot the inner-HTML signature of the
    // first <svg> in the rendered DOM. Different glyphs contain different
    // child shapes (paths, rects, lines), so the inner-HTML alone is enough
    // to distinguish them — and it works for icons that don't use <path>
    // (e.g. WINDOW, which is built from <rect> + <line>).
    const sigByType: Record<string, string> = {};
    for (const c of cases) {
      const { container, unmount } = render(
        <ReactFlowProvider>
          {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
          <RecipeNode
            {...({
              id: c.name,
              data: { type: c.type, name: c.name, inputs: 1, outputs: 1 },
              selected: false,
              type: "recipe",
              xPos: 0,
              yPos: 0,
              isConnectable: false,
              zIndex: 0,
              dragging: false,
            } as any)}
          />
        </ReactFlowProvider>,
      );
      const svg = container.querySelector("svg");
      expect(svg).not.toBeNull();
      // Capture the svg's inner-HTML; each glyph has a unique shape graph.
      sigByType[c.type] = svg?.innerHTML ?? "";
      unmount();
    }
    // No two icons should collide on the same inner-HTML signature.
    // Uniqueness here is the contract that PREPARE != JOIN != GROUPING !=
    // WINDOW != SPLIT.
    const distinct = new Set(Object.values(sigByType));
    expect(distinct.size).toBe(cases.length);
  });
});

// ----------------------------------------------------------------------------
// DatasetNode — one of each connection family.
// ----------------------------------------------------------------------------

describe("Sprint-6 DatasetNode visuals", () => {
  const cases: Array<{
    connectionType: DatasetNodeData["connectionType"];
    family: string;
    name: string;
  }> = [
    { connectionType: "Filesystem",     family: "filesystem", name: "users_csv" },
    { connectionType: "PostgreSQL",     family: "sql",        name: "orders_pg" },
    { connectionType: "S3",             family: "cloud",      name: "events_s3" },
    { connectionType: "MongoDB",        family: "nosql",      name: "sessions" },
  ];

  for (const c of cases) {
    it(`${c.connectionType} carries data-connection-family="${c.family}"`, () => {
      renderDataset({
        datasetType: "INPUT",
        connectionType: c.connectionType,
        name: c.name,
      });
      const node = screen.getByTestId(`dataset-node-${c.name}`);
      expect(node.getAttribute("data-connection-family")).toBe(c.family);
      expect(node.getAttribute("data-dataset-type")).toBe("INPUT");
      // Stripe color is exposed via the --ds-stripe inline CSS variable.
      const style = node.getAttribute("style") ?? "";
      expect(style).toMatch(/--ds-stripe/);
      // The inline value must reference the right design-token CSS variable.
      expect(style).toContain(`var(--dataset-stripe-${c.family})`);
    });
  }

  it("INPUT/INTERMEDIATE/OUTPUT all render with the same family stripe", () => {
    const types: Array<DatasetNodeData["datasetType"]> = [
      "INPUT",
      "INTERMEDIATE",
      "OUTPUT",
    ];
    const observed: string[] = [];
    for (const t of types) {
      const { unmount } = render(
        <ReactFlowProvider>
          {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
          <DatasetNode
            {...({
              id: `n_${t}`,
              data: {
                datasetType: t,
                connectionType: "Filesystem",
                name: `n_${t}`,
              },
              selected: false,
              type: "dataset",
              xPos: 0,
              yPos: 0,
              isConnectable: false,
              zIndex: 0,
              dragging: false,
            } as any)}
          />
        </ReactFlowProvider>,
      );
      const node = screen.getByTestId(`dataset-node-n_${t}`);
      const style = node.getAttribute("style") ?? "";
      const m = style.match(/--ds-stripe:\s*([^;]+);?/);
      observed.push(m?.[1].trim() ?? "");
      unmount();
    }
    // The family is filesystem-driven; all three INPUT/INTERMEDIATE/OUTPUT
    // must resolve to the SAME stripe-color CSS expression.
    expect(new Set(observed).size).toBe(1);
    expect(observed[0]).toBe("var(--dataset-stripe-filesystem)");
  });
});
