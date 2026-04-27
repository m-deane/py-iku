"""M9 prompt-engineering: snapshot + structural tests for the LLM prompts.

These tests guard the LLM prompt contract that ``LLMCodeAnalyzer`` depends on.
They are intentionally string-level snapshot tests — they assert that key
sections, defensive instructions, and few-shot examples are present in the
prompt string. They do NOT call the live LLM API; the smoke tests below stub
the provider with ``MockProvider``.
"""
from __future__ import annotations

import json

import pytest

from py2dataiku.exceptions import LLMResponseParseError
from py2dataiku.llm.analyzer import (
    ANALYSIS_SYSTEM_PROMPT,
    LLMCodeAnalyzer,
    get_analysis_prompt,
)
from py2dataiku.llm.providers import MockProvider
from py2dataiku.llm.schemas import (
    ANALYSIS_JSON_SCHEMA,
    AnalysisResult,
    OperationType,
)


class TestSystemPromptStructure:
    """The system prompt must contain the canonical sections an effective
    structured-extraction prompt requires: role, objective, non-goals,
    schema reference, examples, output discipline, defensive fallbacks."""

    def test_has_role_section(self):
        assert "# Role" in ANALYSIS_SYSTEM_PROMPT

    def test_has_objective_section(self):
        assert "# Objective" in ANALYSIS_SYSTEM_PROMPT

    def test_has_non_goals_section(self):
        # Non-goals are the strongest defense against hallucinations.
        assert "# Non-Goals" in ANALYSIS_SYSTEM_PROMPT
        # And must explicitly forbid the most common LLM failure modes.
        assert "Do NOT execute" in ANALYSIS_SYSTEM_PROMPT
        assert "Do NOT invent recipe types" in ANALYSIS_SYSTEM_PROMPT
        assert "Do NOT rename DataFrame variables" in ANALYSIS_SYSTEM_PROMPT
        assert "chain-of-thought" in ANALYSIS_SYSTEM_PROMPT.lower()

    def test_has_edge_cases_section(self):
        # Edge-case section is what makes the prompt robust to weird inputs.
        assert "# Edge Cases" in ANALYSIS_SYSTEM_PROMPT
        for keyword in ("Empty", "Imports", "Multi-statement", "Untyped",
                        "Chained", "Custom UDFs", "Connectors", "When uncertain"):
            assert keyword in ANALYSIS_SYSTEM_PROMPT, (
                f"Edge case keyword {keyword!r} missing from prompt"
            )

    def test_has_sklearn_handling_section(self):
        assert "sklearn" in ANALYSIS_SYSTEM_PROMPT.lower()
        # sklearn → DSS processor mappings the LLM gets wrong by default.
        # Note: we deliberately AVOID the literal class names "OneHotEncoder"
        # and "StandardScaler" in the prompt because the LLM might echo them
        # back as suggested_processors (they're NOT DSS processor names).
        # The phantom-names test in test_llm.py guards this invariant.
        assert "min-max scaler" in ANALYSIS_SYSTEM_PROMPT.lower()
        assert "z-score" in ANALYSIS_SYSTEM_PROMPT.lower()
        assert "one-hot" in ANALYSIS_SYSTEM_PROMPT.lower()
        assert "MeasureNormalize" in ANALYSIS_SYSTEM_PROMPT
        assert "CategoricalEncoder" in ANALYSIS_SYSTEM_PROMPT

    def test_has_output_discipline_section(self):
        assert "# Output Discipline" in ANALYSIS_SYSTEM_PROMPT
        # No markdown fences instruction
        assert "No markdown code fences" in ANALYSIS_SYSTEM_PROMPT
        # Defensive uncertainty fallback
        assert "requires_python_recipe" in ANALYSIS_SYSTEM_PROMPT

    def test_has_defensive_uncertainty_fallback(self):
        # When uncertain, prefer prepare-with-no-processors over guessing.
        assert "When uncertain" in ANALYSIS_SYSTEM_PROMPT
        # Two-clause defensive instruction must appear:
        # (a) prefer prepare with no processors, (b) over fabricating a structural recipe.
        lower = ANALYSIS_SYSTEM_PROMPT.lower()
        assert "prepare" in lower
        assert "no" in lower and "processors" in lower

    def test_has_connector_handling(self):
        # Read connectors should map to sync recipes with sources captured.
        for connector in ("read_csv", "read_parquet", "read_sql", "read_excel"):
            assert connector in ANALYSIS_SYSTEM_PROMPT
        for writer in ("to_csv", "to_parquet", "to_sql"):
            assert writer in ANALYSIS_SYSTEM_PROMPT


class TestSystemPromptFewShotExamples:
    """The system prompt must include four worked examples covering the
    most error-prone pandas / sklearn patterns."""

    def test_has_four_numbered_examples(self):
        for i in (1, 2, 3, 4):
            assert f"### Example {i}:" in ANALYSIS_SYSTEM_PROMPT, (
                f"Missing few-shot example #{i}"
            )

    def test_groupby_example_uses_canonical_sum(self):
        # Example 1 must show "function": "SUM" (canonical), not "sum".
        assert '"function": "SUM"' in ANALYSIS_SYSTEM_PROMPT

    def test_melt_example_uses_fold_multiple_columns(self):
        # Example 2 must show melt -> FoldMultipleColumns, NOT pivot.
        assert '"suggested_processors": ["FoldMultipleColumns"]' in ANALYSIS_SYSTEM_PROMPT

    def test_etl_example_demonstrates_self_mutation(self):
        # Example 3 reuses 'orders' as both input and output for dropna.
        # The exact JSON snippet locks this in.
        assert '"input_datasets": ["orders"], "output_dataset": "orders"' in ANALYSIS_SYSTEM_PROMPT

    def test_sklearn_example_uses_measure_normalize(self):
        # Example 4 must show MinMaxScaler -> PREPARE+MeasureNormalize.
        assert "MinMaxScaler" in ANALYSIS_SYSTEM_PROMPT
        assert '"suggested_processors": ["MeasureNormalize"]' in ANALYSIS_SYSTEM_PROMPT

    def test_sklearn_example_uses_categorical_encoder_for_one_hot(self):
        # pd.get_dummies / OneHotEncoder must show CategoricalEncoder.
        assert '"suggested_processors": ["CategoricalEncoder"]' in ANALYSIS_SYSTEM_PROMPT


class TestUserPromptIsTight:
    """The user prompt is per-call (not cached), so it should be small."""

    def test_user_prompt_includes_code(self):
        prompt = get_analysis_prompt("import pandas as pd")
        assert "import pandas as pd" in prompt

    def test_user_prompt_references_required_top_level_fields(self):
        prompt = get_analysis_prompt("x = 1")
        for field in ("code_summary", "total_operations", "complexity_score",
                      "datasets", "steps", "recommendations", "warnings"):
            assert field in prompt

    def test_user_prompt_does_not_duplicate_full_schema(self):
        # The big inline JSON skeleton was moved to the system prompt — the
        # user prompt only references field names. Verify it stayed lean by
        # checking for an enum-listing pattern that used to appear inline.
        prompt = get_analysis_prompt("x = 1")
        assert "filter|join|grouping" not in prompt
        # Also check it's significantly smaller than the system prompt.
        assert len(prompt) < len(ANALYSIS_SYSTEM_PROMPT) // 2

    def test_user_prompt_instructs_no_markdown_fences(self):
        prompt = get_analysis_prompt("x = 1")
        # Either "no markdown" or the equivalent "no commentary" is acceptable.
        lower = prompt.lower()
        assert "no markdown" in lower or "no commentary" in lower

    def test_user_prompt_handles_empty_code(self):
        # Must not crash on empty input.
        prompt = get_analysis_prompt("")
        assert "Python Code to Analyze" in prompt


class TestSchemaContract:
    """The JSON schema must match what LLMFlowGenerator actually consumes."""

    def test_schema_required_top_level_fields(self):
        # These three are non-negotiable — the consumer relies on them.
        assert ANALYSIS_JSON_SCHEMA["required"] == ["steps", "datasets", "code_summary"]

    def test_schema_step_required_fields(self):
        step_schema = ANALYSIS_JSON_SCHEMA["properties"]["steps"]["items"]
        assert step_schema["required"] == ["step_number", "operation", "description"]

    def test_schema_operation_enum_matches_operation_type(self):
        # All OperationType values must be in the schema enum.
        step_schema = ANALYSIS_JSON_SCHEMA["properties"]["steps"]["items"]
        op_enum = step_schema["properties"]["operation"]["enum"]
        for op in OperationType:
            assert op.value in op_enum, f"OperationType.{op.name} missing from schema enum"

    def test_schema_complexity_score_bounded(self):
        # complexity_score is constrained to [1, 10] in both schema and prompt.
        cs = ANALYSIS_JSON_SCHEMA["properties"]["complexity_score"]
        assert cs["minimum"] == 1
        assert cs["maximum"] == 10


class TestSmokeAnalyzeWithStubbedProvider:
    """End-to-end: a stubbed provider returning known JSON must be parsed
    correctly by LLMCodeAnalyzer into a fully-populated AnalysisResult."""

    def _good_response(self) -> str:
        return json.dumps({
            "code_summary": "Read sales, group by region.",
            "total_operations": 2,
            "complexity_score": 3,
            "datasets": [
                {"name": "sales", "source": "sales.csv", "is_input": True, "is_output": False},
                {"name": "totals", "source": "derived", "is_input": False, "is_output": True},
            ],
            "steps": [
                {
                    "step_number": 1,
                    "operation": "read_data",
                    "description": "Read sales.csv",
                    "output_dataset": "sales",
                    "suggested_recipe": "sync",
                },
                {
                    "step_number": 2,
                    "operation": "group_aggregate",
                    "description": "Sum amount per region",
                    "input_datasets": ["sales"],
                    "output_dataset": "totals",
                    "group_by_columns": ["region"],
                    "aggregations": [
                        {"column": "amount", "function": "SUM", "output_column": "amount_sum"}
                    ],
                    "suggested_recipe": "grouping",
                },
            ],
            "recommendations": [],
            "warnings": [],
        })

    def test_stubbed_provider_yields_analysis_result(self):
        provider = MockProvider(responses={"sales": self._good_response()})
        analyzer = LLMCodeAnalyzer(provider=provider)

        result = analyzer.analyze(
            "import pandas as pd\nsales = pd.read_csv('sales.csv')"
        )

        assert isinstance(result, AnalysisResult)
        assert result.code_summary == "Read sales, group by region."
        assert len(result.steps) == 2
        assert result.steps[0].operation == OperationType.READ_DATA
        assert result.steps[1].operation == OperationType.GROUP_AGGREGATE
        # Post-processing fills in step numbers sequentially
        assert [s.step_number for s in result.steps] == [1, 2]

    def test_stubbed_provider_post_processes_recipe_inference(self):
        # An analysis with a step that has no suggested_recipe should still
        # get one filled in by _post_process.
        response = json.dumps({
            "code_summary": "filter",
            "datasets": [],
            "steps": [
                {
                    "step_number": 1,
                    "operation": "filter",
                    "description": "filter rows",
                }
            ],
        })
        provider = MockProvider(responses={"x": response})
        analyzer = LLMCodeAnalyzer(provider=provider)

        result = analyzer.analyze("x")
        assert result.steps[0].suggested_recipe == "prepare"

    def test_stubbed_provider_validates_processor_names(self):
        # An invalid processor name must be dropped and surfaced as a warning.
        response = json.dumps({
            "code_summary": "test",
            "datasets": [],
            "steps": [
                {
                    "step_number": 1,
                    "operation": "transform_column",
                    "description": "test",
                    "suggested_processors": ["FillEmptyWithValue", "NotAProcessor"],
                }
            ],
        })
        provider = MockProvider(responses={"x": response})
        analyzer = LLMCodeAnalyzer(provider=provider)

        result = analyzer.analyze("x")
        assert "FillEmptyWithValue" in result.steps[0].suggested_processors
        assert "NotAProcessor" not in result.steps[0].suggested_processors
        assert any("NotAProcessor" in w for w in result.warnings)


class TestInvalidJsonRaisesParseError:
    """Defensive parsing: bad LLM responses must raise LLMResponseParseError,
    not silently produce a malformed AnalysisResult."""

    def test_truncated_json_raises(self):
        # Truncated JSON — common when the model hits max_tokens.
        provider = MockProvider(responses={"x": '{"code_summary": "trunc'})
        analyzer = LLMCodeAnalyzer(provider=provider)
        with pytest.raises(LLMResponseParseError):
            analyzer.analyze("x")

    def test_garbage_response_raises(self):
        provider = MockProvider(responses={"x": "I'm sorry, I cannot help with that."})
        analyzer = LLMCodeAnalyzer(provider=provider)
        with pytest.raises(LLMResponseParseError):
            analyzer.analyze("x")

    def test_empty_response_raises(self):
        provider = MockProvider(responses={"x": ""})
        analyzer = LLMCodeAnalyzer(provider=provider)
        with pytest.raises(LLMResponseParseError):
            analyzer.analyze("x")

    def test_non_json_object_response_raises(self):
        # Valid JSON but not an object — from_dict will fail on .get().
        provider = MockProvider(responses={"x": "[1, 2, 3]"})
        analyzer = LLMCodeAnalyzer(provider=provider)
        # Either a parse error or AttributeError — we just want a clean failure mode.
        with pytest.raises((LLMResponseParseError, AttributeError, TypeError)):
            analyzer.analyze("x")


class TestPromptDeterminism:
    """The prompt must be byte-identical across imports — Anthropic prompt
    caching only hits when the cached portion is bit-stable."""

    def test_system_prompt_is_byte_stable(self):
        from py2dataiku.llm.analyzer import _build_analysis_system_prompt
        first = _build_analysis_system_prompt()
        second = _build_analysis_system_prompt()
        assert first == second

    def test_user_prompt_is_deterministic_for_same_code(self):
        code = "import pandas as pd\ndf = pd.read_csv('x.csv')"
        a = get_analysis_prompt(code)
        b = get_analysis_prompt(code)
        assert a == b


class TestEndToEndWithStubbedProviderAndGenerator:
    """Smoke test: stubbed provider -> LLMCodeAnalyzer -> LLMFlowGenerator -> DataikuFlow."""

    def test_full_pipeline_smoke(self):
        from py2dataiku.generators.llm_flow_generator import LLMFlowGenerator
        from py2dataiku.models.dataiku_recipe import RecipeType

        response = json.dumps({
            "code_summary": "Customer aggregation",
            "total_operations": 2,
            "complexity_score": 2,
            "datasets": [
                {"name": "customers", "source": "c.csv", "is_input": True},
                {"name": "summary", "is_output": True},
            ],
            "steps": [
                {
                    "step_number": 1,
                    "operation": "read_data",
                    "description": "Read",
                    "output_dataset": "customers",
                    "suggested_recipe": "sync",
                },
                {
                    "step_number": 2,
                    "operation": "group_aggregate",
                    "description": "Aggregate",
                    "input_datasets": ["customers"],
                    "output_dataset": "summary",
                    "group_by_columns": ["region"],
                    "aggregations": [{"column": "amount", "function": "SUM"}],
                    "suggested_recipe": "grouping",
                },
            ],
            "recommendations": [],
            "warnings": [],
        })

        provider = MockProvider(responses={"customers": response})
        analyzer = LLMCodeAnalyzer(provider=provider)
        generator = LLMFlowGenerator()

        analysis = analyzer.analyze(
            "import pandas as pd\ncustomers = pd.read_csv('c.csv')\n"
            "summary = customers.groupby('region').agg({'amount': 'sum'})"
        )
        flow = generator.generate(analysis, flow_name="smoke")

        assert flow.name == "smoke"
        assert len(flow.get_recipes_by_type(RecipeType.GROUPING)) == 1
