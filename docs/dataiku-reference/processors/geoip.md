---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/geoip.html
fetched_at: 2026-04-29
category: processors
---

# Resolve GeoIP

Extract geographic information from an IP address, including:

* **Country name**

* **Country code:** 2, 3 letters

* **Region:** Generate three new columns

  * **Region code.** Depending on country, this can be a state code, a region code, a department identifier, ...

  * **Region name.** Depending on country, this can be a state name, a region name, a department name, ...

  * **Region hierarchy.** When available, this is a comma-separated hierarchical list of region names, from most general to most specific

* **City name**

* **Postal code**

* **Latitude and longitude**

* **GeoPoint**

* **Timezone identifier**

* **Continent name**

> Warning
>
> "The precision of the GeoLite City database varies widely upon on the visitor's ISP."
