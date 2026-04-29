---
source_url: https://doc.dataiku.com/dss/latest/other_recipes/distinct.html
fetched_at: 2026-04-29
category: recipes
---

# Distinct: get unique rows

The "distinct" recipe allows you to deduplicate rows in a dataset by retrieving unique rows. The rows are compared using the columns you specify. You can also choose to get the number of duplicates for each combination. It can be performed on any dataset in DSS, whether it's a SQL dataset or not. The recipe offers visual tools to setup the specifications and aliases.

The "distinct" recipe can have pre-filters and post-filters. The filters documentation is available [here](sampling.html).

## See also

For more information, see also the following articles in the Knowledge Base:

* [Concept | Distinct recipe](https://knowledge.dataiku.com/latest/prepare-transform-data/reduce/concept-distinct-recipe.html)

* [Tutorial | Distinct recipe](https://knowledge.dataiku.com/latest/prepare-transform-data/reduce/tutorial-distinct-recipe.html)

## Engines

Depending on the input dataset types, DSS will adjust the engine it uses to execute the recipe, and choose between Hive, Impala, SparkSQL, plain SQL, and internal DSS. The available engines can be seen and selected by clicking on the cog below the "Run" button.
