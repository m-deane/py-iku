---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/extract-numbers.html
fetched_at: 2026-04-29
category: processors
---

# Extract numbers

Extract numerical values from a text column.

## Options

**Extract several values**

By default, the processor extracts several values and outputs each detected number into a separate column, suffixed with the index of the number. Unselect this option to extract only the first found number.

**Extract values into a JSON array**

Output the found number(s) in a single column as a JSON-array.

Note

In SQL mode, the number of output columns must be fixed beforehand. It is therefore extrapolated from the sample.

**Expand 'k' to '1000' and 'm' to '1000000'**

Automatically expand notations like '10K' and '5M'

**Decimal separator**

Use the program's best guess or choose from between comma and dot separators.
