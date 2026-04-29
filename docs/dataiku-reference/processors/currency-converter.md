---
source_url: https://doc.dataiku.com/dss/latest/preparation/processors/currency-converter.html
fetched_at: 2026-04-29
category: processors
---

# Convert currencies

This processor converts a column with monetary data from one currency to another.

It supports around 40 currencies with historical data

## Input currency

The processor can either use a constant input currency, or read a different input currency from a dedicated column. This can be used to 'realign' different input currencies to a single output

## Output currency

The processor outputs all output in the same currency

## Reference date

The processor includes historical data for the currencies. You can either set the conversion to a fixed date, or use a Date-typed column to use a different reference date for each row
