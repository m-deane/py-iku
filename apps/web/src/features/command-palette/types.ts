/**
 * Shared types for the Cmd+K command palette.
 *
 * A `PaletteItem` is the minimal shape every section produces: an id, a
 * section bucket, primary + secondary display strings, a glyph, and an
 * `invoke()` callback that closes the palette and performs the action.
 */

export type PaletteSection =
  | "Recently used"
  | "Recipes"
  | "Datasets"
  | "Snippets"
  | "Audit events"
  | "Actions"
  | "Help";

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
  /** Called when the user presses Enter / clicks the item. */
  invoke: () => void;
}
