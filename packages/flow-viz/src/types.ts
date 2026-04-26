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
