---
source_url: https://doc.dataiku.com/dss/latest/other_recipes/topn.html
fetched_at: 2026-04-29
category: recipes
---

# Top N: retrieve first N rows

The "top N" recipe allows you to retrieve the first N and the last M rows of subsets with the same grouping keys values. The rows within a subset are ordered by the columns you specify. It can be performed on any dataset in DSS, whether it's a SQL dataset or not. The recipe offers visual tools to setup the specifications and aliases. The "top N" recipe can have pre-filters. The filters documentation is available [here](sampling.html).

See also

For more information, see also the following articles in the Knowledge Base:

*   [Concept | Top N recipe](https://knowledge.dataiku.com/latest/prepare-transform-data/reorder/concept-top-n-recipe.html)

*   [Tutorial | Top N recipe](https://knowledge.dataiku.com/latest/prepare-transform-data/reorder/tutorial-top-n-recipe.html)

## Engines

Depending on the input dataset types, DSS will adjust the engine it uses to execute the recipe, and choose between Hive, Impala, SparkSQL, plain SQL, and internal DSS. The available engines can be seen and selected by clicking on the cog below the "Run" button.

## Notes

*   If no grouping key is provided, the only considered subset will be the whole input dataset.

*   At least one order column is required.

*   When two rows have the same values for both the key and order columns, the order between those two rows is not deterministic and can change over the different builds (different rows may be retrieved for the same input values and recipe settings).

*   The remaining rows output is used to retrieve the rows from the original dataset that does not match the Top N recipe definitions.

*   However, when two rows have the same value according to the key and order columns, some engines may retrieve both rows in the two outputs (because the computations for the outputs are run separately). If one needs to strictly split the input dataset in two, one could use the DSS engine, or a Top N recipe plus a join recipe on the output and the original dataset to retrieve the non-matching rows.

*   Since DSS v4.1, null values are ordered in a specific way, take a look at [Null values handling](sort.html#null-values-handling)
