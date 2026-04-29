"""Tests for RecipeSettings composition pattern."""

import pytest

from py2dataiku.models.dataiku_recipe import (
    DataikuRecipe, RecipeType, Aggregation, JoinKey, JoinType,
)
from py2dataiku.models.prepare_step import PrepareStep, ProcessorType
from py2dataiku.models.recipe_settings import (
    RecipeSettings,
    PrepareSettings,
    GroupingSettings,
    JoinSettings,
    WindowSettings,
    SplitSettings,
    SortSettings,
    TopNSettings,
    DistinctSettings,
    StackSettings,
    PythonSettings,
    PivotSettings,
    SamplingSettings,
    SyncSettings,
    FuzzyJoinSettings,
    GeoJoinSettings,
    GenerateStatisticsSettings,
)


class TestPrepareSettings:
    """Tests for PrepareSettings."""

    def test_to_dict(self):
        step = PrepareStep(
            processor_type=ProcessorType.COLUMN_RENAMER,
            params={"column": "a", "new_name": "b"},
        )
        settings = PrepareSettings(steps=[step])
        d = settings.to_dict()
        assert d["mode"] == "NORMAL"
        assert len(d["steps"]) == 1

    def test_to_display_dict(self):
        step = PrepareStep(
            processor_type=ProcessorType.COLUMN_RENAMER,
            params={"column": "a", "new_name": "b"},
        )
        settings = PrepareSettings(steps=[step])
        d = settings.to_display_dict()
        assert "steps" in d
        assert d["step_count"] == 1

    def test_recipe_with_settings(self):
        """Recipe constructed with settings object produces correct API output."""
        step = PrepareStep(
            processor_type=ProcessorType.FILL_EMPTY_WITH_VALUE,
            params={"column": "x", "value": 0},
        )
        recipe = DataikuRecipe(
            name="prep",
            recipe_type=RecipeType.PREPARE,
            inputs=["in"],
            outputs=["out"],
            settings=PrepareSettings(steps=[step]),
        )
        api = recipe.to_api_dict()
        assert api["params"]["mode"] == "NORMAL"
        assert len(api["params"]["steps"]) == 1


class TestGroupingSettings:
    """Tests for GroupingSettings."""

    def test_to_dict(self):
        settings = GroupingSettings(
            keys=["category"],
            aggregations=[Aggregation(column="amount", function="SUM")],
        )
        d = settings.to_dict()
        assert d["keys"] == [{"column": "category"}]
        assert len(d["aggregations"]) == 1

    def test_recipe_with_settings(self):
        recipe = DataikuRecipe(
            name="group",
            recipe_type=RecipeType.GROUPING,
            inputs=["in"],
            outputs=["out"],
            settings=GroupingSettings(
                keys=["cat"],
                aggregations=[Aggregation(column="val", function="AVG")],
            ),
        )
        api = recipe.to_api_dict()
        assert api["params"]["keys"] == [{"column": "cat"}]


class TestJoinSettings:
    """Tests for JoinSettings."""

    def test_to_dict(self):
        settings = JoinSettings(
            join_type="LEFT",
            join_keys=[JoinKey(left_column="id", right_column="id")],
        )
        d = settings.to_dict()
        assert d["joinType"] == "LEFT"
        assert len(d["joins"]) == 1

    def test_with_selected_columns(self):
        settings = JoinSettings(
            join_type="INNER",
            join_keys=[JoinKey(left_column="id", right_column="id")],
            selected_columns={"left": ["id", "name"], "right": ["value"]},
        )
        d = settings.to_dict()
        assert "selectedColumns" in d


class TestWindowSettings:
    """Tests for WindowSettings."""

    def test_to_dict(self):
        settings = WindowSettings(
            partition_columns=["group"],
            order_columns=["date"],
            aggregations=[{"type": "RUNNING_SUM", "column": "value"}],
        )
        d = settings.to_dict()
        assert d["partitionColumns"] == [{"column": "group"}]
        assert d["orderColumns"] == [{"column": "date"}]


class TestSimpleSettings:
    """Tests for simple settings classes."""

    def test_split_settings(self):
        d = SplitSettings(condition="col > 5").to_dict()
        assert d["splitMode"] == "FILTER"
        assert d["condition"] == "col > 5"

    def test_sort_settings(self):
        d = SortSettings(
            sort_columns=[{"column": "name", "order": "ASC"}]
        ).to_dict()
        assert len(d["sortColumns"]) == 1

    def test_top_n_settings(self):
        d = TopNSettings(top_n=5, ranking_column="score").to_dict()
        assert d["topN"] == 5
        assert d["rankingColumn"] == "score"

    def test_distinct_settings(self):
        d = DistinctSettings(compute_count=True).to_dict()
        assert d["computeCount"] is True

    def test_stack_settings(self):
        d = StackSettings(mode="UNION").to_dict()
        assert d["mode"] == "UNION"

    def test_python_settings(self):
        d = PythonSettings(code="print('hello')").to_dict()
        assert d["code"] == "print('hello')"

    def test_sampling_settings(self):
        d = SamplingSettings(sampling_method="RANDOM_FIXED", sample_size=100).to_dict()
        assert d["samplingMethod"] == "RANDOM_FIXED"
        assert d["sampleSize"] == 100

    def test_pivot_settings(self):
        d = PivotSettings(
            row_columns=["a"],
            column_column="b",
            value_column="c",
            aggregation="SUM",
        ).to_dict()
        assert d["rowColumns"] == ["a"]


class TestBackwardCompatibility:
    """Verify that existing recipe construction still works."""

    def test_legacy_prepare(self):
        """Legacy flat-field construction produces same output as settings."""
        step = PrepareStep(
            processor_type=ProcessorType.COLUMN_RENAMER,
            params={"column": "a", "new_name": "b"},
        )
        legacy = DataikuRecipe(
            name="prep",
            recipe_type=RecipeType.PREPARE,
            inputs=["in"],
            outputs=["out"],
            steps=[step],
        )
        api = legacy.to_api_dict()
        assert "params" in api
        assert api["params"]["mode"] == "NORMAL"
        assert len(api["params"]["steps"]) == 1

    def test_legacy_grouping(self):
        legacy = DataikuRecipe(
            name="group",
            recipe_type=RecipeType.GROUPING,
            inputs=["in"],
            outputs=["out"],
            group_keys=["cat"],
            aggregations=[Aggregation(column="val", function="SUM")],
        )
        api = legacy.to_api_dict()
        assert api["params"]["keys"] == [{"column": "cat"}]

    def test_legacy_join(self):
        legacy = DataikuRecipe(
            name="join",
            recipe_type=RecipeType.JOIN,
            inputs=["left", "right"],
            outputs=["out"],
            join_type=JoinType.LEFT,
            join_keys=[JoinKey(left_column="id", right_column="id")],
        )
        api = legacy.to_api_dict()
        assert api["params"]["joinType"] == "LEFT"

    def test_legacy_python(self):
        legacy = DataikuRecipe(
            name="py",
            recipe_type=RecipeType.PYTHON,
            inputs=["in"],
            outputs=["out"],
            code="df = dataiku.Dataset('in').get_dataframe()",
        )
        api = legacy.to_api_dict()
        assert api["params"]["code"] != ""

    def test_settings_takes_precedence(self):
        """When both settings and flat fields are set, settings wins."""
        recipe = DataikuRecipe(
            name="prep",
            recipe_type=RecipeType.PREPARE,
            inputs=["in"],
            outputs=["out"],
            steps=[],  # flat field has no steps
            settings=PrepareSettings(steps=[
                PrepareStep(processor_type=ProcessorType.COLUMN_RENAMER, params={})
            ]),
        )
        api = recipe.to_api_dict()
        # settings has 1 step, flat has 0 - settings should win
        assert len(api["params"]["steps"]) == 1

    def test_factory_methods_still_work(self):
        """Factory methods produce valid recipes."""
        prep = DataikuRecipe.create_prepare("p", "in", "out")
        assert prep.recipe_type == RecipeType.PREPARE

        group = DataikuRecipe.create_grouping("g", "in", "out", keys=["k"])
        assert group.recipe_type == RecipeType.GROUPING

        join = DataikuRecipe.create_join(
            "j", "left", "right", "out",
            join_keys=[JoinKey(left_column="id", right_column="id")],
        )
        assert join.recipe_type == RecipeType.JOIN

        py = DataikuRecipe.create_python("p", ["in"], ["out"], code="pass")
        assert py.recipe_type == RecipeType.PYTHON

    def test_to_dict_display_with_settings(self):
        """to_dict() produces clean display output when using settings."""
        recipe = DataikuRecipe(
            name="prep",
            recipe_type=RecipeType.PREPARE,
            inputs=["in"],
            outputs=["out"],
            settings=PrepareSettings(steps=[
                PrepareStep(processor_type=ProcessorType.COLUMN_RENAMER, params={})
            ]),
        )
        d = recipe.to_dict()
        assert "steps" in d
        assert d["step_count"] == 1

    def test_no_settings_field_in_output(self):
        """The raw settings object should not appear in to_dict() or to_api_dict()."""
        recipe = DataikuRecipe(
            name="prep",
            recipe_type=RecipeType.PREPARE,
            inputs=["in"],
            outputs=["out"],
            settings=PrepareSettings(steps=[]),
        )
        d = recipe.to_dict()
        # The settings object itself should not leak into the dict
        assert "settings" not in d or not isinstance(d.get("settings"), RecipeSettings)


class TestSyncSettings:
    """Tests for SyncSettings (per docs/dataiku-reference/recipes/sync.md)."""

    def test_defaults(self):
        s = SyncSettings()
        assert s.engine == "DSS"
        assert s.write_mode == "OVERWRITE"
        assert s.schema_resync == "AUTO"
        assert s.partition_dependency == "EQUALS"

    def test_to_dict_round_trip(self):
        s = SyncSettings(engine="SPARK", write_mode="APPEND")
        d = s.to_dict()
        assert d["engine"] == "SPARK"
        assert d["writeMode"] == "APPEND"
        assert d["schemaResync"] == "AUTO"
        assert d["partitionDependency"] == "EQUALS"

    def test_to_display_dict_uses_snake_case(self):
        s = SyncSettings(engine="SQL")
        d = s.to_display_dict()
        assert d["engine"] == "SQL"
        assert d["write_mode"] == "OVERWRITE"
        assert d["schema_resync"] == "AUTO"

    def test_engine_field_round_trips(self):
        """Engine choice (the SYNC-specific knob) survives to_dict()."""
        s = SyncSettings(engine="HIVE")
        assert s.to_dict()["engine"] == "HIVE"

    def test_to_dss_builder_args(self):
        s = SyncSettings(write_mode="APPEND")
        args = s.to_dss_builder_args()
        assert "engineParams" in args
        assert args["writeMode"] == "APPEND"

    def test_recipe_with_settings(self):
        recipe = DataikuRecipe(
            name="sync_to_warehouse",
            recipe_type=RecipeType.SYNC,
            inputs=["staging"],
            outputs=["warehouse"],
            settings=SyncSettings(engine="SPARK"),
        )
        api = recipe.to_api_dict()
        assert api["params"]["engine"] == "SPARK"


class TestFuzzyJoinSettings:
    """Tests for FuzzyJoinSettings (per docs/dataiku-reference/recipes/fuzzy-join.md)."""

    def test_defaults(self):
        s = FuzzyJoinSettings()
        assert s.join_type == "INNER"
        assert s.distance_metric == "DAMERAU_LEVENSHTEIN"
        assert s.threshold == 2.0
        assert s.threshold_relative is False
        assert s.text_normalization == []
        assert s.output_meta is False
        assert s.debug_mode is False

    def test_to_dict(self):
        s = FuzzyJoinSettings(
            join_type="LEFT",
            join_keys=[JoinKey(left_column="name", right_column="company_name")],
            distance_metric="JACCARD",
            threshold=0.5,
            threshold_relative=True,
            text_normalization=["CASE_INSENSITIVE", "REMOVE_PUNCTUATION"],
            output_meta=True,
        )
        d = s.to_dict()
        assert d["joinType"] == "LEFT"
        assert d["distanceMetric"] == "JACCARD"
        assert d["threshold"] == 0.5
        assert d["thresholdRelative"] is True
        assert d["textNormalization"] == ["CASE_INSENSITIVE", "REMOVE_PUNCTUATION"]
        assert d["outputMeta"] is True
        assert len(d["joins"]) == 1

    def test_threshold_round_trip(self):
        """Threshold (the FUZZY_JOIN-specific knob) survives to_dict()."""
        s = FuzzyJoinSettings(threshold=4.5)
        assert s.to_dict()["threshold"] == 4.5

    def test_to_display_dict(self):
        s = FuzzyJoinSettings(
            join_keys=[JoinKey(left_column="a", right_column="b")],
            distance_metric="HAMMING",
        )
        d = s.to_display_dict()
        assert d["join_type"] == "INNER"
        assert d["distance_metric"] == "HAMMING"
        assert d["threshold_relative"] is False

    def test_to_dss_builder_args(self):
        s = FuzzyJoinSettings(
            join_keys=[JoinKey(left_column="x", right_column="y")],
            distance_metric="COSINE",
            threshold=3,
        )
        args = s.to_dss_builder_args()
        assert "engineParams" in args
        assert len(args["joins"]) == 1
        assert args["joins"][0]["conditions"][0]["distanceMetric"] == "COSINE"
        assert args["joins"][0]["conditions"][0]["threshold"] == 3

    def test_with_selected_columns(self):
        s = FuzzyJoinSettings(
            selected_columns={"left": ["id"], "right": ["name"]},
        )
        d = s.to_dict()
        assert d["selectedColumns"] == {"left": ["id"], "right": ["name"]}

    def test_recipe_with_settings(self):
        recipe = DataikuRecipe(
            name="fuzzy_join",
            recipe_type=RecipeType.FUZZY_JOIN,
            inputs=["a", "b"],
            outputs=["matched"],
            settings=FuzzyJoinSettings(
                join_keys=[JoinKey(left_column="name", right_column="name")],
                distance_metric="DAMERAU_LEVENSHTEIN",
                threshold=2,
            ),
        )
        api = recipe.to_api_dict()
        assert api["params"]["distanceMetric"] == "DAMERAU_LEVENSHTEIN"


class TestGeoJoinSettings:
    """Tests for GeoJoinSettings (per docs/dataiku-reference/recipes/geojoin.md)."""

    def test_defaults(self):
        s = GeoJoinSettings()
        assert s.join_type == "INNER"
        assert s.spatial_operator == "INTERSECTS"
        assert s.distance_value is None
        assert s.distance_unit == "METER"

    def test_to_dict_with_distance_operator(self):
        s = GeoJoinSettings(
            spatial_operator="WITHIN_DISTANCE",
            distance_value=5.0,
            distance_unit="KILOMETER",
            join_keys=[JoinKey(left_column="loc", right_column="store_loc")],
        )
        d = s.to_dict()
        assert d["spatialOperator"] == "WITHIN_DISTANCE"
        assert d["distanceValue"] == 5.0
        assert d["distanceUnit"] == "KILOMETER"
        assert len(d["joins"]) == 1

    def test_to_dict_omits_distance_when_unset(self):
        """For non-distance operators (CONTAINS, INTERSECTS, ...) distance_value is None."""
        s = GeoJoinSettings(spatial_operator="CONTAINS")
        d = s.to_dict()
        assert "distanceValue" not in d

    def test_spatial_operator_round_trip(self):
        """spatial_operator (the GEO_JOIN-specific knob) survives to_dict()."""
        s = GeoJoinSettings(spatial_operator="DISJOINT")
        assert s.to_dict()["spatialOperator"] == "DISJOINT"

    def test_to_display_dict(self):
        s = GeoJoinSettings(
            spatial_operator="CONTAINS",
            join_keys=[JoinKey(left_column="poly", right_column="point")],
        )
        d = s.to_display_dict()
        assert d["spatial_operator"] == "CONTAINS"
        assert d["distance_unit"] == "METER"

    def test_to_dss_builder_args_with_distance(self):
        s = GeoJoinSettings(
            spatial_operator="WITHIN_DISTANCE",
            distance_value=10,
            distance_unit="MILE",
            join_keys=[JoinKey(left_column="a", right_column="b")],
        )
        args = s.to_dss_builder_args()
        assert "engineParams" in args
        cond = args["joins"][0]["conditions"][0]
        assert cond["type"] == "WITHIN_DISTANCE"
        assert cond["distanceValue"] == 10
        assert cond["distanceUnit"] == "MILE"

    def test_recipe_with_settings(self):
        recipe = DataikuRecipe(
            name="geo_join",
            recipe_type=RecipeType.GEO_JOIN,
            inputs=["customers", "stores"],
            outputs=["nearest"],
            settings=GeoJoinSettings(
                spatial_operator="WITHIN_DISTANCE",
                distance_value=5,
                distance_unit="KILOMETER",
            ),
        )
        api = recipe.to_api_dict()
        assert api["params"]["spatialOperator"] == "WITHIN_DISTANCE"
        assert api["params"]["distanceValue"] == 5


class TestGenerateStatisticsSettings:
    """Tests for GenerateStatisticsSettings (df.describe() / df.info() mapping)."""

    def test_defaults(self):
        s = GenerateStatisticsSettings()
        assert s.columns == []
        # df.describe() default statistic set
        assert "MEAN" in s.statistic_types
        assert "PERCENTILE_50" in s.statistic_types
        assert s.sampling_method == "FULL"
        assert s.sample_size is None

    def test_to_dict(self):
        s = GenerateStatisticsSettings(
            columns=["price", "quantity"],
            statistic_types=["MEAN", "STDDEV"],
        )
        d = s.to_dict()
        assert d["columns"] == ["price", "quantity"]
        assert d["statisticTypes"] == ["MEAN", "STDDEV"]
        assert d["samplingMethod"] == "FULL"
        assert "sampleSize" not in d

    def test_to_dict_with_sample_size(self):
        s = GenerateStatisticsSettings(
            sampling_method="RANDOM_FIXED_NB", sample_size=1000
        )
        d = s.to_dict()
        assert d["samplingMethod"] == "RANDOM_FIXED_NB"
        assert d["sampleSize"] == 1000

    def test_columns_field_round_trips(self):
        """columns (the GENERATE_STATISTICS-specific knob) survives to_dict()."""
        s = GenerateStatisticsSettings(columns=["a", "b", "c"])
        assert s.to_dict()["columns"] == ["a", "b", "c"]

    def test_to_display_dict(self):
        s = GenerateStatisticsSettings(columns=["amount"])
        d = s.to_display_dict()
        assert d["columns"] == ["amount"]
        assert d["sampling_method"] == "FULL"
        assert "statistic_types" in d

    def test_to_dss_builder_args(self):
        s = GenerateStatisticsSettings(
            columns=["price"], statistic_types=["MEAN", "MAX"]
        )
        args = s.to_dss_builder_args()
        assert args["columns"] == ["price"]
        assert args["statisticTypes"] == ["MEAN", "MAX"]
        assert "engineParams" in args

    def test_recipe_with_settings(self):
        recipe = DataikuRecipe(
            name="profile",
            recipe_type=RecipeType.GENERATE_STATISTICS,
            inputs=["raw"],
            outputs=["stats"],
            settings=GenerateStatisticsSettings(columns=["price"]),
        )
        api = recipe.to_api_dict()
        assert api["params"]["columns"] == ["price"]
