"""Intermediate transformation representation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class TransformationType(Enum):
    """
    Types of transformations detected in Python code.

    These are intermediate representations before mapping to Dataiku recipes.
    """

    # Data loading/saving
    READ_DATA = "read_data"
    WRITE_DATA = "write_data"

    # Column operations
    COLUMN_RENAME = "column_rename"
    COLUMN_DROP = "column_drop"
    COLUMN_SELECT = "column_select"
    COLUMN_COPY = "column_copy"
    COLUMN_CREATE = "column_create"

    # Value transformations
    FILL_NA = "fill_na"
    DROP_NA = "drop_na"
    TYPE_CAST = "type_cast"
    STRING_TRANSFORM = "string_transform"
    NUMERIC_TRANSFORM = "numeric_transform"
    DATE_PARSE = "date_parse"

    # Row operations
    FILTER = "filter"
    DROP_DUPLICATES = "drop_duplicates"
    SORT = "sort"
    HEAD = "head"
    TAIL = "tail"
    SAMPLE = "sample"
    TOP_N = "top_n"

    # Aggregations
    GROUPBY = "groupby"
    WINDOW = "window"
    ROLLING = "rolling"

    # Combining data
    MERGE = "merge"
    JOIN = "join"
    CONCAT = "concat"

    # Reshaping
    PIVOT = "pivot"
    MELT = "melt"
    TRANSPOSE = "transpose"

    # ML operations
    FIT = "fit"
    PREDICT = "predict"
    TRANSFORM = "transform"
    FIT_TRANSFORM = "fit_transform"

    # Custom/unknown
    CUSTOM_FUNCTION = "custom_function"
    UNKNOWN = "unknown"


@dataclass
class Transformation:
    """
    Represents a single transformation detected in Python code.

    This is an intermediate representation that captures the semantics
    of the Python operation before it's mapped to a Dataiku recipe.
    """

    transformation_type: TransformationType
    source_dataframe: Optional[str] = None  # Input variable name
    target_dataframe: Optional[str] = None  # Output variable name
    columns: List[str] = field(default_factory=list)  # Affected columns
    parameters: Dict[str, Any] = field(default_factory=dict)  # Operation parameters

    # Source code information
    source_line: Optional[int] = None
    source_code: Optional[str] = None
    ast_node_type: Optional[str] = None

    # Chain information (for method chains)
    chain_index: Optional[int] = None  # Position in method chain
    chain_id: Optional[str] = None  # ID to group chained operations

    # Mapping hints
    suggested_recipe: Optional[str] = None
    suggested_processor: Optional[str] = None
    requires_python_recipe: bool = False
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "type": self.transformation_type.value,
            "source_dataframe": self.source_dataframe,
            "target_dataframe": self.target_dataframe,
            "columns": self.columns,
            "parameters": self.parameters,
            "source_line": self.source_line,
            "source_code": self.source_code,
            "suggested_recipe": self.suggested_recipe,
            "suggested_processor": self.suggested_processor,
            "requires_python_recipe": self.requires_python_recipe,
            "notes": self.notes,
        }

    @classmethod
    def read_csv(
        cls,
        variable: str,
        filepath: str,
        line: Optional[int] = None,
    ) -> "Transformation":
        """Create a read data transformation."""
        return cls(
            transformation_type=TransformationType.READ_DATA,
            target_dataframe=variable,
            parameters={"filepath": filepath, "format": "csv"},
            source_line=line,
        )

    @classmethod
    def fillna(
        cls,
        dataframe: str,
        column: str,
        value: Any,
        line: Optional[int] = None,
    ) -> "Transformation":
        """Create a fill NA transformation."""
        return cls(
            transformation_type=TransformationType.FILL_NA,
            source_dataframe=dataframe,
            target_dataframe=dataframe,
            columns=[column],
            parameters={"value": value},
            source_line=line,
            suggested_processor="FillEmptyWithValue",
        )

    @classmethod
    def string_method(
        cls,
        dataframe: str,
        column: str,
        method: str,
        args: Optional[List[Any]] = None,
        line: Optional[int] = None,
    ) -> "Transformation":
        """Create a string transformation."""
        return cls(
            transformation_type=TransformationType.STRING_TRANSFORM,
            source_dataframe=dataframe,
            target_dataframe=dataframe,
            columns=[column],
            parameters={"method": method, "args": args or []},
            source_line=line,
            suggested_processor="StringTransformer",
        )

    @classmethod
    def rename_columns(
        cls,
        dataframe: str,
        mapping: Dict[str, str],
        line: Optional[int] = None,
    ) -> "Transformation":
        """Create a column rename transformation."""
        return cls(
            transformation_type=TransformationType.COLUMN_RENAME,
            source_dataframe=dataframe,
            target_dataframe=dataframe,
            columns=list(mapping.keys()),
            parameters={"mapping": mapping},
            source_line=line,
            suggested_processor="ColumnRenamer",
        )

    @classmethod
    def drop_columns(
        cls,
        dataframe: str,
        columns: List[str],
        line: Optional[int] = None,
    ) -> "Transformation":
        """Create a column drop transformation."""
        return cls(
            transformation_type=TransformationType.COLUMN_DROP,
            source_dataframe=dataframe,
            target_dataframe=dataframe,
            columns=columns,
            parameters={},
            source_line=line,
            suggested_processor="ColumnDeleter",
        )

    @classmethod
    def dropna(
        cls,
        dataframe: str,
        columns: Optional[List[str]] = None,
        line: Optional[int] = None,
    ) -> "Transformation":
        """Create a drop NA transformation."""
        return cls(
            transformation_type=TransformationType.DROP_NA,
            source_dataframe=dataframe,
            target_dataframe=dataframe,
            columns=columns or [],
            parameters={"subset": columns},
            source_line=line,
            suggested_processor="RemoveRowsOnEmpty",
        )

    @classmethod
    def drop_duplicates(
        cls,
        dataframe: str,
        columns: Optional[List[str]] = None,
        line: Optional[int] = None,
    ) -> "Transformation":
        """Create a drop duplicates transformation."""
        return cls(
            transformation_type=TransformationType.DROP_DUPLICATES,
            source_dataframe=dataframe,
            target_dataframe=dataframe,
            columns=columns or [],
            parameters={"subset": columns},
            source_line=line,
            suggested_recipe="distinct",
        )

    @classmethod
    def filter_rows(
        cls,
        dataframe: str,
        target: str,
        condition: str,
        line: Optional[int] = None,
    ) -> "Transformation":
        """Create a filter transformation."""
        return cls(
            transformation_type=TransformationType.FILTER,
            source_dataframe=dataframe,
            target_dataframe=target,
            parameters={"condition": condition},
            source_line=line,
            suggested_recipe="split",
        )

    @classmethod
    def merge(
        cls,
        left: str,
        right: str,
        target: str,
        on: Optional[List[str]] = None,
        left_on: Optional[List[str]] = None,
        right_on: Optional[List[str]] = None,
        how: str = "inner",
        line: Optional[int] = None,
    ) -> "Transformation":
        """Create a merge/join transformation."""
        return cls(
            transformation_type=TransformationType.MERGE,
            source_dataframe=left,
            target_dataframe=target,
            parameters={
                "right": right,
                "on": on,
                "left_on": left_on,
                "right_on": right_on,
                "how": how,
            },
            source_line=line,
            suggested_recipe="join",
        )

    @classmethod
    def groupby_agg(
        cls,
        dataframe: str,
        target: str,
        keys: List[str],
        aggregations: Dict[str, str],
        line: Optional[int] = None,
    ) -> "Transformation":
        """Create a groupby aggregation transformation."""
        return cls(
            transformation_type=TransformationType.GROUPBY,
            source_dataframe=dataframe,
            target_dataframe=target,
            columns=keys,
            parameters={"keys": keys, "aggregations": aggregations},
            source_line=line,
            suggested_recipe="grouping",
        )

    @classmethod
    def sort_values(
        cls,
        dataframe: str,
        columns: List[str],
        ascending: bool = True,
        line: Optional[int] = None,
    ) -> "Transformation":
        """Create a sort transformation."""
        return cls(
            transformation_type=TransformationType.SORT,
            source_dataframe=dataframe,
            target_dataframe=dataframe,
            columns=columns,
            parameters={"ascending": ascending},
            source_line=line,
            suggested_recipe="sort",
        )

    @classmethod
    def astype(
        cls,
        dataframe: str,
        column: str,
        dtype: str,
        line: Optional[int] = None,
    ) -> "Transformation":
        """Create a type cast transformation."""
        return cls(
            transformation_type=TransformationType.TYPE_CAST,
            source_dataframe=dataframe,
            target_dataframe=dataframe,
            columns=[column],
            parameters={"dtype": dtype},
            source_line=line,
            suggested_processor="TypeSetter",
        )

    @classmethod
    def custom(
        cls,
        dataframe: str,
        target: str,
        code: str,
        line: Optional[int] = None,
    ) -> "Transformation":
        """Create a custom/unknown transformation."""
        return cls(
            transformation_type=TransformationType.CUSTOM_FUNCTION,
            source_dataframe=dataframe,
            target_dataframe=target,
            parameters={"code": code},
            source_line=line,
            requires_python_recipe=True,
            notes=["Complex operation requires Python recipe"],
        )

    def add_note(self, note: str) -> None:
        """Add a note about this transformation."""
        self.notes.append(note)

    def __repr__(self) -> str:
        return (
            f"Transformation(type={self.transformation_type.value}, "
            f"source={self.source_dataframe}, target={self.target_dataframe})"
        )
