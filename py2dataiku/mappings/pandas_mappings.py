"""Mappings from pandas operations to Dataiku recipes and processors."""

from typing import Any, Dict, List, Optional, Tuple

from py2dataiku.models.prepare_step import PrepareStep, ProcessorType, StringTransformerMode
from py2dataiku.models.dataiku_recipe import RecipeType


class PandasMapper:
    """
    Map pandas operations to Dataiku constructs.

    This class provides mappings between common pandas methods
    and their Dataiku visual recipe/processor equivalents.
    """

    # Method to recipe type mapping
    RECIPE_MAPPINGS: Dict[str, RecipeType] = {
        "merge": RecipeType.JOIN,
        "join": RecipeType.JOIN,
        "concat": RecipeType.STACK,
        "groupby": RecipeType.GROUPING,
        "pivot": RecipeType.PIVOT,
        "pivot_table": RecipeType.PIVOT,
        "melt": RecipeType.PIVOT,  # Unpivot
        "sort_values": RecipeType.SORT,
        "drop_duplicates": RecipeType.DISTINCT,
        "head": RecipeType.TOP_N,
        "nlargest": RecipeType.TOP_N,
        "nsmallest": RecipeType.TOP_N,
        "sample": RecipeType.SAMPLING,
        "cumsum": RecipeType.WINDOW,
        "cumprod": RecipeType.WINDOW,
        "cummin": RecipeType.WINDOW,
        "cummax": RecipeType.WINDOW,
        "diff": RecipeType.WINDOW,
        "shift": RecipeType.WINDOW,
        "rank": RecipeType.WINDOW,
        "nunique": RecipeType.GROUPING,
    }

    # Method to processor type mapping
    PROCESSOR_MAPPINGS: Dict[str, ProcessorType] = {
        "fillna": ProcessorType.FILL_EMPTY_WITH_VALUE,
        "dropna": ProcessorType.REMOVE_ROWS_ON_EMPTY,
        "rename": ProcessorType.COLUMN_RENAMER,
        "drop": ProcessorType.COLUMN_DELETER,
        "astype": ProcessorType.TYPE_SETTER,
        "to_datetime": ProcessorType.DATE_PARSER,
        "round": ProcessorType.ROUND_COLUMN,
        "abs": ProcessorType.ABS_COLUMN,
        "clip": ProcessorType.CLIP_COLUMN,
        "map": ProcessorType.TRANSLATE_VALUES,
        "explode": ProcessorType.UNFOLD,
        "combine_first": ProcessorType.COALESCE,
        "interpolate": ProcessorType.FILL_EMPTY_WITH_PREVIOUS_NEXT,
        "get_dummies": ProcessorType.ONE_HOT_ENCODER,
        "cut": ProcessorType.BINNER,
        "qcut": ProcessorType.BINNER,
    }

    # String accessor method mappings
    STRING_MAPPINGS: Dict[str, StringTransformerMode] = {
        "upper": StringTransformerMode.UPPERCASE,
        "lower": StringTransformerMode.LOWERCASE,
        "title": StringTransformerMode.TITLECASE,
        "capitalize": StringTransformerMode.TITLECASE,
        "strip": StringTransformerMode.TRIM,
        "lstrip": StringTransformerMode.TRIM_LEFT,
        "rstrip": StringTransformerMode.TRIM_RIGHT,
    }

    # Aggregation function mappings
    AGG_MAPPINGS: Dict[str, str] = {
        "sum": "SUM",
        "mean": "AVG",
        "average": "AVG",
        "avg": "AVG",
        "count": "COUNT",
        "size": "COUNT",
        "min": "MIN",
        "max": "MAX",
        "first": "FIRST",
        "last": "LAST",
        "std": "STDDEV",
        "var": "VAR",
        "median": "MEDIAN",
        "nunique": "COUNTDISTINCT",
    }

    # Join type mappings
    JOIN_MAPPINGS: Dict[str, str] = {
        "inner": "INNER",
        "left": "LEFT",
        "right": "RIGHT",
        "outer": "OUTER",
        "cross": "CROSS",
    }

    def get_recipe_type(self, method: str) -> Optional[RecipeType]:
        """Get the Dataiku recipe type for a pandas method."""
        return self.RECIPE_MAPPINGS.get(method)

    def get_processor_type(self, method: str) -> Optional[ProcessorType]:
        """Get the Dataiku processor type for a pandas method."""
        return self.PROCESSOR_MAPPINGS.get(method)

    def get_string_mode(self, method: str) -> Optional[StringTransformerMode]:
        """Get the StringTransformer mode for a string accessor method."""
        return self.STRING_MAPPINGS.get(method)

    def get_agg_function(self, pandas_func: str) -> Optional[str]:
        """Get the Dataiku aggregation function name."""
        return self.AGG_MAPPINGS.get(pandas_func.lower())

    def get_join_type(self, how: str) -> str:
        """Get the Dataiku join type."""
        return self.JOIN_MAPPINGS.get(how.lower(), "INNER")

    def map_fillna(
        self, column: str, value: Any, method: Optional[str] = None
    ) -> PrepareStep:
        """Map fillna() to a PrepareStep."""
        if method == "ffill":
            return PrepareStep(
                processor_type=ProcessorType.FILL_EMPTY_WITH_PREVIOUS_NEXT,
                params={"column": column, "direction": "PREVIOUS"},
            )
        elif method == "bfill":
            return PrepareStep(
                processor_type=ProcessorType.FILL_EMPTY_WITH_PREVIOUS_NEXT,
                params={"column": column, "direction": "NEXT"},
            )
        else:
            return PrepareStep.fill_empty(column, value)

    def map_dropna(
        self,
        subset: Optional[List[str]] = None,
        how: str = "any",
    ) -> PrepareStep:
        """Map dropna() to a PrepareStep."""
        return PrepareStep.remove_rows_on_empty(
            columns=subset or [],
            keep_empty=False,
        )

    def map_rename(self, mapping: Dict[str, str]) -> PrepareStep:
        """Map rename() to a PrepareStep."""
        return PrepareStep.rename_columns(mapping)

    def map_drop_columns(self, columns: List[str]) -> PrepareStep:
        """Map drop(columns=...) to a PrepareStep."""
        return PrepareStep.delete_columns(columns)

    def map_astype(self, column: str, dtype: str) -> PrepareStep:
        """Map astype() to a PrepareStep."""
        type_map = {
            "int": "bigint",
            "int64": "bigint",
            "int32": "int",
            "float": "double",
            "float64": "double",
            "str": "string",
            "string": "string",
            "object": "string",
            "bool": "boolean",
            "boolean": "boolean",
            "datetime64": "date",
            "datetime64[ns]": "date",
        }
        dataiku_type = type_map.get(str(dtype), "string")
        return PrepareStep.set_type(column, dataiku_type)

    def map_string_method(
        self, column: str, method: str, args: Optional[List[Any]] = None
    ) -> Optional[PrepareStep]:
        """Map a string accessor method to a PrepareStep."""
        mode = self.get_string_mode(method)
        if mode:
            return PrepareStep.string_transform(column, mode)

        # Handle other string methods
        if method == "replace" and args and len(args) >= 2:
            return PrepareStep(
                processor_type=ProcessorType.FIND_REPLACE,
                params={
                    "column": column,
                    "find": str(args[0]),
                    "replace": str(args[1]),
                },
            )
        elif method == "split":
            separator = args[0] if args else ","
            return PrepareStep(
                processor_type=ProcessorType.SPLIT_COLUMN,
                params={"column": column, "separator": str(separator)},
            )
        elif method == "extract" and args:
            return PrepareStep.regexp_extract(column, str(args[0]))
        elif method == "contains" and args:
            return PrepareStep(
                processor_type=ProcessorType.FLAG_ON_VALUE,
                params={
                    "column": column,
                    "pattern": str(args[0]),
                    "matchMode": "REGEX",
                },
            )
        elif method == "startswith" and args:
            return PrepareStep(
                processor_type=ProcessorType.FILTER_ON_VALUE,
                params={
                    "column": column,
                    "values": [str(args[0])],
                    "matchingMode": "STARTS_WITH",
                    "keep": True,
                },
            )
        elif method == "endswith" and args:
            return PrepareStep(
                processor_type=ProcessorType.FILTER_ON_VALUE,
                params={
                    "column": column,
                    "values": [str(args[0])],
                    "matchingMode": "ENDS_WITH",
                    "keep": True,
                },
            )
        elif method == "findall" and args:
            return PrepareStep.regexp_extract(column, str(args[0]))
        elif method == "len":
            return PrepareStep(
                processor_type=ProcessorType.FORMULA,
                params={
                    "column": column,
                    "expression": f"length(val(\"{column}\"))",
                },
            )

        return None

    # Window function mappings (pandas methods that map to Dataiku WINDOW recipe)
    WINDOW_MAPPINGS: Dict[str, str] = {
        "cumsum": "RUNNING_SUM",
        "cumprod": "RUNNING_PRODUCT",
        "cummin": "RUNNING_MIN",
        "cummax": "RUNNING_MAX",
        "diff": "LAG_DIFF",
        "shift": "LAG",
        "rank": "RANK",
    }

    # NumPy function to processor mappings
    NUMPY_PROCESSOR_MAPPINGS: Dict[str, ProcessorType] = {
        "select": ProcessorType.SWITCH_CASE,
        "digitize": ProcessorType.BINNER,
    }

    # NumPy window function mappings
    NUMPY_WINDOW_MAPPINGS: Dict[str, str] = {
        "cumsum": "RUNNING_SUM",
        "cumprod": "RUNNING_PRODUCT",
        "diff": "LAG_DIFF",
    }

    # NumPy aggregation to binner mappings
    NUMPY_BINNER_MAPPINGS: Dict[str, str] = {
        "percentile": "QUANTILE",
        "quantile": "QUANTILE",
    }

    def get_window_function(self, method: str) -> Optional[str]:
        """Get the Dataiku WINDOW function for a pandas method."""
        return self.WINDOW_MAPPINGS.get(method)

    def get_numpy_processor(self, func_name: str) -> Optional[ProcessorType]:
        """Get the Dataiku processor type for a NumPy function."""
        return self.NUMPY_PROCESSOR_MAPPINGS.get(func_name)

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
            "json_normalize",
            "resample",
            "pct_change",
        }
        return method in python_only

    def get_alternative_suggestion(self, method: str) -> Optional[str]:
        """Get a suggestion for handling unsupported methods."""
        suggestions = {
            "apply": "Consider using CreateColumnWithGREL for simple transformations",
            "get_dummies": "Use OneHotEncoder processor in Prepare recipe",
            "cut": "Use Binner processor in Prepare recipe",
            "qcut": "Use Binner processor with quantile mode",
            "interpolate": "Use FillEmptyWithPreviousNext processor (LINEAR mode)",
            "shift": "Use Window recipe with LAG function",
            "diff": "Use Window recipe with LAG_DIFF function",
            "rank": "Use Window recipe with RANK function",
            "cumsum": "Use Window recipe with RUNNING_SUM function",
            "cumprod": "Use Window recipe with RUNNING_PRODUCT function",
            "map": "Use TranslateValues processor for dictionary-based mapping",
            "where": "Use IfThenElse processor for conditional assignment",
            "mask": "Use IfThenElse processor for conditional masking",
            "replace": "Use TranslateValues processor for dictionary replacement",
            "explode": "Use Unfold processor to expand list-like columns",
            "combine_first": "Use Coalesce processor to pick first non-null value",
        }
        return suggestions.get(method)
