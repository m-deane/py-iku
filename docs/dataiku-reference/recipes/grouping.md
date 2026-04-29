---
source_url: https://doc.dataiku.com/dss/latest/other_recipes/grouping.html
fetched_at: 2026-04-29
category: recipes
---

# Grouping: aggregating data

The "grouping" recipe allows you to perform aggregations on any dataset in DSS, whether it's a SQL dataset or not. This is the equivalent of a SQL "group by" statement. The recipe offers visual tools to setup the (custom) aggregations and aliases.

The "grouping" recipe can have pre-filters and post-filters. The filters documentation is available [here](sampling.html).

## See also

For more information, see also the following articles in the Knowledge Base:

* [Concept | Group recipe](https://knowledge.dataiku.com/latest/prepare-transform-data/aggregate/concept-group-recipe.html)
* [Tutorial | Group recipe](https://knowledge.dataiku.com/latest/prepare-transform-data/aggregate/tutorial-group-data.html)

## Engines

Depending on the input dataset types, DSS will adjust the engine it uses to execute the recipe, and choose between Hive, Impala, SparkSQL, plain SQL, and internal DSS. The available engines can be seen and selected by clicking on the cog below the "Run" button.
