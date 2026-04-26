---
title: Node Categories
sidebar_position: 5
description: The five visual families of recipe nodes and their colour-coding in the flow canvas.
---

# Node Categories

The 37 `RecipeType` values are grouped into five visual families. The family determines the colour family used for the node (all values from `docs/design/tokens.json`).

## Transform (orange family)

Recipes that reshape data without joining or splitting it.

| Type | pandas mapping | Light bg | Light border |
|------|---------------|----------|-------------|
| PREPARE | Multiple processor steps | `#FFF3E0` | `#FF9800` |
| SYNC | Dataset format conversion | `#ECEFF1` | `#607D8B` |
| SAMPLING | `df.sample()` | `#F1F8E9` | `#8BC34A` |
| DISTINCT | `df.drop_duplicates()` | `#EFEBE9` | `#795548` |
| TOP_N | `df.nlargest()` / `df.nsmallest()` | `#FFF8E1` | `#FFB300` |

## Aggregation (green family)

Recipes that reduce or reshape data by grouping.

| Type | pandas mapping | Light bg | Light border |
|------|---------------|----------|-------------|
| GROUPING | `df.groupby().agg()` | `#E8F5E9` | `#4CAF50` |
| WINDOW | `df.rolling()` / `df.cumsum()` / `df.expanding()` | `#E0F7FA` | `#00BCD4` |
| PIVOT | `df.pivot()` / `df.pivot_table()` | `#E1F5FE` | `#03A9F4` |

## Join (blue family)

Recipes that combine multiple input datasets.

| Type | pandas mapping | Light bg | Light border |
|------|---------------|----------|-------------|
| JOIN | `pd.merge()` / `df.merge()` | `#E3F2FD` | `#2196F3` |
| FUZZY_JOIN | Approximate join | `#E3F2FD` | `#2196F3` |
| GEO_JOIN | Geospatial join | `#E3F2FD` | `#2196F3` |
| STACK | `pd.concat()` | `#F3E5F5` | `#9C27B0` |

## Split (pink family)

Recipes that produce multiple output datasets from one input.

| Type | pandas mapping | Light bg | Light border |
|------|---------------|----------|-------------|
| SPLIT | `df[condition]` (multi-output context) | `#FCE4EC` | `#E91E63` |
| SORT | `df.sort_values()` | `#FFFDE7` | `#FFC107` |
| EXTRACT_FAILED_ROWS | Validation split | `#FBE9E7` | `#FF5722` |

## Code (indigo family)

Recipes that embed custom code.

| Type | Language | Light bg | Light border |
|------|----------|----------|-------------|
| PYTHON | Python | `#E8EAF6` | `#3F51B5` |
| R | R | `#E8EAF6` | `#3F51B5` |
| SQL | SQL | `#E8EAF6` | `#3F51B5` |
| HIVE | HiveQL | `#E8EAF6` | `#3F51B5` |
| PYSPARK | PySpark | `#E8EAF6` | `#3F51B5` |
| SPARKSQL | Spark SQL | `#E8EAF6` | `#3F51B5` |
| (and more) | ... | `#E8EAF6` | `#3F51B5` |

## ML (purple family)

Recipes that use Dataiku ML capabilities.

| Type | Purpose | Light bg | Light border |
|------|---------|----------|-------------|
| PREDICTION_SCORING | Scoring a prediction model | `#F3E5F5` | `#8E24AA` |
| CLUSTERING_SCORING | Scoring a clustering model | `#F3E5F5` | `#8E24AA` |
| EVALUATION | Model evaluation | `#F3E5F5` | `#8E24AA` |
| AI_ASSISTANT_GENERATE | LLM-generated recipe | `#F3E5F5` | `#8E24AA` |

## Remaining types (grey default)

Types not fitting another family use the default grey: bg `#F5F5F5`, border `#9E9E9E`. These include DOWNLOAD, GENERATE_FEATURES, GENERATE_STATISTICS, PUSH_TO_EDITABLE, LIST_FOLDER_CONTENTS, DYNAMIC_REPEAT, UPSERT, LIST_ACCESS.
