---
title: Export (Client-side)
sidebar_position: 9
description: toSvg, toPng, and toPdf exports from packages/flow-viz — client-side canvas export.
---

# Client-side Export

`packages/flow-viz` provides three client-side export functions. These are distinct from the server-side `POST /export/{format}` endpoint — they operate directly on the React Flow canvas DOM, which means they reflect the current visual state (zoom, pan, selection) rather than the full flow.

## toSvg

```typescript
import { toSvg } from "@py-iku-studio/flow-viz";

const svgString = await toSvg(reactFlowInstance, {
  background: "white",   // fill background before export
  width: 1200,           // override viewport width
  height: 800,
});
```

Returns a string containing a complete SVG document. Node colours and fonts match the current theme. Uses the React Flow `getViewport()` API to capture all nodes, including those off-screen.

## toPng

```typescript
import { toPng } from "@py-iku-studio/flow-viz";

const pngBlob = await toPng(reactFlowInstance, {
  scale: 2,   // 2× for retina
  background: "white",
});
```

Rasterises the SVG output via an off-screen `<canvas>` element. Returns a `Blob` with MIME type `image/png`.

## toPdf

```typescript
import { toPdf } from "@py-iku-studio/flow-viz";

const pdfBlob = await toPdf(reactFlowInstance, {
  pageSize: "a4_landscape",
});
```

Wraps the PNG output in a minimal PDF using a PDF generation library. Returns a `Blob` with MIME type `application/pdf`.

Note: `toPdf` is implemented client-side for small flows. For large flows, the UI falls back to calling `POST /export/pdf` on the server (which uses WeasyPrint via the Python API), which handles multi-page pagination correctly.

## Server-side vs client-side export

| | Client-side (flow-viz) | Server-side (API) |
|--|----------------------|------------------|
| SVG | Uses React Flow DOM | Uses `py2dataiku` visualizers |
| PNG | Rasterises from React Flow | Rasterises from py2dataiku SVG |
| PDF | Single-page only | Multi-page (WeasyPrint) |
| Requires API | No | Yes |
| Reflects zoom/pan | Yes | No (always renders full flow) |

The **Export** modal in Studio uses the server-side API for all formats to ensure consistency. The client-side functions are available for embedding scenarios where the API is not available.
