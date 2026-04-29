---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/date-formatter.html
fetched_at: 2026-04-29
category: processors
---

# Format date with custom format

Format data in standard ISO-8601 format (`yyyy-MM-ddTHH:mm:ss.SSSZ`) to another custom date format. Use this processor to convert an ISO-8601 date into a string that may be easier to read.

## Options

**Input column**

Column containing data in ISO-8601 format. Use a Prepare step to parse your data into this format if it isn't already.

**Date format**

Specify the custom date format of the output column using the [Java syntax for date specifier](http://docs.oracle.com/javase/7/docs/api/java/text/SimpleDateFormat.html).

> Common patterns include y (year), M (month in year), w (week in year), d (day in month), E (day name in week), a (am/pm marker), H (hour in day 0-24), h (hour in am/pm 1-12), m (minute in hour), s (second in minute), S (millisecond), Z (time zone).

**Locale**

Translate date information in locale format (like 'mercredi' or 'janvier' in French).

**Timezone**

Change the timezone from the UTC default. Options include using a TZ column, an IP column, or specifying a timezone from the dropdown.

**Output column**

Leave blank to format data in place, or create a separate output column.

> If the output format is not ISO-8601, DSS will treat it as an unparsed date.

## Related resources

For more information on managing dates with Dataiku DSS, please see the [reference documentation](https://doc.dataiku.com/dss/latest/preparation/dates.html).
