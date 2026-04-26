---
title: Catalog Browser
sidebar_position: 2
description: Browse all 37 recipe types and 122 processor types from the Dataiku DSS catalog.
---

# Catalog Browser

Route: `/catalog`

The Catalog Browser provides a searchable, filterable view of the complete Dataiku DSS recipe and processor catalog as understood by `py2dataiku`. It is read-only and backed by the `/catalog/recipes` and `/catalog/processors` API endpoints.

## Recipe catalog

Displays all 37 `RecipeType` values with:

- Recipe name and icon (matching the Dataiku DSS UI glyphs).
- Visual category (see [Node Categories](/flow-viz/node-categories)).
- Short description of when this recipe is produced by conversion.
- The pandas operation(s) that trigger this recipe type.

The 37 recipe types span five visual families:

| Family | Types |
|--------|-------|
| Transform | PREPARE, SYNC, SAMPLING, DISTINCT, TOP_N |
| Aggregation | GROUPING, WINDOW, PIVOT |
| Join | JOIN, FUZZY_JOIN, GEO_JOIN, STACK |
| Split/Filter | SPLIT |
| Sort | SORT |
| Code | PYTHON, R, SQL, HIVE, IMPALA, SPARKSQL, PYSPARK, SPARK_SCALA, SPARKR, SHELL |
| ML | PREDICTION_SCORING, CLUSTERING_SCORING, EVALUATION, AI_ASSISTANT_GENERATE |
| Misc | DOWNLOAD, GENERATE_FEATURES, GENERATE_STATISTICS, PUSH_TO_EDITABLE, LIST_FOLDER_CONTENTS, DYNAMIC_REPEAT, EXTRACT_FAILED_ROWS, UPSERT, LIST_ACCESS |

## Processor catalog

Displays all 122 `ProcessorType` values (steps within a PREPARE recipe). Backed by `ProcessorCatalog().list_processors()`.

Processors are filterable by category:

- Column operations (rename, delete, move, reorder)
- Row operations (filter, deduplicate, limit)
- Type conversion (date parser, type setter, binner)
- String transforms
- Numeric transforms
- Missing value handling
- Encoding (categorical encoder, flag encoder, etc.)
- Fold / unfold (pivot and melt equivalents)
- Geo / geo processing
- NLP / text analysis
- Join steps (for in-PREPARE joins)

### Search

The search box filters both name and description with a debounced 200ms delay. Search terms are matched against the `ProcessorCatalog` entry's `name` and `description` fields. Query parameter: `?q=`.

### Processor detail

Clicking a processor card opens a detail drawer with:

- Full `ProcessorCatalog` entry fields.
- Parameter schema (field names, types, and defaults).
- Example pandas operation that maps to this processor.

This data comes from `GET /catalog/processors/{type}`.

## Non-obvious mappings

Some pandas operations map to processors (inside PREPARE), not top-level recipes:

| pandas | Maps to... |
|--------|-----------|
| `df.melt()` | PREPARE + FOLD_MULTIPLE_COLUMNS processor |
| `df.round()`, `df.abs()`, `df.clip()` | PREPARE + NUMERIC_TRANSFORM processors |
| `df.fillna()` | PREPARE + FILL_EMPTY_WITH_VALUE processor |
| `df.dropna()` | PREPARE + REMOVE_ROWS_ON_EMPTY processor |
| `df.rename()` | PREPARE + COLUMN_RENAMER processor |

See `py2dataiku/mappings/pandas_mappings.py` for the full mapping tables.
