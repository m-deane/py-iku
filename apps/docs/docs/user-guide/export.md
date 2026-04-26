---
title: Export
sidebar_position: 6
description: Download your flow in any supported format — zip, JSON, YAML, SVG, PNG, or PDF.
---

# Export

Studio supports six export formats via the `POST /export/{format}` endpoint, all accessible through the Export modal in the toolbar.

## Formats

| Format | Extension | Content-Type | Notes |
|--------|-----------|-------------|-------|
| `json` | `.json` | `application/json` | `DataikuFlow.to_dict()` payload |
| `yaml` | `.yaml` | `application/yaml` | Human-readable equivalent |
| `svg` | `.svg` | `image/svg+xml` | Pixel-accurate Dataiku-styled diagram |
| `png` | `.png` | `image/png` | Rasterised SVG at 2× for retina |
| `pdf` | `.pdf` | `application/pdf` | Multi-page if flow is tall |
| `zip` | `.zip` | `application/zip` | Bundle: JSON + SVG + `manifest.json` |

## Using the export modal

1. Click **Export** in the toolbar.
2. Select a format from the dropdown.
3. Optionally adjust format-specific options (PDF page size, SVG background colour).
4. Click **Download**. The browser receives the binary stream with a `Content-Disposition: attachment` header.

## Programmatic export

You can export directly via the API without the UI:

```bash
# Export as zip
curl -X POST http://localhost:8000/export/zip \
  -H "Content-Type: application/json" \
  -d '{"flow": <DataikuFlow.to_dict() payload>}' \
  --output flow.zip

# Export as SVG
curl -X POST http://localhost:8000/export/svg \
  -H "Content-Type: application/json" \
  -d '{"flow": <DataikuFlow.to_dict() payload>}' \
  --output flow.svg
```

See [Export API Reference](/api-reference/export) for the full request schema.

## SVG and PNG quality

The SVG and PNG renderers are backed by `py2dataiku`'s visualizer stack (`py2dataiku/visualizers/`). Node colours, fonts, and layout match the Dataiku DSS Flow UI using the token values from `docs/design/tokens.json`.

The PNG renderer rasterises at 2× device pixel ratio for crisp display on HiDPI screens.

## PDF pagination

For tall flows (more than ~15 recipe nodes stacked vertically), the PDF renderer automatically paginates. Each page has a header with the flow name and a footer with the page number. Default page size is A4 landscape; this can be changed via the `opts.page_size` field in the export request.

## Zip bundle contents

```
flow_<name>.zip
├── flow.json          # DataikuFlow.to_dict()
├── flow.svg           # SVG diagram
└── manifest.json      # {name, exported_at, py_iku_version, recipe_count, dataset_count}
```
