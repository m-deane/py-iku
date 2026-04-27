/**
 * Minimal type subset re-exported for flow-viz consumers.
 *
 * RecipeType, DatasetType, DatasetConnectionType are now sourced from
 * @py-iku-studio/types (codegen from /openapi.json). The generated API
 * types use lowercase DSS enum values (e.g. "prepare", "grouping"); the
 * flow-viz rendering layer uses those values directly from this file.
 *
 * NOTE: Existing render code that used uppercase keys (e.g. "PREPARE") is
 * being migrated to lowercase DSS values in this file. See nodes/index.ts.
 */

import type { components } from "@py-iku-studio/types";

/**
 * All 37 RecipeType DSS values (lowercase).
 * Sourced from @py-iku-studio/types codegen; replaced the hand-written union.
 */
export type RecipeType = components["schemas"]["RecipeTypeEnum"];

/**
 * DatasetType DSS values (lowercase: "input", "intermediate", "output").
 * Sourced from @py-iku-studio/types codegen.
 */
export type DatasetType = components["schemas"]["DatasetTypeEnum"];

/**
 * DatasetConnectionType — canonical DSS connection string values.
 * Sourced from @py-iku-studio/types codegen.
 */
export type DatasetConnectionType = components["schemas"]["DatasetConnectionTypeEnum"];

/** Theme name. */
export type ThemeName = "light" | "dark";

/** Node deployment / execution status. */
export type NodeStatus =
  | "none"
  | "not_deployed"
  | "deploying"
  | "deployed"
  | "executing"
  | "done"
  | "error";

/** Recipe node payload as stored on a React Flow node. */
export interface RecipeNodeData {
  type: RecipeType;
  name: string;
  inputs: number;
  outputs: number;
  status?: NodeStatus;
  dimmed?: boolean;
  /**
   * LLM mapping confidence in [0, 1]. ``null`` / ``undefined`` means
   * rule-based or unspecified — the card renders an "R" rule-based
   * badge in that case. The `<RecipeNode>` component derives its
   * shading band from this:
   *   confidence == null OR >= 0.85 -> no shade
   *   0.60 <= confidence < 0.85    -> warn (2px var(--warn-border) + ⚠)
   *   confidence < 0.60            -> danger (2px var(--danger-border) + ⚠ + pulse)
   */
  confidence?: number | null;
  /**
   * Inclusive [start, end] 1-indexed source-line span. Surfaced to the
   * recipe popover as "Lines X-Y of source ↗"; clicking the link drives
   * `monaco.editor.deltaDecorations` in the Convert page editor.
   */
  sourceLines?: [number, number] | null;
  /** One-sentence rationale rendered in the popover above the source-link. */
  reasoning?: string | null;
}

/** Dataset node payload as stored on a React Flow node. */
export interface DatasetNodeData {
  datasetType: DatasetType;
  connectionType: DatasetConnectionType;
  name: string;
  status?: NodeStatus;
  dimmed?: boolean;
}

/** Generic flow-node descriptor used by the layout engine. */
export interface FlowNode {
  id: string;
  type: "recipe" | "dataset";
  data: RecipeNodeData | DatasetNodeData;
  position?: { x: number; y: number };
}

/** Generic edge descriptor. */
export interface FlowEdge {
  id: string;
  source: string;
  target: string;
  data?: {
    optional?: boolean;
    rowBucket?: "thin" | "medium" | "thick";
    schemaChange?: "none" | "modified" | "break";
  };
}

/**
 * Minimal flow shape consumed by `<FlowCanvas>`. Will be replaced by
 * `DataikuFlowModel` from `@py-iku-studio/types` in M5.
 */
export interface MinimalFlow {
  nodes: FlowNode[];
  edges: FlowEdge[];
}
