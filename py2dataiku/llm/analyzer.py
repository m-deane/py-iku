"""LLM-based Python code analyzer for py2dataiku."""

import json
from typing import List, Optional

from py2dataiku.exceptions import LLMResponseParseError, ProviderError
from py2dataiku.llm.providers import LLMProvider, get_provider
from py2dataiku.llm.schemas import AnalysisResult, DataStep, OperationType


# System prompt for code analysis
ANALYSIS_SYSTEM_PROMPT = """You are an expert data engineer specializing in Python data processing and Dataiku DSS.

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

Dataiku Prepare Recipe Processors:
- FillEmptyWithValue: Fill nulls with a constant
- RemoveRowsOnEmpty: Drop rows with nulls
- ColumnRenamer: Rename columns
- ColumnDeleter: Drop columns
- StringTransformer: String operations (upper, lower, trim)
- TypeSetter: Change column data types
- DateParser: Parse string to date
- FilterOnValue: Filter rows by value
- CreateColumnWithGREL: Create computed column
- Binner: Bin numeric values
- Normalizer: Normalize/standardize values
- RegexpExtractor: Extract with regex
- RemoveDuplicates: Deduplicate rows

Be precise and thorough. Extract ALL operations, even implicit ones."""


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
            response_data = self.provider.complete_json(
                prompt=prompt,
                system_prompt=ANALYSIS_SYSTEM_PROMPT,
            )

            result = AnalysisResult.from_dict(response_data)
            result.model_used = self.provider.model_name
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
        existing_datasets: Optional[List[str]] = None,
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
            OperationType.UNPIVOT: "pivot",
            OperationType.SORT: "sort",
            OperationType.TOP_N: "topn",
            OperationType.SAMPLE: "sampling",
            OperationType.CAST_TYPE: "prepare",
            OperationType.PARSE_DATE: "prepare",
            OperationType.CUSTOM_FUNCTION: "python",
            OperationType.UNKNOWN: "python",
        }

        return recipe_map.get(op, "python")

    def get_optimization_suggestions(self, result: AnalysisResult) -> List[str]:
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
