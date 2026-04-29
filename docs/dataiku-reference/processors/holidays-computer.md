---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/holidays-computer.html
fetched_at: 2026-04-29
category: processors
---

# Flag holidays

This processor identifies whether a date is a school holiday, a bank holiday or a weekend.

It takes as input a Date column.

It's worth noting that a Date in DSS corresponds to a point in time, just like a timestamp. Conversely, a holiday is always defined by a timezone-less tuple (year,month,day). Consequently, a timezone must be provided in order to convert this timezone-less representation into a Date.

Although the timezone can be specified explicitly, it may be more convenient to use the country's default timezone.

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

**Input column**

The column containing the date to check.

**Output column prefix**

The prefix to add to output column names.

**Country code**

Choose the country for which to consider holidays and weekends.

**Country's timezone**

Choose the timezone in which to consider the date, it can be UTC or simply the country's default timezone.

**Flag bank holidays**

Computes a boolean column that indicates if the date is a bank holiday. Appends `bank` to the **output column prefix**.

**Flag school holidays (FR only)**

Computes a boolean column that indicates if the date is a school holiday. Appends `school` to the **output column prefix**.

**Flag weekends**

Computes a boolean column that indicates if the date falls on a weekend. Appends `weekend` to the **output column prefix**.

**Extract reasons**

Extracts the holiday name (e.g. "Christmas", "New Year's Day") into an array column. This option creates columns only if **Flag bank holidays** or **Flag school holidays** is selected:

- If **Flag bank holidays** is selected, it appends `bank_reasons` to the **output column prefix** for the newly created column.
- If **Flag school holidays** is selected, it appends `school_reasons` to the **output column prefix** for the newly created column.

**Extract zones (FR only)**

Extracts the holiday zone (e.g. `"A"`, `"B"`) into an array column. Appends `zones` to the **output column prefix** for the newly created column. Only available if **Flag school holidays** is selected.
