"""Metrics, checks, and data quality models for Dataiku DSS."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class MetricType(Enum):
    """Types of dataset metrics in Dataiku DSS."""

    ROW_COUNT = "row_count"
    COLUMN_MIN = "column_min"
    COLUMN_MAX = "column_max"
    COLUMN_AVG = "column_avg"
    COLUMN_SUM = "column_sum"
    COLUMN_STDDEV = "column_stddev"
    COLUMN_DISTINCT = "column_distinct"
    COLUMN_MISSING = "column_missing"
    CUSTOM_SQL = "custom_sql"
    CUSTOM_PYTHON = "custom_python"


class CheckCondition(Enum):
    """Condition types for checks."""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_OR_EQUAL = "greater_or_equal"
    LESS_OR_EQUAL = "less_or_equal"
    BETWEEN = "between"
    NOT_EMPTY = "not_empty"


class CheckSeverity(Enum):
    """Severity levels for failed checks."""

    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass
class DataikuMetric:
    """A metric computed on a dataset."""

    name: str
    metric_type: MetricType
    column: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "name": self.name,
            "type": self.metric_type.value,
        }
        if self.column:
            result["column"] = self.column
        if self.params:
            result["params"] = self.params
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DataikuMetric":
        return cls(
            name=data["name"],
            metric_type=MetricType(data["type"]),
            column=data.get("column"),
            params=data.get("params", {}),
        )

    @classmethod
    def row_count(cls, name: str = "row_count") -> "DataikuMetric":
        """Create a row count metric."""
        return cls(name=name, metric_type=MetricType.ROW_COUNT)

    @classmethod
    def column_min(cls, column: str, name: Optional[str] = None) -> "DataikuMetric":
        """Create a column minimum metric."""
        return cls(
            name=name or f"{column}_min",
            metric_type=MetricType.COLUMN_MIN,
            column=column,
        )

    @classmethod
    def column_max(cls, column: str, name: Optional[str] = None) -> "DataikuMetric":
        """Create a column maximum metric."""
        return cls(
            name=name or f"{column}_max",
            metric_type=MetricType.COLUMN_MAX,
            column=column,
        )

    @classmethod
    def column_avg(cls, column: str, name: Optional[str] = None) -> "DataikuMetric":
        """Create a column average metric."""
        return cls(
            name=name or f"{column}_avg",
            metric_type=MetricType.COLUMN_AVG,
            column=column,
        )

    @classmethod
    def column_missing(cls, column: str, name: Optional[str] = None) -> "DataikuMetric":
        """Create a column missing count metric."""
        return cls(
            name=name or f"{column}_missing",
            metric_type=MetricType.COLUMN_MISSING,
            column=column,
        )

    @classmethod
    def custom_sql(cls, name: str, query: str) -> "DataikuMetric":
        """Create a custom SQL metric."""
        return cls(
            name=name,
            metric_type=MetricType.CUSTOM_SQL,
            params={"query": query},
        )


@dataclass
class DataikuCheck:
    """A check that validates a metric value."""

    name: str
    metric_name: str
    condition: CheckCondition
    value: Any = None
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    severity: CheckSeverity = CheckSeverity.ERROR

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "name": self.name,
            "metric": self.metric_name,
            "condition": self.condition.value,
            "severity": self.severity.value,
        }
        if self.value is not None:
            result["value"] = self.value
        if self.min_value is not None:
            result["minValue"] = self.min_value
        if self.max_value is not None:
            result["maxValue"] = self.max_value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DataikuCheck":
        return cls(
            name=data["name"],
            metric_name=data["metric"],
            condition=CheckCondition(data["condition"]),
            value=data.get("value"),
            min_value=data.get("minValue"),
            max_value=data.get("maxValue"),
            severity=CheckSeverity(data.get("severity", "ERROR")),
        )

    @classmethod
    def not_empty(
        cls, name: str, metric_name: str
    ) -> "DataikuCheck":
        """Create a check that ensures a metric value is not empty/zero."""
        return cls(
            name=name,
            metric_name=metric_name,
            condition=CheckCondition.NOT_EMPTY,
        )

    @classmethod
    def between(
        cls,
        name: str,
        metric_name: str,
        min_value: Any,
        max_value: Any,
        severity: CheckSeverity = CheckSeverity.ERROR,
    ) -> "DataikuCheck":
        """Create a check that ensures a metric value is between bounds."""
        return cls(
            name=name,
            metric_name=metric_name,
            condition=CheckCondition.BETWEEN,
            min_value=min_value,
            max_value=max_value,
            severity=severity,
        )


@dataclass
class DataQualityRule:
    """A data quality rule for column-level validation."""

    name: str
    column: str
    rule_type: str  # not_null, unique, in_range, regex_match, in_set, etc.
    params: Dict[str, Any] = field(default_factory=dict)
    severity: CheckSeverity = CheckSeverity.ERROR

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "column": self.column,
            "ruleType": self.rule_type,
            "params": self.params,
            "severity": self.severity.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DataQualityRule":
        return cls(
            name=data["name"],
            column=data["column"],
            rule_type=data["ruleType"],
            params=data.get("params", {}),
            severity=CheckSeverity(data.get("severity", "ERROR")),
        )

    @classmethod
    def not_null(cls, column: str) -> "DataQualityRule":
        """Create a not-null rule."""
        return cls(
            name=f"{column}_not_null",
            column=column,
            rule_type="not_null",
        )

    @classmethod
    def unique(cls, column: str) -> "DataQualityRule":
        """Create a uniqueness rule."""
        return cls(
            name=f"{column}_unique",
            column=column,
            rule_type="unique",
        )

    @classmethod
    def in_range(
        cls, column: str, min_value: Any, max_value: Any
    ) -> "DataQualityRule":
        """Create an in-range rule."""
        return cls(
            name=f"{column}_in_range",
            column=column,
            rule_type="in_range",
            params={"min": min_value, "max": max_value},
        )

    @classmethod
    def regex_match(cls, column: str, pattern: str) -> "DataQualityRule":
        """Create a regex match rule."""
        return cls(
            name=f"{column}_regex",
            column=column,
            rule_type="regex_match",
            params={"pattern": pattern},
        )

    @classmethod
    def in_set(cls, column: str, values: List[Any]) -> "DataQualityRule":
        """Create an in-set rule."""
        return cls(
            name=f"{column}_in_set",
            column=column,
            rule_type="in_set",
            params={"values": values},
        )
