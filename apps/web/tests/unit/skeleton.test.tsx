import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { Skeleton, SkeletonGrid } from "../../src/components/Skeleton";

describe("<Skeleton />", () => {
  it("renders with default text variant + accessible status role", () => {
    const { getByRole, getByTestId } = render(<Skeleton />);
    const node = getByTestId("skeleton");
    expect(node).toHaveAttribute("aria-busy", "true");
    expect(node).toHaveAttribute("aria-label", "Loading…");
    expect(getByRole("status")).toBe(node);
  });

  it("respects custom width/height/variant", () => {
    const { getByTestId } = render(
      <Skeleton variant="card" width={120} height={80} data-testid="custom" />,
    );
    const node = getByTestId("custom") as HTMLElement;
    expect(node.style.width).toBe("120px");
    expect(node.style.height).toBe("80px");
  });
});

describe("<SkeletonGrid />", () => {
  it("renders the requested number of skeleton cards", () => {
    const { getAllByTestId } = render(<SkeletonGrid count={4} />);
    const cards = getAllByTestId(/^skeleton-card-/);
    expect(cards).toHaveLength(4);
  });

  it("defaults to 6 placeholders when count is omitted", () => {
    const { getAllByTestId } = render(<SkeletonGrid />);
    expect(getAllByTestId(/^skeleton-card-/)).toHaveLength(6);
  });
});
