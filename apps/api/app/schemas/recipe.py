"""Pydantic v2 schemas mirroring DataikuRecipe and RecipeSettings from py-iku."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field

from .processor import PrepareStepModel

# ---------------------------------------------------------------------------
# RecipeTypeEnum — generated from py2dataiku.models.dataiku_recipe.RecipeType
# All 37 members; values match RecipeType.value.
# ---------------------------------------------------------------------------


class RecipeTypeEnum(StrEnum):
    """All 37 Dataiku DSS recipe types."""

    # Visual recipes — Data Preparation
    PREPARE = "prepare"
    SYNC = "sync"
    GROUPING = "grouping"
    WINDOW = "window"
    JOIN = "join"
    FUZZY_JOIN = "fuzzyjoin"
    GEO_JOIN = "geojoin"
    STACK = "stack"
    SPLIT = "split"
    SORT = "sort"
    DISTINCT = "distinct"
    TOP_N = "topn"
    PIVOT = "pivot"
    SAMPLING = "sampling"
    DOWNLOAD = "download"

    # Visual recipes — Additional
    GENERATE_FEATURES = "generate_features"
    GENERATE_STATISTICS = "generate_statistics"
    PUSH_TO_EDITABLE = "push_to_editable"
    LIST_FOLDER_CONTENTS = "list_folder_contents"
    DYNAMIC_REPEAT = "dynamic_repeat"
    EXTRACT_FAILED_ROWS = "extract_failed_rows"
    UPSERT = "upsert"
    LIST_ACCESS = "list_access"

    # Code recipes — Python/R
    PYTHON = "python"
    R = "r"

    # Code recipes — SQL variants
    SQL = "sql_script"
    HIVE = "hive"
    IMPALA = "impala"
    SPARKSQL = "spark_sql_query"

    # Code recipes — Spark variants
    PYSPARK = "pyspark"
    SPARK_SCALA = "spark_scala"
    SPARKR = "sparkr"

    # Code recipes — Other
    SHELL = "shell"

    # ML recipes
    PREDICTION_SCORING = "prediction_scoring"
    CLUSTERING_SCORING = "clustering_scoring"
    EVALUATION = "standalone_evaluation"

    # AI-assisted
    AI_ASSISTANT_GENERATE = "ai_assistant_generate"


# ---------------------------------------------------------------------------
# RecipeSettings discriminated union — 12 subclasses.
# Each subclass mirrors the corresponding RecipeSettings.to_display_dict() output
# plus a `kind` literal used as the discriminator.
# ---------------------------------------------------------------------------


class PrepareSettingsModel(BaseModel):
    """Mirrors PrepareSettings.to_display_dict(): steps + step_count."""

    kind: Literal["prepare"] = "prepare"
    steps: list[PrepareStepModel] = Field(default_factory=list)
    step_count: int = Field(default=0)


class GroupingSettingsModel(BaseModel):
    """Mirrors GroupingSettings.to_display_dict(): keys + aggregations."""

    kind: Literal["grouping"] = "grouping"
    keys: list[str] = Field(default_factory=list)
    aggregations: list[dict[str, Any]] = Field(default_factory=list)


class JoinSettingsModel(BaseModel):
    """Mirrors JoinSettings.to_display_dict(): join_type, join_keys, selected_columns."""

    kind: Literal["join"] = "join"
    join_type: str = Field(default="LEFT")
    join_keys: list[dict[str, Any]] = Field(default_factory=list)
    selected_columns: dict[str, list[str]] | None = None


class WindowSettingsModel(BaseModel):
    """Mirrors WindowSettings.to_dict(): partitionColumns, orderColumns, aggregations."""

    kind: Literal["window"] = "window"
    partitionColumns: list[dict[str, str]] = Field(default_factory=list)
    orderColumns: list[dict[str, str]] = Field(default_factory=list)
    aggregations: list[dict[str, Any]] = Field(default_factory=list)


class SamplingSettingsModel(BaseModel):
    """Mirrors SamplingSettings.to_dict(): samplingMethod + sampleSize."""

    kind: Literal["sampling"] = "sampling"
    samplingMethod: str = Field(default="RANDOM_FIXED_NB")
    sampleSize: int | None = None


class SplitSettingsModel(BaseModel):
    """Mirrors SplitSettings.to_dict(): splitMode + condition."""

    kind: Literal["split"] = "split"
    splitMode: str = Field(default="FILTER")
    condition: str = Field(default="")


class SortSettingsModel(BaseModel):
    """Mirrors SortSettings.to_dict(): sortColumns."""

    kind: Literal["sort"] = "sort"
    sortColumns: list[dict[str, str]] = Field(default_factory=list)


class TopNSettingsModel(BaseModel):
    """Mirrors TopNSettings.to_dict(): topN + rankingColumn."""

    kind: Literal["topn"] = "topn"
    topN: int = Field(default=10)
    rankingColumn: str | None = None


class DistinctSettingsModel(BaseModel):
    """Mirrors DistinctSettings.to_dict(): computeCount."""

    kind: Literal["distinct"] = "distinct"
    computeCount: bool = False


class StackSettingsModel(BaseModel):
    """Mirrors StackSettings.to_dict(): mode."""

    kind: Literal["stack"] = "stack"
    mode: str = Field(default="UNION")


class PythonSettingsModel(BaseModel):
    """Mirrors PythonSettings.to_dict(): code."""

    kind: Literal["python"] = "python"
    code: str = Field(default="")


class PivotSettingsModel(BaseModel):
    """Mirrors PivotSettings.to_dict(): rowColumns, columnColumn, valueColumn, aggregation."""

    kind: Literal["pivot"] = "pivot"
    rowColumns: list[str] = Field(default_factory=list)
    columnColumn: str = Field(default="")
    valueColumn: str = Field(default="")
    aggregation: str = Field(default="SUM")


RecipeSettingsModel = Annotated[
    PrepareSettingsModel
    | GroupingSettingsModel
    | JoinSettingsModel
    | WindowSettingsModel
    | SamplingSettingsModel
    | SplitSettingsModel
    | SortSettingsModel
    | TopNSettingsModel
    | DistinctSettingsModel
    | StackSettingsModel
    | PythonSettingsModel
    | PivotSettingsModel,
    Field(discriminator="kind"),
]

# ---------------------------------------------------------------------------
# DataikuRecipeModel — mirrors DataikuRecipe.to_dict()
# ---------------------------------------------------------------------------


class DataikuRecipeModel(BaseModel):
    """Mirrors DataikuRecipe.to_dict() shape.

    py-iku's to_dict() inlines recipe-type-specific settings via to_display_dict()
    rather than nesting them under a 'settings' key. Those fields pass through via
    `extra="allow"`.

    The `settings` field is declared here as Optional so all 12 RecipeSettings
    subclass schemas are registered in the OpenAPI component registry. In practice
    it will be None for flows produced by py-iku's to_dict(), but callers that
    construct recipes directly may populate it.
    """

    name: str
    type: RecipeTypeEnum
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    source_lines: list[int] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    # Optional composed settings — exposes all 12 subclasses in /openapi.json.
    # py-iku to_dict() inlines these fields instead of nesting them, so this
    # will be None for round-tripped flows.
    settings: RecipeSettingsModel | None = Field(
        default=None,
        description=(
            "Composed recipe settings (discriminated union over 12 subclasses). "
            "Not populated by py-iku to_dict(); present here to expose the full "
            "settings schema contract in /openapi.json."
        ),
    )

    # Recipe-type-specific fields emitted by to_dict() / to_display_dict()
    # (steps, keys, aggregations, join_type, …) pass through via extra.
    model_config = {"extra": "allow"}
