# Appendix A — Glossary

## Scope

This glossary covers DSS terminology and py-iku-specific terms used throughout the book. Each entry is one or two sentences. Where the term has a py-iku-specific meaning that differs from common usage, both are noted. Entries are alphabetical and anchored, so chapters can link to a single term as `appendix-a-glossary.md#term-slug`.

### Aggregation

A reduction over a set of rows producing one row per group. In DSS, aggregations are the body of a `GROUPING` recipe (sum, mean, count, min, max, first, last, and a handful of statistical reductions); see [Dataiku docs: Group recipe](https://doc.dataiku.com/dss/latest/other_recipes/group.html). Chapter 6 covers the pandas-to-`GROUPING` mapping.

### Connection

A DSS-level credential and address pair pointing at a data store (filesystem, S3, Snowflake, BigQuery, and so on). Datasets are bound to connections; recipes inherit the engine implied by their input dataset's connection. py-iku does not configure connections — they are a DSS administration concern — but it does record a `connection_type` on `DataikuDataset`.

### Dataset

A named, schema-bound collection of records that DSS treats as the unit of input and output for recipes. In py-iku, a dataset is represented by `DataikuDataset` and has a `name`, a `dataset_type`, and a `connection_type`. Datasets in the produced flow are not data — they are references to data that DSS will materialize when the flow runs.

### DSS

Dataiku DSS (Data Science Studio), the platform py-iku targets. py-iku targets DSS 14, with the recipe and processor catalogs that version exposes (see [Dataiku docs](https://doc.dataiku.com/dss/latest/)).

### FlowZone

A DSS-level grouping of related flow nodes used to keep large flows visually navigable. py-iku does not assign zones automatically; flow visualizers may color zones if the input flow has them set, but the rule-based and LLM analyzers leave the zone field unset by default.

### GREL

The expression language used inside DSS prepare-recipe formula processors and a handful of other places. py-iku emits GREL strings inside `FORMULA` processor steps when an element-wise pandas expression cannot be represented by a stock processor; Chapter 9 walks through the generation. See [Dataiku docs: Formula language](https://doc.dataiku.com/dss/latest/formula/index.html).

### JOIN

A binary recipe that combines two input datasets on one or more key columns. py-iku produces a `JOIN` recipe from `df.merge(...)` and from `pd.merge(...)`. The join type (inner, left, right, outer) is preserved in `JoinSettings.join_type`. Chapter 6 covers the worked example.

### JSON Schema

The structured-output schema the LLM analyzer hands to the provider so the response is parseable. In Anthropic's API this is the `tool_use` schema; in OpenAI's it is `response_format=json_schema`. The schema is what makes temperature=0 conversion deterministic in practice — the model is constrained to a known shape, so parser failures collapse to a small set of recoverable errors. Chapter 7 covers the contract.

### Lineage

The dependency record that maps each output column back through the recipes and datasets that produced it. DSS computes column-level lineage from the flow configuration. py-iku's job is to produce a flow whose lineage corresponds to the data dependencies in the original pandas script.

### Mapping rule

A `pandas method name → (RecipeType or ProcessorType)` entry in `mappings/pandas_mappings.py`. The library's translation from pandas to DSS is largely a lookup against this table, plus a handful of structural decisions for cases the table cannot resolve alone (filters, conditional logic). Plugin authors register their own mapping rules via `register_pandas_mapping`; Chapter 12 covers the extension surface.

### Optimizer

The post-generation pass implemented in `BaseFlowGenerator._optimize_flow` that simplifies the produced flow without changing its semantics. The dominant optimization is PREPARE merging: adjacent PREPARE recipes on a linear path collapse into a single PREPARE with the union of their steps. The optimizer is fan-out aware and refuses to merge across branch points. Chapter 10 covers the rules.

### Partition

A DSS-level slice of a dataset addressed by a partition key (a date, a country, a tenant). py-iku records partition information on `DataikuDataset.partitioning` when the source code makes it inferrable, but it does not introduce partitioning where the source did not have it.

### PrepareStep

A single step inside a PREPARE recipe. Each step has a `processor_type` and a settings payload typed for that processor. py-iku represents this as `PrepareStep`. The order of `PrepareStep` instances in `recipe.steps` is significant — step N sees the schema produced by step N−1.

### Processor

A unit of element-wise transformation that runs inside a PREPARE recipe, as opposed to a recipe, which is a top-level flow node. DSS 14 defines 122 processor types; py-iku exposes them through the `ProcessorType` enum. The recipe-vs-processor distinction is the central translation choice the library makes; Chapter 3 explains it.

### Recipe

A top-level node in a DSS flow that consumes one or more input datasets and produces one or more output datasets. py-iku represents recipes as `DataikuRecipe`, with a `RecipeType` and a `RecipeSettings` subclass payload typed for that recipe type. DSS 14 supports 37 recipe types; py-iku covers the ones that have a clean pandas analogue.

### RecipeType

The enum in `models/dataiku_recipe.py` whose values are the names of recipe categories that DSS supports. The values used most often in the book are `PREPARE`, `GROUPING`, `JOIN`, `SORT`, `TOP_N`, `WINDOW`, `SPLIT`, `STACK`, `DISTINCT`, `FILTER`, `SAMPLING`, and `PYTHON`. The enum is the canonical authority — chapters always use enum values, never raw strings.

### ProcessorType

The enum in `models/prepare_step.py` whose values are the 122 processor categories that DSS 14 supports. High-frequency entries are `COLUMN_RENAMER`, `COLUMN_REMOVER`, `FILL_EMPTY_WITH_VALUE`, `FILTER_ON_VALUE`, `FILTER_ON_NUMERICAL_RANGE`, `NUMERIC_TRANSFORM`, `STRING_TRANSFORMER`, `FORMULA`, and `FOLD_MULTIPLE_COLUMNS`.

### Sampling

A DSS recipe type that produces a sub-sampled output dataset from a larger input. The sampling method (head, tail, random, stratified) is recorded in `SamplingSettings`. The pandas trigger is `df.sample(...)` or `df.head(...)`. py-iku emits a `SAMPLING` recipe rather than a `TOP_N` for `df.sample`.

### Schema

The ordered list of (column name, column type) pairs attached to a dataset. DSS treats schema as part of the dataset contract; py-iku records schemas where the source code allows them to be inferred (typed reads, type casts) and otherwise leaves them blank for DSS to infer at execution time.

### Settings

The configuration payload attached to a recipe or a prepare step. `RecipeSettings` is an abstract base class with twelve typed subclasses (`PrepareSettings`, `GroupingSettings`, `JoinSettings`, `SortSettings`, and so on). `PrepareStepSettings` is the analogous concept for processors. Settings objects are pydantic-style dataclasses; chapters serialize and deserialize them via `to_dict`/`from_dict`.

### Sort

A unary recipe that produces an output dataset with rows ordered by one or more columns. py-iku produces a `SORT` recipe from `df.sort_values(...)`. Stability and null ordering are preserved in `SortSettings`. Chapter 6 covers the worked example.

### Split

A unary recipe with multiple output datasets, produced when complementary filter predicates are detected on the same source dataframe. py-iku's complementary-filter detection turns `high = df[df["x"] > 10]; low = df[df["x"] <= 10]` into a single `SPLIT` recipe rather than two `FILTER` recipes. Chapter 9 covers the detection logic.

### Stack

A recipe that vertically concatenates two or more input datasets that share a schema. The pandas trigger is `pd.concat([...])`. py-iku produces a `STACK` recipe with the input datasets listed in their concat order.

### Topological order

The linearization of a DAG such that every edge runs from an earlier node to a later one. `flow.graph.topological_sort()` returns the recipes of a flow in a valid topological order. CI assertions on the produced flow use topological order rather than `flow.recipes` directly because the library does not contract a stable insertion order.

### Transformation

The library-internal record of one logical operation extracted from the pandas source. The rule-based analyzer emits a list of `Transformation` objects; the flow generator turns each into either a recipe or a processor step. Plugin authors who write custom recipe handlers receive a `Transformation` and return a `DataikuRecipe`; Chapter 12 covers the contract.

### WINDOW

A recipe type for partitioned, ordered, framed computations. py-iku produces a `WINDOW` recipe from `df.rolling(...)`, `df.expanding(...)`, and `df.cumsum()`. The window frame (rows or range, leading and trailing offsets, partition columns, ordering columns) is captured in `WindowSettings`. Chapter 6 covers the worked example.
