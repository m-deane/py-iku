"""Tests for LLM-based py2dataiku components."""

import json
import pytest

from py2dataiku.llm.schemas import (
    AnalysisResult,
    DataStep,
    DatasetInfo,
    OperationType,
    Aggregation,
    FilterCondition,
    JoinCondition,
    ColumnTransform,
)
from py2dataiku.llm.providers import MockProvider, get_provider
from py2dataiku.llm.analyzer import LLMCodeAnalyzer
from py2dataiku.generators.llm_flow_generator import LLMFlowGenerator
from py2dataiku.models.dataiku_recipe import RecipeType


class TestDataStep:
    """Tests for DataStep schema."""

    def test_create_data_step(self):
        step = DataStep(
            step_number=1,
            operation=OperationType.FILTER,
            description="Filter rows where amount > 100",
        )
        assert step.step_number == 1
        assert step.operation == OperationType.FILTER

    def test_data_step_from_dict(self):
        data = {
            "step_number": 1,
            "operation": "filter",
            "description": "Filter rows",
            "input_datasets": ["df"],
            "output_dataset": "filtered_df",
            "columns": ["amount"],
            "filter_conditions": [
                {"column": "amount", "operator": "greater_than", "value": 100}
            ],
            "suggested_recipe": "prepare",
        }
        step = DataStep.from_dict(data)
        assert step.operation == OperationType.FILTER
        assert len(step.filter_conditions) == 1
        assert step.filter_conditions[0].value == 100

    def test_data_step_to_dict(self):
        step = DataStep(
            step_number=1,
            operation=OperationType.GROUP_AGGREGATE,
            description="Group by category",
            group_by_columns=["category"],
            aggregations=[Aggregation("amount", "sum", "total")],
        )
        d = step.to_dict()
        assert d["operation"] == "group_aggregate"
        assert d["group_by_columns"] == ["category"]
        assert len(d["aggregations"]) == 1

    def test_operation_types(self):
        """Test all operation types are valid."""
        for op in OperationType:
            step = DataStep(step_number=1, operation=op, description=f"Test {op.value}")
            assert step.operation == op


class TestAnalysisResult:
    """Tests for AnalysisResult schema."""

    def test_create_analysis_result(self):
        result = AnalysisResult(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.READ_DATA,
                    description="Read CSV",
                )
            ],
            datasets=[DatasetInfo(name="df", is_input=True)],
            code_summary="Load and process data",
        )
        assert len(result.steps) == 1
        assert len(result.datasets) == 1

    def test_analysis_result_to_json(self):
        result = AnalysisResult(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.READ_DATA,
                    description="Read data",
                )
            ],
            datasets=[],
            code_summary="Test",
        )
        json_str = result.to_json()
        parsed = json.loads(json_str)
        assert parsed["code_summary"] == "Test"
        assert len(parsed["steps"]) == 1

    def test_analysis_result_from_dict(self):
        data = {
            "steps": [
                {
                    "step_number": 1,
                    "operation": "read_data",
                    "description": "Read CSV file",
                }
            ],
            "datasets": [{"name": "df", "is_input": True, "source": "data.csv"}],
            "code_summary": "Data pipeline",
            "total_operations": 1,
        }
        result = AnalysisResult.from_dict(data)
        assert result.code_summary == "Data pipeline"
        assert result.datasets[0].source == "data.csv"


class TestMockProvider:
    """Tests for MockProvider."""

    def test_mock_provider_default_response(self):
        provider = MockProvider()
        response = provider.complete("Test prompt")
        assert response.model == "mock"
        assert "steps" in response.content

    def test_mock_provider_custom_response(self):
        provider = MockProvider(
            responses={
                "test_key": '{"custom": "response"}'
            }
        )
        response = provider.complete("This contains test_key")
        assert "custom" in response.content

    def test_mock_provider_json(self):
        provider = MockProvider()
        data = provider.complete_json("Test")
        assert isinstance(data, dict)
        assert "steps" in data

    def test_mock_provider_tracks_calls(self):
        provider = MockProvider()
        provider.complete("First call")
        provider.complete("Second call")
        assert len(provider.calls) == 2


class TestLLMCodeAnalyzer:
    """Tests for LLMCodeAnalyzer with mock provider."""

    def get_mock_response(self):
        """Get a realistic mock LLM response."""
        return json.dumps({
            "code_summary": "Load customer data, clean it, and aggregate by category",
            "total_operations": 3,
            "complexity_score": 4,
            "datasets": [
                {"name": "df", "source": "data.csv", "is_input": True, "is_output": False},
                {"name": "cleaned", "is_input": False, "is_output": False},
                {"name": "result", "is_input": False, "is_output": True},
            ],
            "steps": [
                {
                    "step_number": 1,
                    "operation": "read_data",
                    "description": "Read CSV file into DataFrame",
                    "input_datasets": [],
                    "output_dataset": "df",
                    "suggested_recipe": "sync",
                },
                {
                    "step_number": 2,
                    "operation": "drop_missing",
                    "description": "Remove rows with missing values",
                    "input_datasets": ["df"],
                    "output_dataset": "cleaned",
                    "columns": ["id"],
                    "suggested_recipe": "prepare",
                    "suggested_processors": ["RemoveRowsOnEmpty"],
                },
                {
                    "step_number": 3,
                    "operation": "group_aggregate",
                    "description": "Group by category and sum amounts",
                    "input_datasets": ["cleaned"],
                    "output_dataset": "result",
                    "group_by_columns": ["category"],
                    "aggregations": [
                        {"column": "amount", "function": "sum", "output_column": "total"}
                    ],
                    "suggested_recipe": "grouping",
                },
            ],
            "recommendations": ["Consider filtering before aggregation"],
            "warnings": [],
        })

    def test_analyze_with_mock(self):
        mock_response = self.get_mock_response()
        provider = MockProvider(responses={"python": mock_response})
        analyzer = LLMCodeAnalyzer(provider=provider)

        code = """
import pandas as pd
df = pd.read_csv('data.csv')
cleaned = df.dropna(subset=['id'])
result = cleaned.groupby('category').agg({'amount': 'sum'})
"""
        result = analyzer.analyze(code)

        assert result.code_summary is not None
        assert len(result.steps) == 3
        assert result.steps[2].operation == OperationType.GROUP_AGGREGATE

    def test_analyze_error_handling(self):
        """Test handling of invalid JSON response raises LLMResponseParseError."""
        from py2dataiku.exceptions import LLMResponseParseError

        provider = MockProvider(responses={"python": "invalid json"})
        analyzer = LLMCodeAnalyzer(provider=provider)

        with pytest.raises(LLMResponseParseError):
            analyzer.analyze("test code")

    def test_post_processing(self):
        """Test that post-processing adds default suggestions."""
        mock_response = json.dumps({
            "code_summary": "Test",
            "datasets": [],
            "steps": [
                {
                    "step_number": 1,
                    "operation": "filter",
                    "description": "Filter data",
                }
            ],
        })
        provider = MockProvider(responses={"python": mock_response})
        analyzer = LLMCodeAnalyzer(provider=provider)

        result = analyzer.analyze("test")

        # Should have suggested recipe added
        assert result.steps[0].suggested_recipe is not None


class TestLLMFlowGenerator:
    """Tests for LLMFlowGenerator."""

    def test_generate_simple_flow(self):
        result = AnalysisResult(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.READ_DATA,
                    description="Read CSV",
                    output_dataset="df",
                ),
                DataStep(
                    step_number=2,
                    operation=OperationType.DROP_MISSING,
                    description="Drop nulls",
                    input_datasets=["df"],
                    output_dataset="cleaned",
                    columns=["id"],
                    suggested_recipe="prepare",
                ),
            ],
            datasets=[
                DatasetInfo(name="df", is_input=True),
                DatasetInfo(name="cleaned", is_output=True),
            ],
            code_summary="Simple pipeline",
        )

        generator = LLMFlowGenerator()
        flow = generator.generate(result)

        assert len(flow.datasets) >= 2
        assert len(flow.recipes) >= 1

    def test_generate_grouping_recipe(self):
        result = AnalysisResult(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.GROUP_AGGREGATE,
                    description="Aggregate by category",
                    input_datasets=["df"],
                    output_dataset="agg",
                    group_by_columns=["category"],
                    aggregations=[Aggregation("amount", "sum", "total")],
                    suggested_recipe="grouping",
                ),
            ],
            datasets=[DatasetInfo(name="df", is_input=True)],
            code_summary="Aggregation pipeline",
        )

        generator = LLMFlowGenerator()
        flow = generator.generate(result)

        grouping_recipes = flow.get_recipes_by_type(RecipeType.GROUPING)
        assert len(grouping_recipes) == 1
        assert grouping_recipes[0].group_keys == ["category"]

    def test_generate_join_recipe(self):
        result = AnalysisResult(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.JOIN,
                    description="Join customers and orders",
                    input_datasets=["customers", "orders"],
                    output_dataset="merged",
                    join_conditions=[JoinCondition("customer_id", "customer_id")],
                    join_type="left",
                    suggested_recipe="join",
                ),
            ],
            datasets=[
                DatasetInfo(name="customers", is_input=True),
                DatasetInfo(name="orders", is_input=True),
            ],
            code_summary="Join pipeline",
        )

        generator = LLMFlowGenerator()
        flow = generator.generate(result)

        join_recipes = flow.get_recipes_by_type(RecipeType.JOIN)
        assert len(join_recipes) == 1

    def test_generate_prepare_with_transforms(self):
        result = AnalysisResult(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.TRANSFORM_COLUMN,
                    description="Uppercase names",
                    input_datasets=["df"],
                    output_dataset="transformed",
                    column_transforms=[
                        ColumnTransform(column="name", operation="uppercase")
                    ],
                    suggested_recipe="prepare",
                ),
            ],
            datasets=[DatasetInfo(name="df", is_input=True)],
            code_summary="Transform pipeline",
        )

        generator = LLMFlowGenerator()
        flow = generator.generate(result)

        prepare_recipes = flow.get_recipes_by_type(RecipeType.PREPARE)
        assert len(prepare_recipes) >= 1

    def test_generate_python_fallback(self):
        result = AnalysisResult(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.CUSTOM_FUNCTION,
                    description="Apply custom function",
                    input_datasets=["df"],
                    output_dataset="processed",
                    requires_python_recipe=True,
                    suggested_recipe="python",
                ),
            ],
            datasets=[DatasetInfo(name="df", is_input=True)],
            code_summary="Custom pipeline",
        )

        generator = LLMFlowGenerator()
        flow = generator.generate(result)

        python_recipes = flow.get_recipes_by_type(RecipeType.PYTHON)
        assert len(python_recipes) == 1
        # Should have recommendation about Python recipe
        assert any("PYTHON" in r.type for r in flow.recommendations)


class TestGetProvider:
    """Tests for provider factory function."""

    def test_get_mock_provider(self):
        provider = get_provider("mock")
        assert provider.model_name == "mock"

    def test_get_unknown_provider(self):
        with pytest.raises(ValueError):
            get_provider("unknown_provider")

    def test_anthropic_requires_key(self):
        """Test that Anthropic provider requires API key."""
        import os
        old_key = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            with pytest.raises(ValueError):
                get_provider("anthropic")
        finally:
            if old_key:
                os.environ["ANTHROPIC_API_KEY"] = old_key

    def test_openai_requires_key(self):
        """Test that OpenAI provider requires API key."""
        import os
        old_key = os.environ.pop("OPENAI_API_KEY", None)
        try:
            with pytest.raises(ValueError):
                get_provider("openai")
        finally:
            if old_key:
                os.environ["OPENAI_API_KEY"] = old_key


class TestEndToEndLLM:
    """End-to-end tests with mock LLM."""

    def test_full_pipeline(self):
        """Test complete pipeline from code to flow with diagrams."""
        # Create mock response for realistic code
        mock_response = json.dumps({
            "code_summary": "Customer analysis pipeline",
            "total_operations": 4,
            "complexity_score": 5,
            "datasets": [
                {"name": "customers", "source": "customers.csv", "is_input": True},
                {"name": "orders", "source": "orders.csv", "is_input": True},
                {"name": "merged", "is_input": False, "is_output": False},
                {"name": "summary", "is_input": False, "is_output": True},
            ],
            "steps": [
                {
                    "step_number": 1,
                    "operation": "read_data",
                    "description": "Read customers",
                    "output_dataset": "customers",
                },
                {
                    "step_number": 2,
                    "operation": "read_data",
                    "description": "Read orders",
                    "output_dataset": "orders",
                },
                {
                    "step_number": 3,
                    "operation": "join",
                    "description": "Join customers with orders",
                    "input_datasets": ["customers", "orders"],
                    "output_dataset": "merged",
                    "join_conditions": [{"left_column": "id", "right_column": "customer_id"}],
                    "join_type": "left",
                    "suggested_recipe": "join",
                },
                {
                    "step_number": 4,
                    "operation": "group_aggregate",
                    "description": "Summarize by customer",
                    "input_datasets": ["merged"],
                    "output_dataset": "summary",
                    "group_by_columns": ["id"],
                    "aggregations": [{"column": "amount", "function": "sum"}],
                    "suggested_recipe": "grouping",
                },
            ],
            "recommendations": [],
            "warnings": [],
        })

        provider = MockProvider(responses={"python": mock_response})
        analyzer = LLMCodeAnalyzer(provider=provider)
        generator = LLMFlowGenerator()

        code = """
import pandas as pd
customers = pd.read_csv('customers.csv')
orders = pd.read_csv('orders.csv')
merged = pd.merge(customers, orders, left_on='id', right_on='customer_id')
summary = merged.groupby('id').agg({'amount': 'sum'})
"""

        # Analyze
        analysis = analyzer.analyze(code)
        assert len(analysis.steps) == 4

        # Generate flow
        flow = generator.generate(analysis, flow_name="customer_pipeline")
        assert flow.name == "customer_pipeline"

        # Check recipes
        join_recipes = flow.get_recipes_by_type(RecipeType.JOIN)
        grouping_recipes = flow.get_recipes_by_type(RecipeType.GROUPING)
        assert len(join_recipes) >= 1
        assert len(grouping_recipes) >= 1

        # Generate diagram
        from py2dataiku.generators.diagram_generator import DiagramGenerator
        diagram_gen = DiagramGenerator()
        mermaid = diagram_gen.to_mermaid(flow)
        assert "flowchart" in mermaid

        # Export
        yaml_output = flow.to_yaml()
        assert "customer_pipeline" in yaml_output
