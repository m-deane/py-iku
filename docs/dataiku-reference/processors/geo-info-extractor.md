---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/geo-info-extractor.html
fetched_at: 2026-04-29
category: processors
---

# Extract from geo column

This processor extracts data from a geometry column.

## Extracts

- Centroid point
- Length (if input is not a point)
- Area (if input is a polygon)

## Warning

"Length and area are expressed in the unit of the CRS, so often in degrees instead of meters."
