import type { RecipeType } from "../types";

export type RecipeCategory = "prep" | "structure" | "code" | "ml" | "io";

const CATEGORY_BY_TYPE: Record<string, RecipeCategory> = {
  PREPARE: "prep", prepare: "prep",
  SAMPLING: "prep", sampling: "prep",
  DISTINCT: "prep", distinct: "prep",
  STACK: "prep", stack: "prep",
  EXTRACT_FAILED_ROWS: "prep", extract_failed_rows: "prep",
  GENERATE_FEATURES: "prep", generate_features: "prep",
  GENERATE_STATISTICS: "prep", generate_statistics: "prep",
  DYNAMIC_REPEAT: "prep", dynamic_repeat: "prep",
  JOIN: "structure", join: "structure",
  FUZZY_JOIN: "structure", fuzzyjoin: "structure", fuzzy_join: "structure",
  GEO_JOIN: "structure", geojoin: "structure", geo_join: "structure",
  GROUPING: "structure", grouping: "structure",
  WINDOW: "structure", window: "structure",
  SPLIT: "structure", split: "structure",
  SORT: "structure", sort: "structure",
  TOP_N: "structure", topn: "structure", top_n: "structure",
  PIVOT: "structure", pivot: "structure",
  PYTHON: "code", python: "code",
  R: "code", r: "code",
  SQL: "code", sql: "code", sql_script: "code",
  HIVE: "code", hive: "code",
  IMPALA: "code", impala: "code",
  SPARKSQL: "code", sparksql: "code", spark_sql_query: "code",
  PYSPARK: "code", pyspark: "code",
  SPARK_SCALA: "code", spark_scala: "code",
  SPARKR: "code", sparkr: "code",
  SHELL: "code", shell: "code",
  PREDICTION_SCORING: "ml", prediction_scoring: "ml",
  CLUSTERING_SCORING: "ml", clustering_scoring: "ml",
  EVALUATION: "ml", evaluation: "ml", standalone_evaluation: "ml",
  AI_ASSISTANT_GENERATE: "ml", ai_assistant_generate: "ml",
  SYNC: "io", sync: "io",
  DOWNLOAD: "io", download: "io",
  PUSH_TO_EDITABLE: "io", push_to_editable: "io",
  UPSERT: "io", upsert: "io",
  LIST_FOLDER_CONTENTS: "io", list_folder_contents: "io",
  LIST_ACCESS: "io", list_access: "io",
};

export function categoryFor(type: RecipeType): RecipeCategory {
  return (CATEGORY_BY_TYPE[String(type)] ?? CATEGORY_BY_TYPE[String(type).toUpperCase()] ?? CATEGORY_BY_TYPE[String(type).toLowerCase()] ?? "structure");
}

const CODE_LANGUAGE_BADGE: Record<string, string> = {
  PYTHON: "py", python: "py",
  R: "R", r: "R",
  SQL: "SQL", sql: "SQL", sql_script: "SQL",
  HIVE: "hql", hive: "hql",
  IMPALA: "impl", impala: "impl",
  SPARKSQL: "sSQL", sparksql: "sSQL", spark_sql_query: "sSQL",
  PYSPARK: "pySp", pyspark: "pySp",
  SPARK_SCALA: "scl", spark_scala: "scl",
  SPARKR: "sR", sparkr: "sR",
  SHELL: "sh", shell: "sh",
};

export function subLabelFor(type: RecipeType): string | null {
  if (categoryFor(type) !== "code") return null;
  const k = String(type);
  return CODE_LANGUAGE_BADGE[k] ?? CODE_LANGUAGE_BADGE[k.toUpperCase()] ?? CODE_LANGUAGE_BADGE[k.toLowerCase()] ?? null;
}
