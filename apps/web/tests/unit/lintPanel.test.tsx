import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { LintPanel, LintBadge } from "../../src/features/inspector/LintPanel";
import type { Client, LintResponse } from "../../src/api/client";

const FLOW = {
  flow_name: "x",
  total_recipes: 1,
  total_datasets: 0,
  datasets: [],
  recipes: [
    { name: "split_x", type: "split", inputs: ["a"], outputs: ["b"] },
  ],
};

function stubClient(opts: {
  lint?: LintResponse;
  fix?: { flow: Record<string, unknown> };
}): Client {
  return {
    lint: vi.fn(async () =>
      opts.lint ?? ({ lints: [], rule_catalog: [] } as LintResponse),
    ),
    lintFix: vi.fn(async () => opts.fix ?? { flow: {} }),
  } as unknown as Client;
}

describe("<LintPanel />", () => {
  it("auto-runs lint on mount and renders findings", async () => {
    const result: LintResponse = {
      lints: [
        {
          rule_id: "split-single-output",
          severity: "blocker",
          recipe_id: "split_x",
          message: "SPLIT 'split_x' has only 1 output(s).",
        },
      ],
      rule_catalog: [],
    };
    render(<LintPanel flow={FLOW} clientImpl={stubClient({ lint: result })} />);
    await waitFor(() => {
      expect(screen.getByTestId("lint-entry-split-single-output")).toBeInTheDocument();
    });
    expect(screen.getByTestId("lint-severity-blocker")).toBeInTheDocument();
    expect(screen.getByTestId("lint-badge")).toHaveTextContent("1 issue");
  });

  it("renders empty state when there are no findings", async () => {
    render(
      <LintPanel
        flow={FLOW}
        clientImpl={stubClient({ lint: { lints: [], rule_catalog: [] } })}
      />,
    );
    await waitFor(() => {
      expect(screen.getByTestId("lint-empty")).toBeInTheDocument();
    });
  });

  it("clicking a fixable lint dispatches lintFix and emits the new flow", async () => {
    const result: LintResponse = {
      lints: [
        {
          rule_id: "merge-adjacent-prepares",
          severity: "warning",
          recipe_id: "p1",
          message: "...",
          fix: { kind: "merge_adjacent_prepares", left: "p1", right: "p2" },
        },
      ],
      rule_catalog: [],
    };
    const fixed = { flow: { flow_name: "fixed" } };
    const onFlowReplaced = vi.fn();
    const stub = stubClient({ lint: result, fix: fixed });
    render(
      <LintPanel flow={FLOW} clientImpl={stub} onFlowReplaced={onFlowReplaced} />,
    );
    await waitFor(() => screen.getByTestId("lint-apply-fix-merge-adjacent-prepares"));
    fireEvent.click(screen.getByTestId("lint-apply-fix-merge-adjacent-prepares"));
    await waitFor(() => {
      expect(stub.lintFix).toHaveBeenCalled();
    });
    expect(onFlowReplaced).toHaveBeenCalledWith(fixed.flow);
  });

  it("LintBadge tones blocker red and shows the count", () => {
    const result: LintResponse = {
      lints: [
        {
          rule_id: "split-single-output",
          severity: "blocker",
          recipe_id: "x",
          message: "blocker",
        },
        {
          rule_id: "x",
          severity: "warning",
          recipe_id: null,
          message: "w",
        },
      ],
      rule_catalog: [],
    };
    render(<LintBadge result={result} />);
    const badge = screen.getByTestId("lint-summary-badge");
    expect(badge).toHaveTextContent("Lint: 2 issues");
    expect(badge.getAttribute("data-tone")).toBe("blocker");
  });

  it("LintBadge renders nothing when there are no lints", () => {
    render(<LintBadge result={{ lints: [], rule_catalog: [] }} />);
    expect(screen.queryByTestId("lint-summary-badge")).toBeNull();
  });
});
