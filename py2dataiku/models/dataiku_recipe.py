"""Recipe model for Dataiku DSS."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from py2dataiku.models.prepare_step import PrepareStep
from py2dataiku.models.recipe_settings import RecipeSettings


class RecipeType(Enum):
    """
    Dataiku recipe types.

    Visual recipes appear as colored circles in the flow.
    Code recipes (Python, SQL, R) are orange circles.
    """

    # Visual recipes (green/teal) - Data Preparation
    PREPARE = "prepare"
    SYNC = "sync"
    GROUPING = "grouping"
    WINDOW = "window"
    JOIN = "join"
    FUZZY_JOIN = "fuzzy_join"
    GEO_JOIN = "geo_join"
    STACK = "stack"
    SPLIT = "split"
    SORT = "sort"
    DISTINCT = "distinct"
    TOP_N = "topn"
    PIVOT = "pivot"
    SAMPLING = "sampling"
    DOWNLOAD = "download"

    # Visual recipes - Additional
    GENERATE_FEATURES = "generate_features"
    GENERATE_STATISTICS = "generate_statistics"
    PUSH_TO_EDITABLE = "push_to_editable"
    LIST_FOLDER_CONTENTS = "list_folder_contents"
    DYNAMIC_REPEAT = "dynamic_repeat"
    EXTRACT_FAILED_ROWS = "extract_failed_rows"
    UPSERT = "upsert"
    LIST_ACCESS = "list_access"

    # Code recipes (orange) - Python/R
    PYTHON = "python"
    R = "r"

    # Code recipes - SQL variants
    SQL = "sql_query"
    HIVE = "hive"
    IMPALA = "impala"
    SPARKSQL = "sparksql"

    # Code recipes - Spark variants
    PYSPARK = "pyspark"
    SPARK_SCALA = "spark_scala"
    SPARKR = "sparkr"

    # Code recipes - Other
    SHELL = "shell"

    # ML recipes (purple)
    PREDICTION_SCORING = "prediction_scoring"
    CLUSTERING_SCORING = "clustering_scoring"
    EVALUATION = "evaluation"

    # AI-assisted
    AI_ASSISTANT_GENERATE = "ai_assistant_generate"


class JoinType(Enum):
    """Join types for Join recipe."""

    INNER = "INNER"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    OUTER = "OUTER"
    CROSS = "CROSS"
    LEFT_ANTI = "LEFT_ANTI"
    RIGHT_ANTI = "RIGHT_ANTI"
    ADVANCED = "ADVANCED"


class JoinConditionType(Enum):
    """Join condition types for advanced joins."""

    EQ = "EQ"  # Equality (default)
    LTE = "LTE"  # Less than or equal
    LT = "LT"  # Less than
    GTE = "GTE"  # Greater than or equal
    GT = "GT"  # Greater than
    NE = "NE"  # Not equal
    WITHIN_RANGE = "WITHIN_RANGE"  # Range condition
    K_NEAREST = "K_NEAREST"  # K nearest neighbors
    K_NEAREST_INFERIOR = "K_NEAREST_INFERIOR"  # K nearest below
    CONTAINS = "CONTAINS"  # String contains
    STARTS_WITH = "STARTS_WITH"  # String starts with


class AggregationFunction(Enum):
    """Aggregation functions for Grouping and Window recipes."""

    # Basic aggregations
    SUM = "SUM"
    AVG = "AVG"
    MEAN = "MEAN"
    COUNT = "COUNT"
    COUNTD = "COUNTD"  # Count distinct
    MIN = "MIN"
    MAX = "MAX"
    FIRST = "FIRST"
    LAST = "LAST"

    # Statistical aggregations
    STD = "STD"
    STDDEV = "STDDEV"
    VAR = "VAR"
    VARIANCE = "VARIANCE"
    MEDIAN = "MEDIAN"
    MODE = "MODE"
    NUNIQUE = "NUNIQUE"

    # Percentile aggregations
    PERCENTILE_25 = "PERCENTILE_25"
    PERCENTILE_50 = "PERCENTILE_50"
    PERCENTILE_75 = "PERCENTILE_75"
    PERCENTILE_90 = "PERCENTILE_90"
    PERCENTILE_95 = "PERCENTILE_95"
    PERCENTILE_99 = "PERCENTILE_99"

    # Collection aggregations
    CONCAT = "CONCAT"
    COLLECT_LIST = "COLLECT_LIST"
    COLLECT_SET = "COLLECT_SET"


class WindowFunctionType(Enum):
    """Window function types for Window recipe."""

    # Ranking functions
    ROW_NUMBER = "ROW_NUMBER"
    RANK = "RANK"
    DENSE_RANK = "DENSE_RANK"
    NTILE = "NTILE"
    PERCENT_RANK = "PERCENT_RANK"
    CUME_DIST = "CUME_DIST"

    # Offset functions
    LAG = "LAG"
    LEAD = "LEAD"
    LAG_DIFF = "LAG_DIFF"
    LEAD_DIFF = "LEAD_DIFF"
    FIRST_VALUE = "FIRST_VALUE"
    LAST_VALUE = "LAST_VALUE"
    NTH_VALUE = "NTH_VALUE"

    # Running/cumulative aggregations
    RUNNING_SUM = "RUNNING_SUM"
    RUNNING_AVG = "RUNNING_AVG"
    RUNNING_MIN = "RUNNING_MIN"
    RUNNING_MAX = "RUNNING_MAX"
    RUNNING_COUNT = "RUNNING_COUNT"

    # Moving window aggregations
    MOVING_AVG = "MOVING_AVG"
    MOVING_SUM = "MOVING_SUM"
    MOVING_MIN = "MOVING_MIN"
    MOVING_MAX = "MOVING_MAX"
    MOVING_STDDEV = "MOVING_STDDEV"


class GeoJoinOperator(Enum):
    """Spatial operators for Geo Join recipe."""

    WITHIN_DISTANCE = "WITHIN_DISTANCE"
    BEYOND_DISTANCE = "BEYOND_DISTANCE"
    INTERSECTS = "INTERSECTS"
    CONTAINS = "CONTAINS"
    WITHIN = "WITHIN"
    TOUCHES = "TOUCHES"
    OVERLAPS = "OVERLAPS"
    CROSSES = "CROSSES"
    DISJOINT = "DISJOINT"


class DistanceUnit(Enum):
    """Distance units for geo operations."""

    METER = "METER"
    KILOMETER = "KILOMETER"
    FOOT = "FOOT"
    YARD = "YARD"
    MILE = "MILE"
    NAUTICAL_MILE = "NAUTICAL_MILE"


class SplitMode(Enum):
    """Split modes for Split recipe."""

    FILTER = "FILTER"  # Based on filter conditions
    RANDOM = "RANDOM"  # Random split
    COLUMN_VALUE = "COLUMN_VALUE"  # Based on column values
    PERCENTILE = "PERCENTILE"  # Based on percentiles


class SamplingMethod(Enum):
    """Sampling methods for Sampling recipe."""

    RANDOM = "RANDOM"
    RANDOM_FIXED = "RANDOM_FIXED"
    FIRST_ROWS = "FIRST_ROWS"
    LAST_ROWS = "LAST_ROWS"
    STRATIFIED = "STRATIFIED"
    CLASS_REBALANCE = "CLASS_REBALANCE"
    RESERVOIR = "RESERVOIR"


@dataclass
class Aggregation:
    """Aggregation specification for Grouping recipe."""

    column: str
    function: str  # SUM, AVG, COUNT, MIN, MAX, FIRST, LAST, etc.
    output_column: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "column": self.column,
            "type": self.function.upper(),
        }
        if self.output_column:
            result["outputColumn"] = self.output_column
        return result


@dataclass
class JoinKey:
    """Join key specification for Join recipe."""

    left_column: str
    right_column: str
    match_type: str = "EXACT"  # EXACT, FUZZY

    def to_dict(self) -> Dict[str, Any]:
        return {
            "left": {"column": self.left_column},
            "right": {"column": self.right_column},
            "matchType": self.match_type,
        }


@dataclass
class DataikuRecipe:
    """
    Represents a recipe in a Dataiku flow.

    Recipes are the transformation nodes that process data.
    They appear as circles in the Dataiku flow visualization.
    """

    name: str
    recipe_type: RecipeType
    inputs: List[str] = field(default_factory=list)  # Dataset names
    outputs: List[str] = field(default_factory=list)  # Dataset names

    # Prepare recipe specific
    steps: List[PrepareStep] = field(default_factory=list)

    # Grouping recipe specific
    group_keys: List[str] = field(default_factory=list)
    aggregations: List[Aggregation] = field(default_factory=list)

    # Join recipe specific
    join_type: JoinType = JoinType.LEFT
    join_keys: List[JoinKey] = field(default_factory=list)
    selected_columns: Optional[Dict[str, List[str]]] = None  # {left: [...], right: [...]}

    # Window recipe specific
    partition_columns: List[str] = field(default_factory=list)
    order_columns: List[str] = field(default_factory=list)
    window_aggregations: List[Dict[str, Any]] = field(default_factory=list)

    # Sampling recipe specific
    sampling_method: SamplingMethod = SamplingMethod.RANDOM
    sample_size: Optional[int] = None

    # Split recipe specific
    split_condition: Optional[str] = None

    # Sort recipe specific
    sort_columns: List[Dict[str, str]] = field(default_factory=list)  # [{column, order}]

    # Top N recipe specific
    top_n: Optional[int] = None
    ranking_column: Optional[str] = None

    # Python recipe specific
    code: Optional[str] = None

    # Composed settings object (optional, takes precedence over flat fields)
    settings: Optional[RecipeSettings] = None

    # Metadata
    source_lines: List[int] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "name": self.name,
            "type": self.recipe_type.value,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "source_lines": self.source_lines,
            "notes": self.notes,
        }

        if self.settings is not None:
            result.update(self.settings.to_display_dict())
        elif self.recipe_type == RecipeType.PREPARE:
            result["steps"] = [s.to_dict() for s in self.steps]
            result["step_count"] = len(self.steps)
        elif self.recipe_type == RecipeType.GROUPING:
            result["keys"] = self.group_keys
            result["aggregations"] = [a.to_dict() for a in self.aggregations]
        elif self.recipe_type == RecipeType.JOIN:
            result["join_type"] = self.join_type.value
            result["join_keys"] = [k.to_dict() for k in self.join_keys]
            if self.selected_columns:
                result["selected_columns"] = self.selected_columns
        elif self.recipe_type == RecipeType.PYTHON:
            result["code"] = self.code

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DataikuRecipe":
        """Reconstruct a DataikuRecipe from a dictionary (inverse of to_dict)."""
        recipe_type = RecipeType(data["type"])
        kwargs: Dict[str, Any] = {
            "name": data["name"],
            "recipe_type": recipe_type,
            "inputs": data.get("inputs", []),
            "outputs": data.get("outputs", []),
            "source_lines": data.get("source_lines", []),
            "notes": data.get("notes", []),
        }

        if recipe_type == RecipeType.PREPARE:
            kwargs["steps"] = [
                PrepareStep.from_dict(s) for s in data.get("steps", [])
            ]
        elif recipe_type == RecipeType.GROUPING:
            kwargs["group_keys"] = data.get("keys", [])
            kwargs["aggregations"] = [
                Aggregation(
                    column=a["column"],
                    function=a.get("type", a.get("function", "")),
                    output_column=a.get("outputColumn"),
                )
                for a in data.get("aggregations", [])
            ]
        elif recipe_type == RecipeType.JOIN:
            kwargs["join_type"] = JoinType(data["join_type"])
            kwargs["join_keys"] = [
                JoinKey(
                    left_column=k["left"]["column"],
                    right_column=k["right"]["column"],
                    match_type=k.get("matchType", "EXACT"),
                )
                for k in data.get("join_keys", [])
            ]
            if data.get("selected_columns"):
                kwargs["selected_columns"] = data["selected_columns"]
        elif recipe_type == RecipeType.PYTHON:
            kwargs["code"] = data.get("code")

        return cls(**kwargs)

    def to_api_dict(self) -> Dict[str, Any]:
        """Convert to Dataiku API-compatible dictionary."""
        base = {
            "type": self.recipe_type.value,
            "name": self.name,
            "inputs": [{"ref": inp} for inp in self.inputs],
            "outputs": [{"ref": out} for out in self.outputs],
        }

        settings = self._build_settings()
        if settings:
            base["settings"] = settings

        return base

    def to_json(self) -> Dict[str, Any]:
        """Convert to Dataiku API-compatible dictionary.

        Note: This method returns a dict, not a JSON string. It is an alias
        for ``to_api_dict()`` kept for backward compatibility.
        """
        return self.to_api_dict()

    def _build_settings(self) -> Dict[str, Any]:
        """Build recipe-specific settings.

        If a composed RecipeSettings object is set, it takes precedence
        over the flat fields. Otherwise, falls back to the legacy if/elif chain.
        """
        if self.settings is not None:
            return self.settings.to_dict()

        if self.recipe_type == RecipeType.PREPARE:
            return {
                "mode": "NORMAL",
                "steps": [s.to_json() for s in self.steps],
            }
        elif self.recipe_type == RecipeType.GROUPING:
            return {
                "keys": [{"column": k} for k in self.group_keys],
                "aggregations": [a.to_dict() for a in self.aggregations],
                "globalCount": False,
            }
        elif self.recipe_type == RecipeType.JOIN:
            settings = {
                "joinType": self.join_type.value,
                "joins": [k.to_dict() for k in self.join_keys],
            }
            if self.selected_columns:
                settings["selectedColumns"] = self.selected_columns
            return settings
        elif self.recipe_type == RecipeType.WINDOW:
            aggregations = []
            for agg in self.window_aggregations:
                entry = dict(agg)
                if "type" in entry and isinstance(entry["type"], WindowFunctionType):
                    entry["type"] = entry["type"].value
                aggregations.append(entry)
            return {
                "partitionColumns": [{"column": c} for c in self.partition_columns],
                "orderColumns": [{"column": c} for c in self.order_columns],
                "aggregations": aggregations,
            }
        elif self.recipe_type == RecipeType.SAMPLING:
            settings: Dict[str, Any] = {
                "samplingMethod": self.sampling_method.value,
            }
            if self.sample_size is not None:
                settings["sampleSize"] = self.sample_size
            return settings
        elif self.recipe_type == RecipeType.SPLIT:
            return {
                "splitMode": "FILTER",
                "condition": self.split_condition or "",
            }
        elif self.recipe_type == RecipeType.SORT:
            return {
                "sortColumns": self.sort_columns,
            }
        elif self.recipe_type == RecipeType.TOP_N:
            return {
                "topN": self.top_n or 10,
                "rankingColumn": self.ranking_column,
            }
        elif self.recipe_type == RecipeType.DISTINCT:
            return {
                "computeCount": False,
            }
        elif self.recipe_type == RecipeType.STACK:
            return {
                "mode": "UNION",
            }
        elif self.recipe_type == RecipeType.PYTHON:
            return {
                "code": self.code or "",
            }
        return {}

    def add_step(self, step: PrepareStep) -> None:
        """Add a step to a Prepare recipe."""
        if self.recipe_type != RecipeType.PREPARE:
            raise ValueError("Steps can only be added to Prepare recipes")
        self.steps.append(step)

    def add_aggregation(
        self,
        column: str,
        function: str,
        output_column: Optional[str] = None,
    ) -> None:
        """Add an aggregation to a Grouping recipe."""
        if self.recipe_type != RecipeType.GROUPING:
            raise ValueError("Aggregations can only be added to Grouping recipes")
        self.aggregations.append(
            Aggregation(column=column, function=function, output_column=output_column)
        )

    def add_join_key(
        self,
        left_column: str,
        right_column: str,
        match_type: str = "EXACT",
    ) -> None:
        """Add a join key to a Join recipe."""
        if self.recipe_type not in (RecipeType.JOIN, RecipeType.FUZZY_JOIN):
            raise ValueError("Join keys can only be added to Join recipes")
        self.join_keys.append(
            JoinKey(
                left_column=left_column,
                right_column=right_column,
                match_type=match_type,
            )
        )

    def add_note(self, note: str) -> None:
        """Add a note about this recipe."""
        self.notes.append(note)

    def get_step_summary(self) -> List[str]:
        """Get a summary of steps for Prepare recipes."""
        if self.recipe_type != RecipeType.PREPARE:
            return []
        return [step.get_description() for step in self.steps]

    @classmethod
    def create_prepare(
        cls,
        name: str,
        input_dataset: str,
        output_dataset: str,
        steps: Optional[List[PrepareStep]] = None,
    ) -> "DataikuRecipe":
        """Factory method to create a Prepare recipe."""
        return cls(
            name=name,
            recipe_type=RecipeType.PREPARE,
            inputs=[input_dataset],
            outputs=[output_dataset],
            steps=steps or [],
        )

    @classmethod
    def create_grouping(
        cls,
        name: str,
        input_dataset: str,
        output_dataset: str,
        keys: List[str],
        aggregations: Optional[List[Aggregation]] = None,
    ) -> "DataikuRecipe":
        """Factory method to create a Grouping recipe."""
        return cls(
            name=name,
            recipe_type=RecipeType.GROUPING,
            inputs=[input_dataset],
            outputs=[output_dataset],
            group_keys=keys,
            aggregations=aggregations or [],
        )

    @classmethod
    def create_join(
        cls,
        name: str,
        left_dataset: str,
        right_dataset: str,
        output_dataset: str,
        join_keys: List[JoinKey],
        join_type: JoinType = JoinType.LEFT,
    ) -> "DataikuRecipe":
        """Factory method to create a Join recipe."""
        return cls(
            name=name,
            recipe_type=RecipeType.JOIN,
            inputs=[left_dataset, right_dataset],
            outputs=[output_dataset],
            join_type=join_type,
            join_keys=join_keys,
        )

    @classmethod
    def create_python(
        cls,
        name: str,
        inputs: List[str],
        outputs: List[str],
        code: str,
    ) -> "DataikuRecipe":
        """Factory method to create a Python recipe."""
        return cls(
            name=name,
            recipe_type=RecipeType.PYTHON,
            inputs=inputs,
            outputs=outputs,
            code=code,
        )

    def __repr__(self) -> str:
        return f"DataikuRecipe(name='{self.name}', type={self.recipe_type.value})"
