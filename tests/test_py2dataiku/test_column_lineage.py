"""Tests for column lineage tracking."""

import pytest

from py2dataiku.models.dataiku_flow import DataikuFlow, ColumnLineage
from py2dataiku.models.dataiku_dataset import DataikuDataset, DatasetType
from py2dataiku.models.dataiku_recipe import (
    DataikuRecipe, RecipeType, Aggregation, JoinKey, JoinType,
)
from py2dataiku.models.prepare_step import PrepareStep, ProcessorType


class TestColumnLineageBasic:
    """Basic column lineage tests."""

    def test_passthrough_column(self):
        """Column that passes through a recipe without transformation."""
        flow = DataikuFlow(name="test")
        flow.add_dataset(DataikuDataset(name="input", dataset_type=DatasetType.INPUT))
        flow.add_recipe(DataikuRecipe(
            name="prep",
            recipe_type=RecipeType.PREPARE,
            inputs=["input"],
            outputs=["output"],
        ))

        lineage = flow.get_column_lineage("age", dataset="output")
        assert lineage.column == "age"
        assert lineage.origin_column == "age"
        assert lineage.origin_dataset == "input"
        assert lineage.final_dataset == "output"
        assert lineage.transformations == []

    def test_renamed_column(self):
        """Column that was renamed in a Prepare recipe."""
        flow = DataikuFlow(name="test")
        flow.add_dataset(DataikuDataset(name="input", dataset_type=DatasetType.INPUT))
        flow.add_recipe(DataikuRecipe(
            name="prep",
            recipe_type=RecipeType.PREPARE,
            inputs=["input"],
            outputs=["output"],
            steps=[
                PrepareStep(
                    processor_type=ProcessorType.COLUMN_RENAMER,
                    params={"column": "old_name", "new_name": "new_name"},
                ),
            ],
        ))

        lineage = flow.get_column_lineage("new_name", dataset="output")
        assert lineage.origin_column == "old_name"
        assert lineage.origin_dataset == "input"
        assert len(lineage.transformations) == 1
        assert lineage.transformations[0]["type"] == "rename"
        assert lineage.transformations[0]["from"] == "old_name"
        assert lineage.transformations[0]["to"] == "new_name"

    def test_copied_column(self):
        """Column created by copying another."""
        flow = DataikuFlow(name="test")
        flow.add_dataset(DataikuDataset(name="input", dataset_type=DatasetType.INPUT))
        flow.add_recipe(DataikuRecipe(
            name="prep",
            recipe_type=RecipeType.PREPARE,
            inputs=["input"],
            outputs=["output"],
            steps=[
                PrepareStep(
                    processor_type=ProcessorType.COLUMN_COPIER,
                    params={"column": "source_col", "new_column": "copied_col"},
                ),
            ],
        ))

        lineage = flow.get_column_lineage("copied_col", dataset="output")
        assert lineage.origin_column == "source_col"
        assert len(lineage.transformations) == 1
        assert lineage.transformations[0]["type"] == "copy"

    def test_transformed_column(self):
        """Column that was transformed in place."""
        flow = DataikuFlow(name="test")
        flow.add_dataset(DataikuDataset(name="input", dataset_type=DatasetType.INPUT))
        flow.add_recipe(DataikuRecipe(
            name="prep",
            recipe_type=RecipeType.PREPARE,
            inputs=["input"],
            outputs=["output"],
            steps=[
                PrepareStep(
                    processor_type=ProcessorType.STRING_TRANSFORMER,
                    params={"column": "name", "mode": "TO_UPPER"},
                ),
            ],
        ))

        lineage = flow.get_column_lineage("name", dataset="output")
        assert lineage.origin_column == "name"
        assert len(lineage.transformations) == 1
        assert lineage.transformations[0]["type"] == "StringTransformer"

    def test_empty_flow_raises(self):
        """Getting lineage on an empty flow raises ValueError."""
        flow = DataikuFlow(name="test")
        with pytest.raises(ValueError, match="no datasets"):
            flow.get_column_lineage("col")

    def test_missing_dataset_raises(self):
        """Getting lineage for a non-existent dataset raises ValueError."""
        flow = DataikuFlow(name="test")
        flow.add_dataset(DataikuDataset(name="input", dataset_type=DatasetType.INPUT))
        with pytest.raises(ValueError, match="not found"):
            flow.get_column_lineage("col", dataset="nonexistent")


class TestColumnLineageMultiStep:
    """Tests for multi-step column lineage."""

    def test_multi_recipe_chain(self):
        """Column traced through multiple recipes."""
        flow = DataikuFlow(name="test")
        flow.add_dataset(DataikuDataset(name="raw", dataset_type=DatasetType.INPUT))
        flow.add_recipe(DataikuRecipe(
            name="rename",
            recipe_type=RecipeType.PREPARE,
            inputs=["raw"],
            outputs=["renamed"],
            steps=[
                PrepareStep(
                    processor_type=ProcessorType.COLUMN_RENAMER,
                    params={"column": "original", "new_name": "intermediate"},
                ),
            ],
        ))
        flow.add_recipe(DataikuRecipe(
            name="transform",
            recipe_type=RecipeType.PREPARE,
            inputs=["renamed"],
            outputs=["final"],
            steps=[
                PrepareStep(
                    processor_type=ProcessorType.COLUMN_RENAMER,
                    params={"column": "intermediate", "new_name": "final_name"},
                ),
            ],
        ))

        lineage = flow.get_column_lineage("final_name", dataset="final")
        assert lineage.origin_column == "original"
        assert lineage.origin_dataset == "raw"
        assert len(lineage.transformations) == 2

    def test_grouping_recipe_key(self):
        """Column used as group key in a Grouping recipe."""
        flow = DataikuFlow(name="test")
        flow.add_dataset(DataikuDataset(name="input", dataset_type=DatasetType.INPUT))
        flow.add_recipe(DataikuRecipe(
            name="group",
            recipe_type=RecipeType.GROUPING,
            inputs=["input"],
            outputs=["grouped"],
            group_keys=["category"],
            aggregations=[
                Aggregation(column="amount", function="SUM"),
            ],
        ))

        lineage = flow.get_column_lineage("category", dataset="grouped")
        assert lineage.origin_column == "category"
        assert lineage.transformations[0]["type"] == "group_key"

    def test_grouping_recipe_aggregation(self):
        """Column created by aggregation in a Grouping recipe."""
        flow = DataikuFlow(name="test")
        flow.add_dataset(DataikuDataset(name="input", dataset_type=DatasetType.INPUT))
        flow.add_recipe(DataikuRecipe(
            name="group",
            recipe_type=RecipeType.GROUPING,
            inputs=["input"],
            outputs=["grouped"],
            group_keys=["category"],
            aggregations=[
                Aggregation(column="amount", function="SUM", output_column="total_amount"),
            ],
        ))

        lineage = flow.get_column_lineage("total_amount", dataset="grouped")
        assert lineage.origin_column == "amount"
        assert lineage.transformations[0]["type"] == "aggregation"
        assert lineage.transformations[0]["function"] == "SUM"

    def test_join_recipe(self):
        """Column passing through a Join recipe."""
        flow = DataikuFlow(name="test")
        flow.add_dataset(DataikuDataset(name="left", dataset_type=DatasetType.INPUT))
        flow.add_dataset(DataikuDataset(name="right", dataset_type=DatasetType.INPUT))
        flow.add_recipe(DataikuRecipe(
            name="join",
            recipe_type=RecipeType.JOIN,
            inputs=["left", "right"],
            outputs=["joined"],
            join_type=JoinType.LEFT,
            join_keys=[JoinKey(left_column="id", right_column="id")],
        ))

        lineage = flow.get_column_lineage("name", dataset="joined")
        assert lineage.transformations[0]["type"] == "join"
        assert lineage.transformations[0]["join_type"] == "LEFT"


class TestColumnLineageToDict:
    """Tests for ColumnLineage serialization."""

    def test_to_dict(self):
        lineage = ColumnLineage(
            column="final_col",
            final_dataset="output",
            origin_dataset="input",
            origin_column="orig_col",
            transformations=[{"type": "rename", "from": "orig_col", "to": "final_col"}],
        )
        d = lineage.to_dict()
        assert d["column"] == "final_col"
        assert d["final_dataset"] == "output"
        assert d["origin"]["dataset"] == "input"
        assert d["origin"]["column"] == "orig_col"
        assert len(d["transformations"]) == 1

    def test_default_dataset_selection(self):
        """When no dataset specified, use last output dataset."""
        flow = DataikuFlow(name="test")
        flow.add_dataset(DataikuDataset(name="input", dataset_type=DatasetType.INPUT))
        flow.add_dataset(DataikuDataset(name="output", dataset_type=DatasetType.OUTPUT))
        flow.add_recipe(DataikuRecipe(
            name="prep",
            recipe_type=RecipeType.PREPARE,
            inputs=["input"],
            outputs=["output"],
        ))

        lineage = flow.get_column_lineage("col")
        assert lineage.final_dataset == "output"
