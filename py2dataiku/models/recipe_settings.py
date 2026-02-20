"""Recipe settings classes for Dataiku DSS recipe types.

Each recipe type has its own settings class that encapsulates the
recipe-specific configuration. This uses composition to replace the
if/elif chain in DataikuRecipe._build_settings().
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from py2dataiku.models.prepare_step import PrepareStep


class RecipeSettings(ABC):
    """Base class for recipe-specific settings."""

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to a Dataiku API-compatible dictionary."""
        ...

    @abstractmethod
    def to_display_dict(self) -> Dict[str, Any]:
        """Convert settings to a human-readable dictionary for to_dict() output."""
        ...


@dataclass
class PrepareSettings(RecipeSettings):
    """Settings for a Prepare recipe."""

    steps: List[PrepareStep] = field(default_factory=list)
    mode: str = "NORMAL"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "steps": [s.to_json() for s in self.steps],
        }

    def to_display_dict(self) -> Dict[str, Any]:
        return {
            "steps": [s.to_dict() for s in self.steps],
            "step_count": len(self.steps),
        }


@dataclass
class GroupingSettings(RecipeSettings):
    """Settings for a Grouping recipe."""

    keys: List[str] = field(default_factory=list)
    aggregations: List[Any] = field(default_factory=list)
    global_count: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "keys": [{"column": k} for k in self.keys],
            "aggregations": [a.to_dict() for a in self.aggregations],
            "globalCount": self.global_count,
        }

    def to_display_dict(self) -> Dict[str, Any]:
        return {
            "keys": self.keys,
            "aggregations": [a.to_dict() for a in self.aggregations],
        }


@dataclass
class JoinSettings(RecipeSettings):
    """Settings for a Join recipe."""

    join_type: str = "LEFT"
    join_keys: List[Any] = field(default_factory=list)
    selected_columns: Optional[Dict[str, List[str]]] = None

    def to_dict(self) -> Dict[str, Any]:
        settings: Dict[str, Any] = {
            "joinType": self.join_type,
            "joins": [k.to_dict() for k in self.join_keys],
        }
        if self.selected_columns:
            settings["selectedColumns"] = self.selected_columns
        return settings

    def to_display_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "join_type": self.join_type,
            "join_keys": [k.to_dict() for k in self.join_keys],
        }
        if self.selected_columns:
            result["selected_columns"] = self.selected_columns
        return result


@dataclass
class WindowSettings(RecipeSettings):
    """Settings for a Window recipe."""

    partition_columns: List[str] = field(default_factory=list)
    order_columns: List[str] = field(default_factory=list)
    aggregations: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        processed_aggs = []
        for agg in self.aggregations:
            entry = dict(agg)
            if "type" in entry and hasattr(entry["type"], "value"):
                entry["type"] = entry["type"].value
            processed_aggs.append(entry)
        return {
            "partitionColumns": [{"column": c} for c in self.partition_columns],
            "orderColumns": [{"column": c} for c in self.order_columns],
            "aggregations": processed_aggs,
        }

    def to_display_dict(self) -> Dict[str, Any]:
        return self.to_dict()


@dataclass
class SamplingSettings(RecipeSettings):
    """Settings for a Sampling recipe."""

    sampling_method: str = "RANDOM"
    sample_size: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        settings: Dict[str, Any] = {
            "samplingMethod": self.sampling_method,
        }
        if self.sample_size is not None:
            settings["sampleSize"] = self.sample_size
        return settings

    def to_display_dict(self) -> Dict[str, Any]:
        return self.to_dict()


@dataclass
class SplitSettings(RecipeSettings):
    """Settings for a Split recipe."""

    split_mode: str = "FILTER"
    condition: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "splitMode": self.split_mode,
            "condition": self.condition,
        }

    def to_display_dict(self) -> Dict[str, Any]:
        return self.to_dict()


@dataclass
class SortSettings(RecipeSettings):
    """Settings for a Sort recipe."""

    sort_columns: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sortColumns": self.sort_columns,
        }

    def to_display_dict(self) -> Dict[str, Any]:
        return self.to_dict()


@dataclass
class TopNSettings(RecipeSettings):
    """Settings for a Top N recipe."""

    top_n: int = 10
    ranking_column: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topN": self.top_n,
            "rankingColumn": self.ranking_column,
        }

    def to_display_dict(self) -> Dict[str, Any]:
        return self.to_dict()


@dataclass
class DistinctSettings(RecipeSettings):
    """Settings for a Distinct recipe."""

    compute_count: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "computeCount": self.compute_count,
        }

    def to_display_dict(self) -> Dict[str, Any]:
        return self.to_dict()


@dataclass
class StackSettings(RecipeSettings):
    """Settings for a Stack recipe."""

    mode: str = "UNION"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
        }

    def to_display_dict(self) -> Dict[str, Any]:
        return self.to_dict()


@dataclass
class PythonSettings(RecipeSettings):
    """Settings for a Python code recipe."""

    code: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
        }

    def to_display_dict(self) -> Dict[str, Any]:
        return {"code": self.code}


@dataclass
class PivotSettings(RecipeSettings):
    """Settings for a Pivot recipe."""

    row_columns: List[str] = field(default_factory=list)
    column_column: str = ""
    value_column: str = ""
    aggregation: str = "SUM"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rowColumns": self.row_columns,
            "columnColumn": self.column_column,
            "valueColumn": self.value_column,
            "aggregation": self.aggregation,
        }

    def to_display_dict(self) -> Dict[str, Any]:
        return self.to_dict()
