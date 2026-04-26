"""LLM-based Python code analyzer for py2dataiku."""

import json
from typing import Optional

from py2dataiku.exceptions import LLMResponseParseError
from py2dataiku.llm.providers import LLMProvider, get_provider
from py2dataiku.llm.schemas import AnalysisResult, DataStep, OperationType
from py2dataiku.mappings.processor_catalog import ProcessorCatalog


def _build_processor_catalog_section() -> str:
    """
    Auto-generate the processor catalog section of the system prompt
    from ``ProcessorCatalog.PROCESSORS``.

    Output is grouped by category and deterministically sorted (categories
    sorted alphabetically; processors within a category sorted by canonical
    ``ProcessorInfo.name``). Only canonical processor names + 1-line
    descriptions are emitted to keep the prompt compact.

    Each registry key maps to a ``ProcessorInfo``. Some keys are aliases
    (e.g. ``ColumnsSelector_delete`` maps to canonical name
    ``ColumnsSelector``) so we de-duplicate by the ``info.name`` field
    within each category.
    """
    by_category: dict[str, dict[str, str]] = {}
    for info in ProcessorCatalog.PROCESSORS.values():
        # De-duplicate aliased entries (different keys, same canonical name).
        # First occurrence wins; if any later entry shares the canonical
        # name, we keep the existing description (they describe the same
        # processor in DSS).
        bucket = by_category.setdefault(info.category, {})
        if info.name not in bucket:
            bucket[info.name] = info.description

    lines: list[str] = ["Dataiku Prepare Recipe Processors (grouped by category):"]
    for category in sorted(by_category):
        lines.append("")
        lines.append(f"{category}:")
        for name in sorted(by_category[category]):
            description = by_category[category][name]
            lines.append(f"- {name}: {description}")
    return "\n".join(lines)


def _build_analysis_system_prompt() -> str:
    """Construct the LLM system prompt with an auto-generated processor catalog."""
    return f"""You are an expert data engineer specializing in Python data processing and Dataiku DSS.

Your task is to analyze Python code that performs data manipulations (using pandas, numpy, etc.) and break it down into discrete data processing steps.

For each step, you must:
1. Identify the operation type (filter, join, aggregate, transform, etc.)
2. Identify input and output datasets (DataFrame variable names)
3. List all columns involved
4. Extract operation-specific details (filter conditions, aggregations, join keys, etc.)
5. Suggest the best Dataiku recipe type for this operation
6. Note if the operation requires a Python recipe (too complex for visual recipes)

Dataiku Recipe Types:
- prepare: Data cleaning, column transforms, filtering, type conversion
- join: Combining datasets on matching keys
- grouping: Aggregations with GROUP BY
- window: Window functions (running totals, LAG, LEAD, RANK)
- stack: Vertical concatenation (UNION)
- split: Splitting data into multiple outputs based on conditions
- pivot: Reshaping data from long to wide format
- sort: Ordering data
- distinct: Removing duplicates
- topn: Getting top/bottom N rows
- sampling: Random sampling
- python: Complex operations requiring custom code

{_build_processor_catalog_section()}

## Mapping Rules (non-obvious cases)

These pandas patterns map to specific DSS recipes — they are the cases where naive lexical matching gets the wrong answer:

- ``df.melt()`` / ``pd.melt(df, ...)`` -> **prepare** recipe with ``FoldMultipleColumns`` processor (NOT ``pivot`` — pivot is the opposite operation, long-to-wide)
- ``df.pivot()`` / ``df.pivot_table()`` -> **pivot** recipe
- ``df.rolling(N).mean()``, ``df.cumsum()``, ``df.expanding()``, ``df.shift()`` -> **window** recipe
- ``df.nlargest(N, col)`` / ``df.nsmallest(N, col)`` -> **topn** recipe
- ``df.head(N)`` / ``df.tail(N)`` / ``df.sample(...)`` -> **sampling** recipe
- ``df.round()``, ``df.abs()``, ``df.clip()`` -> **prepare** recipe with ``CreateColumnWithGREL`` (abs uses ``abs()`` formula)
- ``df.drop_duplicates()`` -> **distinct** recipe
- ``pd.concat([a, b, c])`` (axis=0, default) -> **stack** recipe
- ``df.merge()`` / ``pd.merge()`` -> **join** recipe
- ``pd.cut()`` / ``pd.qcut()`` -> **prepare** recipe with ``Binner`` processor
- ``pd.get_dummies()`` -> **prepare** recipe with ``CategoricalEncoder``
- ``df.groupby(...).agg({{col: ['sum', 'mean']}})`` (multi-function dict) -> **grouping** with one aggregation per (col, func) pair
- ``df[df.x > N]`` (single boolean mask) -> **prepare** with ``FilterOnNumericRange`` (NOT ``FilterOnValue`` — that field is for string matching)
- ``df[df.x == 'foo']`` -> **prepare** with ``FilterOnValue`` and ``matchingMode: FULL_STRING``
- ``df[(df.x > N) & (df.y < M)]`` (compound predicate) -> **prepare** with ``FilterOnFormula`` and a GREL ``formula``
- ``df[cond]`` and ``df[~cond]`` on the same source -> ONE multi-output **split** recipe (not two)

## Aggregation Function Naming

Use canonical DSS names in ``aggregations[].function``: ``SUM``, ``AVG`` (not ``MEAN``), ``COUNT``, ``COUNTD`` (not ``NUNIQUE`` or ``COUNTDISTINCT``), ``MIN``, ``MAX``, ``STDDEV`` (not ``STD``), ``VAR``, ``MEDIAN``, ``FIRST``, ``LAST``.

## Output Discipline

- Respond with EXACTLY ONE valid JSON object. No markdown code fences. No prose before or after.
- ``operation`` MUST be one of the OperationType enum values listed in the schema (e.g. ``read_data``, ``filter``, ``group_aggregate``, ``window_function``, ``join``, ``pivot``, ``unpivot``, ``sort``, ``top_n``, ``sample``, ``cast_type``, ``parse_date``, ``split_column``, ``encode_categorical``, ``normalize_scale``, ``geo_operation``, ``statistics``, ``custom_function``, ``unknown``).
- ``suggested_processors`` MUST contain only canonical names from the processor catalog above. Do NOT invent new names.
- If you cannot confidently map a step to a visual recipe, set ``requires_python_recipe: true`` and ``suggested_recipe: "python"``. Do NOT guess.
- For self-mutating ops like ``df = df.dropna()``, use the SAME variable name for both ``input_datasets`` and ``output_dataset`` — do not invent intermediate names like ``df_temp`` or ``df_initial``.

## Reasoning Approach

For each Python statement, internally: (1) identify the pandas/numpy operation, (2) pick the OperationType, (3) apply the Mapping Rules to pick the recipe, (4) pick processors if recipe is "prepare". Capture the reasoning in the step's ``reasoning`` field. Do NOT emit reasoning text outside the JSON.

Be precise and thorough. Extract ALL operations, even implicit ones."""


# System prompt for code analysis. Built once at import time from the
# ProcessorCatalog so the prompt cannot drift away from the actual code.
ANALYSIS_SYSTEM_PROMPT = _build_analysis_system_prompt()


def get_analysis_prompt(code: str) -> str:
    """Generate the analysis prompt for given code."""
    return f"""Analyze the following Python code and extract all data manipulation steps.

Return a JSON object with this structure:
{{
    "code_summary": "Brief description of what the code does",
    "total_operations": <number of distinct operations>,
    "complexity_score": <1-10 rating of complexity>,
    "datasets": [
        {{
            "name": "variable_name",
            "source": "file path or 'derived'",
            "is_input": true/false,
            "is_output": true/false,
            "inferred_columns": ["col1", "col2"]
        }}
    ],
    "steps": [
        {{
            "step_number": 1,
            "operation": "read_data|filter|join|group_aggregate|transform_column|...",
            "description": "Human-readable description",
            "input_datasets": ["dataset_name"],
            "output_dataset": "result_dataset",
            "columns": ["affected_columns"],
            "filter_conditions": [{{"column": "x", "operator": "greater_than", "value": 100}}],
            "aggregations": [{{"column": "amount", "function": "sum", "output_column": "total"}}],
            "group_by_columns": ["category"],
            "join_conditions": [{{"left_column": "id", "right_column": "id", "operator": "equals"}}],
            "join_type": "left|inner|right|outer",
            "column_transforms": [{{"column": "name", "operation": "uppercase"}}],
            "rename_mapping": {{"old_name": "new_name"}},
            "sort_columns": [{{"column": "date", "order": "desc"}}],
            "fill_value": null,
            "source_lines": [10, 11],
            "suggested_recipe": "prepare|join|grouping|...",
            "suggested_processors": ["StringTransformer", "FillEmptyWithValue"],
            "requires_python_recipe": false,
            "reasoning": "Why this mapping was chosen"
        }}
    ],
    "recommendations": ["optimization suggestions"],
    "warnings": ["potential issues"]
}}

Python Code to Analyze:
```python
{code}
```

Respond with ONLY the JSON object, no other text."""


class LLMCodeAnalyzer:
    """
    Analyze Python code using an LLM to extract data manipulation steps.

    This is the primary analyzer for py2dataiku, using an LLM to understand
    code semantics rather than relying on pattern matching.
    """

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        provider_name: str = "anthropic",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """
        Initialize the analyzer.

        Args:
            provider: Pre-configured LLMProvider instance
            provider_name: Provider name if no provider given ("anthropic", "openai")
            api_key: API key for provider
            model: Model name override
        """
        if provider:
            self.provider = provider
        else:
            self.provider = get_provider(provider_name, api_key, model)

    def analyze(self, code: str) -> AnalysisResult:
        """
        Analyze Python code and extract data manipulation steps.

        Args:
            code: Python source code to analyze

        Returns:
            AnalysisResult containing all extracted steps and metadata
        """
        prompt = get_analysis_prompt(code)

        try:
            # Call complete() directly (rather than complete_json) so we can
            # capture LLMResponse.usage and surface it on the AnalysisResult.
            # The MockProvider returns mock JSON that doesn't go through the
            # real-LLM path, so fall back to complete_json there.
            from py2dataiku.llm.providers import (
                AnthropicProvider,
                OpenAIProvider,
                _extract_json,
            )
            if isinstance(self.provider, (AnthropicProvider, OpenAIProvider)):
                # Mirror the JSON-instruction wrapping that complete_json does
                # so behaviour matches existing tests.
                json_system = (ANALYSIS_SYSTEM_PROMPT or "") + (
                    "\n\nYou must respond with valid JSON only. No other text."
                )
                llm_response = self.provider.complete(prompt, json_system)
                json_text = _extract_json(llm_response.content)
                response_data = json.loads(json_text)
                usage = llm_response.usage
            else:
                # MockProvider / custom provider — keep the old contract.
                response_data = self.provider.complete_json(
                    prompt=prompt,
                    system_prompt=ANALYSIS_SYSTEM_PROMPT,
                )
                usage = None

            result = AnalysisResult.from_dict(response_data)
            result.model_used = self.provider.model_name
            result.usage = usage
            result.raw_response = json.dumps(response_data)

            # Post-process to ensure consistency
            result = self._post_process(result)

            return result

        except json.JSONDecodeError as e:
            raise LLMResponseParseError(f"Failed to parse LLM response as JSON: {e}") from e

    def analyze_with_context(
        self,
        code: str,
        context: Optional[str] = None,
        existing_datasets: Optional[list[str]] = None,
    ) -> AnalysisResult:
        """
        Analyze code with additional context.

        Args:
            code: Python source code
            context: Additional context about the codebase or requirements
            existing_datasets: Names of datasets that already exist in Dataiku

        Returns:
            AnalysisResult
        """
        # Build enhanced prompt
        prompt = get_analysis_prompt(code)

        if context:
            prompt = f"Context: {context}\n\n{prompt}"

        if existing_datasets:
            prompt = f"Existing Dataiku datasets: {', '.join(existing_datasets)}\n\n{prompt}"

        try:
            response_data = self.provider.complete_json(
                prompt=prompt,
                system_prompt=ANALYSIS_SYSTEM_PROMPT,
            )

            result = AnalysisResult.from_dict(response_data)
            result.model_used = self.provider.model_name
            result = self._post_process(result)

            return result

        except json.JSONDecodeError as e:
            raise LLMResponseParseError(f"Failed to parse LLM response as JSON: {e}") from e

    def _post_process(self, result: AnalysisResult) -> AnalysisResult:
        """Post-process the analysis result for consistency."""
        # Ensure step numbers are sequential
        for i, step in enumerate(result.steps, 1):
            step.step_number = i

        # Validate operation types
        for step in result.steps:
            if isinstance(step.operation, str):
                try:
                    step.operation = OperationType(step.operation)
                except ValueError:
                    step.operation = OperationType.UNKNOWN

        # Add default suggestions if missing
        for step in result.steps:
            if not step.suggested_recipe:
                step.suggested_recipe = self._infer_recipe(step)

        # Validate suggested_processors against ProcessorCatalog. Wave A
        # determinism prober found the LLM occasionally invents processor
        # names that aren't in the catalog (e.g. invented sklearn names).
        # Drop unknown names and surface a warning so the user knows what
        # happened, rather than silently failing downstream when
        # LLMFlowGenerator tries to look the name up.
        canonical_names = {
            info.name for info in ProcessorCatalog.PROCESSORS.values()
        }
        for step in result.steps:
            if not step.suggested_processors:
                continue
            valid = []
            invalid = []
            for proc_name in step.suggested_processors:
                if proc_name in canonical_names:
                    valid.append(proc_name)
                else:
                    invalid.append(proc_name)
            if invalid:
                step.suggested_processors = valid
                result.warnings.append(
                    f"Step {step.step_number}: dropped unknown processor names "
                    f"{invalid} (not in ProcessorCatalog). Valid alternatives "
                    f"can be found in py2dataiku.mappings.processor_catalog.ProcessorCatalog."
                )

        # Update total operations count
        result.total_operations = len(result.steps)

        return result

    def _infer_recipe(self, step: DataStep) -> str:
        """Infer the best Dataiku recipe type for a step."""
        op = step.operation

        recipe_map = {
            OperationType.READ_DATA: "sync",
            OperationType.WRITE_DATA: "sync",
            OperationType.FILTER: "prepare",
            OperationType.SELECT_COLUMNS: "prepare",
            OperationType.DROP_COLUMNS: "prepare",
            OperationType.RENAME_COLUMNS: "prepare",
            OperationType.ADD_COLUMN: "prepare",
            OperationType.TRANSFORM_COLUMN: "prepare",
            OperationType.FILL_MISSING: "prepare",
            OperationType.DROP_MISSING: "prepare",
            OperationType.DROP_DUPLICATES: "distinct",
            OperationType.GROUP_AGGREGATE: "grouping",
            OperationType.WINDOW_FUNCTION: "window",
            OperationType.JOIN: "join",
            OperationType.UNION: "stack",
            OperationType.PIVOT: "pivot",
            OperationType.UNPIVOT: "prepare",  # FOLD_MULTIPLE_COLUMNS in PREPARE
            OperationType.SORT: "sort",
            OperationType.TOP_N: "topn",
            OperationType.SAMPLE: "sampling",
            OperationType.CAST_TYPE: "prepare",
            OperationType.PARSE_DATE: "prepare",
            OperationType.SPLIT_COLUMN: "prepare",
            OperationType.ENCODE_CATEGORICAL: "prepare",
            OperationType.NORMALIZE_SCALE: "prepare",
            OperationType.GEO_OPERATION: "prepare",
            OperationType.STATISTICS: "generate_statistics",
            OperationType.CUSTOM_FUNCTION: "python",
            OperationType.UNKNOWN: "python",
        }

        return recipe_map.get(op, "python")

    def get_optimization_suggestions(self, result: AnalysisResult) -> list[str]:
        """
        Get optimization suggestions for the analyzed code.

        Args:
            result: Analysis result to optimize

        Returns:
            List of optimization suggestions
        """
        suggestions = []

        # Check for filter after join
        for i, step in enumerate(result.steps):
            if step.operation == OperationType.FILTER and i > 0:
                prev_step = result.steps[i - 1]
                if prev_step.operation == OperationType.JOIN:
                    suggestions.append(
                        f"Step {step.step_number}: Consider moving filter before join "
                        f"to reduce data volume (currently after step {prev_step.step_number})"
                    )

        # Check for multiple consecutive prepare-type operations
        prepare_streak = 0
        for step in result.steps:
            if step.suggested_recipe == "prepare":
                prepare_streak += 1
            else:
                if prepare_streak > 1:
                    suggestions.append(
                        f"Found {prepare_streak} consecutive prepare operations - "
                        "these can be combined into a single Prepare recipe"
                    )
                prepare_streak = 0

        # Check for Python recipe requirements
        python_steps = [s for s in result.steps if s.requires_python_recipe]
        if python_steps:
            suggestions.append(
                f"{len(python_steps)} operation(s) require Python recipes - "
                "review if visual alternatives exist"
            )

        return suggestions
