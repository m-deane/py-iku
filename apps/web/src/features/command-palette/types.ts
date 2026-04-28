/**
 * Shared types for the Cmd+K command palette.
 *
 * A `PaletteItem` is the minimal shape every section produces: an id, a
 * section bucket, primary + secondary display strings, a glyph, and an
 * `invoke()` callback that closes the palette and performs the action.
 *
 * Sprint 3 polish adds optional Raycast-style multi-step arguments. An item
 * may declare `args: ArgSpec[]`; when invoked, the palette enters arg-
 * collection mode and walks the user through each step, collecting choices,
 * before calling `invoke()` with the resolved values. Items without `args`
 * are invoked directly with no arguments — backwards compatible.
 */

export type PaletteSection =
  | "Pinned"
  | "Recipes"
  | "Datasets"
  | "Actions"
  | "Help";

/** A single choice the user can pick at one arg-collection step. */
export interface ArgChoice {
  /** Stable value passed back to `invoke()`. */
  value: string;
  /** User-facing label shown in the dropdown. */
  label: string;
  /** Optional one-line description rendered in the inline preview. */
  description?: string;
  /** Optional secondary detail (e.g. file path for templates). */
  secondary?: string;
}

/**
 * Specification for one argument-collection step. An item with
 * `args: [a, b, c]` walks through them left-to-right; each step's chosen
 * value is appended to the list passed into `invoke()`.
 */
export interface ArgSpec {
  /** Stable key (used by tests + analytics). */
  key: string;
  /** Breadcrumb label (e.g. "Mode", "Provider", "Format"). */
  label: string;
  /** Inline placeholder shown in the search box during this step. */
  placeholder?: string;
  /**
   * Choices for this step. May be a static list or a function that resolves
   * choices lazily — useful for "Open template" where the catalog is fetched
   * after the user picks the action.
   */
  choices: ArgChoice[] | (() => Promise<ArgChoice[]> | ArgChoice[]);
  /**
   * Optional gate: when `false`, the step is skipped. Receives the values
   * collected so far. Used by Convert to skip the Provider step in rule mode.
   */
  when?: (collectedValues: unknown[]) => boolean;
}

/**
 * One row in the palette. Sprint 3 splits the invocation into:
 *   - Single-step items: declare `invoke()` (no args). Default behaviour.
 *   - Multi-step items: declare `args` + `invokeWithArgs(values)`.
 *
 * The legacy `invoke()` field is preserved for both — single-step items
 * still implement it directly; multi-step items implement a no-op that the
 * palette overrides via `invokeWithArgs`.
 */
export interface PaletteItem {
  /** Stable ID for de-dupe and recency tracking. */
  id: string;
  section: PaletteSection;
  primary: string;
  secondary?: string;
  /** Single glyph or short sigil — keeps the row compact. */
  icon?: string;
  /** Free-form keywords merged into the fuzzy index. */
  keywords?: string[];
  /** One-sentence "what" — surfaced in the inline preview pane. */
  description?: string;
  /** Keyboard shortcut hint surfaced in the preview pane (e.g. "⌘ Enter"). */
  shortcut?: string;
  /** Static preview source (snippets only, first 10 lines). */
  previewSource?: string;
  /** Connection-type/column-count metadata for dataset rows. */
  previewMeta?: Record<string, string | number>;

  /** Called when the user presses Enter / clicks the item (no-args path). */
  invoke: () => void;

  /** Multi-step argument-collection schema. Optional. */
  args?: ArgSpec[];
  /** Called once all argument steps complete with the collected values. */
  invokeWithArgs?: (values: unknown[]) => void;
}
