/**
 * Pure helpers for driving Monaco's `editor.deltaDecorations` from a
 * sprint-3 confidence popover. The popover's "Lines X-Y of source ↗"
 * link calls `highlightSourceLines(editor, [start, end])` which builds
 * the decoration array and applies it.
 *
 * Keeping the decoration construction in a pure function lets unit
 * tests exercise the logic without booting a real Monaco instance.
 *
 * The class name is sourced from a CSS module / tokens file (see
 * `sourceLineHighlight.css`) — no inline hex anywhere.
 */

import type { editor } from "monaco-editor";

/** Minimal subset of a Monaco editor we need for highlighting. */
export interface MonacoEditorLike {
  deltaDecorations(
    oldDecorations: ReadonlyArray<string>,
    newDecorations: ReadonlyArray<editor.IModelDeltaDecoration>,
  ): string[];
  revealLineInCenterIfOutsideViewport?: (lineNumber: number) => void;
}

/**
 * Build the `IModelDeltaDecoration[]` payload for highlighting a 1-indexed
 * inclusive `[start, end]` source-line range. Returned as a fresh array
 * each call so callers can apply it directly.
 *
 * Out-of-order ranges (`end < start`) are flipped; ranges are clamped to
 * `>= 1` so we never produce an invalid Monaco range.
 */
export function buildSourceLineDecorations(
  range: [number, number],
): editor.IModelDeltaDecoration[] {
  const start = Math.max(1, Math.min(range[0], range[1]));
  const end = Math.max(1, Math.max(range[0], range[1]));
  return [
    {
      range: {
        startLineNumber: start,
        startColumn: 1,
        endLineNumber: end,
        endColumn: 1,
      },
      options: {
        isWholeLine: true,
        className: "py-iku-source-line-highlight",
        // Glyph-margin marker so users can see the highlight even
        // when scrolled off-screen (pairs with revealLineInCenter).
        glyphMarginClassName: "py-iku-source-line-highlight-glyph",
        // Marker on the minimap (no-op when minimap is disabled, harmless).
        minimap: {
          color: "var(--accent, #0d9488)" as unknown as string,
          position: 1, // monaco's MinimapPosition.Inline
        },
      },
    },
  ];
}

/**
 * Apply (or clear) source-line decorations on a Monaco editor. Returns
 * the new decoration ids so callers can chain a clear() with the same
 * ids on the next call.
 */
export function highlightSourceLines(
  editor: MonacoEditorLike,
  range: [number, number],
  previousIds: ReadonlyArray<string> = [],
): string[] {
  const decorations = buildSourceLineDecorations(range);
  const newIds = editor.deltaDecorations(previousIds, decorations);
  if (typeof editor.revealLineInCenterIfOutsideViewport === "function") {
    editor.revealLineInCenterIfOutsideViewport(decorations[0].range.startLineNumber);
  }
  return newIds;
}

/** Clear any active source-line decorations. */
export function clearSourceLineHighlights(
  editor: MonacoEditorLike,
  previousIds: ReadonlyArray<string>,
): string[] {
  return editor.deltaDecorations(previousIds, []);
}
