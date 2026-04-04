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


# ---------------------------------------------------------------------------
# New comprehensive tests for LLMFlowGenerator
# ---------------------------------------------------------------------------

def _make_analysis(steps, datasets=None, recommendations=None, warnings=None):
    """Helper to build an AnalysisResult with sensible defaults."""
    return AnalysisResult(
        steps=steps,
        datasets=datasets or [],
        code_summary="test",
        recommendations=recommendations or [],
        warnings=warnings or [],
    )


class TestOperationToRecipeFallback:
    """OPERATION_TO_RECIPE drives routing when suggested_recipe is absent."""

    def _single_step_flow(self, operation, extra_kwargs=None):
        kwargs = dict(
            step_number=1,
            operation=operation,
            description=f"Test {operation.value}",
            input_datasets=["src"],
            output_dataset="dst",
        )
        if extra_kwargs:
            kwargs.update(extra_kwargs)
        analysis = _make_analysis(
            steps=[DataStep(**kwargs)],
            datasets=[DatasetInfo(name="src", is_input=True)],
        )
        return LLMFlowGenerator().generate(analysis)

    def test_group_aggregate_produces_grouping(self):
        flow = self._single_step_flow(
            OperationType.GROUP_AGGREGATE,
            {"group_by_columns": ["cat"], "aggregations": [Aggregation("amt", "sum")]},
        )
        assert len(flow.get_recipes_by_type(RecipeType.GROUPING)) == 1

    def test_join_produces_join_recipe(self):
        flow = self._single_step_flow(
            OperationType.JOIN,
            {
                "input_datasets": ["left", "right"],
                "join_conditions": [JoinCondition("id", "id")],
                "join_type": "inner",
            },
        )
        assert len(flow.get_recipes_by_type(RecipeType.JOIN)) == 1

    def test_union_produces_stack_recipe(self):
        flow = self._single_step_flow(
            OperationType.UNION,
            {"input_datasets": ["a", "b"]},
        )
        assert len(flow.get_recipes_by_type(RecipeType.STACK)) == 1

    def test_sort_produces_sort_recipe(self):
        flow = self._single_step_flow(OperationType.SORT)
        assert len(flow.get_recipes_by_type(RecipeType.SORT)) == 1

    def test_drop_duplicates_produces_distinct_recipe(self):
        flow = self._single_step_flow(OperationType.DROP_DUPLICATES)
        assert len(flow.get_recipes_by_type(RecipeType.DISTINCT)) == 1

    def test_window_function_produces_window_recipe(self):
        flow = self._single_step_flow(OperationType.WINDOW_FUNCTION)
        assert len(flow.get_recipes_by_type(RecipeType.WINDOW)) == 1

    def test_top_n_produces_python_recipe(self):
        flow = self._single_step_flow(OperationType.TOP_N)
        assert len(flow.get_recipes_by_type(RecipeType.PYTHON)) == 1

    def test_sample_produces_python_recipe(self):
        flow = self._single_step_flow(OperationType.SAMPLE)
        assert len(flow.get_recipes_by_type(RecipeType.PYTHON)) == 1

    def test_pivot_produces_python_recipe(self):
        flow = self._single_step_flow(OperationType.PIVOT)
        assert len(flow.get_recipes_by_type(RecipeType.PYTHON)) == 1

    def test_fill_missing_produces_prepare_recipe(self):
        flow = self._single_step_flow(
            OperationType.FILL_MISSING, {"columns": ["col_a"], "fill_value": 0}
        )
        assert len(flow.get_recipes_by_type(RecipeType.PREPARE)) >= 1

    def test_drop_missing_produces_prepare_recipe(self):
        flow = self._single_step_flow(
            OperationType.DROP_MISSING, {"columns": ["col_a"]}
        )
        assert len(flow.get_recipes_by_type(RecipeType.PREPARE)) >= 1

    def test_rename_columns_produces_prepare_recipe(self):
        flow = self._single_step_flow(
            OperationType.RENAME_COLUMNS, {"rename_mapping": {"old": "new"}}
        )
        assert len(flow.get_recipes_by_type(RecipeType.PREPARE)) >= 1

    def test_drop_columns_produces_prepare_recipe(self):
        flow = self._single_step_flow(
            OperationType.DROP_COLUMNS, {"columns": ["unwanted"]}
        )
        assert len(flow.get_recipes_by_type(RecipeType.PREPARE)) >= 1

    def test_cast_type_produces_prepare_recipe(self):
        flow = self._single_step_flow(
            OperationType.CAST_TYPE,
            {
                "column_transforms": [
                    ColumnTransform(column="age", operation="cast", parameters={"type": "int"})
                ]
            },
        )
        assert len(flow.get_recipes_by_type(RecipeType.PREPARE)) >= 1

    def test_parse_date_produces_prepare_recipe(self):
        flow = self._single_step_flow(
            OperationType.PARSE_DATE, {"columns": ["created_at"]}
        )
        assert len(flow.get_recipes_by_type(RecipeType.PREPARE)) >= 1

    def test_filter_produces_prepare_recipe(self):
        flow = self._single_step_flow(
            OperationType.FILTER,
            {
                "filter_conditions": [
                    FilterCondition(column="status", operator="equals", value="active")
                ]
            },
        )
        assert len(flow.get_recipes_by_type(RecipeType.PREPARE)) >= 1


class TestConvertToPrepareSteps:
    """_convert_to_prepare_steps covers all handled OperationType branches."""

    def _generator(self):
        gen = LLMFlowGenerator()
        # Minimal state so _create_prepare_recipe works without crashing
        from py2dataiku.models.dataiku_flow import DataikuFlow
        gen.flow = DataikuFlow(name="test")
        gen.recipe_counter = 0
        gen.dataset_map = {}
        return gen

    def test_fill_missing_single_column(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.FILL_MISSING,
            description="fill",
            columns=["price"],
            fill_value="0",
        )
        steps = gen._convert_to_prepare_steps(step)
        assert len(steps) == 1
        assert steps[0].params.get("column") == "price"
        assert steps[0].params.get("value") == "0"

    def test_fill_missing_multiple_columns(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.FILL_MISSING,
            description="fill many",
            columns=["a", "b", "c"],
            fill_value="N/A",
        )
        steps = gen._convert_to_prepare_steps(step)
        assert len(steps) == 3

    def test_fill_missing_default_value_when_none(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.FILL_MISSING,
            description="fill no value",
            columns=["x"],
        )
        steps = gen._convert_to_prepare_steps(step)
        assert len(steps) == 1
        # fill_value defaults to "" per generator code

    def test_drop_missing_with_columns(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.DROP_MISSING,
            description="drop nulls",
            columns=["id", "name"],
        )
        steps = gen._convert_to_prepare_steps(step)
        assert len(steps) == 1
        from py2dataiku.models.prepare_step import ProcessorType
        assert steps[0].processor_type == ProcessorType.REMOVE_ROWS_ON_EMPTY

    def test_drop_missing_without_columns_returns_empty(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.DROP_MISSING,
            description="drop nulls no cols",
        )
        steps = gen._convert_to_prepare_steps(step)
        assert steps == []

    def test_rename_columns_with_mapping(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.RENAME_COLUMNS,
            description="rename",
            rename_mapping={"old_name": "new_name", "x": "y"},
        )
        steps = gen._convert_to_prepare_steps(step)
        assert len(steps) == 1
        from py2dataiku.models.prepare_step import ProcessorType
        assert steps[0].processor_type == ProcessorType.COLUMN_RENAMER

    def test_rename_columns_without_mapping_returns_empty(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.RENAME_COLUMNS,
            description="rename empty",
        )
        steps = gen._convert_to_prepare_steps(step)
        assert steps == []

    def test_drop_columns_with_columns(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.DROP_COLUMNS,
            description="drop cols",
            columns=["temp", "debug"],
        )
        steps = gen._convert_to_prepare_steps(step)
        assert len(steps) == 1
        from py2dataiku.models.prepare_step import ProcessorType
        assert steps[0].processor_type in (
            ProcessorType.COLUMN_DELETER, ProcessorType.COLUMNS_SELECTOR
        )

    def test_transform_column_uppercase(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.TRANSFORM_COLUMN,
            description="uppercase",
            column_transforms=[ColumnTransform(column="name", operation="uppercase")],
        )
        steps = gen._convert_to_prepare_steps(step)
        assert len(steps) == 1
        from py2dataiku.models.prepare_step import ProcessorType
        assert steps[0].processor_type == ProcessorType.STRING_TRANSFORMER

    def test_transform_column_lowercase(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.TRANSFORM_COLUMN,
            description="lowercase",
            column_transforms=[ColumnTransform(column="email", operation="lowercase")],
        )
        steps = gen._convert_to_prepare_steps(step)
        assert len(steps) == 1
        from py2dataiku.models.prepare_step import ProcessorType
        assert steps[0].processor_type == ProcessorType.STRING_TRANSFORMER

    def test_transform_column_trim(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.TRANSFORM_COLUMN,
            description="trim",
            column_transforms=[ColumnTransform(column="notes", operation="trim")],
        )
        steps = gen._convert_to_prepare_steps(step)
        assert len(steps) == 1
        from py2dataiku.models.prepare_step import ProcessorType
        assert steps[0].processor_type == ProcessorType.STRING_TRANSFORMER

    def test_transform_column_round(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.TRANSFORM_COLUMN,
            description="round",
            column_transforms=[
                ColumnTransform(column="amount", operation="round", parameters={"precision": 2})
            ],
        )
        steps = gen._convert_to_prepare_steps(step)
        assert len(steps) == 1
        from py2dataiku.models.prepare_step import ProcessorType
        assert steps[0].processor_type == ProcessorType.ROUND_COLUMN
        assert steps[0].params.get("precision") == 2

    def test_transform_column_abs_uses_grel(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.TRANSFORM_COLUMN,
            description="abs value",
            column_transforms=[ColumnTransform(column="delta", operation="abs")],
        )
        steps = gen._convert_to_prepare_steps(step)
        assert len(steps) == 1
        # abs falls back to GREL expression
        from py2dataiku.models.prepare_step import ProcessorType
        assert steps[0].processor_type == ProcessorType.CREATE_COLUMN_WITH_GREL

    def test_filter_equals_condition(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.FILTER,
            description="filter active",
            filter_conditions=[
                FilterCondition(column="status", operator="equals", value="active")
            ],
        )
        steps = gen._convert_to_prepare_steps(step)
        assert len(steps) == 1

    def test_filter_greater_than_condition(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.FILTER,
            description="filter amount",
            filter_conditions=[
                FilterCondition(column="amount", operator="greater_than", value=100)
            ],
        )
        steps = gen._convert_to_prepare_steps(step)
        assert len(steps) == 1

    def test_filter_multiple_conditions(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.FILTER,
            description="filter multi",
            filter_conditions=[
                FilterCondition(column="a", operator="equals", value="x"),
                FilterCondition(column="b", operator="contains", value="y"),
            ],
        )
        steps = gen._convert_to_prepare_steps(step)
        assert len(steps) == 2

    def test_cast_type_with_cast_operation(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.CAST_TYPE,
            description="cast",
            column_transforms=[
                ColumnTransform(
                    column="age", operation="cast", parameters={"type": "int"}
                )
            ],
        )
        steps = gen._convert_to_prepare_steps(step)
        assert len(steps) == 1
        from py2dataiku.models.prepare_step import ProcessorType
        assert steps[0].processor_type == ProcessorType.TYPE_SETTER

    def test_cast_type_with_astype_operation(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.CAST_TYPE,
            description="astype",
            column_transforms=[
                ColumnTransform(
                    column="score", operation="astype", parameters={"type": "float"}
                )
            ],
        )
        steps = gen._convert_to_prepare_steps(step)
        assert len(steps) == 1

    def test_cast_type_ignores_non_cast_operations(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.CAST_TYPE,
            description="other op",
            column_transforms=[
                ColumnTransform(column="x", operation="something_else")
            ],
        )
        steps = gen._convert_to_prepare_steps(step)
        # no cast/astype/convert operations → empty
        assert steps == []

    def test_parse_date_single_column(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.PARSE_DATE,
            description="parse date",
            columns=["created_at"],
        )
        steps = gen._convert_to_prepare_steps(step)
        assert len(steps) == 1
        from py2dataiku.models.prepare_step import ProcessorType
        assert steps[0].processor_type == ProcessorType.DATE_PARSER

    def test_parse_date_multiple_columns(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.PARSE_DATE,
            description="parse multiple dates",
            columns=["start_date", "end_date"],
        )
        steps = gen._convert_to_prepare_steps(step)
        assert len(steps) == 2

    def test_drop_duplicates_with_columns(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.DROP_DUPLICATES,
            description="dedup",
            columns=["email"],
        )
        steps = gen._convert_to_prepare_steps(step)
        assert len(steps) == 1

    def test_drop_duplicates_without_columns(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.DROP_DUPLICATES,
            description="dedup all",
        )
        steps = gen._convert_to_prepare_steps(step)
        assert len(steps) == 1

    def test_fallback_to_suggested_processors_when_no_result(self):
        gen = self._generator()
        # Use an operation that has no handler (UNKNOWN) but provide suggested_processors
        step = DataStep(
            step_number=1,
            operation=OperationType.UNKNOWN,
            description="unknown op",
            suggested_processors=["FillEmptyWithValue"],
        )
        steps = gen._convert_to_prepare_steps(step)
        assert len(steps) == 1
        from py2dataiku.models.prepare_step import ProcessorType
        assert steps[0].processor_type == ProcessorType.FILL_EMPTY_WITH_VALUE

    def test_fallback_ignores_invalid_processor_names(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.UNKNOWN,
            description="unknown op",
            suggested_processors=["NonExistentProcessor"],
        )
        steps = gen._convert_to_prepare_steps(step)
        # Invalid processor name is silently skipped
        assert steps == []

    def test_fallback_not_used_when_result_already_populated(self):
        gen = self._generator()
        # DROP_MISSING with columns produces a result; suggested_processors should not add more
        step = DataStep(
            step_number=1,
            operation=OperationType.DROP_MISSING,
            description="drop",
            columns=["col"],
            suggested_processors=["FillEmptyWithValue"],
        )
        steps = gen._convert_to_prepare_steps(step)
        assert len(steps) == 1


class TestCreateStackRecipe:
    """_create_stack_recipe with multiple input datasets."""

    def test_stack_two_inputs(self):
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.UNION,
                    description="Union A and B",
                    input_datasets=["table_a", "table_b"],
                    output_dataset="combined",
                    suggested_recipe="stack",
                )
            ],
            datasets=[
                DatasetInfo(name="table_a", is_input=True),
                DatasetInfo(name="table_b", is_input=True),
            ],
        )
        flow = LLMFlowGenerator().generate(analysis)
        stack_recipes = flow.get_recipes_by_type(RecipeType.STACK)
        assert len(stack_recipes) == 1
        recipe = stack_recipes[0]
        assert "table_a" in recipe.inputs
        assert "table_b" in recipe.inputs
        assert "combined" in recipe.outputs

    def test_stack_three_inputs(self):
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.UNION,
                    description="Union three tables",
                    input_datasets=["t1", "t2", "t3"],
                    output_dataset="all_data",
                    suggested_recipe="stack",
                )
            ],
            datasets=[
                DatasetInfo(name="t1", is_input=True),
                DatasetInfo(name="t2", is_input=True),
                DatasetInfo(name="t3", is_input=True),
            ],
        )
        flow = LLMFlowGenerator().generate(analysis)
        recipe = flow.get_recipes_by_type(RecipeType.STACK)[0]
        assert len(recipe.inputs) == 3

    def test_stack_output_dataset_name(self):
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.UNION,
                    description="Stack",
                    input_datasets=["x", "y"],
                    output_dataset="stacked_result",
                    suggested_recipe="stack",
                )
            ],
        )
        flow = LLMFlowGenerator().generate(analysis)
        recipe = flow.get_recipes_by_type(RecipeType.STACK)[0]
        assert recipe.outputs == ["stacked_result"]


class TestCreateSplitRecipe:
    """_create_split_recipe normal case and DAG cycle prevention."""

    def test_split_with_filter_conditions(self):
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.FILTER,
                    description="Split by status",
                    input_datasets=["orders"],
                    output_dataset="active_orders",
                    filter_conditions=[
                        FilterCondition(column="status", operator="equals", value="active")
                    ],
                    suggested_recipe="split",
                )
            ],
            datasets=[DatasetInfo(name="orders", is_input=True)],
        )
        flow = LLMFlowGenerator().generate(analysis)
        split_recipes = flow.get_recipes_by_type(RecipeType.SPLIT)
        assert len(split_recipes) == 1
        recipe = split_recipes[0]
        assert "orders" in recipe.inputs
        assert "active_orders" in recipe.outputs

    def test_split_builds_condition_string(self):
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.FILTER,
                    description="Condition split",
                    input_datasets=["raw"],
                    output_dataset="out",
                    filter_conditions=[
                        FilterCondition(column="amount", operator="greater_than", value=50),
                        FilterCondition(column="active", operator="equals", value=True),
                    ],
                    suggested_recipe="split",
                )
            ],
            datasets=[DatasetInfo(name="raw", is_input=True)],
        )
        flow = LLMFlowGenerator().generate(analysis)
        recipe = flow.get_recipes_by_type(RecipeType.SPLIT)[0]
        assert recipe.split_condition is not None
        assert "AND" in recipe.split_condition

    def test_split_prevents_dag_cycle_when_output_equals_input(self):
        """When output_dataset name matches input_dataset, output gets _filtered suffix."""
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.FILTER,
                    description="In-place split",
                    input_datasets=["data"],
                    output_dataset="data",  # Same as input - would cause cycle
                    suggested_recipe="split",
                )
            ],
            datasets=[DatasetInfo(name="data", is_input=True)],
        )
        flow = LLMFlowGenerator().generate(analysis)
        recipe = flow.get_recipes_by_type(RecipeType.SPLIT)[0]
        # Output must differ from input to prevent cycle
        assert recipe.outputs[0] != "data"
        assert recipe.outputs[0].endswith("_filtered")

    def test_split_no_conditions_produces_empty_condition(self):
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.FILTER,
                    description="No conditions",
                    input_datasets=["src"],
                    output_dataset="tgt",
                    suggested_recipe="split",
                )
            ],
        )
        flow = LLMFlowGenerator().generate(analysis)
        recipe = flow.get_recipes_by_type(RecipeType.SPLIT)[0]
        assert recipe.split_condition == ""


class TestCreateDistinctRecipe:
    """_create_distinct_recipe basic coverage."""

    def test_distinct_creates_correct_recipe_type(self):
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.DROP_DUPLICATES,
                    description="Remove duplicate rows",
                    input_datasets=["raw"],
                    output_dataset="unique_rows",
                    suggested_recipe="distinct",
                )
            ],
            datasets=[DatasetInfo(name="raw", is_input=True)],
        )
        flow = LLMFlowGenerator().generate(analysis)
        distinct_recipes = flow.get_recipes_by_type(RecipeType.DISTINCT)
        assert len(distinct_recipes) == 1

    def test_distinct_io_mapping(self):
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.DROP_DUPLICATES,
                    description="Deduplicate",
                    input_datasets=["dupes"],
                    output_dataset="clean",
                    suggested_recipe="distinct",
                )
            ],
        )
        flow = LLMFlowGenerator().generate(analysis)
        recipe = flow.get_recipes_by_type(RecipeType.DISTINCT)[0]
        assert "dupes" in recipe.inputs
        assert "clean" in recipe.outputs

    def test_distinct_default_output_name_when_no_output_dataset(self):
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.DROP_DUPLICATES,
                    description="Deduplicate",
                    input_datasets=["src"],
                    suggested_recipe="distinct",
                )
            ],
        )
        flow = LLMFlowGenerator().generate(analysis)
        recipe = flow.get_recipes_by_type(RecipeType.DISTINCT)[0]
        assert len(recipe.outputs) == 1
        assert recipe.outputs[0].startswith("distinct_")


class TestCreateSortRecipe:
    """_create_sort_recipe basic coverage."""

    def test_sort_creates_correct_recipe_type(self):
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.SORT,
                    description="Sort by date",
                    input_datasets=["events"],
                    output_dataset="sorted_events",
                    sort_columns=[{"column": "date", "order": "asc"}],
                    suggested_recipe="sort",
                )
            ],
            datasets=[DatasetInfo(name="events", is_input=True)],
        )
        flow = LLMFlowGenerator().generate(analysis)
        sort_recipes = flow.get_recipes_by_type(RecipeType.SORT)
        assert len(sort_recipes) == 1

    def test_sort_preserves_sort_columns(self):
        sort_cols = [{"column": "amount", "order": "desc"}, {"column": "id", "order": "asc"}]
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.SORT,
                    description="Multi-column sort",
                    input_datasets=["src"],
                    output_dataset="sorted",
                    sort_columns=sort_cols,
                    suggested_recipe="sort",
                )
            ],
        )
        flow = LLMFlowGenerator().generate(analysis)
        recipe = flow.get_recipes_by_type(RecipeType.SORT)[0]
        assert recipe.sort_columns == sort_cols

    def test_sort_default_output_name_when_no_output_dataset(self):
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.SORT,
                    description="Sort",
                    input_datasets=["src"],
                    suggested_recipe="sort",
                )
            ],
        )
        flow = LLMFlowGenerator().generate(analysis)
        recipe = flow.get_recipes_by_type(RecipeType.SORT)[0]
        assert recipe.outputs[0].startswith("sorted_")


class TestCreateWindowRecipe:
    """_create_window_recipe basic coverage."""

    def test_window_creates_correct_recipe_type(self):
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.WINDOW_FUNCTION,
                    description="Running sum",
                    input_datasets=["sales"],
                    output_dataset="sales_with_running_sum",
                    group_by_columns=["region"],
                    suggested_recipe="window",
                )
            ],
            datasets=[DatasetInfo(name="sales", is_input=True)],
        )
        flow = LLMFlowGenerator().generate(analysis)
        assert len(flow.get_recipes_by_type(RecipeType.WINDOW)) == 1

    def test_window_partition_columns_set_from_group_by(self):
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.WINDOW_FUNCTION,
                    description="Partition by user",
                    input_datasets=["raw"],
                    output_dataset="windowed",
                    group_by_columns=["user_id", "product"],
                    suggested_recipe="window",
                )
            ],
        )
        flow = LLMFlowGenerator().generate(analysis)
        recipe = flow.get_recipes_by_type(RecipeType.WINDOW)[0]
        assert recipe.partition_columns == ["user_id", "product"]

    def test_window_default_output_name_when_no_output_dataset(self):
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.WINDOW_FUNCTION,
                    description="Window",
                    input_datasets=["src"],
                    suggested_recipe="window",
                )
            ],
        )
        flow = LLMFlowGenerator().generate(analysis)
        recipe = flow.get_recipes_by_type(RecipeType.WINDOW)[0]
        assert recipe.outputs[0].startswith("windowed_")


class TestCreatePythonRecipe:
    """_create_python_recipe generates a code template and adds a recommendation."""

    def test_python_recipe_contains_code(self):
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.CUSTOM_FUNCTION,
                    description="Apply ML model",
                    input_datasets=["features"],
                    output_dataset="predictions",
                    suggested_recipe="python",
                )
            ],
            datasets=[DatasetInfo(name="features", is_input=True)],
        )
        flow = LLMFlowGenerator().generate(analysis)
        python_recipes = flow.get_recipes_by_type(RecipeType.PYTHON)
        assert len(python_recipes) == 1
        recipe = python_recipes[0]
        assert recipe.code is not None
        assert len(recipe.code) > 0

    def test_python_recipe_code_references_input_and_output(self):
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.CUSTOM_FUNCTION,
                    description="Custom step",
                    input_datasets=["my_input"],
                    output_dataset="my_output",
                    suggested_recipe="python",
                )
            ],
        )
        flow = LLMFlowGenerator().generate(analysis)
        recipe = flow.get_recipes_by_type(RecipeType.PYTHON)[0]
        assert "my_input" in recipe.code
        assert "my_output" in recipe.code

    def test_python_recipe_adds_recommendation(self):
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.CUSTOM_FUNCTION,
                    description="Some complex step",
                    input_datasets=["src"],
                    output_dataset="dst",
                    suggested_recipe="python",
                )
            ],
        )
        flow = LLMFlowGenerator().generate(analysis)
        rec_types = [r.type for r in flow.recommendations]
        assert "PYTHON_RECIPE" in rec_types

    def test_python_recipe_has_notes(self):
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.CUSTOM_FUNCTION,
                    description="Complex operation",
                    input_datasets=["src"],
                    output_dataset="dst",
                    suggested_recipe="python",
                )
            ],
        )
        flow = LLMFlowGenerator().generate(analysis)
        recipe = flow.get_recipes_by_type(RecipeType.PYTHON)[0]
        assert len(recipe.notes) >= 1
        assert any("Complex operation" in note for note in recipe.notes)

    def test_python_recipe_includes_reasoning_in_code(self):
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.CUSTOM_FUNCTION,
                    description="Complex",
                    input_datasets=["src"],
                    output_dataset="dst",
                    reasoning="This needs Python because of custom ML logic",
                    suggested_recipe="python",
                )
            ],
        )
        flow = LLMFlowGenerator().generate(analysis)
        recipe = flow.get_recipes_by_type(RecipeType.PYTHON)[0]
        # Reasoning appended to notes
        assert any("custom ML logic" in n for n in recipe.notes)

    def test_python_recipe_for_top_n_operation(self):
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.TOP_N,
                    description="Get top 10 customers",
                    input_datasets=["customers"],
                    output_dataset="top_customers",
                    suggested_recipe="topn",
                )
            ],
        )
        flow = LLMFlowGenerator().generate(analysis)
        assert len(flow.get_recipes_by_type(RecipeType.PYTHON)) == 1


class TestPrepareBufferFlushing:
    """Multiple prepare steps are buffered and flushed as one recipe when a non-prepare step follows."""

    def test_consecutive_prepare_steps_merged(self):
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.DROP_MISSING,
                    description="Drop nulls",
                    input_datasets=["raw"],
                    output_dataset="step1",
                    columns=["id"],
                    suggested_recipe="prepare",
                ),
                DataStep(
                    step_number=2,
                    operation=OperationType.RENAME_COLUMNS,
                    description="Rename",
                    input_datasets=["step1"],
                    output_dataset="step2",
                    rename_mapping={"old": "new"},
                    suggested_recipe="prepare",
                ),
            ],
            datasets=[DatasetInfo(name="raw", is_input=True)],
        )
        flow = LLMFlowGenerator().generate(analysis)
        prepare_recipes = flow.get_recipes_by_type(RecipeType.PREPARE)
        # Two consecutive prepare steps should be merged into one recipe
        assert len(prepare_recipes) == 1
        assert len(prepare_recipes[0].steps) == 2

    def test_prepare_buffer_flushed_before_grouping(self):
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.DROP_MISSING,
                    description="Clean nulls",
                    input_datasets=["raw"],
                    output_dataset="clean",
                    columns=["id"],
                    suggested_recipe="prepare",
                ),
                DataStep(
                    step_number=2,
                    operation=OperationType.GROUP_AGGREGATE,
                    description="Aggregate",
                    input_datasets=["clean"],
                    output_dataset="agg",
                    group_by_columns=["region"],
                    aggregations=[Aggregation("amount", "sum")],
                    suggested_recipe="grouping",
                ),
            ],
            datasets=[DatasetInfo(name="raw", is_input=True)],
        )
        flow = LLMFlowGenerator().generate(analysis)
        assert len(flow.get_recipes_by_type(RecipeType.PREPARE)) == 1
        assert len(flow.get_recipes_by_type(RecipeType.GROUPING)) == 1

    def test_prepare_buffer_flushed_before_join(self):
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.FILL_MISSING,
                    description="Fill",
                    input_datasets=["raw"],
                    output_dataset="filled",
                    columns=["score"],
                    fill_value="0",
                    suggested_recipe="prepare",
                ),
                DataStep(
                    step_number=2,
                    operation=OperationType.JOIN,
                    description="Join",
                    input_datasets=["filled", "lookup"],
                    output_dataset="joined",
                    join_conditions=[JoinCondition("id", "id")],
                    join_type="left",
                    suggested_recipe="join",
                ),
            ],
            datasets=[
                DatasetInfo(name="raw", is_input=True),
                DatasetInfo(name="lookup", is_input=True),
            ],
        )
        flow = LLMFlowGenerator().generate(analysis)
        assert len(flow.get_recipes_by_type(RecipeType.PREPARE)) == 1
        assert len(flow.get_recipes_by_type(RecipeType.JOIN)) == 1

    def test_trailing_prepare_steps_flushed_at_end(self):
        """Prepare steps at the end of the pipeline are flushed after all steps."""
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.GROUP_AGGREGATE,
                    description="Aggregate",
                    input_datasets=["raw"],
                    output_dataset="agg",
                    group_by_columns=["cat"],
                    aggregations=[Aggregation("val", "sum")],
                    suggested_recipe="grouping",
                ),
                DataStep(
                    step_number=2,
                    operation=OperationType.RENAME_COLUMNS,
                    description="Rename after agg",
                    input_datasets=["agg"],
                    output_dataset="final",
                    rename_mapping={"val_sum": "total"},
                    suggested_recipe="prepare",
                ),
            ],
            datasets=[DatasetInfo(name="raw", is_input=True)],
        )
        flow = LLMFlowGenerator().generate(analysis)
        # The trailing prepare step must appear in the flow
        assert len(flow.get_recipes_by_type(RecipeType.PREPARE)) == 1
        assert len(flow.get_recipes_by_type(RecipeType.GROUPING)) == 1

    def test_three_consecutive_prepare_steps_in_one_recipe(self):
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.DROP_MISSING,
                    description="Drop",
                    input_datasets=["src"],
                    output_dataset="s1",
                    columns=["a"],
                    suggested_recipe="prepare",
                ),
                DataStep(
                    step_number=2,
                    operation=OperationType.RENAME_COLUMNS,
                    description="Rename",
                    input_datasets=["s1"],
                    output_dataset="s2",
                    rename_mapping={"a": "b"},
                    suggested_recipe="prepare",
                ),
                DataStep(
                    step_number=3,
                    operation=OperationType.PARSE_DATE,
                    description="Parse date",
                    input_datasets=["s2"],
                    output_dataset="s3",
                    columns=["created"],
                    suggested_recipe="prepare",
                ),
            ],
            datasets=[DatasetInfo(name="src", is_input=True)],
        )
        flow = LLMFlowGenerator().generate(analysis)
        prepare_recipes = flow.get_recipes_by_type(RecipeType.PREPARE)
        assert len(prepare_recipes) == 1
        assert len(prepare_recipes[0].steps) == 3


class TestWriteDataHandling:
    """WRITE_DATA step marks a dataset as OUTPUT."""

    def test_write_data_marks_dataset_as_output(self):
        from py2dataiku.models.dataiku_dataset import DatasetType

        # The prepare step creates an intermediate output named "<input>_prepared_<n>".
        # The WRITE_DATA step references that intermediate by name so the generator
        # can locate and upgrade it to OUTPUT.
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.READ_DATA,
                    description="Read",
                    output_dataset="raw",
                ),
                DataStep(
                    step_number=2,
                    operation=OperationType.DROP_MISSING,
                    description="Clean",
                    input_datasets=["raw"],
                    output_dataset="clean",
                    columns=["id"],
                    suggested_recipe="prepare",
                ),
                DataStep(
                    step_number=3,
                    operation=OperationType.WRITE_DATA,
                    description="Write result",
                    # Reference the actual output produced by the prepare recipe
                    input_datasets=["raw_prepared_1"],
                ),
            ],
            datasets=[
                DatasetInfo(name="raw", is_input=True),
            ],
        )
        flow = LLMFlowGenerator().generate(analysis)
        output_datasets = [ds for ds in flow.datasets if ds.dataset_type == DatasetType.OUTPUT]
        assert len(output_datasets) >= 1

    def test_write_data_to_new_dataset(self):
        from py2dataiku.models.dataiku_dataset import DatasetType

        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.WRITE_DATA,
                    description="Write to final",
                    input_datasets=["result"],
                ),
            ],
            datasets=[DatasetInfo(name="result")],
        )
        flow = LLMFlowGenerator().generate(analysis)
        result_ds = flow.get_dataset("result")
        assert result_ds is not None
        assert result_ds.dataset_type == DatasetType.OUTPUT


class TestOptimizeFlag:
    """generate() respects optimize=True (default) and optimize=False."""

    def _simple_analysis(self):
        return _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.DROP_MISSING,
                    description="Clean",
                    input_datasets=["raw"],
                    output_dataset="clean",
                    columns=["id"],
                    suggested_recipe="prepare",
                ),
            ],
            datasets=[DatasetInfo(name="raw", is_input=True)],
        )

    def test_optimize_true_returns_flow(self):
        flow = LLMFlowGenerator().generate(self._simple_analysis(), optimize=True)
        assert flow is not None
        assert len(flow.recipes) >= 1

    def test_optimize_false_returns_flow(self):
        flow = LLMFlowGenerator().generate(self._simple_analysis(), optimize=False)
        assert flow is not None
        assert len(flow.recipes) >= 1

    def test_optimization_note_always_present(self):
        flow = LLMFlowGenerator().generate(self._simple_analysis())
        # optimization_notes includes the model_used note
        assert len(flow.optimization_notes) >= 1

    def test_optimize_false_does_not_crash(self):
        """Disabling optimize should not raise any exception."""
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.JOIN,
                    description="Join",
                    input_datasets=["a", "b"],
                    output_dataset="joined",
                    join_conditions=[JoinCondition("id", "id")],
                    suggested_recipe="join",
                )
            ],
            datasets=[
                DatasetInfo(name="a", is_input=True),
                DatasetInfo(name="b", is_input=True),
            ],
        )
        flow = LLMFlowGenerator().generate(analysis, optimize=False)
        assert len(flow.get_recipes_by_type(RecipeType.JOIN)) == 1


class TestRecommendationsAndWarnings:
    """Analysis recommendations and warnings are forwarded to the flow."""

    def test_recommendations_added_to_flow(self):
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.GROUP_AGGREGATE,
                    description="Agg",
                    input_datasets=["raw"],
                    output_dataset="agg",
                    group_by_columns=["cat"],
                    aggregations=[Aggregation("val", "sum")],
                    suggested_recipe="grouping",
                )
            ],
            recommendations=[
                "Consider adding a filter before aggregation for performance.",
                "Index the group-by column.",
            ],
        )
        flow = LLMFlowGenerator().generate(analysis)
        messages = [r.message for r in flow.recommendations]
        assert any("filter" in m for m in messages)
        assert any("Index" in m for m in messages)

    def test_recommendations_have_llm_suggestion_type(self):
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.DROP_MISSING,
                    description="Drop",
                    input_datasets=["src"],
                    output_dataset="dst",
                    columns=["id"],
                    suggested_recipe="prepare",
                )
            ],
            recommendations=["Review null handling strategy."],
        )
        flow = LLMFlowGenerator().generate(analysis)
        llm_recs = [r for r in flow.recommendations if r.type == "LLM_SUGGESTION"]
        assert len(llm_recs) >= 1

    def test_warnings_added_to_flow(self):
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.DROP_MISSING,
                    description="Drop",
                    input_datasets=["src"],
                    output_dataset="dst",
                    columns=["id"],
                    suggested_recipe="prepare",
                )
            ],
            warnings=["Large dataset detected - consider sampling first."],
        )
        flow = LLMFlowGenerator().generate(analysis)
        assert "Large dataset detected - consider sampling first." in flow.warnings

    def test_multiple_warnings_all_forwarded(self):
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.DROP_MISSING,
                    description="Drop",
                    input_datasets=["src"],
                    output_dataset="dst",
                    columns=["id"],
                    suggested_recipe="prepare",
                )
            ],
            warnings=["Warning A", "Warning B", "Warning C"],
        )
        flow = LLMFlowGenerator().generate(analysis)
        for w in ["Warning A", "Warning B", "Warning C"]:
            assert w in flow.warnings

    def test_no_recommendations_or_warnings_by_default(self):
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.DROP_MISSING,
                    description="Drop",
                    input_datasets=["src"],
                    output_dataset="dst",
                    columns=["id"],
                    suggested_recipe="prepare",
                )
            ],
        )
        flow = LLMFlowGenerator().generate(analysis)
        # No LLM_SUGGESTION recommendations (python recipe recs may be absent here)
        llm_recs = [r for r in flow.recommendations if r.type == "LLM_SUGGESTION"]
        assert len(llm_recs) == 0
        assert len(flow.warnings) == 0

    def test_model_used_added_to_optimization_notes(self):
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.DROP_MISSING,
                    description="Drop",
                    input_datasets=["src"],
                    output_dataset="dst",
                    columns=["id"],
                    suggested_recipe="prepare",
                )
            ],
        )
        analysis.model_used = "claude-3-sonnet"
        flow = LLMFlowGenerator().generate(analysis)
        assert any("claude-3-sonnet" in note for note in flow.optimization_notes)

    def test_model_used_fallback_when_none(self):
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.DROP_MISSING,
                    description="Drop",
                    input_datasets=["src"],
                    output_dataset="dst",
                    columns=["id"],
                    suggested_recipe="prepare",
                )
            ],
        )
        analysis.model_used = None
        flow = LLMFlowGenerator().generate(analysis)
        assert any("LLM" in note for note in flow.optimization_notes)


class TestNewPrepareStepHandlers:
    """Tests for the four newly added OperationType handlers in _convert_to_prepare_steps."""

    def _generator(self):
        gen = LLMFlowGenerator()
        from py2dataiku.models.dataiku_flow import DataikuFlow
        gen.flow = DataikuFlow(name="test")
        gen.recipe_counter = 0
        gen.dataset_map = {}
        return gen

    # --- SELECT_COLUMNS ---

    def test_select_columns_creates_columns_selector(self):
        from py2dataiku.models.prepare_step import ProcessorType
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.SELECT_COLUMNS,
            description="Keep only id and name",
            columns=["id", "name"],
        )
        steps = gen._convert_to_prepare_steps(step)
        assert len(steps) == 1
        assert steps[0].processor_type == ProcessorType.COLUMNS_SELECTOR

    def test_select_columns_params_contain_columns_and_keep_true(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.SELECT_COLUMNS,
            description="Select subset",
            columns=["a", "b", "c"],
        )
        steps = gen._convert_to_prepare_steps(step)
        assert steps[0].params["columns"] == ["a", "b", "c"]
        assert steps[0].params["keep"] is True

    def test_select_columns_empty_columns_returns_empty(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.SELECT_COLUMNS,
            description="Select nothing",
        )
        steps = gen._convert_to_prepare_steps(step)
        assert steps == []

    def test_select_columns_produces_prepare_recipe_in_flow(self):
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.SELECT_COLUMNS,
                    description="Keep only key columns",
                    input_datasets=["raw"],
                    output_dataset="slim",
                    columns=["id", "amount"],
                    suggested_recipe="prepare",
                )
            ],
            datasets=[DatasetInfo(name="raw", is_input=True)],
        )
        flow = LLMFlowGenerator().generate(analysis)
        prepare_recipes = flow.get_recipes_by_type(RecipeType.PREPARE)
        assert len(prepare_recipes) >= 1
        assert len(prepare_recipes[0].steps) == 1

    # --- ADD_COLUMN ---

    def test_add_column_with_transforms_creates_grel_step(self):
        from py2dataiku.models.prepare_step import ProcessorType
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.ADD_COLUMN,
            description="Add revenue column",
            column_transforms=[
                ColumnTransform(column="revenue", operation="price * quantity")
            ],
        )
        steps = gen._convert_to_prepare_steps(step)
        assert len(steps) == 1
        assert steps[0].processor_type == ProcessorType.CREATE_COLUMN_WITH_GREL

    def test_add_column_with_transforms_uses_expression_from_operation(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.ADD_COLUMN,
            description="Computed column",
            column_transforms=[
                ColumnTransform(column="full_name", operation="first_name + ' ' + last_name")
            ],
        )
        steps = gen._convert_to_prepare_steps(step)
        assert steps[0].params["expression"] == "first_name + ' ' + last_name"

    def test_add_column_with_output_column_uses_output_column_name(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.ADD_COLUMN,
            description="Derive new column",
            column_transforms=[
                ColumnTransform(
                    column="src",
                    operation="src * 2",
                    output_column="doubled",
                )
            ],
        )
        steps = gen._convert_to_prepare_steps(step)
        assert steps[0].params["column"] == "doubled"

    def test_add_column_without_output_column_uses_transform_column(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.ADD_COLUMN,
            description="In-place compute",
            column_transforms=[
                ColumnTransform(column="score", operation="score / 100")
            ],
        )
        steps = gen._convert_to_prepare_steps(step)
        assert steps[0].params["column"] == "score"

    def test_add_column_multiple_transforms_creates_multiple_steps(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.ADD_COLUMN,
            description="Multiple new columns",
            column_transforms=[
                ColumnTransform(column="col_a", operation="val1"),
                ColumnTransform(column="col_b", operation="val2"),
            ],
        )
        steps = gen._convert_to_prepare_steps(step)
        assert len(steps) == 2

    def test_add_column_no_transforms_uses_columns_fallback(self):
        from py2dataiku.models.prepare_step import ProcessorType
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.ADD_COLUMN,
            description="New column, no details",
            columns=["new_col"],
        )
        steps = gen._convert_to_prepare_steps(step)
        assert len(steps) == 1
        assert steps[0].processor_type == ProcessorType.CREATE_COLUMN_WITH_GREL
        assert steps[0].params["column"] == "new_col"
        assert steps[0].params["expression"] == ""

    def test_add_column_no_transforms_no_columns_uses_placeholder_name(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.ADD_COLUMN,
            description="Completely empty",
        )
        steps = gen._convert_to_prepare_steps(step)
        assert len(steps) == 1
        assert steps[0].params["column"] == "new_column"

    def test_add_column_produces_prepare_recipe_in_flow(self):
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.ADD_COLUMN,
                    description="Add tax column",
                    input_datasets=["sales"],
                    output_dataset="sales_with_tax",
                    column_transforms=[
                        ColumnTransform(
                            column="tax",
                            operation="amount * 0.2",
                            output_column="tax",
                        )
                    ],
                    suggested_recipe="prepare",
                )
            ],
            datasets=[DatasetInfo(name="sales", is_input=True)],
        )
        flow = LLMFlowGenerator().generate(analysis)
        prepare_recipes = flow.get_recipes_by_type(RecipeType.PREPARE)
        assert len(prepare_recipes) >= 1

    # --- SPLIT_COLUMN ---

    def test_split_column_creates_columns_splitter(self):
        from py2dataiku.models.prepare_step import ProcessorType
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.SPLIT_COLUMN,
            description="Split full_name on space",
            columns=["full_name"],
        )
        steps = gen._convert_to_prepare_steps(step)
        assert len(steps) == 1
        assert steps[0].processor_type == ProcessorType.SPLIT_COLUMN

    def test_split_column_uses_first_column(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.SPLIT_COLUMN,
            description="Split col",
            columns=["address", "city"],  # only first should be used
        )
        steps = gen._convert_to_prepare_steps(step)
        assert steps[0].params["column"] == "address"

    def test_split_column_default_separator_is_space(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.SPLIT_COLUMN,
            description="Split with default sep",
            columns=["name"],
        )
        steps = gen._convert_to_prepare_steps(step)
        assert steps[0].params["separator"] == " "

    def test_split_column_reads_separator_from_transform_parameters(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.SPLIT_COLUMN,
            description="Split on comma",
            columns=["tags"],
            column_transforms=[
                ColumnTransform(
                    column="tags",
                    operation="split",
                    parameters={"separator": ","},
                )
            ],
        )
        steps = gen._convert_to_prepare_steps(step)
        assert steps[0].params["separator"] == ","

    def test_split_column_reads_sep_alias_from_transform_parameters(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.SPLIT_COLUMN,
            description="Split on pipe",
            columns=["values"],
            column_transforms=[
                ColumnTransform(
                    column="values",
                    operation="split",
                    parameters={"sep": "|"},
                )
            ],
        )
        steps = gen._convert_to_prepare_steps(step)
        assert steps[0].params["separator"] == "|"

    def test_split_column_empty_columns_returns_empty(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.SPLIT_COLUMN,
            description="Split nothing",
        )
        steps = gen._convert_to_prepare_steps(step)
        assert steps == []

    def test_split_column_produces_prepare_recipe_in_flow(self):
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.SPLIT_COLUMN,
                    description="Split name",
                    input_datasets=["people"],
                    output_dataset="people_split",
                    columns=["full_name"],
                    column_transforms=[
                        ColumnTransform(
                            column="full_name",
                            operation="split",
                            parameters={"separator": " "},
                        )
                    ],
                    suggested_recipe="prepare",
                )
            ],
            datasets=[DatasetInfo(name="people", is_input=True)],
        )
        flow = LLMFlowGenerator().generate(analysis)
        assert len(flow.get_recipes_by_type(RecipeType.PREPARE)) >= 1

    # --- UNPIVOT ---

    def test_unpivot_creates_fold_multiple_columns(self):
        from py2dataiku.models.prepare_step import ProcessorType
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.UNPIVOT,
            description="Unpivot monthly columns",
            columns=["jan", "feb", "mar"],
        )
        steps = gen._convert_to_prepare_steps(step)
        assert len(steps) == 1
        assert steps[0].processor_type == ProcessorType.FOLD_MULTIPLE_COLUMNS

    def test_unpivot_params_include_columns(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.UNPIVOT,
            description="Melt quarters",
            columns=["q1", "q2", "q3", "q4"],
        )
        steps = gen._convert_to_prepare_steps(step)
        assert steps[0].params["columns"] == ["q1", "q2", "q3", "q4"]

    def test_unpivot_params_include_var_name_and_value_name(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.UNPIVOT,
            description="Unpivot",
            columns=["a", "b"],
        )
        steps = gen._convert_to_prepare_steps(step)
        # fold_multiple_columns sets default varName and valueName
        assert "varName" in steps[0].params
        assert "valueName" in steps[0].params

    def test_unpivot_empty_columns_returns_empty(self):
        gen = self._generator()
        step = DataStep(
            step_number=1,
            operation=OperationType.UNPIVOT,
            description="Unpivot nothing",
        )
        steps = gen._convert_to_prepare_steps(step)
        assert steps == []

    def test_unpivot_produces_prepare_recipe_in_flow(self):
        analysis = _make_analysis(
            steps=[
                DataStep(
                    step_number=1,
                    operation=OperationType.UNPIVOT,
                    description="Melt wide to long",
                    input_datasets=["wide"],
                    output_dataset="long",
                    columns=["2020", "2021", "2022"],
                    suggested_recipe="prepare",
                )
            ],
            datasets=[DatasetInfo(name="wide", is_input=True)],
        )
        flow = LLMFlowGenerator().generate(analysis)
        prepare_recipes = flow.get_recipes_by_type(RecipeType.PREPARE)
        assert len(prepare_recipes) >= 1
        assert len(prepare_recipes[0].steps) == 1
