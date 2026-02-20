"""Generate Dataiku flows from LLM-analyzed steps."""

from typing import Dict, List, Optional

from py2dataiku.generators.base_generator import BaseFlowGenerator
from py2dataiku.llm.schemas import (
    AnalysisResult,
    DataStep,
    OperationType,
)
from py2dataiku.mappings.pandas_mappings import PandasMapper
from py2dataiku.models.dataiku_flow import DataikuFlow
from py2dataiku.models.dataiku_recipe import (
    Aggregation,
    DataikuRecipe,
    JoinKey,
    JoinType,
    RecipeType,
)
from py2dataiku.models.dataiku_dataset import DataikuDataset, DatasetType
from py2dataiku.models.prepare_step import PrepareStep, ProcessorType, StringTransformerMode


class LLMFlowGenerator(BaseFlowGenerator):
    """
    Generate Dataiku flows from LLM-analyzed code.

    This generator takes the structured output from LLMCodeAnalyzer
    and converts it to a complete DataikuFlow with datasets and recipes.
    """

    def __init__(self):
        super().__init__()
        self.dataset_map: Dict[str, str] = {}  # variable name -> dataset name

    def generate(
        self,
        analysis: AnalysisResult,
        flow_name: str = "converted_flow",
        optimize: bool = True,
    ) -> DataikuFlow:
        """
        Generate a Dataiku flow from LLM analysis result.

        Args:
            analysis: AnalysisResult from LLMCodeAnalyzer
            flow_name: Name for the generated flow
            optimize: Whether to optimize the flow

        Returns:
            DataikuFlow object
        """
        self.flow = DataikuFlow(name=flow_name)
        self.recipe_counter = 0
        self.dataset_map = {}

        # Register datasets from analysis
        for ds_info in analysis.datasets:
            ds_type = DatasetType.INPUT if ds_info.is_input else (
                DatasetType.OUTPUT if ds_info.is_output else DatasetType.INTERMEDIATE
            )
            dataset = DataikuDataset(
                name=self._sanitize_name(ds_info.name),
                dataset_type=ds_type,
                source_variable=ds_info.name,
            )
            # Add inferred columns
            for col in ds_info.inferred_columns:
                dataset.add_column(col, "string")  # Default type

            self.flow.add_dataset(dataset)
            self.dataset_map[ds_info.name] = dataset.name

        # Group steps by output dataset and recipe type for merging
        prepare_steps_buffer: List[DataStep] = []
        current_input: Optional[str] = None

        for step in analysis.steps:
            # Handle data reading
            if step.operation == OperationType.READ_DATA:
                if step.output_dataset:
                    current_input = self._get_or_create_dataset(
                        step.output_dataset, DatasetType.INPUT
                    )
                continue

            # Handle data writing
            if step.operation == OperationType.WRITE_DATA:
                if step.input_datasets:
                    ds = self.flow.get_dataset(
                        self._get_or_create_dataset(step.input_datasets[0], DatasetType.OUTPUT)
                    )
                    if ds:
                        ds.dataset_type = DatasetType.OUTPUT
                continue

            # Get input dataset for this step
            if step.input_datasets:
                current_input = self._get_or_create_dataset(
                    step.input_datasets[0], DatasetType.INTERMEDIATE
                )

            # Route based on suggested recipe type
            suggested = (step.suggested_recipe or "python").lower().strip()

            if suggested == "prepare":
                # Buffer prepare steps to merge them
                prepare_steps_buffer.append(step)

            elif suggested == "grouping":
                # Flush prepare buffer first
                if prepare_steps_buffer:
                    current_input = self._create_prepare_recipe(
                        current_input, prepare_steps_buffer
                    )
                    prepare_steps_buffer = []

                current_input = self._create_grouping_recipe(step, current_input)

            elif suggested == "join":
                if prepare_steps_buffer:
                    current_input = self._create_prepare_recipe(
                        current_input, prepare_steps_buffer
                    )
                    prepare_steps_buffer = []

                current_input = self._create_join_recipe(step, current_input)

            elif suggested == "stack":
                if prepare_steps_buffer:
                    current_input = self._create_prepare_recipe(
                        current_input, prepare_steps_buffer
                    )
                    prepare_steps_buffer = []

                current_input = self._create_stack_recipe(step)

            elif suggested == "split":
                if prepare_steps_buffer:
                    current_input = self._create_prepare_recipe(
                        current_input, prepare_steps_buffer
                    )
                    prepare_steps_buffer = []

                current_input = self._create_split_recipe(step, current_input)

            elif suggested == "distinct":
                if prepare_steps_buffer:
                    current_input = self._create_prepare_recipe(
                        current_input, prepare_steps_buffer
                    )
                    prepare_steps_buffer = []

                current_input = self._create_distinct_recipe(step, current_input)

            elif suggested == "sort":
                if prepare_steps_buffer:
                    current_input = self._create_prepare_recipe(
                        current_input, prepare_steps_buffer
                    )
                    prepare_steps_buffer = []

                current_input = self._create_sort_recipe(step, current_input)

            elif suggested == "window":
                if prepare_steps_buffer:
                    current_input = self._create_prepare_recipe(
                        current_input, prepare_steps_buffer
                    )
                    prepare_steps_buffer = []

                current_input = self._create_window_recipe(step, current_input)

            elif suggested in ("python", "topn", "sampling", "pivot"):
                if prepare_steps_buffer:
                    current_input = self._create_prepare_recipe(
                        current_input, prepare_steps_buffer
                    )
                    prepare_steps_buffer = []

                current_input = self._create_python_recipe(step, current_input)

            # Update dataset map
            if step.output_dataset:
                self.dataset_map[step.output_dataset] = current_input

        # Flush remaining prepare steps
        if prepare_steps_buffer:
            self._create_prepare_recipe(current_input, prepare_steps_buffer)

        # Add analysis recommendations to flow
        for rec in analysis.recommendations:
            self.flow.add_recommendation(
                type="LLM_SUGGESTION",
                priority="MEDIUM",
                message=rec,
            )

        for warn in analysis.warnings:
            self.flow.warnings.append(warn)

        self.flow.optimization_notes.append(
            f"Analyzed with {analysis.model_used or 'LLM'}"
        )

        if optimize:
            self._optimize_flow()

        return self.flow

    def _get_or_create_dataset(self, name: str, ds_type: DatasetType) -> str:
        """Get existing dataset or create new one."""
        sanitized = self._sanitize_name(name)

        if sanitized in self.dataset_map:
            return self.dataset_map[sanitized]

        if self.flow.get_dataset(sanitized):
            return sanitized

        dataset = DataikuDataset(name=sanitized, dataset_type=ds_type)
        self.flow.add_dataset(dataset)
        self.dataset_map[name] = sanitized
        return sanitized

    def _create_prepare_recipe(
        self, input_dataset: Optional[str], steps: List[DataStep]
    ) -> str:
        """Create a Prepare recipe from multiple steps."""
        self.recipe_counter += 1
        output_name = f"{input_dataset or 'data'}_prepared_{self.recipe_counter}"

        prepare_steps = []
        for step in steps:
            prepare_steps.extend(self._convert_to_prepare_steps(step))

        recipe = DataikuRecipe.create_prepare(
            name=f"prepare_{self.recipe_counter}",
            input_dataset=input_dataset or "",
            output_dataset=output_name,
            steps=prepare_steps,
        )

        # Add reasoning notes
        for step in steps:
            if step.reasoning:
                recipe.notes.append(step.reasoning)

        self.flow.add_recipe(recipe)
        return output_name

    def _convert_to_prepare_steps(self, step: DataStep) -> List[PrepareStep]:
        """Convert a DataStep to PrepareStep objects."""
        result = []

        op = step.operation

        if op == OperationType.FILL_MISSING:
            for col in step.columns:
                result.append(PrepareStep.fill_empty(col, step.fill_value or ""))

        elif op == OperationType.DROP_MISSING:
            if step.columns:
                result.append(PrepareStep.remove_rows_on_empty(step.columns))

        elif op == OperationType.RENAME_COLUMNS:
            if step.rename_mapping:
                result.append(PrepareStep.rename_columns(step.rename_mapping))

        elif op == OperationType.DROP_COLUMNS:
            if step.columns:
                result.append(PrepareStep.delete_columns(step.columns))

        elif op == OperationType.TRANSFORM_COLUMN:
            for transform in step.column_transforms:
                prep_step = self._create_transform_step(transform)
                if prep_step:
                    result.append(prep_step)

        elif op == OperationType.FILTER:
            for condition in step.filter_conditions:
                result.append(
                    PrepareStep.filter_on_value(
                        column=condition.column,
                        values=[condition.value],
                        matching_mode=self._map_operator(condition.operator),
                        keep=True,
                    )
                )

        elif op == OperationType.CAST_TYPE:
            for transform in step.column_transforms:
                if transform.operation in ("cast", "astype", "convert"):
                    target_type = transform.parameters.get("type", "string")
                    result.append(PrepareStep.set_type(transform.column, target_type))

        elif op == OperationType.PARSE_DATE:
            for col in step.columns:
                result.append(PrepareStep.parse_date(col))

        elif op == OperationType.DROP_DUPLICATES:
            result.append(PrepareStep.remove_duplicates(step.columns or None))

        # Use suggested processors from LLM if available
        if not result and step.suggested_processors:
            for proc_name in step.suggested_processors:
                try:
                    proc_type = ProcessorType(proc_name)
                    result.append(PrepareStep(processor_type=proc_type, params={}))
                except ValueError:
                    pass

        return result

    def _create_transform_step(self, transform) -> Optional[PrepareStep]:
        """Create a PrepareStep from a column transform."""
        op = transform.operation.lower()

        string_ops = {
            "uppercase": StringTransformerMode.UPPERCASE,
            "upper": StringTransformerMode.UPPERCASE,
            "lowercase": StringTransformerMode.LOWERCASE,
            "lower": StringTransformerMode.LOWERCASE,
            "title": StringTransformerMode.TITLECASE,
            "titlecase": StringTransformerMode.TITLECASE,
            "strip": StringTransformerMode.TRIM,
            "trim": StringTransformerMode.TRIM,
        }

        if op in string_ops:
            return PrepareStep.string_transform(transform.column, string_ops[op])

        if op in ("round", "rounding"):
            precision = transform.parameters.get("precision", 2)
            return PrepareStep(
                processor_type=ProcessorType.ROUND_COLUMN,
                params={"column": transform.column, "precision": precision},
            )

        if op in ("abs", "absolute"):
            return PrepareStep(
                processor_type=ProcessorType.ABS_COLUMN,
                params={"column": transform.column},
            )

        # Default: create GREL expression
        return PrepareStep.create_column_grel(
            column=transform.output_column or transform.column,
            expression=f"{transform.column}",  # Placeholder
        )

    def _map_operator(self, operator: str) -> str:
        """Map filter operator to Dataiku matching mode."""
        op_map = {
            "equals": "EQUALS",
            "not_equals": "NOT_EQUALS",
            "greater_than": "GREATER_THAN",
            "greater_or_equal": "GREATER_OR_EQUAL",
            "less_than": "LESS_THAN",
            "less_or_equal": "LESS_OR_EQUAL",
            "contains": "CONTAINS",
            "starts_with": "STARTS_WITH",
            "ends_with": "ENDS_WITH",
            "regex": "REGEX",
            "in": "IN",
        }
        return op_map.get(operator.lower(), "EQUALS")

    def _create_grouping_recipe(
        self, step: DataStep, input_dataset: Optional[str]
    ) -> str:
        """Create a Grouping recipe."""
        self.recipe_counter += 1
        output_name = step.output_dataset or f"grouped_{self.recipe_counter}"
        output_name = self._sanitize_name(output_name)

        aggregations = [
            Aggregation(
                column=agg.column,
                function=agg.function.upper(),
                output_column=agg.output_column,
            )
            for agg in step.aggregations
        ]

        recipe = DataikuRecipe.create_grouping(
            name=f"grouping_{self.recipe_counter}",
            input_dataset=input_dataset or "",
            output_dataset=output_name,
            keys=step.group_by_columns,
            aggregations=aggregations,
        )

        if step.reasoning:
            recipe.notes.append(step.reasoning)

        self.flow.add_recipe(recipe)
        return output_name

    def _create_join_recipe(
        self, step: DataStep, left_input: Optional[str]
    ) -> str:
        """Create a Join recipe."""
        self.recipe_counter += 1
        output_name = step.output_dataset or f"joined_{self.recipe_counter}"
        output_name = self._sanitize_name(output_name)

        # Get right input
        right_input = ""
        if len(step.input_datasets) > 1:
            right_input = self._get_or_create_dataset(
                step.input_datasets[1], DatasetType.INTERMEDIATE
            )

        # Map join type
        join_type = JoinType(
            PandasMapper.JOIN_MAPPINGS.get(
                (step.join_type or "inner").lower(), "INNER"
            )
        )

        join_keys = [
            JoinKey(
                left_column=jc.left_column,
                right_column=jc.right_column,
            )
            for jc in step.join_conditions
        ]

        recipe = DataikuRecipe.create_join(
            name=f"join_{self.recipe_counter}",
            left_dataset=left_input or "",
            right_dataset=right_input,
            output_dataset=output_name,
            join_keys=join_keys,
            join_type=join_type,
        )

        if step.reasoning:
            recipe.notes.append(step.reasoning)

        self.flow.add_recipe(recipe)
        return output_name

    def _create_stack_recipe(self, step: DataStep) -> str:
        """Create a Stack recipe."""
        self.recipe_counter += 1
        output_name = step.output_dataset or f"stacked_{self.recipe_counter}"
        output_name = self._sanitize_name(output_name)

        inputs = [
            self._get_or_create_dataset(ds, DatasetType.INTERMEDIATE)
            for ds in step.input_datasets
        ]

        recipe = DataikuRecipe(
            name=f"stack_{self.recipe_counter}",
            recipe_type=RecipeType.STACK,
            inputs=inputs,
            outputs=[output_name],
        )

        self.flow.add_recipe(recipe)
        return output_name

    def _create_split_recipe(
        self, step: DataStep, input_dataset: Optional[str]
    ) -> str:
        """Create a Split recipe."""
        self.recipe_counter += 1
        output_name = step.output_dataset or f"filtered_{self.recipe_counter}"
        output_name = self._sanitize_name(output_name)

        # Build condition string
        conditions = []
        for fc in step.filter_conditions:
            conditions.append(f"{fc.column} {fc.operator} {fc.value}")
        condition_str = " AND ".join(conditions) if conditions else ""

        recipe = DataikuRecipe(
            name=f"split_{self.recipe_counter}",
            recipe_type=RecipeType.SPLIT,
            inputs=[input_dataset or ""],
            outputs=[output_name],
            split_condition=condition_str,
        )

        if step.reasoning:
            recipe.notes.append(step.reasoning)

        self.flow.add_recipe(recipe)
        return output_name

    def _create_distinct_recipe(
        self, step: DataStep, input_dataset: Optional[str]
    ) -> str:
        """Create a Distinct recipe."""
        self.recipe_counter += 1
        output_name = step.output_dataset or f"distinct_{self.recipe_counter}"
        output_name = self._sanitize_name(output_name)

        recipe = DataikuRecipe(
            name=f"distinct_{self.recipe_counter}",
            recipe_type=RecipeType.DISTINCT,
            inputs=[input_dataset or ""],
            outputs=[output_name],
        )

        self.flow.add_recipe(recipe)
        return output_name

    def _create_sort_recipe(
        self, step: DataStep, input_dataset: Optional[str]
    ) -> str:
        """Create a Sort recipe."""
        self.recipe_counter += 1
        output_name = step.output_dataset or f"sorted_{self.recipe_counter}"
        output_name = self._sanitize_name(output_name)

        recipe = DataikuRecipe(
            name=f"sort_{self.recipe_counter}",
            recipe_type=RecipeType.SORT,
            inputs=[input_dataset or ""],
            outputs=[output_name],
            sort_columns=step.sort_columns,
        )

        self.flow.add_recipe(recipe)
        return output_name

    def _create_window_recipe(
        self, step: DataStep, input_dataset: Optional[str]
    ) -> str:
        """Create a Window recipe."""
        self.recipe_counter += 1
        output_name = step.output_dataset or f"windowed_{self.recipe_counter}"
        output_name = self._sanitize_name(output_name)

        recipe = DataikuRecipe(
            name=f"window_{self.recipe_counter}",
            recipe_type=RecipeType.WINDOW,
            inputs=[input_dataset or ""],
            outputs=[output_name],
            partition_columns=step.group_by_columns,
        )

        self.flow.add_recipe(recipe)
        return output_name

    def _create_python_recipe(
        self, step: DataStep, input_dataset: Optional[str]
    ) -> str:
        """Create a Python recipe for complex operations."""
        self.recipe_counter += 1
        output_name = step.output_dataset or f"processed_{self.recipe_counter}"
        output_name = self._sanitize_name(output_name)

        # Generate code comment
        code = f"""# {step.description}
# Operation: {step.operation.value}
# Suggested processors: {', '.join(step.suggested_processors) if step.suggested_processors else 'None'}

import dataiku
import pandas as pd

# Read input
input_dataset = dataiku.Dataset("{input_dataset or 'INPUT'}")
df = input_dataset.get_dataframe()

# TODO: Implement {step.operation.value} operation
# {step.reasoning or ''}

# Write output
output_dataset = dataiku.Dataset("{output_name}")
output_dataset.write_with_schema(df)
"""

        recipe = DataikuRecipe.create_python(
            name=f"python_{self.recipe_counter}",
            inputs=[input_dataset] if input_dataset else [],
            outputs=[output_name],
            code=code,
        )

        recipe.notes.append(f"Complex operation: {step.description}")
        if step.reasoning:
            recipe.notes.append(step.reasoning)

        self.flow.add_recipe(recipe)

        # Add recommendation
        self.flow.add_recommendation(
            type="PYTHON_RECIPE",
            priority="MEDIUM",
            message=f"Step '{step.description}' requires Python recipe",
            action="Review if visual recipe alternative exists",
        )

        return output_name

    # _optimize_flow and _sanitize_name are inherited from BaseFlowGenerator
