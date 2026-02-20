"""Dataset model for Dataiku DSS."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class DatasetType(Enum):
    """Type of dataset in the flow."""

    INPUT = "input"
    INTERMEDIATE = "intermediate"
    OUTPUT = "output"


class DatasetConnectionType(Enum):
    """Connection type for a dataset in Dataiku DSS."""

    FILESYSTEM = "Filesystem"
    SQL_POSTGRESQL = "PostgreSQL"
    SQL_MYSQL = "MySQL"
    SQL_BIGQUERY = "BigQuery"
    SQL_SNOWFLAKE = "Snowflake"
    SQL_REDSHIFT = "Redshift"
    S3 = "S3"
    GCS = "GCS"
    AZURE_BLOB = "AzureBlob"
    HDFS = "HDFS"
    MANAGED_FOLDER = "ManagedFolder"
    MONGODB = "MongoDB"
    ELASTICSEARCH = "Elasticsearch"


@dataclass
class ColumnSchema:
    """Schema for a single column."""

    name: str
    type: str  # string, int, float, date, boolean, etc.
    nullable: bool = True
    default: Optional[Any] = None
    format: Optional[str] = None  # For dates, etc.

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "name": self.name,
            "type": self.type,
            "nullable": self.nullable,
        }
        if self.default is not None:
            result["default"] = self.default
        if self.format is not None:
            result["format"] = self.format
        return result


@dataclass
class DataikuDataset:
    """
    Represents a dataset (node) in a Dataiku flow.

    Datasets are the data containers that recipes read from and write to.
    They appear as blue squares in the Dataiku flow visualization.
    """

    name: str
    dataset_type: DatasetType = DatasetType.INTERMEDIATE
    connection_type: DatasetConnectionType = DatasetConnectionType.FILESYSTEM
    schema: List[ColumnSchema] = field(default_factory=list)
    source_variable: Optional[str] = None  # Original Python variable name
    source_line: Optional[int] = None  # Line number in source code
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "type": self.dataset_type.value,
            "connection_type": self.connection_type.value,
            "schema": [col.to_dict() for col in self.schema],
            "source_variable": self.source_variable,
            "source_line": self.source_line,
            "notes": self.notes,
        }

    def to_json(self) -> Dict[str, Any]:
        """Convert to Dataiku API-compatible JSON."""
        result = {
            "name": self.name,
            "projectKey": "${PROJECT_KEY}",  # Placeholder
            "type": self.connection_type.value,
        }
        if self.schema:
            result["schema"] = {
                "columns": [col.to_dict() for col in self.schema],
                "userModified": False,
            }
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DataikuDataset":
        """Reconstruct a DataikuDataset from a dictionary (inverse of to_dict)."""
        schema = [
            ColumnSchema(
                name=col["name"],
                type=col["type"],
                nullable=col.get("nullable", True),
                default=col.get("default"),
                format=col.get("format"),
            )
            for col in data.get("schema", [])
        ]
        connection_type = DatasetConnectionType.FILESYSTEM
        if "connection_type" in data:
            connection_type = DatasetConnectionType(data["connection_type"])
        return cls(
            name=data["name"],
            dataset_type=DatasetType(data["type"]),
            connection_type=connection_type,
            schema=schema,
            source_variable=data.get("source_variable"),
            source_line=data.get("source_line"),
            notes=data.get("notes", []),
        )

    def add_column(
        self,
        name: str,
        col_type: str,
        nullable: bool = True,
        default: Optional[Any] = None,
    ) -> None:
        """Add a column to the schema."""
        self.schema.append(
            ColumnSchema(name=name, type=col_type, nullable=nullable, default=default)
        )

    def add_note(self, note: str) -> None:
        """Add a note about this dataset."""
        self.notes.append(note)

    @property
    def is_input(self) -> bool:
        """Check if this is an input dataset."""
        return self.dataset_type == DatasetType.INPUT

    @property
    def is_output(self) -> bool:
        """Check if this is an output dataset."""
        return self.dataset_type == DatasetType.OUTPUT

    def __repr__(self) -> str:
        return f"DataikuDataset(name='{self.name}', type={self.dataset_type.value})"
