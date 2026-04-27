import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { SuggestMappingBanner } from "../../src/features/suggest/SuggestMappingBanner";
import {
  applySuggestionToEditor,
  APPLY_CONFIDENCE_THRESHOLD,
  type MonacoLikeEditor,
} from "../../src/features/suggest/useSuggestMapping";

const ORIGINAL_SOURCE = `import pandas as pd
df = pd.read_csv('trades.csv')
result = df.groupby(['book'])['pnl'].sum()
`;

const HIGH_CONFIDENCE_RESPONSE = {
  confidence: 0.92,
  suggested_recipe_type: "GROUPING",
  transformed_pandas: `import pandas as pd
df = pd.read_csv('trades.csv')
result = df.groupby(['book'], as_index=False)['pnl'].sum()
`,
  reasoning:
    "The snippet aggregates rows by book — a textbook GROUPING recipe.",
  model: "mock",
  usage: {},
  cost_usd: 0,
};

const LOW_CONFIDENCE_RESPONSE = {
  confidence: 0.4,
  suggested_recipe_type: "PYTHON",
  transformed_pandas: ORIGINAL_SOURCE,
  reasoning:
    "Mostly sklearn primitives — no clean visual-recipe equivalent.",
  model: "mock",
  usage: {},
  cost_usd: 0,
};

// ---------------------------------------------------------------------------
// Stub Monaco editor used by Apply tests. Records every executeEdits call.
// ---------------------------------------------------------------------------

function makeStubEditor(initial: string): MonacoLikeEditor & {
  edits: Array<{ source: string; text: string }>;
  text: string;
} {
  let text = initial;
  const edits: Array<{ source: string; text: string }> = [];
  return {
    edits,
    get text() {
      return text;
    },
    getModel() {
      return {
        getValue: () => text,
        findMatches(needle: string) {
          const start = text.indexOf(needle);
          if (start === -1) return [];
          // Build a fake range; numbers are 1-indexed Monaco-style.
          const before = text.slice(0, start);
          const startLine = (before.match(/\n/g) || []).length + 1;
          const startCol =
            start - (before.lastIndexOf("\n") + 1 || 0) + 1;
          const after = text.slice(start, start + needle.length);
          const endLine = startLine + (after.match(/\n/g) || []).length;
          const endCol = needle.includes("\n")
            ? after.length - after.lastIndexOf("\n")
            : startCol + needle.length;
          return [
            {
              range: {
                startLineNumber: startLine,
                startColumn: startCol,
                endLineNumber: endLine,
                endColumn: endCol,
              },
            },
          ];
        },
        getFullModelRange() {
          const lines = text.split("\n").length;
          return {
            startLineNumber: 1,
            startColumn: 1,
            endLineNumber: lines,
            endColumn: text.split("\n")[lines - 1].length + 1,
          };
        },
      };
    },
    executeEdits(source: string, e) {
      edits.push({ source, text: e[0].text });
      // For tests we just swap the model text wholesale to the new text —
      // good enough for assertions about content after edit.
      text = e[0].text;
      return true;
    },
  };
}

describe("applySuggestionToEditor", () => {
  it("performs an exact replacement when the original is found", () => {
    const editor = makeStubEditor(ORIGINAL_SOURCE);
    const result = applySuggestionToEditor(
      editor,
      ORIGINAL_SOURCE,
      HIGH_CONFIDENCE_RESPONSE.transformed_pandas,
    );
    expect(result.applied).toBe(true);
    expect(result.mode).toBe("exact");
    expect(editor.edits.length).toBe(1);
    expect(editor.edits[0].source).toBe("py-iku-suggest-mapping");
    expect(editor.edits[0].text).toBe(
      HIGH_CONFIDENCE_RESPONSE.transformed_pandas,
    );
  });

  it("falls back to a full-model replace when the original isn't found", () => {
    const editor = makeStubEditor("# unrelated source");
    const result = applySuggestionToEditor(
      editor,
      ORIGINAL_SOURCE,
      HIGH_CONFIDENCE_RESPONSE.transformed_pandas,
    );
    expect(result.applied).toBe(true);
    expect(result.mode).toBe("full-replace");
  });

  it("returns noop when the editor has no model", () => {
    const editor = {
      getModel: () => null,
      executeEdits: () => true,
    } as MonacoLikeEditor;
    const result = applySuggestionToEditor(editor, "a", "b");
    expect(result.applied).toBe(false);
    expect(result.mode).toBe("noop");
  });
});

describe("<SuggestMappingBanner />", () => {
  it("starts in idle, fetches on Show, and renders the suggested type", async () => {
    const suggestMapping = vi.fn(async () => HIGH_CONFIDENCE_RESPONSE);
    render(
      <SuggestMappingBanner
        pythonSource={ORIGINAL_SOURCE}
        recipeName="custom_blotter"
        options={{ clientImpl: { suggestMapping } }}
      />,
    );
    fireEvent.click(screen.getByTestId("suggest-show"));
    await waitFor(() =>
      expect(screen.getByTestId("suggest-type")).toHaveTextContent("GROUPING"),
    );
    expect(screen.getByTestId("suggest-confidence")).toHaveTextContent(
      "92% confidence",
    );
    expect(screen.getByTestId("suggest-reasoning")).toHaveTextContent(
      "GROUPING recipe",
    );
    expect(suggestMapping).toHaveBeenCalledTimes(1);
    const calls = suggestMapping.mock.calls as unknown as Array<
      Array<{ python_source: string }>
    >;
    expect(calls[0]?.[0]?.python_source).toBe(ORIGINAL_SOURCE);
  });

  it("shows Apply CTA only when confidence ≥ threshold AND editor is present", async () => {
    const suggestMapping = vi.fn(async () => HIGH_CONFIDENCE_RESPONSE);
    const editor = makeStubEditor(ORIGINAL_SOURCE);
    render(
      <SuggestMappingBanner
        pythonSource={ORIGINAL_SOURCE}
        editor={editor}
        options={{ clientImpl: { suggestMapping } }}
      />,
    );
    fireEvent.click(screen.getByTestId("suggest-show"));
    await waitFor(() =>
      expect(screen.getByTestId("suggest-apply")).toBeInTheDocument(),
    );
  });

  it("hides Apply CTA when confidence is below threshold", async () => {
    const suggestMapping = vi.fn(async () => LOW_CONFIDENCE_RESPONSE);
    const editor = makeStubEditor(ORIGINAL_SOURCE);
    render(
      <SuggestMappingBanner
        pythonSource={ORIGINAL_SOURCE}
        editor={editor}
        options={{ clientImpl: { suggestMapping } }}
      />,
    );
    fireEvent.click(screen.getByTestId("suggest-show"));
    await waitFor(() =>
      expect(screen.getByTestId("suggest-info-only")).toBeInTheDocument(),
    );
    expect(screen.queryByTestId("suggest-apply")).not.toBeInTheDocument();
  });

  it("Apply replaces editor source via executeEdits", async () => {
    const suggestMapping = vi.fn(async () => HIGH_CONFIDENCE_RESPONSE);
    const editor = makeStubEditor(ORIGINAL_SOURCE);
    const onApplied = vi.fn();
    render(
      <SuggestMappingBanner
        pythonSource={ORIGINAL_SOURCE}
        editor={editor}
        onApplied={onApplied}
        options={{ clientImpl: { suggestMapping } }}
      />,
    );
    fireEvent.click(screen.getByTestId("suggest-show"));
    await waitFor(() =>
      expect(screen.getByTestId("suggest-apply")).toBeInTheDocument(),
    );

    fireEvent.click(screen.getByTestId("suggest-apply"));
    expect(editor.edits.length).toBe(1);
    expect(editor.edits[0].text).toBe(
      HIGH_CONFIDENCE_RESPONSE.transformed_pandas,
    );
    expect(onApplied).toHaveBeenCalledWith({ mode: "exact" });
    expect(screen.getByTestId("suggest-applied")).toBeInTheDocument();
  });

  it("Surfaces an error region without crashing", async () => {
    const suggestMapping = vi.fn(async () => {
      throw new Error("boom");
    });
    render(
      <SuggestMappingBanner
        pythonSource={ORIGINAL_SOURCE}
        options={{ clientImpl: { suggestMapping } }}
      />,
    );
    fireEvent.click(screen.getByTestId("suggest-show"));
    await waitFor(() => {
      expect(screen.getByTestId("suggest-error")).toHaveTextContent("boom");
    });
  });

  it("renders a Dismiss button when onDismiss is supplied", async () => {
    const suggestMapping = vi.fn(async () => HIGH_CONFIDENCE_RESPONSE);
    const onDismiss = vi.fn();
    render(
      <SuggestMappingBanner
        pythonSource={ORIGINAL_SOURCE}
        onDismiss={onDismiss}
        options={{ clientImpl: { suggestMapping } }}
      />,
    );
    fireEvent.click(screen.getByTestId("suggest-dismiss"));
    expect(onDismiss).toHaveBeenCalledTimes(1);
  });

  it("APPLY_CONFIDENCE_THRESHOLD is 0.7", () => {
    expect(APPLY_CONFIDENCE_THRESHOLD).toBe(0.7);
  });
});
