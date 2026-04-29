"""Recipe settings classes for Dataiku DSS recipe types.

Each recipe type has its own settings class that encapsulates the
recipe-specific configuration. This uses composition to replace the
if/elif chain in DataikuRecipe._build_settings().
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

from py2dataiku.models.prepare_step import PrepareStep


def _default_engine_params() -> dict[str, Any]:
    """Return the default DSS engine parameters shared across recipe types."""
    return {
        "hive": {
            "skipPrerunValidate": False,
            "hiveconf": [],
            "inheritConf": "default",
        },
        "sqlPipelineParams": {
            "pipelineAllowMerge": True,
            "pipelineAllowStart": True,
        },
        "impala": {"forceStreamMode": True},
        "spark": {"inheritConf": "default", "sparkConf": []},
    }


class RecipeSettings(ABC):
    """Base class for recipe-specific settings."""

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Convert settings to a Dataiku API-compatible dictionary."""
        ...

    @abstractmethod
    def to_display_dict(self) -> dict[str, Any]:
        """Convert settings to a human-readable dictionary for to_dict() output."""
        ...

    @abstractmethod
    def to_dss_builder_args(self) -> dict[str, Any]:
        """Convert settings to a dict suitable for the DSS recipe builder API.

        The returned dict can be used to update recipe settings obtained from
        ``recipe.get_settings()`` when using the dataikuapi builder pattern::

            builder = project.new_recipe("shaker")
            builder.with_input("dataset_in")
            builder.with_output("dataset_out")
            recipe = builder.create()
            settings = recipe.get_settings()
            settings.update(recipe_settings.to_dss_builder_args())
            settings.save()
        """
        ...


@dataclass
class PrepareSettings(RecipeSettings):
    """Settings for a Prepare recipe."""

    steps: list[PrepareStep] = field(default_factory=list)
    mode: str = "NORMAL"

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "steps": [s.to_json() for s in self.steps],
        }

    def to_display_dict(self) -> dict[str, Any]:
        return {
            "steps": [s.to_dict() for s in self.steps],
            "step_count": len(self.steps),
        }

    def to_dss_builder_args(self) -> dict[str, Any]:
        steps = []
        for step in self.steps:
            step_config = {
                "metaType": step.meta_type,
                "type": step.processor_type.value if hasattr(step.processor_type, 'value') else str(step.processor_type),
                "disabled": step.disabled,
                "params": step.params,
                "preview": False,
                "alwaysShowComment": False,
                "comment": "",
            }
            steps.append(step_config)

        engine_params = _default_engine_params()
        engine_params["hive"]["addDkuUdf"] = False
        engine_params["hive"]["executionEngine"] = "HIVESERVER2"
        engine_params["spark"]["sparkConf"] = []
        engine_params["dkuHadoop"] = {"inheritConf": "default"}

        return {
            "steps": steps,
            "maxJobsPerCategory": {
                "PREPARE_FILTERING": 1,
                "PREPARE_PARSING": 1,
                "PREPARE_OTHERS": 1,
                "PREPARE_MERGE_COLUMNS": 1,
                "PREPARE_RESHAPING": 1,
                "PREPARE_EXPLODE": 1,
            },
            "engineParams": engine_params,
            "colSelection": {"mode": "ALL"},
            "virtualInputs": [],
            "filterExpression": {},
        }


@dataclass
class GroupingSettings(RecipeSettings):
    """Settings for a Grouping recipe."""

    keys: list[str] = field(default_factory=list)
    aggregations: list[Any] = field(default_factory=list)
    global_count: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "keys": [{"column": k} for k in self.keys],
            "aggregations": [a.to_dict() for a in self.aggregations],
            "globalCount": self.global_count,
        }

    def to_display_dict(self) -> dict[str, Any]:
        return {
            "keys": self.keys,
            "aggregations": [a.to_dict() for a in self.aggregations],
        }

    def to_dss_builder_args(self) -> dict[str, Any]:
        agg_flags = ("sum", "avg", "count", "min", "max", "stddev", "countDistinct")
        values = []
        for a in self.aggregations:
            entry: dict[str, Any] = {"column": a.column, "type": "COLUMN"}
            func = a.function.upper()
            for flag in agg_flags:
                entry[flag] = (func == flag.upper())
            values.append(entry)
        return {
            "engineParams": _default_engine_params(),
            "keys": [{"column": k} for k in self.keys],
            "values": values,
            "globalCount": self.global_count,
            "computeMode": "GLOBAL",
            "preFilter": {},
            "postFilter": {},
            "computedColumns": [],
        }


@dataclass
class JoinSettings(RecipeSettings):
    """Settings for a Join recipe."""

    join_type: str = "LEFT"
    join_keys: list[Any] = field(default_factory=list)
    selected_columns: Optional[dict[str, list[str]]] = None

    def to_dict(self) -> dict[str, Any]:
        settings: dict[str, Any] = {
            "joinType": self.join_type,
            "joins": [k.to_dict() for k in self.join_keys],
        }
        if self.selected_columns:
            settings["selectedColumns"] = self.selected_columns
        return settings

    def to_display_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "join_type": self.join_type,
            "join_keys": [k.to_dict() for k in self.join_keys],
        }
        if self.selected_columns:
            result["selected_columns"] = self.selected_columns
        return result

    def to_dss_builder_args(self) -> dict[str, Any]:
        num_inputs = max(len(self.join_keys) + 1, 2) if self.join_keys else 2
        joins = []
        if self.join_keys:
            conditions = []
            for k in self.join_keys:
                conditions.append({
                    "type": "EQ",
                    "column1": {"name": k.left_column, "table": 0},
                    "column2": {"name": k.right_column, "table": 1},
                })
            joins.append({
                "table1": 0,
                "table2": 1,
                "conditionsMode": "AND",
                "joinType": self.join_type,
                "conditions": conditions,
                "outerJoinOnTheLeft": True,
            })
        result: dict[str, Any] = {
            "engineParams": _default_engine_params(),
            "virtualInputs": [
                {"index": i, "computedColumns": [], "preFilter": {}}
                for i in range(num_inputs)
            ],
            "joins": joins,
            "postFilter": {},
            "enableAutoCastInJoinConditions": False,
            "computedColumns": [],
            "selectedColumns": self.selected_columns if self.selected_columns else [],
            "limitOutputColumns": False,
        }
        return result


@dataclass
class WindowSettings(RecipeSettings):
    """Settings for a Window recipe."""

    partition_columns: list[str] = field(default_factory=list)
    order_columns: list[str] = field(default_factory=list)
    aggregations: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
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

    def to_display_dict(self) -> dict[str, Any]:
        return self.to_dict()

    def to_dss_builder_args(self) -> dict[str, Any]:
        values = []
        for _i, agg in enumerate(self.aggregations):
            entry = dict(agg)
            agg_type = entry.pop("type", "")
            if hasattr(agg_type, "value"):
                agg_type = agg_type.value
            values.append({
                "column": entry.get("column", ""),
                "windowAggregation": agg_type,
                "outputColumn": entry.get("outputColumn", f"{entry.get('column', '')}_{agg_type}"),
                "windowDefinitionIndex": 0,
            })
        window_def: dict[str, Any] = {
            "partitionBy": self.partition_columns,
            "orderBy": self.order_columns,
            "frameType": "ROWS",
            "frameStart": {"mode": "UNBOUNDED_PRECEDING"},
            "frameEnd": {"mode": "CURRENT_ROW"},
        }
        return {
            "windowDefinitions": [window_def],
            "values": values,
        }


@dataclass
class SamplingSettings(RecipeSettings):
    """Settings for a Sampling recipe."""

    sampling_method: str = "RANDOM_FIXED_NB"
    sample_size: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        settings: dict[str, Any] = {
            "samplingMethod": self.sampling_method,
        }
        if self.sample_size is not None:
            settings["sampleSize"] = self.sample_size
        return settings

    def to_display_dict(self) -> dict[str, Any]:
        return self.to_dict()

    def to_dss_builder_args(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "samplingMethod": self.sampling_method,
            "targetRatio": 0.02,
            "seed": 1337,
            "ascendingOrder": True,
        }
        if self.sample_size is not None:
            result["maxRecords"] = self.sample_size
        return result


@dataclass
class SplitSettings(RecipeSettings):
    """Settings for a Split recipe."""

    split_mode: str = "FILTER"
    condition: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "splitMode": self.split_mode,
            "condition": self.condition,
        }

    def to_display_dict(self) -> dict[str, Any]:
        return self.to_dict()

    def to_dss_builder_args(self) -> dict[str, Any]:
        return {
            "mode": "VALUES",
            "splits": [
                {
                    "filter": {"conditions": [], "enabled": True},
                    "output": {},
                }
            ],
            "column": "",
            "defaultOutputIndex": -1,
        }


@dataclass
class SortSettings(RecipeSettings):
    """Settings for a Sort recipe."""

    sort_columns: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sortColumns": self.sort_columns,
        }

    def to_display_dict(self) -> dict[str, Any]:
        return self.to_dict()

    def to_dss_builder_args(self) -> dict[str, Any]:
        return {
            "engineParams": _default_engine_params(),
            "orders": [
                {
                    "column": sc.get("column", ""),
                    "ascending": sc.get("order", "asc").lower() != "desc",
                }
                for sc in self.sort_columns
            ],
            "preFilter": {},
            "computedColumns": [],
        }


@dataclass
class TopNSettings(RecipeSettings):
    """Settings for a Top N recipe."""

    top_n: int = 10
    ranking_column: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "topN": self.top_n,
            "rankingColumn": self.ranking_column,
        }

    def to_display_dict(self) -> dict[str, Any]:
        return self.to_dict()

    def to_dss_builder_args(self) -> dict[str, Any]:
        order_by = []
        if self.ranking_column:
            order_by.append({"column": self.ranking_column, "ascending": False})
        return {
            "limit": self.top_n,
            "orderBy": order_by,
            "groupBy": [],
        }


@dataclass
class DistinctSettings(RecipeSettings):
    """Settings for a Distinct recipe."""

    compute_count: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "computeCount": self.compute_count,
        }

    def to_display_dict(self) -> dict[str, Any]:
        return self.to_dict()

    def to_dss_builder_args(self) -> dict[str, Any]:
        return {
            "engineParams": _default_engine_params(),
            "columns": [],
            "keepAllColumns": True,
            "preFilter": {},
            "computedColumns": [],
            "postFilter": {},
        }


@dataclass
class StackSettings(RecipeSettings):
    """Settings for a Stack recipe."""

    mode: str = "UNION"

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
        }

    def to_display_dict(self) -> dict[str, Any]:
        return self.to_dict()

    def to_dss_builder_args(self) -> dict[str, Any]:
        dss_mode = "UNION_ALL" if self.mode == "UNION" else self.mode
        return {
            "mode": dss_mode,
            "virtualInputs": [{"index": 0}, {"index": 1}],
            "selectedColumns": [],
            "originColumn": {"name": "__dku_input_origin", "enabled": False},
        }


@dataclass
class PythonSettings(RecipeSettings):
    """Settings for a Python code recipe."""

    code: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
        }

    def to_display_dict(self) -> dict[str, Any]:
        return {"code": self.code}

    def to_dss_builder_args(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "envSelection": {"envMode": "INHERIT"},
            "pythonParams": {
                "pythonVersion": "python3",
                "runAsUser": False,
            },
        }


@dataclass
class PivotSettings(RecipeSettings):
    """Settings for a Pivot recipe."""

    row_columns: list[str] = field(default_factory=list)
    column_column: str = ""
    value_column: str = ""
    aggregation: str = "SUM"

    def to_dict(self) -> dict[str, Any]:
        return {
            "rowColumns": self.row_columns,
            "columnColumn": self.column_column,
            "valueColumn": self.value_column,
            "aggregation": self.aggregation,
        }

    def to_display_dict(self) -> dict[str, Any]:
        return self.to_dict()

    def to_dss_builder_args(self) -> dict[str, Any]:
        aggregations = []
        if self.value_column:
            aggregations.append({
                "column": self.value_column,
                "type": self.aggregation.lower(),
            })
        return {
            "keyColumns": self.row_columns,
            "pivotColumn": self.column_column,
            "aggregations": aggregations,
            "pivotColumnMaxValues": 100,
            "explicitValues": [],
        }


@dataclass
class SyncSettings(RecipeSettings):
    """Settings for a Sync recipe.

    Sync copies data from one dataset to another, optionally between
    different storage backends. Per docs/dataiku-reference/recipes/sync.md
    (https://doc.dataiku.com/dss/latest/other_recipes/sync.html).
    """

    engine: str = "DSS"
    """Execution engine. One of: ``DSS`` (DSS streaming, always available),
    ``SPARK``, ``SQL``, ``HIVE``, ``IMPALA``, or a fast-path engine name.
    Per docs/dataiku-reference/recipes/sync.md L39-L62."""

    write_mode: str = "OVERWRITE"
    """Output write mode. ``OVERWRITE`` replaces the existing dataset (default
    DSS behavior when re-running a sync). Per docs/dataiku-reference/recipes/sync.md."""

    schema_resync: str = "AUTO"
    """Schema resynchronization policy. ``AUTO`` keeps the output schema
    aligned with the input. Per docs/dataiku-reference/recipes/sync.md L19-L29."""

    partition_dependency: str = "EQUALS"
    """Partition dependency for partitioned syncs. ``EQUALS`` is the default
    DSS behavior — output partitions mirror input partitions one-to-one.
    Per docs/dataiku-reference/recipes/sync.md L31-L37."""

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine": self.engine,
            "writeMode": self.write_mode,
            "schemaResync": self.schema_resync,
            "partitionDependency": self.partition_dependency,
        }

    def to_display_dict(self) -> dict[str, Any]:
        return {
            "engine": self.engine,
            "write_mode": self.write_mode,
            "schema_resync": self.schema_resync,
            "partition_dependency": self.partition_dependency,
        }

    def to_dss_builder_args(self) -> dict[str, Any]:
        return {
            "engineParams": _default_engine_params(),
            "writeMode": self.write_mode,
        }


@dataclass
class FuzzyJoinSettings(RecipeSettings):
    """Settings for a Fuzzy Join recipe.

    Fuzzy join performs nearest-match joins where keys don't match exactly.
    Per docs/dataiku-reference/recipes/fuzzy-join.md
    (https://doc.dataiku.com/dss/latest/other_recipes/fuzzy-join.html).
    """

    join_type: str = "INNER"
    """Join type: ``INNER`` | ``OUTER`` | ``LEFT`` | ``RIGHT``. Per
    docs/dataiku-reference/recipes/fuzzy-join.md L17-L25."""

    join_keys: list[Any] = field(default_factory=list)
    """JoinKey-like objects describing per-pair fuzzy matching rules.
    Per docs/dataiku-reference/recipes/fuzzy-join.md L27-L31."""

    distance_metric: str = "DAMERAU_LEVENSHTEIN"
    """Distance metric used to score key similarity. One of:
    ``DAMERAU_LEVENSHTEIN`` | ``HAMMING`` | ``JACCARD`` | ``COSINE`` (text),
    ``EUCLIDEAN`` (numeric), ``GEOSPATIAL`` (geopoint), ``EQUALITY`` (strict).
    Per docs/dataiku-reference/recipes/fuzzy-join.md L33-L64."""

    threshold: float = 2.0
    """Match threshold; absolute or relative depending on
    :attr:`threshold_relative`. Per docs/dataiku-reference/recipes/fuzzy-join.md L66-L72."""

    threshold_relative: bool = False
    """Whether the threshold is interpreted as a percentage of the key length
    (``True``) or as an absolute distance value (``False``, the DSS default).
    Per docs/dataiku-reference/recipes/fuzzy-join.md L66-L72."""

    text_normalization: list[str] = field(default_factory=list)
    """Optional text-normalization steps applied before matching, e.g.
    ``CASE_INSENSITIVE``, ``REMOVE_PUNCTUATION``, ``CLEAR_SALUTATIONS``,
    ``CLEAR_STOP_WORDS``, ``STEM``, ``ALPHABETIC_SORT``.
    Per docs/dataiku-reference/recipes/fuzzy-join.md L45-L55."""

    output_meta: bool = False
    """If True, emit an additional meta column with per-row matching
    details (distance type, threshold, calculated distance, match
    result, joined values). Per docs/dataiku-reference/recipes/fuzzy-join.md L77-L86."""

    debug_mode: bool = False
    """If True, force a cross join and enable meta output for debugging
    unmatched rows. Per docs/dataiku-reference/recipes/fuzzy-join.md L88-L92."""

    selected_columns: Optional[dict[str, list[str]]] = None
    """Optional output-column selection. Per docs/dataiku-reference/recipes/fuzzy-join.md L94-L96."""

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "joinType": self.join_type,
            "joins": [k.to_dict() for k in self.join_keys],
            "distanceMetric": self.distance_metric,
            "threshold": self.threshold,
            "thresholdRelative": self.threshold_relative,
            "textNormalization": list(self.text_normalization),
            "outputMeta": self.output_meta,
            "debugMode": self.debug_mode,
        }
        if self.selected_columns:
            result["selectedColumns"] = self.selected_columns
        return result

    def to_display_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "join_type": self.join_type,
            "join_keys": [k.to_dict() for k in self.join_keys],
            "distance_metric": self.distance_metric,
            "threshold": self.threshold,
            "threshold_relative": self.threshold_relative,
            "text_normalization": list(self.text_normalization),
            "output_meta": self.output_meta,
            "debug_mode": self.debug_mode,
        }
        if self.selected_columns:
            result["selected_columns"] = self.selected_columns
        return result

    def to_dss_builder_args(self) -> dict[str, Any]:
        joins = []
        if self.join_keys:
            conditions = []
            for k in self.join_keys:
                conditions.append({
                    "type": "FUZZY",
                    "column1": {"name": k.left_column, "table": 0},
                    "column2": {"name": k.right_column, "table": 1},
                    "distanceMetric": self.distance_metric,
                    "threshold": self.threshold,
                    "thresholdRelative": self.threshold_relative,
                })
            joins.append({
                "table1": 0,
                "table2": 1,
                "conditionsMode": "AND",
                "joinType": self.join_type,
                "conditions": conditions,
                "outerJoinOnTheLeft": True,
            })
        return {
            "engineParams": _default_engine_params(),
            "virtualInputs": [
                {"index": 0, "computedColumns": [], "preFilter": {}},
                {"index": 1, "computedColumns": [], "preFilter": {}},
            ],
            "joins": joins,
            "postFilter": {},
            "computedColumns": [],
            "selectedColumns": self.selected_columns if self.selected_columns else [],
            "limitOutputColumns": False,
            "textNormalization": list(self.text_normalization),
            "outputMeta": self.output_meta,
            "debugMode": self.debug_mode,
        }


@dataclass
class GeoJoinSettings(RecipeSettings):
    """Settings for a Geo Join recipe.

    Geo join performs spatial joins between datasets containing geometry
    or geopoint columns. Per docs/dataiku-reference/recipes/geojoin.md
    (https://doc.dataiku.com/dss/latest/other_recipes/geojoin.html).
    """

    join_type: str = "INNER"
    """Join type: ``INNER`` | ``LEFT`` | ``RIGHT`` | ``FULL`` | ``CROSS``.
    Per docs/dataiku-reference/recipes/geojoin.md L11."""

    join_keys: list[Any] = field(default_factory=list)
    """JoinKey-like objects describing per-pair geospatial matching rules.
    Per docs/dataiku-reference/recipes/geojoin.md L51-L62."""

    spatial_operator: str = "INTERSECTS"
    """Spatial relation operator. One of: ``CONTAINS`` | ``IS_CONTAINED`` |
    ``WITHIN_DISTANCE`` | ``BEYOND_DISTANCE`` | ``INTERSECTS`` | ``TOUCHES`` |
    ``DISJOINT`` | ``STRICT_EQUALITY``.
    Per docs/dataiku-reference/recipes/geojoin.md L64-L74."""

    distance_value: Optional[float] = None
    """Distance value for ``WITHIN_DISTANCE`` / ``BEYOND_DISTANCE`` operators.
    Required for those operators, ignored otherwise.
    Per docs/dataiku-reference/recipes/geojoin.md L76."""

    distance_unit: str = "METER"
    """Distance unit: ``METER`` | ``KILOMETER`` | ``FOOT`` | ``YARD`` |
    ``MILE`` | ``NAUTICAL_MILE``. Per docs/dataiku-reference/recipes/geojoin.md L76."""

    selected_columns: Optional[dict[str, list[str]]] = None
    """Optional output-column selection. Per docs/dataiku-reference/recipes/geojoin.md L78-L80."""

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "joinType": self.join_type,
            "joins": [k.to_dict() for k in self.join_keys],
            "spatialOperator": self.spatial_operator,
            "distanceUnit": self.distance_unit,
        }
        if self.distance_value is not None:
            result["distanceValue"] = self.distance_value
        if self.selected_columns:
            result["selectedColumns"] = self.selected_columns
        return result

    def to_display_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "join_type": self.join_type,
            "join_keys": [k.to_dict() for k in self.join_keys],
            "spatial_operator": self.spatial_operator,
            "distance_unit": self.distance_unit,
        }
        if self.distance_value is not None:
            result["distance_value"] = self.distance_value
        if self.selected_columns:
            result["selected_columns"] = self.selected_columns
        return result

    def to_dss_builder_args(self) -> dict[str, Any]:
        joins = []
        if self.join_keys:
            conditions = []
            for k in self.join_keys:
                cond: dict[str, Any] = {
                    "type": self.spatial_operator,
                    "column1": {"name": k.left_column, "table": 0},
                    "column2": {"name": k.right_column, "table": 1},
                }
                if self.distance_value is not None:
                    cond["distanceValue"] = self.distance_value
                    cond["distanceUnit"] = self.distance_unit
                conditions.append(cond)
            joins.append({
                "table1": 0,
                "table2": 1,
                "conditionsMode": "AND",
                "joinType": self.join_type,
                "conditions": conditions,
                "outerJoinOnTheLeft": True,
            })
        return {
            "engineParams": _default_engine_params(),
            "virtualInputs": [
                {"index": 0, "computedColumns": [], "preFilter": {}},
                {"index": 1, "computedColumns": [], "preFilter": {}},
            ],
            "joins": joins,
            "postFilter": {},
            "computedColumns": [],
            "selectedColumns": self.selected_columns if self.selected_columns else [],
            "limitOutputColumns": False,
        }


@dataclass
class GenerateStatisticsSettings(RecipeSettings):
    """Settings for a Generate Statistics recipe.

    Generate Statistics profiles a dataset, producing summary statistics
    for selected columns. Maps from pandas ``df.describe()`` / ``df.info()``
    per CLAUDE.md. (No public DSS doc snapshot is captured under
    ``docs/dataiku-reference/recipes/`` — this class is built from the
    pandas mapping in ``mappings/pandas_mappings.py`` and DSS recipe-type
    ``generate_statistics``.)
    """

    columns: list[str] = field(default_factory=list)
    """Columns to profile. Empty list means all columns."""

    statistic_types: list[str] = field(default_factory=lambda: [
        "COUNT", "MEAN", "STDDEV", "MIN", "PERCENTILE_25",
        "PERCENTILE_50", "PERCENTILE_75", "MAX",
    ])
    """Statistics to compute. Defaults match pandas' ``df.describe()``
    output (count / mean / std / min / 25% / 50% / 75% / max)."""

    sampling_method: str = "FULL"
    """Sampling strategy: ``FULL`` (entire dataset, default) or
    ``HEAD_SEQUENTIAL`` / ``RANDOM_FIXED_NB`` / ``RANDOM_FIXED_RATIO``."""

    sample_size: Optional[int] = None
    """Sample size when sampling_method != ``FULL``. ``None`` uses DSS default."""

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "columns": list(self.columns),
            "statisticTypes": list(self.statistic_types),
            "samplingMethod": self.sampling_method,
        }
        if self.sample_size is not None:
            result["sampleSize"] = self.sample_size
        return result

    def to_display_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "columns": list(self.columns),
            "statistic_types": list(self.statistic_types),
            "sampling_method": self.sampling_method,
        }
        if self.sample_size is not None:
            result["sample_size"] = self.sample_size
        return result

    def to_dss_builder_args(self) -> dict[str, Any]:
        return {
            "engineParams": _default_engine_params(),
            "columns": list(self.columns),
            "statisticTypes": list(self.statistic_types),
            "samplingMethod": self.sampling_method,
            "sampleSize": self.sample_size if self.sample_size is not None else 10000,
        }
