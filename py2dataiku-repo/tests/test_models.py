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
