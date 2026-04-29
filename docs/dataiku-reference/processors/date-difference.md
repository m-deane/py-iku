---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/date-difference.html
fetched_at: 2026-04-29
category: processors
---

# Compute difference between dates

Compute the difference between an ISO-8601 formatted date column (`yyyy-MM-ddTHH:mm:ss.SSSZ`) and another time reference: the current time, a fixed date, or another column.

The difference can be expressed in various **output time units**: years, months, weeks, days, hours, minutes or seconds.

If the output unit is set to **Days**, you can choose to exclude weekends and bank holidays from the computation, based on a selected country's calendar.

## Supported Countries

| Country | Default timezone | Weekend days |
|---------|------------------|--------------|
| AE | Asia/Dubai | Saturday, Sunday |
| DE | Europe/Berlin | Saturday, Sunday |
| ES | Europe/Madrid | Saturday, Sunday |
| FR | Europe/Paris | Saturday, Sunday |
| IN | Asia/Kolkata | Saturday, Sunday |
| OM | Asia/Dubai | Friday, Saturday |
| SA | Asia/Riyadh | Friday, Saturday |
| US | America/New_York | Saturday, Sunday |

## Options

**Time since column**

Column containing data in ISO-8601 format. Use a Prepare step to parse your data into this format if it isn't already.

**Until**

Choose the second time reference to compute the difference - now, another date column, or a fixed date.

**Output time unit**

Determine the unit of time in which to express the datetime difference - year, month, week, day, hour, minute or second.

**Output column**

Column into which the datetime difference will be written.

**Reverse output**

Multiply the computed difference by -1, reversing it: `3 days` -> `-3 days`.

**Exclude weekends**

Exclude weekend days based on the selected calendar. Only available when the **Output time unit** is set to **Days**.

**Exclude bank holidays**

Exclude bank holiday days. Only available when the **Output time unit** is set to **Days**. Only for the whole country, not for specific regions.

**Country code**

Choose the country for which to consider holidays and weekends. Only available if **Exclude weekends** or **Exclude bank holidays** is selected.

**Country's timezone**

Holidays are defined by a year, month and day. However, a date in DSS corresponds to a precise point in time. To determine if a date falls on a holiday, it is necessary to know the timezone in which to consider the date.

By default, the country's standard timezone is used, but you can specify another one. Only available if **Exclude weekends** or **Exclude bank holidays** is selected.
