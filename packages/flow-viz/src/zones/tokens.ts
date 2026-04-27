/**
 * Zone palette accessors. Reads the `color.theme.<theme>.zone[]` arrays
 * from `tokens.json`. Falls back to a neutral grey pair if the index is
 * out of range.
 */

import tokensJson from "../../../../docs/design/tokens.json";
import type { ThemeName } from "../types";

interface ZonePair {
  fill: string;
  border: string;
}

interface TokensJson {
  color: {
    theme: Record<ThemeName, { zone: ZonePair[] }>;
  };
}

const TOKENS = tokensJson as unknown as TokensJson;

const FALLBACK: ZonePair = { fill: "#EEEEEE", border: "#9E9E9E" };

export function getZoneColor(index: number, theme: ThemeName): ZonePair {
  const palette = TOKENS.color.theme[theme]?.zone ?? [];
  const wrapped = ((index % palette.length) + palette.length) % palette.length;
  return palette[wrapped] ?? FALLBACK;
}

/** Number of palette entries (8 per `tokens.json`). */
export const ZONE_PALETTE_SIZE: number = TOKENS.color.theme.light.zone.length;

/** Default border-radius for zones (per node-spec.md). */
export const ZONE_RADIUS = 12;

/** Padding around a zone's nodes when computing bounding boxes. */
export const ZONE_PADDING = 24;
