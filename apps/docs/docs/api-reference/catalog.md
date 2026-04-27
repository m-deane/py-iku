---
title: Catalog
sidebar_position: 3
description: GET /catalog/recipes and /catalog/processors — recipe and processor catalog endpoints.
---

:::note API stable as of M7
The API surface described in this section is stable as of M7. See [/audit](/user-guide/audit-log) for a change log of events. Breaking changes will be versioned.
:::

# Catalog

## GET /catalog/recipes

List all 37 Dataiku recipe types. Response is cached for 60 seconds (`Cache-Control: public, max-age=60`).

### Response 200

```json
[
  {
    "type": "PREPARE",
    "name": "Prepare",
    "category": "transform",
    "icon": "prepare",
    "description": "Apply a sequence of processors to transform a dataset."
  },
  {
    "type": "GROUPING",
    "name": "Grouping",
    "category": "aggregation",
    "icon": "grouping",
    "description": "Group rows and compute aggregations (sum, count, mean, etc.)."
  }
]
```

### Example

```bash
curl http://localhost:8000/catalog/recipes
```

---

## GET /catalog/processors

List all 122 processor types (steps within a PREPARE recipe). Backed by `ProcessorCatalog().list_processors()`.

### Query parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `q` | string | Full-text search on name and description. |
| `category` | string | Filter by processor category. |

### Response 200

```json
[
  {
    "type": "COLUMN_RENAMER",
    "name": "Column Renamer",
    "category": "column",
    "description": "Rename one or more columns.",
    "parameters": [
      { "name": "renamings", "type": "array", "description": "List of {from, to} pairs." }
    ]
  }
]
```

### Example

```bash
# All processors
curl http://localhost:8000/catalog/processors

# Search for "date"
curl "http://localhost:8000/catalog/processors?q=date"

# Filter by category
curl "http://localhost:8000/catalog/processors?category=column"
```

---

## GET /catalog/processors/\{type\}

Get the full catalog entry for a single processor type.

### Path parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `type` | `ProcessorType` | Processor type value (e.g. `COLUMN_RENAMER`). Case-sensitive. |

### Response 200

```json
{
  "type": "COLUMN_RENAMER",
  "name": "Column Renamer",
  "category": "column",
  "description": "Rename one or more columns.",
  "parameters": [...],
  "pandas_equivalent": "df.rename(columns={...})",
  "example": {
    "type": "COLUMN_RENAMER",
    "params": { "renamings": [{"from": "old_name", "to": "new_name"}] }
  }
}
```

### Status codes

| Code | Meaning |
|------|---------|
| 200 | Found |
| 404 | Unknown processor type |
| 422 | Invalid `type` path parameter |
