/**
 * Minimal type subset re-exported for flow-viz consumers.
 *
 * @canonical-source: packages/types when M1b lands. Until then these literals
 * mirror the Python `RecipeType`, `DatasetType`, and `DatasetConnectionType`
 * enums, derived from the keys present in `docs/design/tokens.json`.
 */

/** All 37 RecipeType members from py2dataiku.models.dataiku_recipe.RecipeType. */
export type RecipeType =
  | "PREPARE"
  | "SYNC"
  | "GROUPING"
  | "WINDOW"
  | "JOIN"
  | "FUZZY_JOIN"
  | "GEO_JOIN"
  | "STACK"
  | "SPLIT"
  | "SORT"
  | "DISTINCT"
  | "TOP_N"
  | "PIVOT"
  | "SAMPLING"
  | "DOWNLOAD"
  | "GENERATE_FEATURES"
  | "GENERATE_STATISTICS"
  | "PUSH_TO_EDITABLE"
  | "LIST_FOLDER_CONTENTS"
  | "DYNAMIC_REPEAT"
  | "EXTRACT_FAILED_ROWS"
  | "UPSERT"
  | "LIST_ACCESS"
  | "PYTHON"
  | "R"
  | "SQL"
  | "HIVE"
  | "IMPALA"
  | "SPARKSQL"
  | "PYSPARK"
  | "SPARK_SCALA"
  | "SPARKR"
  | "SHELL"
  | "PREDICTION_SCORING"
  | "CLUSTERING_SCORING"
  | "EVALUATION"
  | "AI_ASSISTANT_GENERATE";

/** DatasetType from py2dataiku.models.dataiku_dataset.DatasetType. */
export type DatasetType = "INPUT" | "INTERMEDIATE" | "OUTPUT";

/** Subset of DatasetConnectionType used for shape mapping in node-spec.md. */
export type DatasetConnectionType =
  | "FILESYSTEM"
  | "MANAGED_FOLDER"
  | "SQL_POSTGRESQL"
  | "SQL_MYSQL"
  | "SQL_BIGQUERY"
  | "SQL_SNOWFLAKE"
  | "SQL_REDSHIFT"
  | "S3"
  | "GCS"
  | "AZURE_BLOB"
  | "HDFS"
  | "MONGODB"
  | "ELASTICSEARCH";

/** Theme name. */
export type ThemeName = "light" | "dark";

/** Node deployment / execution status. M3a renders only `none`. */
export type NodeStatus =
  | "none"
  | "not_deployed"
  | "deploying"
  | "deployed"
  | "executing"
  | "error";

/** Recipe node payload as stored on a React Flow node. */
export interface RecipeNodeData {
  type: RecipeType;
  name: string;
  inputs: number;
  outputs: number;
  status?: NodeStatus;
}

/** Dataset node payload as stored on a React Flow node. */
export interface DatasetNodeData {
  datasetType: DatasetType;
  connectionType: DatasetConnectionType;
  name: string;
  status?: NodeStatus;
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
