---
source_url: https://doc.dataiku.com/dss/latest/other_recipes/window.html
fetched_at: 2026-04-29
category: recipes
---

# Window: analytics functions

The "window" recipe allows you to perform analytics functions on any dataset in DSS, whether it's a SQL dataset or not. This is the equivalent of a SQL "over" statement. The recipe offers visual tools to setup the windows and aliases. The "window" recipe can have pre-filters and post-filters.

## Engines

Depending on the input dataset types, DSS will adjust the engine it uses to execute the recipe, and choose between Hive, Impala, SparkSQL, plain SQL, and internal DSS. The available engines can be seen and selected by clicking on the cog below the "Run" button.

**Note:** The DSS engine has different default window behavior than when using a SQL engine. When using the **DSS engine**, the window will default to the _whole_ frame if no window is specified. As a result, you can see different window behavior when switching between the DSS engine and a SQL engine. In order to see the same result when using the DSS Engine as you would with the SQL engine, you can enable the Window Frame option with both the "Limit preceding rows" and "Limit following rows" options unchecked.

## Notes

- Since DSS v4.1, null values are ordered in a specific way, per the sort documentation's null values handling section.
