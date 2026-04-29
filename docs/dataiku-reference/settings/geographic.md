---
source_url: https://doc.dataiku.com/dss/latest/preparation/geographic.html
fetched_at: 2026-04-29
category: settings
---

# Geographic processors

The prepare recipe provides a variety of processors to work with geographic information.

For an overview of all geographic capabilities in DSS, please see [Geographic data](../geographic/index.html)

DSS also provides a set of formulas to compute geographic operations (see [Formula language](../formula/index.html))

## Geopoint converters

DSS provides two processors to convert between a Geopoint column and latitude/longitude columns:

* [Create GeoPoint from lat/lon](processors/geopoint-create.html)
* [Extract lat/lon from GeoPoint](processors/geopoint-extract.html)

## Resolve GeoIP

The [Resolve GeoIP](processors/geoip.html) processor uses the GeoLite City database (https://www.maxmind.com) to resolve an IP address to the associated geographic coordinates.

It produces two kinds of information:

* Administrative data (country, region, city, ...)
* Geographic data (latitude, longitude)

The output GeoPoint can be used for [Map Charts](../visualization/charts-maps.html).

## Reverse geocoding

Please see [Geocoding and reverse geocoding](../geographic/geocoding.html)

## Zipcode geocoding

Please see [Geocoding and reverse geocoding](../geographic/geocoding.html)

## Change coordinates system

This processor changes the Coordinates Reference System (CRS) of a geometry or geopoint column.

Source and target CRS can be given either as an EPSG code (e.g., "EPSG:4326") or as a projected coordinate system WKT (e.g., "PROJCS[...]").

Use this processor to convert data projected in a different CRS to the WGS84 (EPSG:4326) coordinates system.

## Compute distances between geospatial objects

The [Compute distance between geospatial objects](processors/geo-distance.html) processor allows you to compute distance between geospatial objects

## Create area around a geopoint

The [Create area around a geopoint](processors/geopoint-buffer.html) processor performs creation of polygons centered on input geopoints. For each input geospatial point, a spatial polygon is created around it, delimiting the area of influence covered by the point (all the points that fall within a given distance from the geopoint). The shape area of the polygon can be either rectangular or circular (using an approximation) and the size will depend on the selected parameters.

## Extract from geo column

The [Extract from geo column](processors/geo-info-extractor.html) processor extracts data from a geometry column:

* centroid point,
* length (if input is not a point),
* area (if input is a polygon).
