"""Tests for round-trip serialization of DataikuFlow and its components."""

import json

import pytest
import yaml

from py2dataiku.models.dataiku_dataset import ColumnSchema, DataikuDataset, DatasetType
from py2dataiku.models.dataiku_flow import DataikuFlow, FlowRecommendation
from py2dataiku.models.dataiku_recipe import (
    Aggregation,
    DataikuRecipe,
    JoinKey,
    JoinType,
    RecipeType,
    SamplingMethod,
)
from py2dataiku.models.prepare_step import PrepareStep, ProcessorType


class TestColumnSchemaRoundTrip:
    """Test ColumnSchema serialization round-trip."""

    def test_basic_column(self):
        col = ColumnSchema(name="age", type="int")
        d = col.to_dict()
        assert d["name"] == "age"
        assert d["type"] == "int"
        assert d["nullable"] is True

    def test_column_with_all_fields(self):
        col = ColumnSchema(
            name="created_at",
            type="date",
            nullable=False,
            default="2024-01-01",
            format="yyyy-MM-dd",
        )
        d = col.to_dict()
        assert d["name"] == "created_at"
        assert d["type"] == "date"
        assert d["nullable"] is False
        assert d["default"] == "2024-01-01"
        assert d["format"] == "yyyy-MM-dd"


class TestDataikuDatasetRoundTrip:
    """Test DataikuDataset serialization round-trip."""

    def test_simple_dataset(self):
        ds = DataikuDataset(name="input_data", dataset_type=DatasetType.INPUT)
        d = ds.to_dict()
        restored = DataikuDataset.from_dict(d)
        assert restored.name == ds.name
        assert restored.dataset_type == ds.dataset_type
        assert restored.schema == []
        assert restored.notes == []

    def test_dataset_with_schema(self):
        ds = DataikuDataset(
            name="users",
            dataset_type=DatasetType.OUTPUT,
            schema=[
                ColumnSchema(name="id", type="int", nullable=False),
                ColumnSchema(name="name", type="string"),
                ColumnSchema(name="joined", type="date", format="yyyy-MM-dd"),
            ],
            source_variable="df_users",
            source_line=42,
            notes=["User table"],
        )
        d = ds.to_dict()
        restored = DataikuDataset.from_dict(d)
        assert restored.name == "users"
        assert restored.dataset_type == DatasetType.OUTPUT
        assert len(restored.schema) == 3
        assert restored.schema[0].name == "id"
        assert restored.schema[0].nullable is False
        assert restored.schema[2].format == "yyyy-MM-dd"
        assert restored.source_variable == "df_users"
        assert restored.source_line == 42
        assert restored.notes == ["User table"]

    def test_all_dataset_types(self):
        for dt in DatasetType:
            ds = DataikuDataset(name=f"ds_{dt.value}", dataset_type=dt)
            restored = DataikuDataset.from_dict(ds.to_dict())
            assert restored.dataset_type == dt


class TestPrepareStepRoundTrip:
    """Test PrepareStep serialization round-trip."""

    def test_simple_step(self):
        step = PrepareStep(
            processor_type=ProcessorType.COLUMN_DELETER,
            params={"columns": ["temp_col"]},
        )
        d = step.to_dict()
        restored = PrepareStep.from_dict(d)
        assert restored.processor_type == ProcessorType.COLUMN_DELETER
        assert restored.params == {"columns": ["temp_col"]}
        assert restored.disabled is False

    def test_disabled_step(self):
        step = PrepareStep(
            processor_type=ProcessorType.FILL_EMPTY_WITH_VALUE,
            params={"column": "score", "value": "0"},
            disabled=True,
            name="Fill missing scores",
        )
        d = step.to_dict()
        restored = PrepareStep.from_dict(d)
        assert restored.disabled is True
        assert restored.name == "Fill missing scores"
        assert restored.params["column"] == "score"

    def test_various_processor_types(self):
        types_to_test = [
            ProcessorType.COLUMN_RENAMER,
            ProcessorType.STRING_TRANSFORMER,
            ProcessorType.FILTER_ON_VALUE,
            ProcessorType.TYPE_SETTER,
            ProcessorType.DATE_PARSER,
            ProcessorType.REMOVE_ROWS_ON_EMPTY,
        ]
        for pt in types_to_test:
            step = PrepareStep(
                processor_type=pt,
                params={"column": "test"},
            )
            restored = PrepareStep.from_dict(step.to_dict())
            assert restored.processor_type == pt


class TestDataikuRecipeRoundTrip:
    """Test DataikuRecipe serialization round-trip."""

    def test_prepare_recipe(self):
        recipe = DataikuRecipe(
            name="prepare_data",
            recipe_type=RecipeType.PREPARE,
            inputs=["raw_data"],
            outputs=["clean_data"],
            steps=[
                PrepareStep(
                    processor_type=ProcessorType.COLUMN_DELETER,
                    params={"columns": ["temp"]},
                ),
                PrepareStep(
                    processor_type=ProcessorType.FILL_EMPTY_WITH_VALUE,
                    params={"column": "score", "value": "0"},
                ),
            ],
            source_lines=[10, 15],
            notes=["Data cleaning step"],
        )
        d = recipe.to_dict()
        restored = DataikuRecipe.from_dict(d)
        assert restored.name == "prepare_data"
        assert restored.recipe_type == RecipeType.PREPARE
        assert restored.inputs == ["raw_data"]
        assert restored.outputs == ["clean_data"]
        assert len(restored.steps) == 2
        assert restored.steps[0].processor_type == ProcessorType.COLUMN_DELETER
        assert restored.steps[1].params["column"] == "score"
        assert restored.source_lines == [10, 15]
        assert restored.notes == ["Data cleaning step"]

    def test_grouping_recipe(self):
        recipe = DataikuRecipe(
            name="group_sales",
            recipe_type=RecipeType.GROUPING,
            inputs=["sales"],
            outputs=["sales_by_region"],
            group_keys=["region", "product"],
            aggregations=[
                Aggregation(column="amount", function="SUM", output_column="total"),
                Aggregation(column="quantity", function="AVG"),
            ],
        )
        d = recipe.to_dict()
        restored = DataikuRecipe.from_dict(d)
        assert restored.recipe_type == RecipeType.GROUPING
        assert restored.group_keys == ["region", "product"]
        assert len(restored.aggregations) == 2
        assert restored.aggregations[0].column == "amount"
        assert restored.aggregations[0].function == "SUM"
        assert restored.aggregations[0].output_column == "total"

    def test_join_recipe(self):
        recipe = DataikuRecipe(
            name="join_users_orders",
            recipe_type=RecipeType.JOIN,
            inputs=["users", "orders"],
            outputs=["user_orders"],
            join_type=JoinType.INNER,
            join_keys=[
                JoinKey(left_column="user_id", right_column="customer_id"),
            ],
            selected_columns={"left": ["name", "email"], "right": ["order_id", "amount"]},
        )
        d = recipe.to_dict()
        restored = DataikuRecipe.from_dict(d)
        assert restored.recipe_type == RecipeType.JOIN
        assert restored.join_type == JoinType.INNER
        assert len(restored.join_keys) == 1
        assert restored.join_keys[0].left_column == "user_id"
        assert restored.join_keys[0].right_column == "customer_id"
        assert restored.selected_columns == {
            "left": ["name", "email"],
            "right": ["order_id", "amount"],
        }

    def test_python_recipe(self):
        recipe = DataikuRecipe(
            name="custom_transform",
            recipe_type=RecipeType.PYTHON,
            inputs=["input_data"],
            outputs=["output_data"],
            code="df['new_col'] = df['a'] + df['b']",
        )
        d = recipe.to_dict()
        restored = DataikuRecipe.from_dict(d)
        assert restored.recipe_type == RecipeType.PYTHON
        assert restored.code == "df['new_col'] = df['a'] + df['b']"

    def test_simple_recipe_types(self):
        """Test round-trip for recipe types with minimal config."""
        for rt in [RecipeType.SYNC, RecipeType.DISTINCT, RecipeType.STACK]:
            recipe = DataikuRecipe(
                name=f"test_{rt.value}",
                recipe_type=rt,
                inputs=["in"],
                outputs=["out"],
            )
            restored = DataikuRecipe.from_dict(recipe.to_dict())
            assert restored.recipe_type == rt
            assert restored.inputs == ["in"]
            assert restored.outputs == ["out"]


class TestDataikuFlowRoundTrip:
    """Test DataikuFlow serialization round-trip via dict, JSON, YAML."""

    def _build_flow(self) -> DataikuFlow:
        """Build a comprehensive flow for testing."""
        flow = DataikuFlow(
            name="test_pipeline",
            source_file="test_script.py",
            generation_timestamp="2024-01-15T10:30:00",
        )

        # Add datasets
        flow.datasets = [
            DataikuDataset(
                name="raw_data",
                dataset_type=DatasetType.INPUT,
                schema=[
                    ColumnSchema(name="id", type="int", nullable=False),
                    ColumnSchema(name="name", type="string"),
                ],
            ),
            DataikuDataset(name="clean_data", dataset_type=DatasetType.INTERMEDIATE),
            DataikuDataset(name="summary", dataset_type=DatasetType.OUTPUT),
        ]

        # Add recipes
        flow.recipes = [
            DataikuRecipe(
                name="prepare_data",
                recipe_type=RecipeType.PREPARE,
                inputs=["raw_data"],
                outputs=["clean_data"],
                steps=[
                    PrepareStep(
                        processor_type=ProcessorType.FILL_EMPTY_WITH_VALUE,
                        params={"column": "name", "value": "Unknown"},
                    ),
                    PrepareStep(
                        processor_type=ProcessorType.COLUMN_DELETER,
                        params={"columns": ["temp"]},
                        disabled=True,
                    ),
                ],
            ),
            DataikuRecipe(
                name="group_data",
                recipe_type=RecipeType.GROUPING,
                inputs=["clean_data"],
                outputs=["summary"],
                group_keys=["category"],
                aggregations=[
                    Aggregation(column="amount", function="SUM"),
                    Aggregation(column="id", function="COUNT"),
                ],
            ),
        ]

        # Add recommendations
        flow.recommendations = [
            FlowRecommendation(
                type="PERFORMANCE",
                priority="MEDIUM",
                message="Consider adding index on category column",
                impact="May improve grouping performance",
            ),
        ]
        flow.optimization_notes = ["Merged 2 prepare steps"]

        return flow

    def test_round_trip_dict(self):
        """Test dict serialization round-trip."""
        flow = self._build_flow()
        d = flow.to_dict()
        restored = DataikuFlow.from_dict(d)

        assert restored.name == flow.name
        assert restored.source_file == flow.source_file
        assert restored.generation_timestamp == flow.generation_timestamp

        # Datasets
        assert len(restored.datasets) == len(flow.datasets)
        for orig, rest in zip(flow.datasets, restored.datasets):
            assert rest.name == orig.name
            assert rest.dataset_type == orig.dataset_type
            assert len(rest.schema) == len(orig.schema)

        # Recipes
        assert len(restored.recipes) == len(flow.recipes)
        assert restored.recipes[0].recipe_type == RecipeType.PREPARE
        assert len(restored.recipes[0].steps) == 2
        assert restored.recipes[0].steps[1].disabled is True
        assert restored.recipes[1].recipe_type == RecipeType.GROUPING
        assert restored.recipes[1].group_keys == ["category"]
        assert len(restored.recipes[1].aggregations) == 2

        # Recommendations
        assert len(restored.recommendations) == 1
        assert restored.recommendations[0].type == "PERFORMANCE"
        assert restored.recommendations[0].priority == "MEDIUM"

        # Optimization notes
        assert restored.optimization_notes == ["Merged 2 prepare steps"]

    def test_round_trip_json(self):
        """Test JSON serialization round-trip."""
        flow = self._build_flow()
        json_str = flow.to_json()
        restored = DataikuFlow.from_json(json_str)

        assert restored.name == flow.name
        assert len(restored.datasets) == len(flow.datasets)
        assert len(restored.recipes) == len(flow.recipes)
        assert restored.recipes[0].recipe_type == RecipeType.PREPARE

    def test_round_trip_yaml(self):
        """Test YAML serialization round-trip."""
        flow = self._build_flow()
        yaml_str = flow.to_yaml()
        restored = DataikuFlow.from_yaml(yaml_str)

        assert restored.name == flow.name
        assert len(restored.datasets) == len(flow.datasets)
        assert len(restored.recipes) == len(flow.recipes)
        assert restored.recipes[1].group_keys == ["category"]

    def test_empty_flow_round_trip(self):
        """Test round-trip of an empty flow."""
        flow = DataikuFlow(name="empty")
        restored = DataikuFlow.from_dict(flow.to_dict())
        assert restored.name == "empty"
        assert restored.datasets == []
        assert restored.recipes == []

    def test_join_flow_round_trip(self):
        """Test round-trip of a flow with a join recipe."""
        flow = DataikuFlow(name="join_flow")
        flow.datasets = [
            DataikuDataset(name="left", dataset_type=DatasetType.INPUT),
            DataikuDataset(name="right", dataset_type=DatasetType.INPUT),
            DataikuDataset(name="joined", dataset_type=DatasetType.OUTPUT),
        ]
        flow.recipes = [
            DataikuRecipe(
                name="join_lr",
                recipe_type=RecipeType.JOIN,
                inputs=["left", "right"],
                outputs=["joined"],
                join_type=JoinType.LEFT,
                join_keys=[
                    JoinKey(left_column="id", right_column="id"),
                    JoinKey(left_column="date", right_column="date"),
                ],
            ),
        ]

        restored = DataikuFlow.from_json(flow.to_json())
        assert restored.recipes[0].join_type == JoinType.LEFT
        assert len(restored.recipes[0].join_keys) == 2
        assert restored.recipes[0].join_keys[1].left_column == "date"

    def test_json_is_valid_json(self):
        """Test that to_json produces valid JSON."""
        flow = self._build_flow()
        json_str = flow.to_json()
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
        assert parsed["flow_name"] == "test_pipeline"

    def test_yaml_is_valid_yaml(self):
        """Test that to_yaml produces valid YAML."""
        flow = self._build_flow()
        yaml_str = flow.to_yaml()
        parsed = yaml.safe_load(yaml_str)
        assert isinstance(parsed, dict)
        assert parsed["flow_name"] == "test_pipeline"

    def test_dict_round_trip_preserves_structure(self):
        """Test that to_dict -> from_dict -> to_dict produces identical dicts."""
        flow = self._build_flow()
        d1 = flow.to_dict()
        d2 = DataikuFlow.from_dict(d1).to_dict()
        assert d1 == d2
