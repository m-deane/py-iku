/**
 * Unit tests for the Monaco source-line highlight helper.
 *
 * The recipe popover's "Lines X-Y of source ↗" link calls
 * `highlightSourceLines(editor, [start, end])` which constructs the
 * `IModelDeltaDecoration[]` payload and hands it to
 * `editor.deltaDecorations(...)`. We mock the editor with a thin stub
 * so we can assert the exact decoration shape without booting Monaco.
 */

import { describe, it, expect, vi } from "vitest";
import {
  buildSourceLineDecorations,
  highlightSourceLines,
  clearSourceLineHighlights,
  type MonacoEditorLike,
} from "../../src/features/editor/sourceLineHighlight";

interface StubEditor {
  // Loose typing: vi.fn() returns Mock<any[], unknown> in vitest 1.x and
  // the Monaco typings expect a precise overloaded signature. We erase
  // through `any` here; consumers cast to MonacoEditorLike at call sites.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  deltaDecorations: any;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  revealLineInCenterIfOutsideViewport: any;
}

function makeStubEditor(): StubEditor & MonacoEditorLike {
  const stub: StubEditor = {
    deltaDecorations: vi.fn(
      (_old: ReadonlyArray<string>, _new: ReadonlyArray<unknown>) =>
        _new.map((_x: unknown, i: number) => `dec-${i}`),
    ),
    revealLineInCenterIfOutsideViewport: vi.fn(),
  };
  return stub as unknown as StubEditor & MonacoEditorLike;
}

describe("buildSourceLineDecorations() — pure helper", () => {
  it("builds a whole-line range with the correct className", () => {
    const decorations = buildSourceLineDecorations([3, 5]);
    expect(decorations).toHaveLength(1);
    expect(decorations[0].range).toEqual({
      startLineNumber: 3,
      startColumn: 1,
      endLineNumber: 5,
      endColumn: 1,
    });
    expect(decorations[0].options.isWholeLine).toBe(true);
    expect(decorations[0].options.className).toBe(
      "py-iku-source-line-highlight",
    );
  });

  it("flips out-of-order ranges so end >= start", () => {
    const decorations = buildSourceLineDecorations([7, 2]);
    expect(decorations[0].range.startLineNumber).toBe(2);
    expect(decorations[0].range.endLineNumber).toBe(7);
  });

  it("clamps below-1 line numbers to 1 (Monaco is 1-indexed)", () => {
    const decorations = buildSourceLineDecorations([0, 0]);
    expect(decorations[0].range.startLineNumber).toBe(1);
    expect(decorations[0].range.endLineNumber).toBe(1);
  });
});

describe("highlightSourceLines() — applies decorations on the editor", () => {
  it("calls deltaDecorations with the expected payload and reveals the line", () => {
    const editor = makeStubEditor();
    const ids = highlightSourceLines(editor, [4, 6]);
    expect(editor.deltaDecorations).toHaveBeenCalledTimes(1);
    const [oldDecs, newDecs] = editor.deltaDecorations.mock.calls[0];
    expect(oldDecs).toEqual([]);
    expect(newDecs).toHaveLength(1);
    expect(newDecs[0].range.startLineNumber).toBe(4);
    expect(newDecs[0].range.endLineNumber).toBe(6);
    expect(editor.revealLineInCenterIfOutsideViewport).toHaveBeenCalledWith(4);
    expect(ids).toEqual(["dec-0"]);
  });

  it("passes previousIds so old decorations are replaced (not appended)", () => {
    const editor = makeStubEditor();
    const previous = ["existing-1"];
    highlightSourceLines(editor, [10, 12], previous);
    const [oldDecs] = editor.deltaDecorations.mock.calls[0];
    expect(oldDecs).toEqual(previous);
  });
});

describe("clearSourceLineHighlights() — clears decorations", () => {
  it("calls deltaDecorations with [] to remove all highlights", () => {
    const editor = makeStubEditor();
    clearSourceLineHighlights(editor, ["dec-0", "dec-1"]);
    const [oldDecs, newDecs] = editor.deltaDecorations.mock.calls[0];
    expect(oldDecs).toEqual(["dec-0", "dec-1"]);
    expect(newDecs).toEqual([]);
  });
});
