import { describe, expect, it } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { CurveDiffPage } from "../../src/features/curve-diff/CurveDiffPage";
import {
  computeDiff,
  CURVE_A,
  CURVE_B,
  exceedsThreshold,
  FIXTURES,
} from "../../src/features/curve-diff/curve-fixtures";

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/diff/curves"]}>
      <CurveDiffPage />
    </MemoryRouter>,
  );
}

describe("<CurveDiffPage />", () => {
  it("ships two embedded fixtures (yesterday + today)", () => {
    expect(FIXTURES.length).toBe(2);
    expect(CURVE_A.points.length).toBeGreaterThan(0);
    expect(CURVE_B.points.length).toBe(CURVE_A.points.length);
  });

  it("computeDiff aligns tenors and signs deltas correctly", () => {
    const rows = computeDiff(CURVE_A, CURVE_B);
    expect(rows.length).toBe(CURVE_A.points.length);
    // M+1 rallied 78.55 -> 79.15 ⇒ +0.60.
    const m1 = rows.find((r) => r.tenor === "M+1");
    expect(m1?.delta_abs).toBeCloseTo(0.6, 5);
    expect(m1?.delta_pct).toBeCloseTo((0.6 / 78.55) * 100, 5);
    // M+8 has the big test jump 76.40 -> 77.85 ⇒ +1.45.
    const m8 = rows.find((r) => r.tenor === "M+8");
    expect(m8?.delta_abs).toBeCloseTo(1.45, 5);
  });

  it("exceedsThreshold fires for tenors >= threshold_pct", () => {
    const rows = computeDiff(CURVE_A, CURVE_B);
    const m8 = rows.find((r) => r.tenor === "M+8")!;
    expect(exceedsThreshold(m8, 1.0)).toBe(true);
    expect(exceedsThreshold(m8, 5.0)).toBe(false);
  });

  it("renders the tenor table and summary strip on first paint", () => {
    renderPage();
    expect(screen.getByTestId("curve-diff-page")).toBeInTheDocument();
    expect(screen.getByTestId("curve-diff-table")).toBeInTheDocument();
    expect(screen.getByTestId("curve-diff-summary")).toBeInTheDocument();
    // M+1 row exists.
    expect(
      screen.getByTestId("curve-diff-row-M+1"),
    ).toBeInTheDocument();
  });

  it("flags rows above the threshold and updates summary count", () => {
    renderPage();
    // Default threshold is 1.0 % — M+8 (~1.9%) should be flagged.
    const m8 = screen.getByTestId("curve-diff-row-M+8");
    expect(m8).toHaveAttribute("data-flagged", "true");
    // M+1 (~0.76%) should NOT be flagged at 1%.
    const m1 = screen.getByTestId("curve-diff-row-M+1");
    expect(m1).toHaveAttribute("data-flagged", "false");
  });

  it("threshold input controls flag count", () => {
    renderPage();
    const input = screen.getByTestId(
      "curve-diff-threshold",
    ) as HTMLInputElement;
    fireEvent.change(input, { target: { value: "0.1" } });
    // At 0.1% almost every tenor should flag.
    const flagged = Number.parseInt(
      screen.getByTestId("curve-diff-flagged-count").textContent ?? "0",
      10,
    );
    expect(flagged).toBeGreaterThanOrEqual(10);
    fireEvent.change(input, { target: { value: "10" } });
    const flaggedHigh = Number.parseInt(
      screen.getByTestId("curve-diff-flagged-count").textContent ?? "0",
      10,
    );
    expect(flaggedHigh).toBe(0);
  });

  it("two pickers select different curves", () => {
    renderPage();
    const aSelect = screen.getByTestId(
      "curve-a-select",
    ) as HTMLSelectElement;
    const bSelect = screen.getByTestId(
      "curve-b-select",
    ) as HTMLSelectElement;
    expect(aSelect.value).not.toBe(bSelect.value);
  });
});
