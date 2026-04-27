import { describe, it, expect, vi } from "vitest";
import { render, fireEvent } from "@testing-library/react";
import { Banner } from "../../src/components/Banner";

describe("<Banner />", () => {
  it("renders danger variant with role=alert by default", () => {
    const { getByTestId } = render(<Banner title="Boom" />);
    const node = getByTestId("banner");
    expect(node).toHaveAttribute("role", "alert");
    expect(node).toHaveAttribute("data-variant", "danger");
    expect(node).toHaveTextContent("Boom");
  });

  it("info variant uses status role (non-blocking)", () => {
    const { getByTestId } = render(<Banner variant="info" title="Heads up" />);
    const node = getByTestId("banner");
    expect(node).toHaveAttribute("role", "status");
    expect(node).toHaveAttribute("data-variant", "info");
  });

  it("renders Retry button when onRetry is provided and fires it on click", () => {
    const onRetry = vi.fn();
    const { getByTestId } = render(
      <Banner title="Network error" onRetry={onRetry} />,
    );
    const retry = getByTestId("banner-retry");
    expect(retry).toHaveTextContent(/retry/i);
    fireEvent.click(retry);
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it("renders dismiss when onDismiss is provided", () => {
    const onDismiss = vi.fn();
    const { getByTestId } = render(
      <Banner title="Heads up" variant="warn" onDismiss={onDismiss} />,
    );
    const dismiss = getByTestId("banner-dismiss");
    fireEvent.click(dismiss);
    expect(onDismiss).toHaveBeenCalledOnce();
  });

  it("supports a custom retry label", () => {
    const { getByTestId } = render(
      <Banner title="x" onRetry={() => undefined} retryLabel="Try again" />,
    );
    expect(getByTestId("banner-retry")).toHaveTextContent("Try again");
  });
});
