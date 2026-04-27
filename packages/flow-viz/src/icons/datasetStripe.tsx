/**
 * Sprint-6: dataset-stripe colour helper.
 *
 * Returns a CSS variable (defined in `apps/web/src/styles/ui-tokens.css`)
 * keyed by DatasetConnectionType — the vertical stripe on the LEFT edge
 * of the dataset rectangle node mirrors real DSS conventions:
 *   • filesystem-style → green
 *   • SQL family       → blue
 *   • cloud object     → orange
 *   • inline           → red
 *   • NoSQL            → purple
 *   • HTTP / API       → yellow
 */

import type { DatasetConnectionType } from "../types";

/** Family classification used to group connection types under one color. */
export type ConnectionFamily =
  | "filesystem"
  | "sql"
  | "cloud"
  | "inline"
  | "nosql"
  | "http"
  | "default";

const FAMILY_BY_CONNECTION: Record<string, ConnectionFamily> = {
  // Filesystem
  Filesystem: "filesystem",
  FILESYSTEM: "filesystem",
  filesystem: "filesystem",
  ManagedFolder: "filesystem",
  MANAGED_FOLDER: "filesystem",
  managed_folder: "filesystem",

  // SQL family
  PostgreSQL: "sql",
  SQL_POSTGRESQL: "sql",
  postgresql: "sql",
  MySQL: "sql",
  SQL_MYSQL: "sql",
  mysql: "sql",
  BigQuery: "sql",
  SQL_BIGQUERY: "sql",
  bigquery: "sql",
  Snowflake: "sql",
  SQL_SNOWFLAKE: "sql",
  snowflake: "sql",
  Redshift: "sql",
  SQL_REDSHIFT: "sql",
  redshift: "sql",
  HDFS: "cloud",  // HDFS uses cloud-style stripe per task spec
  hdfs: "cloud",
  // Cloud object stores
  S3: "cloud",
  s3: "cloud",
  GCS: "cloud",
  gcs: "cloud",
  Azure: "cloud",
  AZURE_BLOB: "cloud",
  azure_blob: "cloud",
  // NoSQL family
  MongoDB: "nosql",
  MONGODB: "nosql",
  mongodb: "nosql",
  Elasticsearch: "http",  // search index → "API/HTTP-y" yellow
  ELASTICSEARCH: "http",
  elasticsearch: "http",
  // Inline
  Inline: "inline",
  INLINE: "inline",
  inline: "inline",
  // HTTP / API
  HTTP: "http",
  Http: "http",
  http: "http",
};

const FAMILY_TO_VAR: Record<ConnectionFamily, string> = {
  filesystem: "var(--dataset-stripe-filesystem)",
  sql: "var(--dataset-stripe-sql)",
  cloud: "var(--dataset-stripe-cloud)",
  inline: "var(--dataset-stripe-inline)",
  nosql: "var(--dataset-stripe-nosql)",
  http: "var(--dataset-stripe-http)",
  default: "var(--dataset-stripe-default)",
};

/**
 * Resolve a CSS variable expression for the left-edge stripe color of a
 * dataset node, given its DSS connection type. Returns a `var(--…)` string
 * suitable for inline `style={{ borderLeftColor: … }}` (or our CSS module
 * via a custom property).
 */
export function datasetStripeColor(
  connectionType: DatasetConnectionType | string,
): string {
  const k = String(connectionType);
  const fam =
    FAMILY_BY_CONNECTION[k] ??
    FAMILY_BY_CONNECTION[k.toUpperCase()] ??
    FAMILY_BY_CONNECTION[k.toLowerCase()] ??
    "default";
  return FAMILY_TO_VAR[fam];
}

/** Returns the abstract family for a connection type. Useful for tests. */
export function familyFor(
  connectionType: DatasetConnectionType | string,
): ConnectionFamily {
  const k = String(connectionType);
  return (
    FAMILY_BY_CONNECTION[k] ??
    FAMILY_BY_CONNECTION[k.toUpperCase()] ??
    FAMILY_BY_CONNECTION[k.toLowerCase()] ??
    "default"
  );
}

export const KNOWN_CONNECTION_TYPES: readonly string[] = Object.keys(
  FAMILY_BY_CONNECTION,
);
