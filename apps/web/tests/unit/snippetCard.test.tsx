import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { SnippetCard } from "../../src/features/snippets/SnippetCard";
import type { Snippet } from "../../src/features/snippets/snippets";

const SAMPLE: Snippet = {
  id: "sample",
  name: "Sample snippet",
  description: "A demo snippet for the card test.",
  code: "import pandas as pd\n",
  tags: ["pandas", "demo"],
  category: "pandas",
};

describe("<SnippetCard />", () => {
  it("renders the name, description, category badge and tags", () => {
    render(<SnippetCard snippet={SAMPLE} onOpen={vi.fn()} />);
    expect(screen.getByText("Sample snippet")).toBeInTheDocument();
    expect(screen.getByText(/A demo snippet/i)).toBeInTheDocument();
    // Category badge has an aria-label distinguishing it from the tag chip.
    expect(screen.getByLabelText(/category pandas/i)).toBeInTheDocument();
    // Both "pandas" (badge + tag) appear, so use getAllByText.
    expect(screen.getAllByText("pandas").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("demo")).toBeInTheDocument();
  });

  it("calls onOpen with the snippet when the open button is clicked", () => {
    const onOpen = vi.fn();
    render(<SnippetCard snippet={SAMPLE} onOpen={onOpen} />);
    fireEvent.click(screen.getByTestId("snippet-open-sample"));
    expect(onOpen).toHaveBeenCalledTimes(1);
    expect(onOpen).toHaveBeenCalledWith(SAMPLE);
  });
});
