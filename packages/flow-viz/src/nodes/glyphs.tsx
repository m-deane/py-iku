/**
 * Inline SVG glyphs for RecipeType members lacking a dedicated icon in
 * `py2dataiku/visualizers/icons.py`.
 *
 * Each glyph is a 24x24 monochrome SVG that takes a `color` prop. They are
 * intentionally simple — single-stroke / single-fill — so they render
 * legibly inside the 70x70 recipe tile and survive PNG/SVG export.
 *
 * Per `docs/design/icon-inventory.md`, the following 23 RecipeType members
 * resolved to the default square in M3a; M3b adds dedicated SVG glyphs for
 * each one (plus a few extras to upgrade Unicode-only types). The list:
 *
 *   FUZZY_JOIN, GEO_JOIN, SYNC, STACK, SORT, DISTINCT, TOP_N, PIVOT,
 *   SAMPLING, DOWNLOAD, GENERATE_FEATURES, GENERATE_STATISTICS,
 *   PUSH_TO_EDITABLE, LIST_FOLDER_CONTENTS, DYNAMIC_REPEAT,
 *   EXTRACT_FAILED_ROWS, UPSERT, LIST_ACCESS, R, SQL, HIVE, IMPALA,
 *   SPARKSQL, PYSPARK, SPARK_SCALA, SPARKR, SHELL, PREDICTION_SCORING,
 *   CLUSTERING_SCORING, EVALUATION, AI_ASSISTANT_GENERATE.
 */

import type { JSX } from "react";
import type { RecipeType } from "../types";

interface GlyphProps {
  color: string;
  size?: number;
}

const VIEWBOX = "0 0 24 24";

function withDefaults(props: GlyphProps): { color: string; size: number } {
  return { color: props.color, size: props.size ?? 20 };
}

/** Two overlapping fuzzy bowties for FUZZY_JOIN. */
function FuzzyJoinGlyph(props: GlyphProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VIEWBOX} width={size} height={size} aria-hidden="true">
      <path d="M3 6 L11 12 L3 18 Z" fill="none" stroke={color} strokeWidth="1.4" strokeDasharray="2 1.5" />
      <path d="M21 6 L13 12 L21 18 Z" fill="none" stroke={color} strokeWidth="1.4" strokeDasharray="2 1.5" />
      <line x1="11" y1="12" x2="13" y2="12" stroke={color} strokeWidth="1.4" />
    </svg>
  );
}

/** Pin on a globe arc for GEO_JOIN. */
function GeoJoinGlyph(props: GlyphProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VIEWBOX} width={size} height={size} aria-hidden="true">
      <circle cx="12" cy="11" r="8" fill="none" stroke={color} strokeWidth="1.4" />
      <ellipse cx="12" cy="11" rx="8" ry="3" fill="none" stroke={color} strokeWidth="1" />
      <path d="M12 6 a3 3 0 1 0 0.01 0 z" fill={color} />
      <path d="M12 9 L12 13" stroke={color} strokeWidth="1.4" />
    </svg>
  );
}

/** Two horizontal arrows pointing in opposite directions for SYNC. */
function SyncGlyph(props: GlyphProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VIEWBOX} width={size} height={size} aria-hidden="true">
      <path d="M3 8 L18 8 L15 5 M18 8 L15 11" fill="none" stroke={color} strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M21 16 L6 16 L9 13 M6 16 L9 19" fill="none" stroke={color} strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/** Three stacked rectangles for STACK. */
function StackGlyph(props: GlyphProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VIEWBOX} width={size} height={size} aria-hidden="true">
      <rect x="4" y="5" width="16" height="3.5" fill="none" stroke={color} strokeWidth="1.4" />
      <rect x="4" y="10.5" width="16" height="3.5" fill="none" stroke={color} strokeWidth="1.4" />
      <rect x="4" y="16" width="16" height="3.5" fill="none" stroke={color} strokeWidth="1.4" />
    </svg>
  );
}

/** Up/down arrows for SORT. */
function SortGlyph(props: GlyphProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VIEWBOX} width={size} height={size} aria-hidden="true">
      <path d="M7 4 L7 20 M3 8 L7 4 L11 8" fill="none" stroke={color} strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M17 4 L17 20 M13 16 L17 20 L21 16" fill="none" stroke={color} strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/** Bullseye for DISTINCT (unique rings). */
function DistinctGlyph(props: GlyphProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VIEWBOX} width={size} height={size} aria-hidden="true">
      <circle cx="12" cy="12" r="9" fill="none" stroke={color} strokeWidth="1.4" />
      <circle cx="12" cy="12" r="5.5" fill="none" stroke={color} strokeWidth="1.4" />
      <circle cx="12" cy="12" r="2" fill={color} />
    </svg>
  );
}

/** Top-N bar chart with a star on top of the tallest bar. */
function TopNGlyph(props: GlyphProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VIEWBOX} width={size} height={size} aria-hidden="true">
      <rect x="4" y="14" width="3.5" height="6" fill={color} />
      <rect x="9" y="10" width="3.5" height="10" fill={color} />
      <rect x="14" y="6" width="3.5" height="14" fill={color} />
      <path d="M15.75 2 L16.6 3.7 L18.5 4 L17.1 5.4 L17.4 7.3 L15.75 6.4 L14.1 7.3 L14.4 5.4 L13 4 L14.9 3.7 Z" fill={color} />
    </svg>
  );
}

/** Pivot glyph: 4-way swap. */
function PivotGlyph(props: GlyphProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VIEWBOX} width={size} height={size} aria-hidden="true">
      <rect x="4" y="4" width="16" height="16" fill="none" stroke={color} strokeWidth="1.4" />
      <line x1="12" y1="4" x2="12" y2="20" stroke={color} strokeWidth="1.4" />
      <line x1="4" y1="12" x2="20" y2="12" stroke={color} strokeWidth="1.4" />
      <path d="M9 8 L7 8 L7 6 M15 16 L17 16 L17 18" fill="none" stroke={color} strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}

/** Sampling: dotted scattered points. */
function SamplingGlyph(props: GlyphProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VIEWBOX} width={size} height={size} aria-hidden="true">
      <circle cx="6" cy="7" r="1.4" fill={color} />
      <circle cx="13" cy="5" r="1.4" fill={color} />
      <circle cx="18" cy="10" r="1.4" fill={color} />
      <circle cx="9" cy="13" r="1.4" fill={color} />
      <circle cx="16" cy="16" r="1.4" fill={color} />
      <circle cx="6" cy="18" r="1.4" fill={color} />
      <circle cx="13" cy="19" r="1.4" fill={color} />
    </svg>
  );
}

/** Cloud + down arrow for DOWNLOAD. */
function DownloadGlyph(props: GlyphProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VIEWBOX} width={size} height={size} aria-hidden="true">
      <path d="M5 11 a4 4 0 0 1 7-3 a3 3 0 0 1 5 3 a3 3 0 0 1 -1 6 H6 a3 3 0 0 1 -1 -6 Z" fill="none" stroke={color} strokeWidth="1.4" />
      <path d="M12 14 L12 21 M9 18 L12 21 L15 18" fill="none" stroke={color} strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/** Sparkles + columns for GENERATE_FEATURES. */
function GenerateFeaturesGlyph(props: GlyphProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VIEWBOX} width={size} height={size} aria-hidden="true">
      <rect x="3" y="11" width="3" height="9" fill={color} />
      <rect x="8" y="7" width="3" height="13" fill={color} />
      <rect x="13" y="13" width="3" height="7" fill={color} />
      <path d="M19 4 L19.7 6.3 L22 7 L19.7 7.7 L19 10 L18.3 7.7 L16 7 L18.3 6.3 Z" fill={color} />
    </svg>
  );
}

/** Histogram for GENERATE_STATISTICS. */
function GenerateStatisticsGlyph(props: GlyphProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VIEWBOX} width={size} height={size} aria-hidden="true">
      <rect x="3" y="14" width="3" height="6" fill="none" stroke={color} strokeWidth="1.4" />
      <rect x="6" y="10" width="3" height="10" fill="none" stroke={color} strokeWidth="1.4" />
      <rect x="9" y="6" width="3" height="14" fill="none" stroke={color} strokeWidth="1.4" />
      <rect x="12" y="10" width="3" height="10" fill="none" stroke={color} strokeWidth="1.4" />
      <rect x="15" y="14" width="3" height="6" fill="none" stroke={color} strokeWidth="1.4" />
      <rect x="18" y="17" width="3" height="3" fill="none" stroke={color} strokeWidth="1.4" />
    </svg>
  );
}

/** Pencil into table for PUSH_TO_EDITABLE. */
function PushToEditableGlyph(props: GlyphProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VIEWBOX} width={size} height={size} aria-hidden="true">
      <rect x="3" y="9" width="12" height="12" fill="none" stroke={color} strokeWidth="1.4" />
      <line x1="3" y1="13" x2="15" y2="13" stroke={color} strokeWidth="1" />
      <line x1="3" y1="17" x2="15" y2="17" stroke={color} strokeWidth="1" />
      <line x1="9" y1="9" x2="9" y2="21" stroke={color} strokeWidth="1" />
      <path d="M16 8 L20 4 L22 6 L18 10 Z" fill="none" stroke={color} strokeWidth="1.4" strokeLinejoin="round" />
    </svg>
  );
}

/** Folder with a list-bullets motif for LIST_FOLDER_CONTENTS. */
function ListFolderContentsGlyph(props: GlyphProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VIEWBOX} width={size} height={size} aria-hidden="true">
      <path d="M3 7 V20 H21 V9 H12 L10 7 Z" fill="none" stroke={color} strokeWidth="1.4" strokeLinejoin="round" />
      <circle cx="7" cy="13" r="0.9" fill={color} />
      <line x1="9" y1="13" x2="18" y2="13" stroke={color} strokeWidth="1" />
      <circle cx="7" cy="16.5" r="0.9" fill={color} />
      <line x1="9" y1="16.5" x2="18" y2="16.5" stroke={color} strokeWidth="1" />
    </svg>
  );
}

/** Loop arrow for DYNAMIC_REPEAT. */
function DynamicRepeatGlyph(props: GlyphProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VIEWBOX} width={size} height={size} aria-hidden="true">
      <path d="M5 9 a8 8 0 0 1 14 -2 M19 4 V8 H15" fill="none" stroke={color} strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M19 15 a8 8 0 0 1 -14 2 M5 20 V16 H9" fill="none" stroke={color} strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/** Funnel + warn dot for EXTRACT_FAILED_ROWS. */
function ExtractFailedRowsGlyph(props: GlyphProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VIEWBOX} width={size} height={size} aria-hidden="true">
      <path d="M3 4 H21 L15 12 V20 L9 17 V12 Z" fill="none" stroke={color} strokeWidth="1.4" strokeLinejoin="round" />
      <circle cx="18" cy="18" r="3.5" fill={color} />
      <line x1="18" y1="16.5" x2="18" y2="18" stroke="white" strokeWidth="1.5" />
      <circle cx="18" cy="19.5" r="0.5" fill="white" />
    </svg>
  );
}

/** Up arrow into table for UPSERT. */
function UpsertGlyph(props: GlyphProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VIEWBOX} width={size} height={size} aria-hidden="true">
      <rect x="3" y="11" width="18" height="10" fill="none" stroke={color} strokeWidth="1.4" />
      <line x1="3" y1="15" x2="21" y2="15" stroke={color} strokeWidth="1" />
      <line x1="9" y1="11" x2="9" y2="21" stroke={color} strokeWidth="1" />
      <line x1="15" y1="11" x2="15" y2="21" stroke={color} strokeWidth="1" />
      <path d="M12 2 L12 9 M9 5 L12 2 L15 5" fill="none" stroke={color} strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/** Key for LIST_ACCESS. */
function ListAccessGlyph(props: GlyphProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VIEWBOX} width={size} height={size} aria-hidden="true">
      <circle cx="7" cy="12" r="4" fill="none" stroke={color} strokeWidth="1.4" />
      <line x1="11" y1="12" x2="22" y2="12" stroke={color} strokeWidth="1.4" />
      <line x1="17" y1="12" x2="17" y2="16" stroke={color} strokeWidth="1.4" />
      <line x1="20" y1="12" x2="20" y2="15" stroke={color} strokeWidth="1.4" />
    </svg>
  );
}

/** R logo glyph (stylized "R"). */
function RGlyph(props: GlyphProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VIEWBOX} width={size} height={size} aria-hidden="true">
      <ellipse cx="12" cy="12" rx="9" ry="6" fill="none" stroke={color} strokeWidth="1.4" />
      <text x="12" y="16" textAnchor="middle" fontSize="10" fontFamily="serif" fontWeight="700" fill={color}>R</text>
    </svg>
  );
}

/** SQL: stylized cylinder + "SQL". */
function SqlGlyph(props: GlyphProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VIEWBOX} width={size} height={size} aria-hidden="true">
      <ellipse cx="12" cy="6" rx="8" ry="2.5" fill="none" stroke={color} strokeWidth="1.4" />
      <path d="M4 6 V18 A8 2.5 0 0 0 20 18 V6" fill="none" stroke={color} strokeWidth="1.4" />
      <text x="12" y="16" textAnchor="middle" fontSize="6" fontFamily="monospace" fontWeight="700" fill={color}>SQL</text>
    </svg>
  );
}

/** Hive (bee/honeycomb) glyph. */
function HiveGlyph(props: GlyphProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VIEWBOX} width={size} height={size} aria-hidden="true">
      <polygon points="12,3 19,7 19,15 12,19 5,15 5,7" fill="none" stroke={color} strokeWidth="1.4" />
      <polygon points="12,8 15,9.5 15,12.5 12,14 9,12.5 9,9.5" fill={color} />
    </svg>
  );
}

/** Impala (deer head) abstract glyph. */
function ImpalaGlyph(props: GlyphProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VIEWBOX} width={size} height={size} aria-hidden="true">
      <path d="M5 3 L8 9 M19 3 L16 9 M5 3 L8 6 M19 3 L16 6" stroke={color} strokeWidth="1.4" strokeLinecap="round" />
      <ellipse cx="12" cy="14" rx="6" ry="6" fill="none" stroke={color} strokeWidth="1.4" />
      <circle cx="10" cy="13" r="0.8" fill={color} />
      <circle cx="14" cy="13" r="0.8" fill={color} />
    </svg>
  );
}

/** Spark SQL: lightning + table. */
function SparkSqlGlyph(props: GlyphProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VIEWBOX} width={size} height={size} aria-hidden="true">
      <path d="M11 2 L5 13 H10 L8 22 L17 10 H12 Z" fill={color} />
      <text x="20" y="22" textAnchor="end" fontSize="5" fontFamily="monospace" fontWeight="700" fill={color}>SQL</text>
    </svg>
  );
}

/** PySpark: lightning + λ. */
function PySparkGlyph(props: GlyphProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VIEWBOX} width={size} height={size} aria-hidden="true">
      <path d="M11 2 L5 13 H10 L8 22 L17 10 H12 Z" fill={color} />
      <text x="22" y="22" textAnchor="end" fontSize="7" fontFamily="serif" fontWeight="700" fill={color}>λ</text>
    </svg>
  );
}

/** Spark Scala. */
function SparkScalaGlyph(props: GlyphProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VIEWBOX} width={size} height={size} aria-hidden="true">
      <path d="M11 2 L5 13 H10 L8 22 L17 10 H12 Z" fill={color} />
      <text x="22" y="22" textAnchor="end" fontSize="6" fontFamily="serif" fontWeight="700" fill={color}>S</text>
    </svg>
  );
}

/** SparkR. */
function SparkRGlyph(props: GlyphProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VIEWBOX} width={size} height={size} aria-hidden="true">
      <path d="M11 2 L5 13 H10 L8 22 L17 10 H12 Z" fill={color} />
      <text x="22" y="22" textAnchor="end" fontSize="6" fontFamily="serif" fontWeight="700" fill={color}>R</text>
    </svg>
  );
}

/** Shell: terminal prompt. */
function ShellGlyph(props: GlyphProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VIEWBOX} width={size} height={size} aria-hidden="true">
      <rect x="3" y="5" width="18" height="14" rx="1.5" fill="none" stroke={color} strokeWidth="1.4" />
      <path d="M6 10 L9 12.5 L6 15" fill="none" stroke={color} strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      <line x1="11" y1="15" x2="17" y2="15" stroke={color} strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}

/** Prediction (target with crosshair). */
function PredictionScoringGlyph(props: GlyphProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VIEWBOX} width={size} height={size} aria-hidden="true">
      <circle cx="12" cy="12" r="9" fill="none" stroke={color} strokeWidth="1.4" />
      <circle cx="12" cy="12" r="5" fill="none" stroke={color} strokeWidth="1.4" />
      <line x1="12" y1="2" x2="12" y2="6" stroke={color} strokeWidth="1.4" />
      <line x1="12" y1="18" x2="12" y2="22" stroke={color} strokeWidth="1.4" />
      <line x1="2" y1="12" x2="6" y2="12" stroke={color} strokeWidth="1.4" />
      <line x1="18" y1="12" x2="22" y2="12" stroke={color} strokeWidth="1.4" />
      <circle cx="12" cy="12" r="1.5" fill={color} />
    </svg>
  );
}

/** Clustering (3 dot clusters). */
function ClusteringScoringGlyph(props: GlyphProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VIEWBOX} width={size} height={size} aria-hidden="true">
      <circle cx="6" cy="6" r="1.4" fill={color} />
      <circle cx="9" cy="5" r="1.4" fill={color} />
      <circle cx="7" cy="9" r="1.4" fill={color} />
      <circle cx="17" cy="7" r="1.4" fill={color} />
      <circle cx="20" cy="9" r="1.4" fill={color} />
      <circle cx="18" cy="11" r="1.4" fill={color} />
      <circle cx="11" cy="17" r="1.4" fill={color} />
      <circle cx="14" cy="19" r="1.4" fill={color} />
      <circle cx="12" cy="20" r="1.4" fill={color} />
    </svg>
  );
}

/** Evaluation (checkmark in circle). */
function EvaluationGlyph(props: GlyphProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VIEWBOX} width={size} height={size} aria-hidden="true">
      <circle cx="12" cy="12" r="9" fill="none" stroke={color} strokeWidth="1.4" />
      <path d="M7 12 L11 16 L17 9" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/** AI assistant (sparkle). */
function AiAssistantGenerateGlyph(props: GlyphProps): JSX.Element {
  const { color, size } = withDefaults(props);
  return (
    <svg viewBox={VIEWBOX} width={size} height={size} aria-hidden="true">
      <path d="M12 2 L13.5 8.5 L20 10 L13.5 11.5 L12 18 L10.5 11.5 L4 10 L10.5 8.5 Z" fill={color} />
      <path d="M19 17 L19.7 19.3 L22 20 L19.7 20.7 L19 23 L18.3 20.7 L16 20 L18.3 19.3 Z" fill={color} />
    </svg>
  );
}

/** Map of RecipeType → SVG component. Only includes types that have a
 *  dedicated SVG; consumers should fall back to the Unicode glyph when
 *  this returns undefined. Keys use lowercase DSS values from @py-iku-studio/types. */
const SVG_GLYPHS: Partial<Record<RecipeType, (props: GlyphProps) => JSX.Element>> = {
  "fuzzyjoin": FuzzyJoinGlyph,
  "geojoin": GeoJoinGlyph,
  "sync": SyncGlyph,
  "stack": StackGlyph,
  "sort": SortGlyph,
  "distinct": DistinctGlyph,
  "topn": TopNGlyph,
  "pivot": PivotGlyph,
  "sampling": SamplingGlyph,
  "download": DownloadGlyph,
  "generate_features": GenerateFeaturesGlyph,
  "generate_statistics": GenerateStatisticsGlyph,
  "push_to_editable": PushToEditableGlyph,
  "list_folder_contents": ListFolderContentsGlyph,
  "dynamic_repeat": DynamicRepeatGlyph,
  "extract_failed_rows": ExtractFailedRowsGlyph,
  "upsert": UpsertGlyph,
  "list_access": ListAccessGlyph,
  "r": RGlyph,
  "sql_script": SqlGlyph,
  "hive": HiveGlyph,
  "impala": ImpalaGlyph,
  "spark_sql_query": SparkSqlGlyph,
  "pyspark": PySparkGlyph,
  "spark_scala": SparkScalaGlyph,
  "sparkr": SparkRGlyph,
  "shell": ShellGlyph,
  "prediction_scoring": PredictionScoringGlyph,
  "clustering_scoring": ClusteringScoringGlyph,
  "standalone_evaluation": EvaluationGlyph,
  "ai_assistant_generate": AiAssistantGenerateGlyph,
};

/** Lookup map: accept BOTH UPPERCASE Python enum names and lowercase DSS
 *  canonical names. The two key conventions coexist while the codebase
 *  migrates from one to the other. */
const SVG_GLYPHS_DUAL: Record<string, (props: GlyphProps) => JSX.Element> = {
  ...SVG_GLYPHS,
  FUZZY_JOIN: FuzzyJoinGlyph,
  GEO_JOIN: GeoJoinGlyph,
  SYNC: SyncGlyph,
  STACK: StackGlyph,
  SORT: SortGlyph,
  DISTINCT: DistinctGlyph,
  TOP_N: TopNGlyph,
  PIVOT: PivotGlyph,
  SAMPLING: SamplingGlyph,
  DOWNLOAD: DownloadGlyph,
  GENERATE_FEATURES: GenerateFeaturesGlyph,
  GENERATE_STATISTICS: GenerateStatisticsGlyph,
  PUSH_TO_EDITABLE: PushToEditableGlyph,
  LIST_FOLDER_CONTENTS: ListFolderContentsGlyph,
  DYNAMIC_REPEAT: DynamicRepeatGlyph,
  EXTRACT_FAILED_ROWS: ExtractFailedRowsGlyph,
  UPSERT: UpsertGlyph,
  LIST_ACCESS: ListAccessGlyph,
  R: RGlyph,
  SQL: SqlGlyph,
  HIVE: HiveGlyph,
  IMPALA: ImpalaGlyph,
  SPARKSQL: SparkSqlGlyph,
  PYSPARK: PySparkGlyph,
  SPARK_SCALA: SparkScalaGlyph,
  SPARKR: SparkRGlyph,
  SHELL: ShellGlyph,
  PREDICTION_SCORING: PredictionScoringGlyph,
  CLUSTERING_SCORING: ClusteringScoringGlyph,
  EVALUATION: EvaluationGlyph,
  AI_ASSISTANT_GENERATE: AiAssistantGenerateGlyph,
};

/** Returns the SVG glyph component for `type` if one is defined. */
export function getSvgGlyph(
  type: RecipeType,
): ((props: GlyphProps) => JSX.Element) | undefined {
  const k = String(type);
  return SVG_GLYPHS_DUAL[k] ?? SVG_GLYPHS_DUAL[k.toUpperCase()] ?? SVG_GLYPHS_DUAL[k.toLowerCase()];
}

/** All RecipeType members that have a custom SVG glyph (for tests + docs). */
export const SVG_GLYPH_TYPES: readonly string[] = Object.keys(SVG_GLYPHS_DUAL);
