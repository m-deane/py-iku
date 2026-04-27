/**
 * Unit tests for the Convert page's confidence summary panel
 * (segmented bar + counts + "Review low-confidence" CTA).
 *
 * Spec recap:
 *   - "12 recipes converted • 11 high (≥85%) • 1 medium (≥60%) • 0 low"
 *   - segmented bar — green / amber / red proportional to bucket counts
 *   - clicking a segment selects the matching band → parent dims others
 *   - "Review low-confidence →" appears iff there is at least one low.
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import {
  ConfidencePanel,
  countConfidence,
} from "../../src/features/conversion/ConfidencePanel";
import type { Recipe } from "../../src/api/types";

function recipe(over: Partial<Recipe>): Recipe {
  return {
    name: "r",
    type: "prepare",
    inputs: [],
    outputs: [],
    source_lines: [],
    notes: [],
    confidence: null,
    sourceLines: null,
    reasoning: null,
    ...over,
  } as Recipe;
}

describe("countConfidence() — pure helper", () => {
  it("buckets recipes by confidence band", () => {
    const recipes: Recipe[] = [
      recipe({ name: "h1", confidence: 0.99 }),
      recipe({ name: "h2", confidence: 0.85 }),
      recipe({ name: "m1", confidence: 0.72 }),
      recipe({ name: "l1", confidence: 0.4 }),
      recipe({ name: "r1", confidence: null }),
    ];
    expect(countConfidence(recipes)).toEqual({
      total: 5,
      high: 2,
      medium: 1,
      low: 1,
      ruleBased: 1,
    });
  });

  it("returns all-zero counts for an empty flow", () => {
    expect(countConfidence([])).toEqual({
      total: 0,
      high: 0,
      medium: 0,
      low: 0,
      ruleBased: 0,
    });
  });
});

describe("<ConfidencePanel />", () => {
  it("renders the spec-shaped summary line", () => {
    const recipes: Recipe[] = [
      ...Array.from({ length: 11 }).map((_, i) =>
        recipe({ name: `h${i}`, confidence: 0.95 }),
      ),
      recipe({ name: "m", confidence: 0.7 }),
    ];
    render(<ConfidencePanel recipes={recipes} />);
    const summary = screen.getByTestId("confidence-panel-summary");
    expect(summary).toHaveTextContent("12 recipes converted");
    expect(summary).toHaveTextContent("11 high");
    expect(summary).toHaveTextContent("1 medium");
    expect(summary).toHaveTextContent("0 low");
  });

  it("renders one segment per non-empty bucket and skips empty ones", () => {
    const recipes: Recipe[] = [
      recipe({ name: "h", confidence: 0.95 }),
      recipe({ name: "l", confidence: 0.3 }),
      // No medium recipes — that segment must not render.
    ];
    render(<ConfidencePanel recipes={recipes} />);
    expect(screen.getByTestId("confidence-segment-high")).toBeInTheDocument();
    expect(screen.getByTestId("confidence-segment-low")).toBeInTheDocument();
    expect(
      screen.queryByTestId("confidence-segment-medium"),
    ).not.toBeInTheDocument();
  });

  it("calls onSelectBand when a segment is clicked, and toggles back to null on second click", () => {
    const onSelect = vi.fn();
    const recipes: Recipe[] = [
      recipe({ name: "h", confidence: 0.95 }),
      recipe({ name: "m", confidence: 0.7 }),
    ];
    const { rerender } = render(
      <ConfidencePanel recipes={recipes} onSelectBand={onSelect} />,
    );
    const med = screen.getByTestId("confidence-segment-medium");
    fireEvent.click(med);
    expect(onSelect).toHaveBeenCalledWith("medium");

    // Selecting an already-selected segment toggles it off.
    rerender(
      <ConfidencePanel
        recipes={recipes}
        onSelectBand={onSelect}
        selectedBand="medium"
      />,
    );
    fireEvent.click(screen.getByTestId("confidence-segment-medium"));
    expect(onSelect).toHaveBeenCalledWith(null);
  });

  it("renders the Review low-confidence CTA only when low > 0", () => {
    const onSelect = vi.fn();
    const onReview = vi.fn();
    const high: Recipe[] = [recipe({ name: "h", confidence: 0.95 })];
    const { rerender } = render(
      <ConfidencePanel
        recipes={high}
        onSelectBand={onSelect}
        onReviewLow={onReview}
      />,
    );
    expect(
      screen.queryByTestId("confidence-review-low"),
    ).not.toBeInTheDocument();

    const withLow: Recipe[] = [
      recipe({ name: "h", confidence: 0.95 }),
      recipe({ name: "l", confidence: 0.3 }),
    ];
    rerender(
      <ConfidencePanel
        recipes={withLow}
        onSelectBand={onSelect}
        onReviewLow={onReview}
      />,
    );
    const cta = screen.getByTestId("confidence-review-low");
    fireEvent.click(cta);
    expect(onReview).toHaveBeenCalled();
    expect(onSelect).toHaveBeenCalledWith("low");
  });
});
