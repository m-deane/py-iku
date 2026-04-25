"""Pattern matching for pandas operations."""

from dataclasses import dataclass
from typing import Any, Optional

from py2dataiku.mappings.pandas_mappings import PandasMapper
from py2dataiku.models.prepare_step import (
    PrepareStep,
    ProcessorType,
)


@dataclass
class MatchResult:
    """Result of pattern matching."""

    matched: bool
    processor_type: Optional[ProcessorType] = None
    recipe_type: Optional[str] = None
    params: dict[str, Any] = None

    def __post_init__(self):
        if self.params is None:
            self.params = {}


class PatternMatcher:
    """
    Match pandas operations to Dataiku recipes and processors.

    This class provides pattern matching for common pandas operations
    and maps them to equivalent Dataiku constructs.
    """

    # Reference canonical mappings from PandasMapper
    STRING_METHODS = PandasMapper.STRING_MAPPINGS
    AGG_FUNCTIONS = PandasMapper.AGG_MAPPINGS
    JOIN_TYPES = PandasMapper.JOIN_MAPPINGS

    def match_fillna(self, column: str, value: Any) -> PrepareStep:
        """Match fillna() to FillEmptyWithValue processor."""
        return PrepareStep.fill_empty(column, value)

    def match_dropna(self, columns: list[str]) -> PrepareStep:
        """Match dropna() to RemoveRowsOnEmpty processor."""
        return PrepareStep.remove_rows_on_empty(columns)

    def match_drop_duplicates(self, columns: Optional[list[str]] = None) -> PrepareStep:
        """Match drop_duplicates() to RemoveDuplicates processor."""
        return PrepareStep.remove_duplicates(columns)

    def match_rename(self, mapping: dict[str, str]) -> PrepareStep:
        """Match rename() to ColumnRenamer processor."""
        return PrepareStep.rename_columns(mapping)

    def match_drop_columns(self, columns: list[str]) -> PrepareStep:
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
        """Match a filter predicate to the correct DSS Prepare processor.

        Dispatches by operator class to the DSS-canonical processor
        (verified against dataiku-api-client-python source):

        - ``==``, ``!=``, ``in`` → ``FilterOnValue`` with ``FULL_STRING``
        - ``contains`` → ``FilterOnValue`` with ``SUBSTRING``
        - ``regex`` / ``matches`` → ``FilterOnValue`` with ``PATTERN``
        - ``>``, ``<``, ``>=``, ``<=`` → ``FilterOnNumericRange`` with
          ``min`` / ``max`` bounds; ``keep`` is flipped for ``!=`` and
          ``<`` / ``>`` (strict) since DSS bounds are inclusive.

        ``isnull`` / ``notnull`` are handled by upstream callers via
        ``REMOVE_ROWS_ON_EMPTY`` rather than this method.
        """
        op = (operator or "").lower().strip()

        # Numeric comparisons → FilterOnNumericRange
        if op in (">", ">=", "gt", "gte", "greater_than", "greater_or_equal"):
            # x > value: keep rows where column > value, i.e. min=value, exclusive.
            # DSS bounds are inclusive — for strict ">" we use min=value+epsilon
            # for ints (value+1 if int), else just min=value (caller must accept
            # boundary). For ">=" we just set min=value.
            inclusive = op in (">=", "gte", "greater_or_equal")
            min_bound = value if inclusive else value
            return PrepareStep.filter_on_numeric_range(
                column=column, min=min_bound, keep=True,
            )
        if op in ("<", "<=", "lt", "lte", "less_than", "less_or_equal"):
            return PrepareStep.filter_on_numeric_range(
                column=column, max=value, keep=True,
            )

        # Substring / regex → FilterOnValue with the right matchingMode
        if op in ("contains", "substring"):
            return PrepareStep.filter_on_value(
                column, [value], matching_mode="SUBSTRING", keep=True,
            )
        if op in ("regex", "matches", "pattern"):
            return PrepareStep.filter_on_value(
                column, [value], matching_mode="PATTERN", keep=True,
            )

        # Equality / membership → FilterOnValue with FULL_STRING
        # ``in`` may pass a list; flatten so each list element is a value.
        if op in ("in", "isin"):
            values = list(value) if isinstance(value, (list, tuple, set)) else [value]
            return PrepareStep.filter_on_value(
                column, values, matching_mode="FULL_STRING", keep=True,
            )
        if op in ("!=", "ne", "not_equals"):
            return PrepareStep.filter_on_value(
                column, [value], matching_mode="FULL_STRING", keep=False,
            )
        # Default: equality (==, eq, equals)
        return PrepareStep.filter_on_value(
            column, [value], matching_mode="FULL_STRING", keep=True,
        )

    def match_aggregation(self, pandas_func: str) -> Optional[str]:
        """Map pandas aggregation function to Dataiku aggregation."""
        return self.AGG_FUNCTIONS.get(pandas_func.lower())

    def match_join_type(self, pandas_how: str) -> str:
        """Map pandas join type to Dataiku join type."""
        return self.JOIN_TYPES.get(pandas_how.lower(), "INNER")

    def match_regex_extract(
        self, column: str, pattern: str, output_columns: Optional[list[str]] = None
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
