/**
 * Backwards-compatible re-export shim.
 *
 * The canonical snippet catalogue now lives in
 * ``../snippets/snippets.ts`` so the gallery and the picker share
 * the same source of truth.  This file keeps the old import path
 * working for callers that haven't moved over yet.
 */

export {
  DEFAULT_SNIPPET_ID,
  SNIPPET_CATEGORIES,
  SNIPPETS,
  getDefaultCode,
  getSnippet,
  getSnippetsByCategory,
} from "../snippets/snippets";
export type { Snippet, SnippetCategory } from "../snippets/snippets";
