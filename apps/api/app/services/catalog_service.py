"""Catalog service — lists recipes and processors from py-iku."""

from __future__ import annotations

from py2dataiku.mappings.processor_catalog import ProcessorCatalog
from py2dataiku.models.dataiku_recipe import RecipeType
from py2dataiku.visualizers.icons import RecipeIcons

from ..schemas.catalog import ProcessorCatalogEntry, RecipeCatalogEntry
from ..schemas.processor import ProcessorTypeEnum
from ..schemas.recipe import RecipeTypeEnum

# ---------------------------------------------------------------------------
# Static metadata for recipe catalog entries.
# Source: py-iku CLAUDE.md recipe type documentation + DSS 14 recipe reference.
# ---------------------------------------------------------------------------

_RECIPE_META: dict[str, dict[str, str | list[str]]] = {
    "prepare": {
        "category": "Visual",
        "description": "Apply a sequence of transformation steps (processors) to a dataset.",
        "pandas_examples": ["df.str.strip()", "df.fillna()", "df.astype()", "df.rename()"],
    },
    "sync": {
        "category": "Visual",
        "description": "Copy data from one dataset to another, optionally across connections.",
        "pandas_examples": ["df.copy()"],
    },
    "grouping": {
        "category": "Visual",
        "description": "Aggregate rows by grouping keys and apply aggregation functions.",
        "pandas_examples": ["df.groupby().agg()", "df.groupby().sum()", "df.groupby().mean()"],
    },
    "window": {
        "category": "Visual",
        "description": "Compute window/rolling functions over partitioned, ordered data.",
        "pandas_examples": ["df.rolling()", "df.cumsum()", "df.expanding()", "df.shift()"],
    },
    "join": {
        "category": "Visual",
        "description": "Join two datasets on one or more key columns.",
        "pandas_examples": ["df.merge()", "pd.merge()"],
    },
    "fuzzyjoin": {
        "category": "Visual",
        "description": "Join datasets using approximate/fuzzy string matching.",
        "pandas_examples": [],
    },
    "geojoin": {
        "category": "Visual",
        "description": "Join datasets using geographic spatial conditions.",
        "pandas_examples": [],
    },
    "stack": {
        "category": "Visual",
        "description": "Vertically stack (union) two or more datasets.",
        "pandas_examples": ["pd.concat(axis=0)", "pd.concat([df1, df2])"],
    },
    "split": {
        "category": "Visual",
        "description": "Split a dataset into multiple outputs based on conditions.",
        "pandas_examples": ["df[condition]", "df.query()"],
    },
    "sort": {
        "category": "Visual",
        "description": "Sort dataset rows by one or more columns.",
        "pandas_examples": ["df.sort_values()", "df.sort_index()"],
    },
    "distinct": {
        "category": "Visual",
        "description": "Remove duplicate rows, optionally keeping a count column.",
        "pandas_examples": ["df.drop_duplicates()"],
    },
    "topn": {
        "category": "Visual",
        "description": "Keep the top N rows ranked by a column.",
        "pandas_examples": ["df.nlargest()", "df.nsmallest()"],
    },
    "pivot": {
        "category": "Visual",
        "description": "Pivot rows into columns using an aggregation function.",
        "pandas_examples": ["df.pivot_table()", "df.pivot()"],
    },
    "sampling": {
        "category": "Visual",
        "description": "Sample rows using random, stratified, or head/tail methods.",
        "pandas_examples": ["df.sample()", "df.head()", "df.tail()"],
    },
    "download": {
        "category": "Visual",
        "description": "Download data from an external URL into a managed dataset.",
        "pandas_examples": [],
    },
    "generate_features": {
        "category": "Visual",
        "description": "Auto-generate features from existing columns.",
        "pandas_examples": [],
    },
    "generate_statistics": {
        "category": "Visual",
        "description": "Compute summary statistics for a dataset.",
        "pandas_examples": ["df.describe()", "df.info()"],
    },
    "push_to_editable": {
        "category": "Visual",
        "description": "Push a dataset to an editable (user-writable) dataset.",
        "pandas_examples": [],
    },
    "list_folder_contents": {
        "category": "Visual",
        "description": "List files in a managed folder.",
        "pandas_examples": [],
    },
    "dynamic_repeat": {
        "category": "Visual",
        "description": "Dynamically repeat a sub-flow for each input row.",
        "pandas_examples": [],
    },
    "extract_failed_rows": {
        "category": "Visual",
        "description": "Extract rows that failed validation checks.",
        "pandas_examples": [],
    },
    "upsert": {
        "category": "Visual",
        "description": "Upsert (insert or update) rows into a target dataset.",
        "pandas_examples": [],
    },
    "list_access": {
        "category": "Visual",
        "description": "List access permissions on a dataset.",
        "pandas_examples": [],
    },
    "python": {
        "category": "Code",
        "description": "Run a custom Python script on input datasets.",
        "pandas_examples": [],
    },
    "r": {
        "category": "Code",
        "description": "Run a custom R script on input datasets.",
        "pandas_examples": [],
    },
    "sql_script": {
        "category": "Code",
        "description": "Run a SQL script against connected databases.",
        "pandas_examples": [],
    },
    "hive": {
        "category": "Code",
        "description": "Run a Hive HQL query on a Hadoop cluster.",
        "pandas_examples": [],
    },
    "impala": {
        "category": "Code",
        "description": "Run an Impala SQL query.",
        "pandas_examples": [],
    },
    "spark_sql_query": {
        "category": "Code",
        "description": "Run a Spark SQL query.",
        "pandas_examples": [],
    },
    "pyspark": {
        "category": "Code",
        "description": "Run a PySpark Python script.",
        "pandas_examples": [],
    },
    "spark_scala": {
        "category": "Code",
        "description": "Run a Spark Scala script.",
        "pandas_examples": [],
    },
    "sparkr": {
        "category": "Code",
        "description": "Run a SparkR script.",
        "pandas_examples": [],
    },
    "shell": {
        "category": "Code",
        "description": "Run a shell command or script.",
        "pandas_examples": [],
    },
    "prediction_scoring": {
        "category": "ML",
        "description": "Score a dataset using a saved ML prediction model.",
        "pandas_examples": ["model.predict()"],
    },
    "clustering_scoring": {
        "category": "ML",
        "description": "Assign cluster labels using a saved clustering model.",
        "pandas_examples": ["model.predict()"],
    },
    "standalone_evaluation": {
        "category": "ML",
        "description": "Evaluate a saved model on a labeled test dataset.",
        "pandas_examples": [],
    },
    "ai_assistant_generate": {
        "category": "AI",
        "description": "Generate data or transformations using an AI assistant.",
        "pandas_examples": [],
    },
}


def list_recipes() -> list[RecipeCatalogEntry]:
    """Return a catalog entry for each of the 37 RecipeType values."""
    entries: list[RecipeCatalogEntry] = []
    for rt in RecipeType:
        value = rt.value
        meta = _RECIPE_META.get(value, {})
        icon = RecipeIcons.get_unicode(value)
        entries.append(
            RecipeCatalogEntry(
                type=RecipeTypeEnum(value),
                name=RecipeIcons.get_label(value),
                category=str(meta.get("category", "Visual")),
                icon=icon,
                description=str(meta.get("description", "")),
                pandas_examples=list(meta.get("pandas_examples", [])),  # type: ignore[arg-type]
            )
        )
    return entries


def list_processors(
    q: str | None = None,
    category: str | None = None,
) -> list[ProcessorCatalogEntry]:
    """List processors from ProcessorCatalog, optionally filtered by name/category."""
    catalog = ProcessorCatalog()
    all_keys = catalog.list_processors()
    entries: list[ProcessorCatalogEntry] = []
    for key in all_keys:
        info = catalog.get_processor(key)
        if info is None:
            continue
        if category and info.category.lower() != category.lower():
            continue
        if q and q.lower() not in info.name.lower() and q.lower() not in info.description.lower():
            continue
        # Resolve ProcessorTypeEnum by value (info.name is the DSS value string)
        try:
            ptype: ProcessorTypeEnum | str = ProcessorTypeEnum(info.name)
        except ValueError:
            ptype = info.name  # fallback for catalog-only keys

        entries.append(
            ProcessorCatalogEntry(
                type=ptype,
                name=info.name,
                category=info.category,
                description=info.description,
                required_params=info.required_params,
                optional_params=info.optional_params,
                examples=info.example_params,
            )
        )
    return entries


def get_processor(processor_type: str) -> ProcessorCatalogEntry:
    """Return a single processor catalog entry by type string.

    Raises KeyError if the processor is not in the catalog (caller converts to 404).
    """
    catalog = ProcessorCatalog()
    info = catalog.get_processor(processor_type)
    if info is None:
        raise KeyError(f"Processor type '{processor_type}' not found in catalog")
    try:
        ptype: ProcessorTypeEnum | str = ProcessorTypeEnum(info.name)
    except ValueError:
        ptype = info.name

    return ProcessorCatalogEntry(
        type=ptype,
        name=info.name,
        category=info.category,
        description=info.description,
        required_params=info.required_params,
        optional_params=info.optional_params,
        examples=info.example_params,
    )
