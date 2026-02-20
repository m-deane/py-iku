"""JSON schemas and data models for LLM responses."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import json


class OperationType(Enum):
    """Types of data operations that can be detected."""

    # Data I/O
    READ_DATA = "read_data"
    WRITE_DATA = "write_data"

    # Transformations
    FILTER = "filter"
    SELECT_COLUMNS = "select_columns"
    DROP_COLUMNS = "drop_columns"
    RENAME_COLUMNS = "rename_columns"
    ADD_COLUMN = "add_column"
    TRANSFORM_COLUMN = "transform_column"

    # Missing values
    FILL_MISSING = "fill_missing"
    DROP_MISSING = "drop_missing"

    # Deduplication
    DROP_DUPLICATES = "drop_duplicates"

    # Aggregation
    GROUP_AGGREGATE = "group_aggregate"
    WINDOW_FUNCTION = "window_function"

    # Combining data
    JOIN = "join"
    UNION = "union"

    # Reshaping
    PIVOT = "pivot"
    UNPIVOT = "unpivot"

    # Sorting/Ordering
    SORT = "sort"
    TOP_N = "top_n"
    SAMPLE = "sample"

    # Type conversion
    CAST_TYPE = "cast_type"
    PARSE_DATE = "parse_date"

    # String/Column operations
    SPLIT_COLUMN = "split_column"
    ENCODE_CATEGORICAL = "encode_categorical"

    # Scaling/Normalization
    NORMALIZE_SCALE = "normalize_scale"

    # Geographic
    GEO_OPERATION = "geo_operation"

    # Custom/Complex
    CUSTOM_FUNCTION = "custom_function"
    UNKNOWN = "unknown"


@dataclass
class ColumnTransform:
    """Details of a column transformation."""

    column: str
    operation: str  # e.g., "uppercase", "trim", "round", "abs"
    parameters: Dict[str, Any] = field(default_factory=dict)
    output_column: Optional[str] = None  # If different from input


@dataclass
class Aggregation:
    """Details of an aggregation operation."""

    column: str
    function: str  # sum, avg, count, min, max, etc.
    output_column: Optional[str] = None


@dataclass
class JoinCondition:
    """Details of a join condition."""

    left_column: str
    right_column: str
    operator: str = "equals"  # equals, fuzzy, geo, etc.


@dataclass
class FilterCondition:
    """Details of a filter condition."""

    column: str
    operator: str  # equals, not_equals, greater_than, contains, regex, etc.
    value: Any
    logic: str = "and"  # and, or


@dataclass
class DataStep:
    """
    A single data manipulation step extracted from code.

    This is the core unit of the LLM analysis - each step represents
    one logical data operation that maps to a Dataiku recipe or processor.
    """

    step_number: int
    operation: OperationType
    description: str  # Human-readable description of what this step does

    # Input/Output
    input_datasets: List[str] = field(default_factory=list)
    output_dataset: Optional[str] = None

    # Columns involved
    columns: List[str] = field(default_factory=list)

    # Operation-specific details
    filter_conditions: List[FilterCondition] = field(default_factory=list)
    aggregations: List[Aggregation] = field(default_factory=list)
    group_by_columns: List[str] = field(default_factory=list)
    join_conditions: List[JoinCondition] = field(default_factory=list)
    join_type: Optional[str] = None  # inner, left, right, outer
    column_transforms: List[ColumnTransform] = field(default_factory=list)
    rename_mapping: Dict[str, str] = field(default_factory=dict)
    sort_columns: List[Dict[str, str]] = field(default_factory=list)  # [{column, order}]
    fill_value: Optional[Any] = None

    # Source code reference
    source_lines: List[int] = field(default_factory=list)
    source_code: Optional[str] = None

    # Dataiku mapping hints from LLM
    suggested_recipe: Optional[str] = None  # prepare, join, grouping, etc.
    suggested_processors: List[str] = field(default_factory=list)
    requires_python_recipe: bool = False
    reasoning: Optional[str] = None  # LLM's explanation for the mapping

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step_number": self.step_number,
            "operation": self.operation.value,
            "description": self.description,
            "input_datasets": self.input_datasets,
            "output_dataset": self.output_dataset,
            "columns": self.columns,
            "filter_conditions": [
                {"column": f.column, "operator": f.operator, "value": f.value}
                for f in self.filter_conditions
            ],
            "aggregations": [
                {"column": a.column, "function": a.function, "output_column": a.output_column}
                for a in self.aggregations
            ],
            "group_by_columns": self.group_by_columns,
            "join_conditions": [
                {"left": j.left_column, "right": j.right_column, "operator": j.operator}
                for j in self.join_conditions
            ],
            "join_type": self.join_type,
            "column_transforms": [
                {"column": t.column, "operation": t.operation, "parameters": t.parameters}
                for t in self.column_transforms
            ],
            "rename_mapping": self.rename_mapping,
            "sort_columns": self.sort_columns,
            "fill_value": self.fill_value,
            "source_lines": self.source_lines,
            "suggested_recipe": self.suggested_recipe,
            "suggested_processors": self.suggested_processors,
            "requires_python_recipe": self.requires_python_recipe,
            "reasoning": self.reasoning,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DataStep":
        """Create from dictionary (LLM response)."""
        try:
            operation = OperationType(data.get("operation", "unknown"))
        except ValueError:
            operation = OperationType.UNKNOWN
        return cls(
            step_number=data.get("step_number", 0),
            operation=operation,
            description=data.get("description", ""),
            input_datasets=data.get("input_datasets", []),
            output_dataset=data.get("output_dataset"),
            columns=data.get("columns", []),
            filter_conditions=[
                FilterCondition(
                    column=f.get("column", ""),
                    operator=f.get("operator", "equals"),
                    value=f.get("value"),
                )
                for f in data.get("filter_conditions", [])
            ],
            aggregations=[
                Aggregation(
                    column=a.get("column", ""),
                    function=a.get("function", ""),
                    output_column=a.get("output_column"),
                )
                for a in data.get("aggregations", [])
            ],
            group_by_columns=data.get("group_by_columns", []),
            join_conditions=[
                JoinCondition(
                    left_column=j.get("left", j.get("left_column", "")),
                    right_column=j.get("right", j.get("right_column", "")),
                    operator=j.get("operator", "equals"),
                )
                for j in data.get("join_conditions", [])
            ],
            join_type=data.get("join_type"),
            column_transforms=[
                ColumnTransform(
                    column=t.get("column", ""),
                    operation=t.get("operation", ""),
                    parameters=t.get("parameters", {}),
                )
                for t in data.get("column_transforms", [])
            ],
            rename_mapping=data.get("rename_mapping", {}),
            sort_columns=data.get("sort_columns", []),
            fill_value=data.get("fill_value"),
            source_lines=data.get("source_lines", []),
            source_code=data.get("source_code"),
            suggested_recipe=data.get("suggested_recipe"),
            suggested_processors=data.get("suggested_processors", []),
            requires_python_recipe=data.get("requires_python_recipe", False),
            reasoning=data.get("reasoning"),
        )


@dataclass
class DatasetInfo:
    """Information about a dataset identified in the code."""

    name: str
    source: Optional[str] = None  # file path, database table, etc.
    is_input: bool = False
    is_output: bool = False
    inferred_columns: List[str] = field(default_factory=list)


@dataclass
class AnalysisResult:
    """
    Complete result of LLM code analysis.

    Contains all extracted data steps and metadata about the analysis.
    """

    steps: List[DataStep]
    datasets: List[DatasetInfo]

    # Analysis metadata
    code_summary: str = ""
    total_operations: int = 0
    complexity_score: int = 0  # 1-10 scale

    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Raw LLM response for debugging
    raw_response: Optional[str] = None
    model_used: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "steps": [s.to_dict() for s in self.steps],
            "datasets": [
                {
                    "name": d.name,
                    "source": d.source,
                    "is_input": d.is_input,
                    "is_output": d.is_output,
                    "inferred_columns": d.inferred_columns,
                }
                for d in self.datasets
            ],
            "code_summary": self.code_summary,
            "total_operations": self.total_operations,
            "complexity_score": self.complexity_score,
            "recommendations": self.recommendations,
            "warnings": self.warnings,
            "model_used": self.model_used,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnalysisResult":
        """Create from dictionary (LLM response)."""
        return cls(
            steps=[DataStep.from_dict(s) for s in data.get("steps", [])],
            datasets=[
                DatasetInfo(
                    name=d.get("name", ""),
                    source=d.get("source"),
                    is_input=d.get("is_input", False),
                    is_output=d.get("is_output", False),
                    inferred_columns=d.get("inferred_columns", []),
                )
                for d in data.get("datasets", [])
            ],
            code_summary=data.get("code_summary", ""),
            total_operations=data.get("total_operations", 0),
            complexity_score=data.get("complexity_score", 0),
            recommendations=data.get("recommendations", []),
            warnings=data.get("warnings", []),
        )


# JSON Schema for LLM prompt (to ensure structured output)
ANALYSIS_JSON_SCHEMA = {
    "type": "object",
    "required": ["steps", "datasets", "code_summary"],
    "properties": {
        "code_summary": {
            "type": "string",
            "description": "Brief summary of what the code does"
        },
        "total_operations": {"type": "integer"},
        "complexity_score": {"type": "integer", "minimum": 1, "maximum": 10},
        "datasets": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string"},
                    "source": {"type": "string"},
                    "is_input": {"type": "boolean"},
                    "is_output": {"type": "boolean"},
                    "inferred_columns": {"type": "array", "items": {"type": "string"}}
                }
            }
        },
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["step_number", "operation", "description"],
                "properties": {
                    "step_number": {"type": "integer"},
                    "operation": {
                        "type": "string",
                        "enum": [op.value for op in OperationType]
                    },
                    "description": {"type": "string"},
                    "input_datasets": {"type": "array", "items": {"type": "string"}},
                    "output_dataset": {"type": "string"},
                    "columns": {"type": "array", "items": {"type": "string"}},
                    "filter_conditions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "column": {"type": "string"},
                                "operator": {"type": "string"},
                                "value": {}
                            }
                        }
                    },
                    "aggregations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "column": {"type": "string"},
                                "function": {"type": "string"},
                                "output_column": {"type": "string"}
                            }
                        }
                    },
                    "group_by_columns": {"type": "array", "items": {"type": "string"}},
                    "join_conditions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "left_column": {"type": "string"},
                                "right_column": {"type": "string"},
                                "operator": {"type": "string"}
                            }
                        }
                    },
                    "join_type": {"type": "string"},
                    "column_transforms": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "column": {"type": "string"},
                                "operation": {"type": "string"},
                                "parameters": {"type": "object"}
                            }
                        }
                    },
                    "rename_mapping": {"type": "object"},
                    "sort_columns": {"type": "array"},
                    "fill_value": {},
                    "source_lines": {"type": "array", "items": {"type": "integer"}},
                    "suggested_recipe": {"type": "string"},
                    "suggested_processors": {"type": "array", "items": {"type": "string"}},
                    "requires_python_recipe": {"type": "boolean"},
                    "reasoning": {"type": "string"}
                }
            }
        },
        "recommendations": {"type": "array", "items": {"type": "string"}},
        "warnings": {"type": "array", "items": {"type": "string"}}
    }
}
