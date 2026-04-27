/**
 * Lint-badge contract on the ConvertPage.
 *
 * The LintBadge from inspector/LintPanel renders next to the metric tiles
 * once a successful conversion completes. The badge's visibility depends on
 * the lint result the page fetches in the background; we exercise that path
 * by stubbing the convert-client + lint-client and asserting the badge text.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, act, waitFor } from "@testing-library/react";
import { ConvertPage } from "../../src/features/conversion/ConvertPage";
import { useFlowStore } from "../../src/state/flowStore";
import { useSettingsStore } from "../../src/state/settingsStore";
import {
  client,
  type ConvertResponse,
  type LintResponse,
} from "../../src/api/client";
import { getDefaultCode } from "../../src/features/editor/snippets";

function fakeResponse(): ConvertResponse {
  return {
    flow: {
      name: "demo_flow",
      recipes: [
        { name: "g1", type: "GROUPING", inputs: ["raw"], outputs: ["agg"] },
      ],
      datasets: [
        { name: "raw", type: "csv" },
        { name: "agg", type: "csv" },
      ],
    },
    score: { complexity: 4, recipe_count: 1, dataset_count: 2 },
    warnings: [],
  };
}

function fakeLint(count: number): LintResponse {
  return {
    lints: Array.from({ length: count }).map((_, i) => ({
      rule_id: `dummy-${i}`,
      severity: "warning",
      recipe_id: "g1",
      message: `placeholder lint ${i}`,
    })),
    rule_catalog: [],
  };
}

describe("<ConvertPage /> — lint badge in metric tile row", () => {
  beforeEach(() => {
    act(() => {
      useFlowStore.getState().reset();
      useFlowStore.getState().setCurrentCode(getDefaultCode());
      useFlowStore.getState().setConversionMode("rule");
      useSettingsStore.getState().reset();
    });
  });

  it("shows the badge with N issues after the lint call resolves", async () => {
    const convertImpl = vi.fn().mockResolvedValue(fakeResponse());
    // Stub the global client.lint so the post-convert background lint call
    // resolves immediately with 2 warnings.
    const lintSpy = vi
      .spyOn(client, "lint")
      .mockResolvedValue(fakeLint(2));

    try {
      render(<ConvertPage useFallbackEditor convertImpl={convertImpl} />);
      fireEvent.click(screen.getByRole("button", { name: /^convert$/i }));

      // 1) Convert completes → stat tiles render.
      await waitFor(() => {
        expect(screen.getByTestId("status-success")).toBeInTheDocument();
      });
      // 2) Lint result resolves → badge appears with the count.
      await waitFor(() => {
        expect(screen.getByTestId("lint-summary-badge")).toBeInTheDocument();
      });
      expect(screen.getByTestId("lint-summary-badge")).toHaveTextContent(
        /lint:\s*2 issues/i,
      );
    } finally {
      lintSpy.mockRestore();
    }
  });

  it("hides the badge when the lint result has zero issues", async () => {
    const convertImpl = vi.fn().mockResolvedValue(fakeResponse());
    const lintSpy = vi
      .spyOn(client, "lint")
      .mockResolvedValue(fakeLint(0));

    try {
      render(<ConvertPage useFallbackEditor convertImpl={convertImpl} />);
      fireEvent.click(screen.getByRole("button", { name: /^convert$/i }));

      await waitFor(() => {
        expect(screen.getByTestId("status-success")).toBeInTheDocument();
      });
      // Give the lint call a beat to resolve and re-render.
      await waitFor(() => {
        expect(lintSpy).toHaveBeenCalled();
      });
      // Empty lint → badge stays unmounted (LintBadge returns null).
      expect(screen.queryByTestId("lint-summary-badge")).not.toBeInTheDocument();
    } finally {
      lintSpy.mockRestore();
    }
  });
});
