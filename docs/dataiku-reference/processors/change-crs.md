---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/change-crs.html
fetched_at: 2026-04-29
category: processors
---

# Change coordinates system

This processor changes the Coordinates Reference System (CRS) of a geometry or geopoint column.

Source and target CRS can be given either as an EPSG code (e.g., "EPSG:4326") or as a projected coordinate system WKT (e.g., "PROJCS[...]").

## Warning

Dataiku uses the WGS84 (EPSG:4326) coordinates system when processing geometries. Before manipulating any geospatial data in Dataiku, make sure they are projected in the WGS84 (EPSG:4326) coordinates system.

Use this processor to convert data projected in a different CRS to the WGS84 (EPSG:4326) coordinates system.
