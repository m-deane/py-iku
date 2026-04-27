/**
 * Zone overlay primitive.
 *
 * Renders a single translucent zone rectangle with a dashed border + label
 * badge per the Zone Overlay Spec in `docs/design/node-spec.md` section 4.
 *
 * Colors come from `tokens.json`'s `color.theme.<theme>.zone[i]` palette,
 * which carries 8 fill/border pairs. The component is a pure SVG/HTML
 * primitive — it knows nothing about React Flow viewport. The host layer
 * (`ZoneLayer`) positions multiple Zone instances inside an absolutely
 * positioned container that lives behind the React Flow node layer.
 */

import type { CSSProperties, JSX } from "react";
import type { ThemeName } from "../types";
import { ZONE_RADIUS, getZoneColor } from "./tokens";

export interface ZoneRect {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface ZoneProps {
  /** Index into the 8-entry zone palette. */
  paletteIndex: number;
  /** Bounding box of the zone, in React Flow viewport pixels. */
  rect: ZoneRect;
  /** Display label rendered top-left. */
  label: string;
  /** Light/dark theme. */
  theme: ThemeName;
}

export function Zone(props: ZoneProps): JSX.Element {
  const { paletteIndex, rect, label, theme } = props;
  const colors = getZoneColor(paletteIndex, theme);
  const style: CSSProperties = {
    position: "absolute",
    left: rect.x,
    top: rect.y,
    width: rect.width,
    height: rect.height,
    background: colors.fill,
    opacity: 0.6,
    border: `1.5px dashed ${colors.border}`,
    borderRadius: ZONE_RADIUS,
    pointerEvents: "none",
    boxSizing: "border-box",
  };
  const labelStyle: CSSProperties = {
    position: "absolute",
    top: 6,
    left: 10,
    fontSize: 11,
    fontWeight: 700,
    color: colors.border,
    fontFamily: "var(--typography-fontfamily-base, Arial, Helvetica, sans-serif)",
    pointerEvents: "none",
    background: "transparent",
  };
  return (
    <div
      style={style}
      data-zone-index={paletteIndex}
      data-zone-label={label}
      data-testid={`zone-${label}`}
    >
      <span style={labelStyle}>{label}</span>
    </div>
  );
}
