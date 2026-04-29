---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/geo-join.html
fetched_at: 2026-04-29
category: processors
---

# Geo join with other dataset (memory-based)

> Warning: "Memory-based geo join processor is deprecated. Use a dedicated geo join recipe instead."

## Overview

This processor performs geographic nearest-neighbour joining between two datasets containing geo coordinates.

## Example use case

A common scenario involves processing geo-tagged events where you need to identify the closest point of interest from a separate dataset. For each event location, the processor retrieves matching details and identifiers from the nearest point of interest.

## Requirements

Both datasets must contain latitude and longitude columns. The current dataset's coordinate columns can be generated from prior processing steps, such as GeoIP resolution. Similarly, the joined dataset requires its own latitude and longitude columns.

## Parameters

The processor requires:

- Latitude and longitude columns from the current dataset
- The target dataset name (must be in the same project)
- Latitude and longitude columns from the joined dataset
- Specific columns from the joined dataset to include in output

## Output

The processor generates all columns from the joined dataset. For each row in the current dataset, output rows contain data from the nearest matching row in the joined dataset.

Additionally, a 'join_distance' column is created, indicating the distance to the nearest neighbor in kilometers.
