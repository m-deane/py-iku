---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/numerical-format-convert.html
fetched_at: 2026-04-29
category: processors
---

# Convert number formats

Convert numbers from one language/country-specific format to another.

## Options

**Column**

Convert numbers in the following columns:

- A single column
- An explicit list of columns
- All columns matching a regex pattern
- All columns

**Input format**

Number format of input column(s). Decimal numbers are stored in the raw format. Supported formats:

- Raw: 1234567890.123 (required format for numeric columns fed to other DSS mechanisms)
- French: 1 234 567 890,123 (also: Canadian, Danish, Finnish, Swedish)
- English: 1,234,567,890.123 (also: Thai)
- Italian: 1.234.567.890,123 (also: Norwegian, Spanish)
- Swiss: 1'234'567'890.123

**Output format**

Number format of output column(s). See supported formats above.
