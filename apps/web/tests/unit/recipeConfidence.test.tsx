/**
 * Unit tests for the per-recipe confidence visual treatment.
 *
 * The shading bands are rendered by `<RecipeNode>` in
 * `@py-iku-studio/flow-viz`. Because that component takes a React Flow
 * `NodeProps` shape and depends on the ReactFlow context, we mount it
 * inside `<ReactFlowProvider>` for the test.
 *
 * Bands under test (sprint-3 spec):
 *   confidence == null OR >= 0.85 -> no shading; `data-confidence-band="high"|"rule-based"`
 *   0.60 <= confidence < 0.85    -> medium: 2px var(--warn-border) + ⚠ glyph
 *   confidence < 0.60            -> low: 2px var(--danger-border) + ⚠ + pulsing animation
 *   confidence == null           -> "R" rule-based badge in the bottom-left
 */

import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ReactFlowProvider } from "reactflow";
import { RecipeNode, bandFor } from "../../../../packages/flow-viz/src/nodes/RecipeNode";
import type { RecipeNodeData } from "../../../../packages/flow-viz/src/types";

function mountNode(data: RecipeNodeData): HTMLElement {
  const props = {
    id: "n1",
    data,
    selected: false,
    type: "recipe",
    xPos: 0,
    yPos: 0,
    zIndex: 0,
    isConnectable: true,
    targetPosition: undefined,
    sourcePosition: undefined,
    dragging: false,
    dragHandle: undefined,
  } as unknown as Parameters<typeof RecipeNode>[0];
  render(
    <ReactFlowProvider>
      <RecipeNode {...props} />
    </ReactFlowProvider>,
  );
  return screen.getByTestId(`recipe-node-${data.name}`);
}

describe("bandFor() — pure helper", () => {
  it("classifies confidences into the four bands", () => {
    expect(bandFor(undefined)).toBe("rule-based");
    expect(bandFor(null)).toBe("rule-based");
    expect(bandFor(0.95)).toBe("high");
    expect(bandFor(0.85)).toBe("high"); // boundary inclusive
    expect(bandFor(0.84)).toBe("medium");
    expect(bandFor(0.6)).toBe("medium"); // boundary inclusive
    expect(bandFor(0.59)).toBe("low");
    expect(bandFor(0)).toBe("low");
  });
});

describe("<RecipeNode /> — confidence shading bands", () => {
  it("renders no shading and no warn glyph for high-confidence recipes", () => {
    const node = mountNode({
      type: "grouping",
      name: "agg_high",
      inputs: 1,
      outputs: 1,
      confidence: 0.92,
    });
    expect(node.dataset.confidenceBand).toBe("high");
    expect(
      screen.queryByTestId("confidence-warn-agg_high"),
    ).not.toBeInTheDocument();
    expect(screen.queryByTestId("rule-badge-agg_high")).not.toBeInTheDocument();
    // No medium/low CSS class applied (we read the className for the
    // CSS-module hash, so we just check the band marker).
    expect(node.className).not.toMatch(/confidenceMedium/);
    expect(node.className).not.toMatch(/confidenceLow/);
  });

  it("renders the warn glyph and medium class for medium-confidence recipes", () => {
    const node = mountNode({
      type: "join",
      name: "join_med",
      inputs: 2,
      outputs: 1,
      confidence: 0.72,
    });
    expect(node.dataset.confidenceBand).toBe("medium");
    expect(screen.getByTestId("confidence-warn-join_med")).toBeInTheDocument();
    expect(node.className).toMatch(/confidenceMedium/);
    expect(node.className).not.toMatch(/confidenceLow/);
  });

  it("renders the warn glyph + low class + pulse for low-confidence recipes", () => {
    const node = mountNode({
      type: "python",
      name: "udf_low",
      inputs: 1,
      outputs: 1,
      confidence: 0.42,
    });
    expect(node.dataset.confidenceBand).toBe("low");
    const warn = screen.getByTestId("confidence-warn-udf_low");
    expect(warn).toBeInTheDocument();
    expect(warn).toHaveAttribute("aria-label", "low confidence");
    expect(node.className).toMatch(/confidenceLow/);
    // The "low" class is also what triggers the pulsing keyframe animation
    // in the CSS module — asserting the class is sufficient (jsdom doesn't
    // run @keyframes, but the contract is "this class is present").
  });

  it("renders the 'R' rule-based badge for confidence == null", () => {
    const node = mountNode({
      type: "prepare",
      name: "rule_recipe",
      inputs: 1,
      outputs: 1,
      confidence: null,
    });
    expect(node.dataset.confidenceBand).toBe("rule-based");
    expect(screen.getByTestId("rule-badge-rule_recipe")).toHaveTextContent("R");
    // Rule-based recipes do NOT get the warn glyph.
    expect(
      screen.queryByTestId("confidence-warn-rule_recipe"),
    ).not.toBeInTheDocument();
  });

  it("opens the popover on Enter and closes on Esc (keyboard a11y)", () => {
    const node = mountNode({
      type: "join",
      name: "j_a11y",
      inputs: 2,
      outputs: 1,
      confidence: 0.7,
      reasoning: "judgement call on key inference",
      sourceLines: [3, 3],
    });
    // Tab focus -> the card is focusable (tabIndex=0).
    node.focus();
    expect(node).toHaveFocus();
    expect(node).toHaveAttribute("aria-expanded", "false");
    // Enter opens the popover.
    fireEvent.keyDown(node, { key: "Enter" });
    const popover = screen.getByTestId("recipe-popover-j_a11y");
    expect(popover).toBeInTheDocument();
    expect(node).toHaveAttribute("aria-expanded", "true");
    // The reasoning sentence + source link are inside the popover.
    expect(
      screen.getByTestId("recipe-popover-reasoning-j_a11y"),
    ).toHaveTextContent(/judgement call/);
    expect(
      screen.getByTestId("recipe-popover-source-link-j_a11y"),
    ).toHaveTextContent(/Lines 3.*3.*source/);
    // Esc closes (and returns focus to the card).
    fireEvent.keyDown(popover, { key: "Escape" });
    expect(
      screen.queryByTestId("recipe-popover-j_a11y"),
    ).not.toBeInTheDocument();
    expect(node).toHaveAttribute("aria-expanded", "false");
  });
});
