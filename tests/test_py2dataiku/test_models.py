"""Tests for py2dataiku data models."""

import pytest

from py2dataiku.models.dataiku_dataset import DataikuDataset, DatasetType, ColumnSchema
from py2dataiku.models.dataiku_recipe import (
    DataikuRecipe,
    RecipeType,
    JoinType,
    JoinKey,
    Aggregation,
)
from py2dataiku.models.dataiku_flow import DataikuFlow
from py2dataiku.models.prepare_step import PrepareStep, ProcessorType, StringTransformerMode
from py2dataiku.models.transformation import Transformation, TransformationType


class TestDataikuDataset:
    """Tests for DataikuDataset model."""

    def test_create_dataset(self):
        ds = DataikuDataset(name="test_dataset")
        assert ds.name == "test_dataset"
        assert ds.dataset_type == DatasetType.INTERMEDIATE

    def test_input_dataset(self):
        ds = DataikuDataset(name="input", dataset_type=DatasetType.INPUT)
        assert ds.is_input
        assert not ds.is_output

    def test_output_dataset(self):
        ds = DataikuDataset(name="output", dataset_type=DatasetType.OUTPUT)
        assert ds.is_output
        assert not ds.is_input

    def test_add_column(self):
        ds = DataikuDataset(name="test")
        ds.add_column("id", "bigint", nullable=False)
        ds.add_column("name", "string")
        assert len(ds.schema) == 2
        assert ds.schema[0].name == "id"
        assert ds.schema[0].nullable is False

    def test_to_dict(self):
        ds = DataikuDataset(
            name="test",
            dataset_type=DatasetType.INPUT,
            source_variable="df",
        )
        d = ds.to_dict()
        assert d["name"] == "test"
        assert d["type"] == "input"
        assert d["source_variable"] == "df"


class TestPrepareStep:
    """Tests for PrepareStep model."""

    def test_fill_empty(self):
        step = PrepareStep.fill_empty("col", 0)
        assert step.processor_type == ProcessorType.FILL_EMPTY_WITH_VALUE
        assert step.params["column"] == "col"
        assert step.params["value"] == "0"

    def test_rename_columns(self):
        step = PrepareStep.rename_columns({"old": "new"})
        assert step.processor_type == ProcessorType.COLUMN_RENAMER
        assert step.params["renamings"] == [{"from": "old", "to": "new"}]

    def test_delete_columns(self):
        step = PrepareStep.delete_columns(["col1", "col2"])
        assert step.processor_type == ProcessorType.COLUMN_DELETER
        assert step.params["columns"] == ["col1", "col2"]

    def test_string_transform(self):
        step = PrepareStep.string_transform("name", StringTransformerMode.LOWERCASE)
        assert step.processor_type == ProcessorType.STRING_TRANSFORMER
        assert step.params["column"] == "name"
        assert step.params["mode"] == "TO_LOWER"

    def test_to_json(self):
        step = PrepareStep.fill_empty("col", 0)
        j = step.to_json()
        assert j["metaType"] == "PROCESSOR"
        assert j["type"] == "FillEmptyWithValue"
        assert j["disabled"] is False

    def test_get_description(self):
        step = PrepareStep.fill_empty("age", 0)
        desc = step.get_description()
        assert "age" in desc
        assert "0" in desc


class TestDataikuRecipe:
    """Tests for DataikuRecipe model."""

    def test_create_prepare(self):
        recipe = DataikuRecipe.create_prepare(
            name="prepare_1",
            input_dataset="raw",
            output_dataset="cleaned",
        )
        assert recipe.recipe_type == RecipeType.PREPARE
        assert recipe.inputs == ["raw"]
        assert recipe.outputs == ["cleaned"]

    def test_create_join(self):
        recipe = DataikuRecipe.create_join(
            name="join_1",
            left_dataset="left",
            right_dataset="right",
            output_dataset="joined",
            join_keys=[JoinKey("id", "id")],
            join_type=JoinType.LEFT,
        )
        assert recipe.recipe_type == RecipeType.JOIN
        assert recipe.join_type == JoinType.LEFT
        assert len(recipe.join_keys) == 1

    def test_create_grouping(self):
        recipe = DataikuRecipe.create_grouping(
            name="agg_1",
            input_dataset="data",
            output_dataset="aggregated",
            keys=["category"],
            aggregations=[Aggregation("amount", "SUM")],
        )
        assert recipe.recipe_type == RecipeType.GROUPING
        assert recipe.group_keys == ["category"]
        assert len(recipe.aggregations) == 1

    def test_add_step(self):
        recipe = DataikuRecipe.create_prepare("r", "in", "out")
        step = PrepareStep.fill_empty("col", 0)
        recipe.add_step(step)
        assert len(recipe.steps) == 1

    def test_add_step_wrong_type(self):
        recipe = DataikuRecipe(name="join", recipe_type=RecipeType.JOIN)
        step = PrepareStep.fill_empty("col", 0)
        with pytest.raises(ValueError):
            recipe.add_step(step)

    def test_to_json(self):
        recipe = DataikuRecipe.create_prepare("r", "in", "out")
        recipe.add_step(PrepareStep.fill_empty("col", 0))
        j = recipe.to_json()
        assert j["type"] == "prepare"
        assert j["name"] == "r"
        assert len(j["settings"]["steps"]) == 1


class TestDataikuFlow:
    """Tests for DataikuFlow model."""

    def test_create_flow(self):
        flow = DataikuFlow(name="test_flow")
        assert flow.name == "test_flow"
        assert len(flow.datasets) == 0
        assert len(flow.recipes) == 0

    def test_add_dataset(self):
        flow = DataikuFlow()
        ds = DataikuDataset(name="data", dataset_type=DatasetType.INPUT)
        flow.add_dataset(ds)
        assert len(flow.datasets) == 1
        assert flow.get_dataset("data") == ds

    def test_add_recipe(self):
        flow = DataikuFlow()
        recipe = DataikuRecipe.create_prepare("prep", "in", "out")
        flow.add_recipe(recipe)
        assert len(flow.recipes) == 1
        # Should auto-create datasets
        assert flow.get_dataset("in") is not None
        assert flow.get_dataset("out") is not None

    def test_get_recipes_by_type(self):
        flow = DataikuFlow()
        flow.add_recipe(DataikuRecipe.create_prepare("p1", "a", "b"))
        flow.add_recipe(DataikuRecipe.create_prepare("p2", "b", "c"))
        flow.add_recipe(
            DataikuRecipe(name="j1", recipe_type=RecipeType.JOIN, inputs=["c", "d"], outputs=["e"])
        )

        prepare_recipes = flow.get_recipes_by_type(RecipeType.PREPARE)
        assert len(prepare_recipes) == 2

        join_recipes = flow.get_recipes_by_type(RecipeType.JOIN)
        assert len(join_recipes) == 1

    def test_to_yaml(self):
        flow = DataikuFlow(name="test")
        flow.add_recipe(DataikuRecipe.create_prepare("prep", "in", "out"))
        yaml_str = flow.to_yaml()
        assert "test" in yaml_str
        assert "prep" in yaml_str

    def test_validate(self):
        flow = DataikuFlow()
        flow.add_recipe(DataikuRecipe.create_prepare("prep", "in", "out"))
        result = flow.validate()
        assert result["valid"] is True

    def test_get_summary(self):
        flow = DataikuFlow(name="test_flow")
        flow.add_recipe(DataikuRecipe.create_prepare("prep", "in", "out"))
        summary = flow.get_summary()
        assert "test_flow" in summary
        assert "Datasets: 2" in summary
        assert "Recipes: 1" in summary


class TestDataikuFlowValidation:
    """Tests for DataikuFlow validation edge cases."""

    def test_validate_empty_flow(self):
        """Test validation of a flow with no recipes."""
        flow = DataikuFlow(name="empty")
        result = flow.validate()
        assert result["valid"] is True

    def test_validate_orphan_datasets(self):
        """Test validation detects orphan datasets."""
        flow = DataikuFlow(name="orphan_test")
        ds = DataikuDataset(name="orphan", dataset_type=DatasetType.INTERMEDIATE)
        flow.add_dataset(ds)
        result = flow.validate()
        # Intermediate datasets not connected to any recipe should produce a warning
        if "warnings" in result and result["warnings"]:
            warnings = result["warnings"]
            assert any("orphan" in w.get("message", "").lower() for w in warnings)

    def test_duplicate_recipe_names(self):
        """Test that duplicate recipe names can be detected."""
        flow = DataikuFlow(name="dup_test")
        flow.add_recipe(DataikuRecipe.create_prepare("prep", "a", "b"))
        flow.add_recipe(DataikuRecipe.create_prepare("prep", "c", "d"))
        # Both recipes exist
        assert len(flow.recipes) == 2

    def test_flow_len(self):
        """Test __len__ returns recipe count."""
        flow = DataikuFlow()
        assert len(flow) == 0
        flow.add_recipe(DataikuRecipe.create_prepare("p1", "a", "b"))
        assert len(flow) == 1
        flow.add_recipe(DataikuRecipe.create_prepare("p2", "b", "c"))
        assert len(flow) == 2

    def test_flow_iter(self):
        """Test __iter__ yields recipes."""
        flow = DataikuFlow()
        r1 = DataikuRecipe.create_prepare("p1", "a", "b")
        r2 = DataikuRecipe.create_prepare("p2", "b", "c")
        flow.add_recipe(r1)
        flow.add_recipe(r2)
        recipes = list(flow)
        assert len(recipes) == 2
        assert recipes[0].name == "p1"
        assert recipes[1].name == "p2"


class TestRecipeValidation:
    """Tests for recipe validation edge cases."""

    def test_recipe_with_no_inputs(self):
        """Test recipe with empty inputs."""
        recipe = DataikuRecipe(
            name="no_input",
            recipe_type=RecipeType.PYTHON,
            inputs=[],
            outputs=["out"],
        )
        assert len(recipe.inputs) == 0

    def test_recipe_with_no_outputs(self):
        """Test recipe with empty outputs."""
        recipe = DataikuRecipe(
            name="no_output",
            recipe_type=RecipeType.PYTHON,
            inputs=["in"],
            outputs=[],
        )
        assert len(recipe.outputs) == 0

    def test_prepare_recipe_step_types(self):
        """Test that prepare recipe validates step processor types."""
        recipe = DataikuRecipe.create_prepare("prep", "in", "out")
        step = PrepareStep(
            processor_type=ProcessorType.COLUMN_RENAMER,
            params={"renamings": [{"from": "a", "to": "b"}]},
        )
        recipe.add_step(step)
        assert recipe.steps[0].processor_type == ProcessorType.COLUMN_RENAMER


class TestTransformation:
    """Tests for Transformation model."""

    def test_read_csv(self):
        trans = Transformation.read_csv("df", "data.csv", line=1)
        assert trans.transformation_type == TransformationType.READ_DATA
        assert trans.target_dataframe == "df"
        assert trans.parameters["filepath"] == "data.csv"

    def test_fillna(self):
        trans = Transformation.fillna("df", "col", 0)
        assert trans.transformation_type == TransformationType.FILL_NA
        assert trans.columns == ["col"]
        assert trans.suggested_processor == "FillEmptyWithValue"

    def test_merge(self):
        trans = Transformation.merge(
            left="df1",
            right="df2",
            target="merged",
            on=["id"],
            how="left",
        )
        assert trans.transformation_type == TransformationType.MERGE
        assert trans.parameters["right"] == "df2"
        assert trans.parameters["how"] == "left"
        assert trans.suggested_recipe == "join"

    def test_groupby_agg(self):
        trans = Transformation.groupby_agg(
            dataframe="df",
            target="agg",
            keys=["category"],
            aggregations={"amount": "sum"},
        )
        assert trans.transformation_type == TransformationType.GROUPBY
        assert trans.columns == ["category"]
        assert trans.suggested_recipe == "grouping"


class TestRecipeApiDictStructure:
    """Tests for to_api_dict() / to_json() structure for each recipe type."""

    def test_prepare_api_dict(self):
        recipe = DataikuRecipe.create_prepare("p", "in", "out")
        recipe.add_step(PrepareStep.fill_empty("col", 0))
        api = recipe.to_api_dict()
        assert api["type"] == "prepare"
        assert api["settings"]["mode"] == "NORMAL"
        assert isinstance(api["settings"]["steps"], list)

    def test_grouping_api_dict(self):
        recipe = DataikuRecipe.create_grouping(
            "g", "in", "out", keys=["cat"],
            aggregations=[Aggregation("val", "SUM")]
        )
        api = recipe.to_api_dict()
        assert api["type"] == "grouping"
        assert api["settings"]["keys"] == [{"column": "cat"}]
        assert api["settings"]["globalCount"] is False

    def test_join_api_dict(self):
        recipe = DataikuRecipe.create_join(
            "j", "left", "right", "out",
            join_keys=[JoinKey("id", "id")],
            join_type=JoinType.INNER,
        )
        api = recipe.to_api_dict()
        assert api["type"] == "join"
        assert api["settings"]["joinType"] == "INNER"
        assert len(api["settings"]["joins"]) == 1

    def test_python_api_dict(self):
        recipe = DataikuRecipe.create_python(
            "py", ["in"], ["out"], code="import dataiku"
        )
        api = recipe.to_api_dict()
        assert api["type"] == "python"
        assert api["settings"]["code"] == "import dataiku"

    def test_split_api_dict(self):
        recipe = DataikuRecipe(
            name="split", recipe_type=RecipeType.SPLIT,
            inputs=["in"], outputs=["out"],
            split_condition="value > 100",
        )
        api = recipe.to_api_dict()
        assert api["type"] == "split"
        assert api["settings"]["splitMode"] == "FILTER"
        assert api["settings"]["condition"] == "value > 100"

    def test_sort_api_dict(self):
        recipe = DataikuRecipe(
            name="sort", recipe_type=RecipeType.SORT,
            inputs=["in"], outputs=["out"],
            sort_columns=[{"column": "name", "order": "ASC"}],
        )
        api = recipe.to_api_dict()
        assert api["type"] == "sort"
        assert len(api["settings"]["sortColumns"]) == 1

    def test_distinct_api_dict(self):
        recipe = DataikuRecipe(
            name="distinct", recipe_type=RecipeType.DISTINCT,
            inputs=["in"], outputs=["out"],
        )
        api = recipe.to_api_dict()
        assert api["type"] == "distinct"
        assert api["settings"]["computeCount"] is False

    def test_stack_api_dict(self):
        recipe = DataikuRecipe(
            name="stack", recipe_type=RecipeType.STACK,
            inputs=["a", "b"], outputs=["out"],
        )
        api = recipe.to_api_dict()
        assert api["type"] == "stack"
        assert api["settings"]["mode"] == "UNION"

    def test_top_n_api_dict(self):
        recipe = DataikuRecipe(
            name="topn", recipe_type=RecipeType.TOP_N,
            inputs=["in"], outputs=["out"],
            top_n=5, ranking_column="score",
        )
        api = recipe.to_api_dict()
        assert api["type"] == "topn"
        assert api["settings"]["topN"] == 5
        assert api["settings"]["rankingColumn"] == "score"

    def test_window_api_dict(self):
        recipe = DataikuRecipe(
            name="window", recipe_type=RecipeType.WINDOW,
            inputs=["in"], outputs=["out"],
            partition_columns=["group"],
            order_columns=["date"],
            window_aggregations=[{"type": "RUNNING_SUM", "column": "value"}],
        )
        api = recipe.to_api_dict()
        assert api["type"] == "window"
        assert api["settings"]["partitionColumns"] == [{"column": "group"}]

    def test_sampling_api_dict(self):
        from py2dataiku.models.dataiku_recipe import SamplingMethod
        recipe = DataikuRecipe(
            name="sample", recipe_type=RecipeType.SAMPLING,
            inputs=["in"], outputs=["out"],
            sampling_method=SamplingMethod.RANDOM_FIXED,
            sample_size=1000,
        )
        api = recipe.to_api_dict()
        assert api["type"] == "sampling"
        assert api["settings"]["samplingMethod"] == "RANDOM_FIXED"
        assert api["settings"]["sampleSize"] == 1000


class TestRecipeAddMethods:
    """Tests for recipe add methods."""

    def test_add_aggregation(self):
        recipe = DataikuRecipe.create_grouping("g", "in", "out", keys=["k"])
        recipe.add_aggregation("val", "SUM", output_column="total")
        assert len(recipe.aggregations) == 1
        assert recipe.aggregations[0].output_column == "total"

    def test_add_aggregation_wrong_type(self):
        recipe = DataikuRecipe.create_prepare("p", "in", "out")
        with pytest.raises(ValueError, match="Grouping"):
            recipe.add_aggregation("val", "SUM")

    def test_add_join_key(self):
        recipe = DataikuRecipe(
            name="j", recipe_type=RecipeType.JOIN,
            inputs=["a", "b"], outputs=["out"],
        )
        recipe.add_join_key("id_left", "id_right")
        assert len(recipe.join_keys) == 1
        assert recipe.join_keys[0].left_column == "id_left"

    def test_add_join_key_wrong_type(self):
        recipe = DataikuRecipe.create_prepare("p", "in", "out")
        with pytest.raises(ValueError, match="Join"):
            recipe.add_join_key("a", "b")

    def test_add_note(self):
        recipe = DataikuRecipe.create_prepare("p", "in", "out")
        recipe.add_note("This is a note")
        assert len(recipe.notes) == 1
        assert recipe.notes[0] == "This is a note"

    def test_get_step_summary(self):
        recipe = DataikuRecipe.create_prepare("p", "in", "out")
        recipe.add_step(PrepareStep.fill_empty("col", 0))
        summary = recipe.get_step_summary()
        assert len(summary) == 1
        assert isinstance(summary[0], str)

    def test_get_step_summary_non_prepare(self):
        recipe = DataikuRecipe(
            name="j", recipe_type=RecipeType.JOIN,
            inputs=["a", "b"], outputs=["out"],
        )
        assert recipe.get_step_summary() == []


class TestFlowZones:
    """Tests for FlowZone functionality."""

    def test_add_zone(self):
        from py2dataiku.models.dataiku_flow import FlowZone
        flow = DataikuFlow(name="test")
        zone = FlowZone(name="input_zone", color="#ff0000")
        flow.add_zone(zone)
        assert len(flow.zones) == 1
        assert flow.get_zone("input_zone") is not None

    def test_get_zone_missing(self):
        flow = DataikuFlow(name="test")
        assert flow.get_zone("nonexistent") is None

    def test_zone_add_dataset(self):
        from py2dataiku.models.dataiku_flow import FlowZone
        zone = FlowZone(name="test")
        zone.add_dataset("ds1")
        zone.add_dataset("ds1")  # duplicate should not be added
        assert zone.datasets == ["ds1"]

    def test_zone_add_recipe(self):
        from py2dataiku.models.dataiku_flow import FlowZone
        zone = FlowZone(name="test")
        zone.add_recipe("r1")
        zone.add_recipe("r1")  # duplicate
        assert zone.recipes == ["r1"]

    def test_zone_to_dict_and_from_dict(self):
        from py2dataiku.models.dataiku_flow import FlowZone
        zone = FlowZone(name="z1", color="#aabbcc", datasets=["d1"], recipes=["r1"])
        d = zone.to_dict()
        restored = FlowZone.from_dict(d)
        assert restored.name == "z1"
        assert restored.color == "#aabbcc"
        assert restored.datasets == ["d1"]


class TestFlowFromDict:
    """Tests for DataikuFlow.from_dict round-trip."""

    def test_round_trip(self):
        flow = DataikuFlow(name="round_trip")
        flow.add_dataset(DataikuDataset(name="input", dataset_type=DatasetType.INPUT))
        flow.add_recipe(DataikuRecipe.create_prepare("prep", "input", "output"))

        d = flow.to_dict()
        restored = DataikuFlow.from_dict(d)
        assert restored.name == "round_trip"
        assert len(restored.recipes) == 1
        assert len(restored.datasets) == 2

    def test_round_trip_json(self):
        flow = DataikuFlow(name="json_test")
        flow.add_recipe(DataikuRecipe.create_prepare("p", "a", "b"))
        json_str = flow.to_json()
        restored = DataikuFlow.from_json(json_str)
        assert restored.name == "json_test"

    def test_round_trip_yaml(self):
        flow = DataikuFlow(name="yaml_test")
        flow.add_recipe(DataikuRecipe.create_prepare("p", "a", "b"))
        yaml_str = flow.to_yaml()
        restored = DataikuFlow.from_yaml(yaml_str)
        assert restored.name == "yaml_test"
