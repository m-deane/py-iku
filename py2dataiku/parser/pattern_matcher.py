"""Pattern matching for pandas operations."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from py2dataiku.models.prepare_step import PrepareStep, ProcessorType, StringTransformerMode


@dataclass
class MatchResult:
    """Result of pattern matching."""

    matched: bool
    processor_type: Optional[ProcessorType] = None
    recipe_type: Optional[str] = None
    params: Dict[str, Any] = None

    def __post_init__(self):
        if self.params is None:
            self.params = {}


class PatternMatcher:
    """
    Match pandas operations to Dataiku recipes and processors.

    This class provides pattern matching for common pandas operations
    and maps them to equivalent Dataiku constructs.
    """

    # String method mappings
    STRING_METHODS = {
        "upper": StringTransformerMode.UPPERCASE,
        "lower": StringTransformerMode.LOWERCASE,
        "title": StringTransformerMode.TITLECASE,
        "strip": StringTransformerMode.TRIM,
        "lstrip": StringTransformerMode.TRIM_LEFT,
        "rstrip": StringTransformerMode.TRIM_RIGHT,
    }

    # Aggregation function mappings (pandas -> Dataiku)
    AGG_FUNCTIONS = {
        "sum": "SUM",
        "mean": "AVG",
        "avg": "AVG",
        "count": "COUNT",
        "min": "MIN",
        "max": "MAX",
        "first": "FIRST",
        "last": "LAST",
        "std": "STDDEV",
        "var": "VAR",
        "median": "MEDIAN",
    }

    # Join type mappings
    JOIN_TYPES = {
        "inner": "INNER",
        "left": "LEFT",
        "right": "RIGHT",
        "outer": "OUTER",
        "cross": "CROSS",
    }

    def match_fillna(self, column: str, value: Any) -> PrepareStep:
        """Match fillna() to FillEmptyWithValue processor."""
        return PrepareStep.fill_empty(column, value)

    def match_dropna(self, columns: List[str]) -> PrepareStep:
        """Match dropna() to RemoveRowsOnEmpty processor."""
        return PrepareStep.remove_rows_on_empty(columns)

    def match_drop_duplicates(self, columns: Optional[List[str]] = None) -> PrepareStep:
        """Match drop_duplicates() to RemoveDuplicates processor."""
        return PrepareStep.remove_duplicates(columns)

    def match_rename(self, mapping: Dict[str, str]) -> PrepareStep:
        """Match rename() to ColumnRenamer processor."""
        return PrepareStep.rename_columns(mapping)

    def match_drop_columns(self, columns: List[str]) -> PrepareStep:
        """Match drop(columns=...) to ColumnDeleter processor."""
        return PrepareStep.delete_columns(columns)

    def match_string_method(
        self, column: str, method: str
    ) -> Optional[PrepareStep]:
        """Match string accessor methods to StringTransformer processor."""
        mode = self.STRING_METHODS.get(method)
        if mode:
            return PrepareStep.string_transform(column, mode)
        return None

    def match_astype(self, column: str, dtype: str) -> PrepareStep:
        """Match astype() to TypeSetter processor."""
        # Map pandas dtypes to Dataiku types
        type_map = {
            "int": "bigint",
            "int64": "bigint",
            "int32": "int",
            "float": "double",
            "float64": "double",
            "str": "string",
            "string": "string",
            "bool": "boolean",
            "datetime64": "date",
        }
        dataiku_type = type_map.get(dtype, "string")
        return PrepareStep.set_type(column, dataiku_type)

    def match_to_datetime(self, column: str) -> PrepareStep:
        """Match pd.to_datetime() to DateParser processor."""
        return PrepareStep.parse_date(column)

    def match_filter(
        self, column: str, operator: str, value: Any
    ) -> PrepareStep:
        """Match filter conditions to FilterOnValue processor."""
        # Map operators to matching modes
        mode_map = {
            "==": "EQUALS",
            "!=": "NOT_EQUALS",
            ">": "GREATER_THAN",
            ">=": "GREATER_OR_EQUAL",
            "<": "LESS_THAN",
            "<=": "LESS_OR_EQUAL",
            "in": "IN",
            "contains": "CONTAINS",
        }
        matching_mode = mode_map.get(operator, "EQUALS")
        return PrepareStep.filter_on_value(
            column, [value], matching_mode, keep=True
        )

    def match_aggregation(self, pandas_func: str) -> Optional[str]:
        """Map pandas aggregation function to Dataiku aggregation."""
        return self.AGG_FUNCTIONS.get(pandas_func.lower())

    def match_join_type(self, pandas_how: str) -> str:
        """Map pandas join type to Dataiku join type."""
        return self.JOIN_TYPES.get(pandas_how.lower(), "INNER")

    def match_regex_extract(
        self, column: str, pattern: str, output_columns: Optional[List[str]] = None
    ) -> PrepareStep:
        """Match str.extract() to RegexpExtractor processor."""
        return PrepareStep.regexp_extract(column, pattern, output_columns)

    def match_split(
        self, column: str, separator: str
    ) -> PrepareStep:
        """Match str.split() to SplitColumn processor."""
        return PrepareStep(
            processor_type=ProcessorType.SPLIT_COLUMN,
            params={"column": column, "separator": separator},
        )

    def requires_python_recipe(self, method: str) -> bool:
        """Check if a method requires a Python recipe."""
        python_only = {
            "apply",
            "applymap",
            "transform",
            "pipe",
            "eval",
            "query",
            "assign",
            "stack",
            "unstack",
            "explode",
            "json_normalize",
        }
        return method in python_only
