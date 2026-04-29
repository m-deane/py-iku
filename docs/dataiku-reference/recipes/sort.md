---
source_url: https://doc.dataiku.com/dss/latest/other_recipes/sort.html
fetched_at: 2026-04-29
category: recipes
---

# Sort: order values

The "sort" recipe allows you to order a dataset by specifying a list of columns, each with ascending or descending order. It can be performed on any dataset in DSS, whether it's a SQL dataset or not. However, for the recipe to be useful, the output dataset must preserve the writing order. The most common ones are Filesystem and HDFS; you can check it in the settings tab of the dataset if the option is available. When creating a new Sort recipe, the output dataset will be configured to preserve the order in writing if possible. The recipe also offers visual tools to setup the specifications and aliases. The "sort" recipe can have pre-filters.

## Engines

Depending on the input dataset types, DSS will adjust the engine it uses to execute the recipe, and choose between Hive, Impala, SparkSQL, plain SQL, and internal DSS. The available engines can be seen and selected by clicking on the cogwheel below the "Run" button.

## Null values handling

Since DSS version 4.1 and if the database engine allows it, the null values are sorted in a specific order. In the ascending order, the null values will be placed at the beginning and in descending order, the null values will be placed at the end. The main goal is to group together null values and empty strings as DSS consider both the same. Thus using most of the recent database engines or DSS engine provide the same outputs. However some database engines such as Vertica, Sybase IQ, and DB2 cannot explicitly order null values and using these engines may result in different outputs.

## Write ordering

When the output dataset of the recipe preserves writing order, the recipe makes sense. In contrary, the Sort recipe is probably useless and the rows of the output dataset will lose their ordering. In this case, you may want to use a different processing:

* if your input and output datasets has the same connection, remove the Sort recipe and edit the read-order settings of the output dataset

* if your input and output datasets has different connections, replace the Sort recipe by a Sync recipe and edit the read-order settings of the output dataset
