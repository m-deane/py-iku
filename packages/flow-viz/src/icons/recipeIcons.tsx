/**
 * Sprint-6: typed recipe-icon library mimicking the real Dataiku DSS flow.
 *
 * Each icon is an inline single-color SVG glyph that takes a `color` prop
 * (driven by the recipe-family CSS token) and a `size` prop (default 22px,
 * sized for the 52px DSS-style circle).
 *
 * Coverage: every member of the RecipeType enum (37 in DSS 14) maps to an
 * icon here. Where an existing glyph in `nodes/glyphs.tsx` already nailed
 * the DSS treatment we re-use it; the rest are new in this file so the
 * Studio canvas reads as DSS at a glance.
 */

import type { JSX } from "react";
import type { RecipeType } from "../types";
import { getSvgGlyph as getLegacyGlyph } from "../nodes/glyphs";

export interface RecipeIconProps {
  color: string;
  size?: number;
  /** Optional title for accessibility / hover. */
  title?: string;
}

const VB = "0 0 24 24";

function withDefaults(props: RecipeIconProps): { color: string; size: number } {
  return { color: props.color, size: props.size ?? 22 };
}

/* -------------------------------------------------------------------------
 * NEW glyphs for types the legacy glyphs file did not cover.
 * The legacy file already supplies: FUZZY_JOIN, GEO_JOIN, SYNC, STACK, SORT,
 * DISTINCT, TOP_N, PIVOT, SAMPLING, DOWNLOAD, GENERATE_FEATURES,
 * GENERATE_STATISTICS, PUSH_TO_EDITABLE, LIST_FOLDER_CONTENTS, DYNAMIC_REPEAT,
 * EXTRACT_FAILED_ROWS, UPSERT, LIST_ACCESS, R, SQL, HIVE, IMPALA, SPARKSQL,
 * PYSPARK, SPARK_SCALA, SPARKR, SHELL, PREDICTION_SCORING,
 * CLUSTERING_SCORING, standalone_evaluation, AI_ASSISTANT_GENERATE.
 * ----------------------------------------------------------------------- */

/** Broom for PREPARE. */
function PrepareIcon(props: RecipeIconProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VB} width={size} height={size} aria-hidden="true">
      <path
        d="M14 3 L21 10 L17 14 L10 7 Z"
        fill={color}
        stroke={color}
        strokeWidth="1"
        strokeLinejoin="round"
      />
      <path
        d="M10 7 L4 13 L7 21 L17 14"
        fill="none"
        stroke={color}
        strokeWidth="1.6"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      <path d="M5 16 L9 19 M7 14 L11 17" stroke={color} strokeWidth="1.2" strokeLinecap="round" />
    </svg>
  );
}

/** Bowtie for JOIN. */
function JoinIcon(props: RecipeIconProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VB} width={size} height={size} aria-hidden="true">
      <path d="M3 5 L11 12 L3 19 Z" fill={color} opacity="0.85" />
      <path d="M21 5 L13 12 L21 19 Z" fill={color} opacity="0.85" />
      <line x1="11" y1="12" x2="13" y2="12" stroke={color} strokeWidth="1.6" />
    </svg>
  );
}

/** Sigma for GROUPING. */
function GroupingIcon(props: RecipeIconProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VB} width={size} height={size} aria-hidden="true">
      <path
        d="M19 5 H6 L13 12 L6 19 H19"
        fill="none"
        stroke={color}
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/** Window-frame icon for WINDOW. */
function WindowIcon(props: RecipeIconProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VB} width={size} height={size} aria-hidden="true">
      <rect x="3.5" y="4.5" width="17" height="15" rx="1.5" fill="none" stroke={color} strokeWidth="1.6" />
      <line x1="3.5" y1="9.5" x2="20.5" y2="9.5" stroke={color} strokeWidth="1.6" />
      <line x1="12" y1="9.5" x2="12" y2="19.5" stroke={color} strokeWidth="1.6" />
      <rect x="6" y="12" width="3" height="2" fill={color} opacity="0.6" />
    </svg>
  );
}

/** Branching arrows for SPLIT. */
function SplitIcon(props: RecipeIconProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VB} width={size} height={size} aria-hidden="true">
      <path
        d="M4 12 H10 M10 12 L18 6 M10 12 L18 18 M16 4 L18 6 L16 8 M16 16 L18 18 L16 20"
        fill="none"
        stroke={color}
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="10" cy="12" r="1.3" fill={color} />
    </svg>
  );
}

/** Python logo (two slanted blocks). */
function PythonIcon(props: RecipeIconProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VB} width={size} height={size} aria-hidden="true">
      <path
        d="M8 3 H14 a3 3 0 0 1 3 3 v3 H10 a3 3 0 0 0 -3 3 v3 H6 a3 3 0 0 1 -3 -3 V8 a3 3 0 0 1 3 -3 h2 z"
        fill={color}
        opacity="0.9"
      />
      <path
        d="M16 21 H10 a3 3 0 0 1 -3 -3 v-3 H14 a3 3 0 0 0 3 -3 v-3 h1 a3 3 0 0 1 3 3 v6 a3 3 0 0 1 -3 3 z"
        fill={color}
        opacity="0.7"
      />
      <circle cx="9" cy="6.5" r="0.9" fill="white" />
      <circle cx="15" cy="17.5" r="0.9" fill="white" />
    </svg>
  );
}

/** Stats bars for GENERATE_STATISTICS — already in legacy but slightly upgraded. */
/** (legacy GenerateStatisticsGlyph is reused via getLegacyGlyph fallback) */

/** Backward-compat fallback default — same square the legacy code uses. */
function DefaultIcon(props: RecipeIconProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VB} width={size} height={size} aria-hidden="true">
      <rect x="5" y="5" width="14" height="14" rx="2" fill="none" stroke={color} strokeWidth="1.6" />
      <line x1="5" y1="10" x2="19" y2="10" stroke={color} strokeWidth="1.2" />
      <line x1="10" y1="10" x2="10" y2="19" stroke={color} strokeWidth="1.2" />
    </svg>
  );
}

/** Map: NEW DSS-style icons for the 7 types we own here. The remaining 30
 * recipe types are handled by re-using glyphs from `nodes/glyphs.tsx` so
 * the icon library now covers ALL 37 RecipeType members. */
const NEW_ICONS: Record<string, (p: RecipeIconProps) => JSX.Element> = {
  // PREPARE
  PREPARE: PrepareIcon,
  prepare: PrepareIcon,
  // JOIN
  JOIN: JoinIcon,
  join: JoinIcon,
  // GROUPING
  GROUPING: GroupingIcon,
  grouping: GroupingIcon,
  // WINDOW
  WINDOW: WindowIcon,
  window: WindowIcon,
  // SPLIT
  SPLIT: SplitIcon,
  split: SplitIcon,
  // PYTHON
  PYTHON: PythonIcon,
  python: PythonIcon,
};

/**
 * Returns a typed React node rendering the DSS-style glyph for a given
 * recipe type. Falls back to the legacy glyph library, then to a default
 * square so every RecipeType member resolves to *something* visible.
 */
export function recipeIconFor(
  recipeType: RecipeType | string,
  props: RecipeIconProps,
): JSX.Element {
  const k = String(recipeType);
  const NewComp =
    NEW_ICONS[k] ?? NEW_ICONS[k.toUpperCase()] ?? NEW_ICONS[k.toLowerCase()];
  if (NewComp) return <NewComp {...props} />;
  const Legacy = getLegacyGlyph(k as RecipeType);
  if (Legacy) return <Legacy color={props.color} size={props.size ?? 22} />;
  return <DefaultIcon {...props} />;
}

/** Recipe types we ship a dedicated DSS-style icon for at the new layer. */
export const RECIPE_ICON_TYPES: readonly string[] = Object.keys(NEW_ICONS);

/**
 * The full set of RecipeType members the icon library can resolve via
 * either the new `NEW_ICONS` map or the legacy glyph map. Used by tests to
 * verify ≥ 30 recipe types render an inline `<svg>` (currently 37 / 37).
 */
export function listIconCoverage(allTypes: readonly string[]): {
  total: number;
  covered: string[];
  uncovered: string[];
} {
  const covered: string[] = [];
  const uncovered: string[] = [];
  for (const t of allTypes) {
    const has =
      Boolean(NEW_ICONS[t]) ||
      Boolean(NEW_ICONS[t.toUpperCase()]) ||
      Boolean(NEW_ICONS[t.toLowerCase()]) ||
      Boolean(getLegacyGlyph(t as RecipeType));
    if (has) covered.push(t);
    else uncovered.push(t);
  }
  return { total: allTypes.length, covered, uncovered };
}
