"""Pydantic v2 schemas mirroring DataikuFlow, DataikuDataset from py-iku."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from .recipe import DataikuRecipeModel

# ---------------------------------------------------------------------------
# DatasetTypeEnum / DatasetConnectionTypeEnum
# ---------------------------------------------------------------------------


class DatasetTypeEnum(StrEnum):
    """Dataset types — mirrors DatasetType enum values."""

    INPUT = "input"
    INTERMEDIATE = "intermediate"
    OUTPUT = "output"


class DatasetConnectionTypeEnum(StrEnum):
    """Dataset connection types — mirrors DatasetConnectionType enum values."""

    FILESYSTEM = "Filesystem"
    SQL_POSTGRESQL = "PostgreSQL"
    SQL_MYSQL = "MySQL"
    SQL_BIGQUERY = "BigQuery"
    SQL_SNOWFLAKE = "Snowflake"
    SQL_REDSHIFT = "Redshift"
    S3 = "S3"
    GCS = "GCS"
    AZURE_BLOB = "Azure"
    HDFS = "HDFS"
    MANAGED_FOLDER = "ManagedFolder"
    MONGODB = "MongoDB"
    ELASTICSEARCH = "Elasticsearch"


# ---------------------------------------------------------------------------
# ColumnSchemaModel — mirrors ColumnSchema.to_dict()
# ---------------------------------------------------------------------------


class ColumnSchemaModel(BaseModel):
    """Mirrors ColumnSchema.to_dict()."""

    name: str
    type: str
    nullable: bool = True
    default: Any = None
    format: str | None = None


# ---------------------------------------------------------------------------
# DataikuDatasetModel — mirrors DataikuDataset.to_dict()
# ---------------------------------------------------------------------------


class DataikuDatasetModel(BaseModel):
    """Mirrors DataikuDataset.to_dict() exactly."""

    name: str
    type: DatasetTypeEnum
    connection_type: DatasetConnectionTypeEnum = DatasetConnectionTypeEnum.FILESYSTEM
    schema_: list[ColumnSchemaModel] = Field(
        default_factory=list, alias="schema", serialization_alias="schema"
    )
    source_variable: str | None = None
    source_line: int | None = None
    notes: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# FlowZoneModel — mirrors FlowZone.to_dict()
# ---------------------------------------------------------------------------


class FlowZoneModel(BaseModel):
    """Mirrors FlowZone.to_dict()."""

    name: str
    color: str = "#4b96e6"
    datasets: list[str] = Field(default_factory=list)
    recipes: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# FlowRecommendationModel — mirrors FlowRecommendation.to_dict()
# ---------------------------------------------------------------------------


class FlowRecommendationModel(BaseModel):
    """Mirrors FlowRecommendation.to_dict()."""

    type: str
    priority: str
    message: str
    impact: str | None = None
    action: str | None = None
    source_lines: list[int] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# DataikuFlowModel — mirrors DataikuFlow.to_dict()
# ---------------------------------------------------------------------------


class DataikuFlowModel(BaseModel):
    """Mirrors DataikuFlow.to_dict() shape exactly.

    Validates that all recipe inputs/outputs reference datasets that exist
    in the datasets list.
    """

    flow_name: str = "converted_flow"
    generated_from: str | None = None
    generation_timestamp: str | None = None
    total_recipes: int = 0
    total_datasets: int = 0
    datasets: list[DataikuDatasetModel] = Field(default_factory=list)
    recipes: list[DataikuRecipeModel] = Field(default_factory=list)
    optimization_notes: list[str] = Field(default_factory=list)
    recommendations: list[FlowRecommendationModel] = Field(default_factory=list)
    zones: list[FlowZoneModel] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_dataset_references(self) -> "DataikuFlowModel":  # noqa: UP037
        """Reject flows whose recipes reference dataset names not in datasets list."""
        known = {ds.name for ds in self.datasets}
        for recipe in self.recipes:
            for ref in list(recipe.inputs) + list(recipe.outputs):
                if ref not in known:
                    raise ValueError(
                        f"Recipe '{recipe.name}' references unknown dataset '{ref}'. "
                        f"Known datasets: {sorted(known)}"
                    )
        return self
