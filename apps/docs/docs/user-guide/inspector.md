---
title: Inspector Panel
sidebar_position: 4
description: Per-node detail panel — recipe settings, processor list, input/output datasets.
---

# Inspector Panel

The Inspector Panel opens as a right-side drawer whenever you click a node in the flow canvas. It shows the full structured representation of that node's `DataikuRecipe` or `DataikuDataset`.

## Recipe inspector

For recipe nodes, the inspector shows:

### Header

- Recipe type badge (e.g. `GROUPING`) with the type-specific colour from `tokens.json`.
- Recipe name (auto-sanitised from the output dataset name).
- Input and output dataset list.

### Settings tab

Displays the typed `RecipeSettings` subclass fields for this recipe. Each `RecipeType` has a corresponding settings subclass:

| Recipe | Settings class | Key fields shown |
|--------|---------------|-----------------|
| GROUPING | `GroupingSettings` | group_by, aggregations (column → function) |
| JOIN | `JoinSettings` | join_type (inner/left/right/outer), join_conditions, output_columns |
| PREPARE | `PrepareSettings` | steps list (each with type + params) |
| SORT | `SortSettings` | columns, ascending[] |
| WINDOW | `WindowSettings` | partition_by, order_by, window_functions |
| SPLIT | `SplitSettings` | filters, output_names |
| DISTINCT | `DistinctSettings` | columns |
| TOP_N | `TopNSettings` | n, order_by, ascending |
| PIVOT | `PivotSettings` | row_identifier, column_to_pivot, value_to_aggregate |

Settings are displayed as a structured property list, not raw JSON, so field names are human-readable.

### Processors tab (PREPARE only)

For PREPARE recipes, the Processors tab lists each `PrepareStep` in order:

- Processor type (e.g. `COLUMN_RENAMER`).
- Parameters (e.g. `old_name → new_name`).
- Step index and a drag handle (UI note: drag reordering is display-only in M8; editing is planned for M10).

### Raw JSON tab

Shows the raw `DataikuRecipe.to_dict()` payload with syntax highlighting. A **Copy** button copies to clipboard.

## Dataset inspector

For dataset nodes, the inspector shows:

- Dataset name.
- Dataset type (`DatasetType` enum value).
- Connection type (`DatasetConnectionType` enum value).
- Role: input, intermediate, or output.
- Whether the node is a source (no incoming edges) or sink (no outgoing edges).
- Deployment status badge — currently always `not_deployed` (will be live in M10 with DSS write-back).
