---
title: Zone Overlays
sidebar_position: 6
description: Zone and ZoneLayer components — grouping recipes visually in the flow canvas.
---

# Zone Overlays

Zones are coloured rectangular overlays that group related recipe and dataset nodes. They are rendered behind all nodes, providing a visual clustering mechanism that maps to Dataiku DSS "Flow Zones".

## Zone data model

Each zone in the `DataikuFlow` carries:

```typescript
interface Zone {
  id: string;
  label: string;
  node_ids: string[];   // recipe and dataset node ids included in this zone
  color_index?: number; // 0-7; cycles if undefined
}
```

## ZoneLayer

`ZoneLayer` is the container component that renders all zones:

```tsx
import { ZoneLayer } from "@py-iku-studio/flow-viz";

// Used internally by FlowCanvas; also available for custom layouts
<ZoneLayer zones={flow.zones ?? []} nodePositions={elkLayout.positions} />
```

`ZoneLayer` computes the bounding rectangle for each zone by:

1. Looking up the ELK-positioned `(x, y, width, height)` for each `node_id`.
2. Taking the union rectangle.
3. Expanding by `tokens.space.zonePadding` (20px) on all sides.
4. Rendering an SVG `<rect>` with rounded corners (radius 8) and the zone's fill/border colour.

## Colour cycling

`tokens.json` defines 8 zone colour slots (index 0–7). If a flow has more than 8 zones, the colour index wraps using `color_index % 8`. Light mode zone colours:

| Index | Fill | Border |
|-------|------|--------|
| 0 | `#E3F2FD` | `#90CAF9` |
| 1 | `#F3E5F5` | `#CE93D8` |
| 2 | `#E8F5E9` | `#A5D6A7` |
| 3 | `#FFF3E0` | `#FFCC80` |
| 4 | `#FCE4EC` | `#F48FB1` |
| 5 | `#E0F7FA` | `#80DEEA` |
| 6 | `#FFF8E1` | `#FFD54F` |
| 7 | `#EFEBE9` | `#BCAAA4` |

## Zone labels

Each zone displays its `label` string in the upper-left corner of the zone rectangle. Font: `tokens.typography.fontSize.zoneLabel` (11px), monospace.

## Interaction

- Click a zone label to select all nodes within that zone.
- Zones do not respond to drag in M8 (they re-compute from node positions). Zone-level drag is planned for M10.

## DSS Flow Zones

Dataiku DSS Flow Zones are a first-class concept in the DSS UI. The `py2dataiku` library does not yet generate zone assignments automatically (planned for M10). In M8, zone data must be added manually to `flow.zones` or set via `FlowCanvas` props.
