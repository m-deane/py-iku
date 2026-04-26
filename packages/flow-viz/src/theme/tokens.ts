/**
 * Token loader and lookup helpers.
 *
 * Token JSON is imported at build time. Functions return raw hex strings; for
 * runtime CSS theming use the generated `tokens.css` (see
 * `scripts/sync-tokens.ts`) which exposes the same data as CSS variables.
 *
 * `TODO:designer-decision` markers in `tokens.json` propagate as `undefined`
 * from these helpers; callers fall back to the appropriate "default" entry.
 */

import tokensJson from "../../../../docs/design/tokens.json";
import type { DatasetConnectionType, DatasetType, RecipeType, ThemeName } from "../types";

interface ColorTriplet {
  bg: string;
  border: string;
  text: string;
}

interface ThemedTriplet {
  light: ColorTriplet;
  dark: ColorTriplet;
}

interface TokensJson {
  color: {
    theme: Record<ThemeName, { background: string; grid: string; connection: string; connectionHover: string }>;
    recipe: Record<string, ThemedTriplet>;
    dataset: Record<string, ThemedTriplet>;
    connection: Record<string, ThemedTriplet>;
  };
  typography: {
    fontFamily: { base: string; mono: string };
    fontSize: { dataset: number; recipe: number; icon: number; zoneLabel: number };
    fontWeight: { normal: number; medium: number; bold: number };
  };
  space: {
    layerSpacing: number;
    nodeSpacing: number;
    padding: number;
    zonePadding: number;
  };
  radius: { dataset: number; recipe: number };
  node: Record<string, { width: number; height: number; icon?: string; label?: string }>;
}

export interface Tokens {
  raw: TokensJson;
  recipeColor(type: RecipeType, theme: ThemeName): ColorTriplet;
  datasetColor(type: DatasetType, theme: ThemeName): ColorTriplet;
  connectionColor(type: DatasetConnectionType, theme: ThemeName): ColorTriplet;
}

const TOKENS = tokensJson as unknown as TokensJson;

const DEFAULT_RECIPE: Record<ThemeName, ColorTriplet> = {
  light: { bg: "#F5F5F5", border: "#9E9E9E", text: "#616161" },
  dark: { bg: "#424242", border: "#9E9E9E", text: "#BDBDBD" },
};

const DEFAULT_DATASET: Record<ThemeName, ColorTriplet> = {
  light: { bg: "#ECEFF1", border: "#78909C", text: "#455A64" },
  dark: { bg: "#2D2D2D", border: "#78909C", text: "#B0BEC5" },
};

function isUsable(value: string | undefined): value is string {
  return typeof value === "string" && !value.includes("TODO");
}

function sanitizeTriplet(t: ColorTriplet | undefined, fallback: ColorTriplet): ColorTriplet {
  if (!t) return fallback;
  return {
    bg: isUsable(t.bg) ? t.bg : fallback.bg,
    border: isUsable(t.border) ? t.border : fallback.border,
    text: isUsable(t.text) ? t.text : fallback.text,
  };
}

export function loadTokens(): Tokens {
  return {
    raw: TOKENS,
    recipeColor(type, theme) {
      const entry = TOKENS.color.recipe[type];
      return sanitizeTriplet(entry?.[theme], DEFAULT_RECIPE[theme]);
    },
    datasetColor(type, theme) {
      const entry = TOKENS.color.dataset[type];
      return sanitizeTriplet(entry?.[theme], DEFAULT_DATASET[theme]);
    },
    connectionColor(type, theme) {
      const entry = TOKENS.color.connection[type];
      return sanitizeTriplet(entry?.[theme], DEFAULT_DATASET[theme]);
    },
  };
}

const _tokens = loadTokens();

/** Lookup the recipe color triplet for a given type and theme. */
export function getRecipeColor(type: RecipeType, theme: ThemeName): ColorTriplet {
  return _tokens.recipeColor(type, theme);
}

/** Lookup the dataset color triplet by DatasetType. */
export function getDatasetColor(type: DatasetType, theme: ThemeName): ColorTriplet {
  return _tokens.datasetColor(type, theme);
}

/** Lookup the connection-type color triplet. */
export function getConnectionColor(
  type: DatasetConnectionType,
  theme: ThemeName,
): ColorTriplet {
  return _tokens.connectionColor(type, theme);
}

/**
 * Map a connection type to one of the three abstract dataset shapes per
 * `node-spec.md` section 2: `cylinder` (relational), `folder` (filesystem),
 * `document` (unstructured / object store / search index).
 */
export type DatasetShape = "cylinder" | "folder" | "document";

const SHAPE_MAP: Record<DatasetConnectionType, DatasetShape> = {
  FILESYSTEM: "folder",
  MANAGED_FOLDER: "folder",
  SQL_POSTGRESQL: "cylinder",
  SQL_MYSQL: "cylinder",
  SQL_BIGQUERY: "cylinder",
  SQL_SNOWFLAKE: "cylinder",
  SQL_REDSHIFT: "cylinder",
  HDFS: "cylinder",
  S3: "document",
  GCS: "document",
  AZURE_BLOB: "document",
  MONGODB: "document",
  ELASTICSEARCH: "document",
};

export function getDatasetShape(type: DatasetConnectionType): DatasetShape {
  return SHAPE_MAP[type] ?? "folder";
}

/** Layout-engine spacing pulled from tokens. */
export const SPACING = {
  layer: TOKENS.space.layerSpacing,
  node: TOKENS.space.nodeSpacing,
  padding: TOKENS.space.padding,
  zone: TOKENS.space.zonePadding,
} as const;

/** Default node sizes pulled from tokens. */
export const NODE_SIZES = {
  recipe: { width: 70, height: 70 },
  dataset: { width: 160, height: 50 },
} as const;
