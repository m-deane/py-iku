---
title: Export
sidebar_position: 6
description: POST /export/\{format\} — download a flow as zip, json, yaml, svg, png, or pdf.
---

:::note API stable as of M7
The API surface described in this section is stable as of M7. See [/audit](/user-guide/audit-log) for a change log of events. Breaking changes will be versioned.
:::

# Export

## POST /export/\{format\}

Export a `DataikuFlow` in the specified format. Returns a binary stream with appropriate `Content-Type` and `Content-Disposition: attachment` headers.

### Path parameters

| Parameter | Allowed values |
|-----------|---------------|
| `format` | `zip` \| `json` \| `yaml` \| `svg` \| `png` \| `pdf` |

### Request

```json
{
  "flow": { ...DataikuFlow.to_dict()... },
  "opts": {
    "page_size": "a4_landscape",
    "background": "white",
    "scale": 2
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `flow` | object | Yes | `DataikuFlow.to_dict()` payload. |
| `opts` | object | No | Format-specific options (see below). |

### Format-specific options

**PDF:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `page_size` | string | `"a4_landscape"` | Page size. Options: `a4_portrait`, `a4_landscape`, `letter_landscape`. |

**PNG:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `scale` | number | `2` | Device pixel ratio multiplier. |

**SVG:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `background` | string | `"white"` | Background colour (CSS colour value). |

### Response headers

```
Content-Type: image/svg+xml
Content-Disposition: attachment; filename="flow.svg"
```

### Content-Type by format

| Format | Content-Type |
|--------|-------------|
| `zip` | `application/zip` |
| `json` | `application/json` |
| `yaml` | `application/yaml` |
| `svg` | `image/svg+xml` |
| `png` | `image/png` |
| `pdf` | `application/pdf` |

### Status codes

| Code | Meaning |
|------|---------|
| 200 | Export succeeded (binary stream) |
| 400 | Unknown format |
| 422 | Invalid flow payload |
| 500 | Render error |

### Example

```bash
# Export as SVG
curl -X POST http://localhost:8000/export/svg \
  -H "Content-Type: application/json" \
  -d '{"flow": <DataikuFlow.to_dict()>}' \
  --output flow.svg

# Export as zip bundle
curl -X POST http://localhost:8000/export/zip \
  -H "Content-Type: application/json" \
  -d '{"flow": <DataikuFlow.to_dict()>}' \
  --output flow.zip
```
