"""Generate Dataiku flows from LLM-analyzed steps."""

from typing import Optional

from py2dataiku.generators.base_generator import BaseFlowGenerator
from py2dataiku.llm.schemas import (
    AnalysisResult,
    DataStep,
    OperationType,
)
from py2dataiku.mappings.pandas_mappings import PandasMapper
from py2dataiku.models.dataiku_dataset import DataikuDataset, DatasetType
from py2dataiku.models.dataiku_flow import DataikuFlow
from py2dataiku.models.dataiku_recipe import (
    Aggregation,
    DataikuRecipe,
    JoinKey,
    JoinType,
    RecipeType,
)
from py2dataiku.models.prepare_step import (
    PrepareStep,
    ProcessorType,
    StringTransformerMode,
)


class LLMFlowGenerator(BaseFlowGenerator):
    """
    Generate Dataiku flows from LLM-analyzed code.

    This generator takes the structured output from LLMCodeAnalyzer
    and converts it to a complete DataikuFlow with datasets and recipes.
    """

    # Fallback mapping from OperationType to suggested recipe string.
    # Used when the LLM doesn't provide a suggested_recipe.
    OPERATION_TO_RECIPE: dict[OperationType, str] = {
        OperationType.GROUP_AGGREGATE: "grouping",
        OperationType.JOIN: "join",
        OperationType.UNION: "stack",
        OperationType.SORT: "sort",
        OperationType.DROP_DUPLICATES: "distinct",
        OperationType.WINDOW_FUNCTION: "window",
        OperationType.TOP_N: "topn",
        OperationType.SAMPLE: "sampling",
        OperationType.PIVOT: "pivot",
        OperationType.UNPIVOT: "prepare",
        OperationType.FILTER: "prepare",
        OperationType.FILL_MISSING: "prepare",
        OperationType.DROP_MISSING: "prepare",
        OperationType.RENAME_COLUMNS: "prepare",
        OperationType.DROP_COLUMNS: "prepare",
        OperationType.SELECT_COLUMNS: "prepare",
        OperationType.ADD_COLUMN: "prepare",
        OperationType.TRANSFORM_COLUMN: "prepare",
        OperationType.CAST_TYPE: "prepare",
        OperationType.PARSE_DATE: "prepare",
        OperationType.SPLIT_COLUMN: "prepare",
        OperationType.ENCODE_CATEGORICAL: "prepare",
        OperationType.NORMALIZE_SCALE: "prepare",
        OperationType.GEO_OPERATION: "prepare",
        OperationType.STATISTICS: "generate_statistics",
    }

    def __init__(self):
        super().__init__()
        self.dataset_map: dict[str, str] = {}  # variable name -> dataset name

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
        prepare_steps_buffer: list[DataStep] = []
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

            # Route based on suggested recipe type, falling back to operation type
            suggested = (step.suggested_recipe or "").lower().strip()
            if not suggested:
                suggested = self.OPERATION_TO_RECIPE.get(step.operation, "python")

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

            elif suggested == "topn":
                if prepare_steps_buffer:
                    current_input = self._create_prepare_recipe(
                        current_input, prepare_steps_buffer
                    )
                    prepare_steps_buffer = []

                current_input = self._create_topn_recipe(step, current_input)

            elif suggested == "sampling":
                if prepare_steps_buffer:
                    current_input = self._create_prepare_recipe(
                        current_input, prepare_steps_buffer
                    )
                    prepare_steps_buffer = []

                current_input = self._create_sampling_recipe(step, current_input)

            elif suggested == "pivot":
                if prepare_steps_buffer:
                    current_input = self._create_prepare_recipe(
                        current_input, prepare_steps_buffer
                    )
                    prepare_steps_buffer = []

                current_input = self._create_pivot_recipe(step, current_input)

            elif suggested == "generate_statistics":
                if prepare_steps_buffer:
                    current_input = self._create_prepare_recipe(
                        current_input, prepare_steps_buffer
                    )
                    prepare_steps_buffer = []

                # Statistics is a profiling side-output: it does NOT
                # advance the working dataset for subsequent steps.
                self._create_statistics_recipe(step, current_input)

            elif suggested == "python":
                if prepare_steps_buffer:
                    current_input = self._create_prepare_recipe(
                        current_input, prepare_steps_buffer
                    )
                    prepare_steps_buffer = []

                current_input = self._create_python_recipe(step, current_input)

            else:
                # Unknown recipe hint — warn and fall back to Python
                if prepare_steps_buffer:
                    current_input = self._create_prepare_recipe(
                        current_input, prepare_steps_buffer
                    )
                    prepare_steps_buffer = []

                self.flow.warnings.append(
                    f"Unknown suggested_recipe '{step.suggested_recipe}' for step "
                    f"{step.step_number} ({step.operation.value}); falling back to Python recipe"
                )
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
        self, input_dataset: Optional[str], steps: list[DataStep]
    ) -> str:
        """Create a Prepare recipe from multiple steps."""
        self.recipe_counter += 1

        # Prefer the LLM-declared output dataset of the LAST step in the buffer
        # (the buffer's final intent). Fall back to a generated name.
        declared_output: Optional[str] = None
        for step in reversed(steps):
            if step.output_dataset:
                declared_output = step.output_dataset
                break

        if declared_output:
            output_name = self._sanitize_name(declared_output)
        else:
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

    def _convert_to_prepare_steps(self, step: DataStep) -> list[PrepareStep]:
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
            # Route each filter condition to the DSS-canonical processor:
            # numeric comparisons -> FilterOnNumericRange,
            # equality / membership -> FilterOnValue + FULL_STRING,
            # contains / regex -> FilterOnValue + SUBSTRING/PATTERN.
            # See pattern_matcher.match_filter for the dispatch logic.
            from py2dataiku.parser.pattern_matcher import PatternMatcher
            _pm = PatternMatcher()
            for condition in step.filter_conditions:
                result.append(
                    _pm.match_filter(
                        column=condition.column,
                        operator=condition.operator,
                        value=condition.value,
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

        elif op == OperationType.SELECT_COLUMNS:
            if step.columns:
                result.append(
                    PrepareStep(
                        processor_type=ProcessorType.COLUMNS_SELECTOR,
                        params={"columns": step.columns, "keep": True, "mode": "keep"},
                    )
                )

        elif op == OperationType.ADD_COLUMN:
            if step.column_transforms:
                for transform in step.column_transforms:
                    expression = transform.operation if transform.operation else ""
                    result.append(
                        PrepareStep.create_column_grel(
                            column=transform.output_column or transform.column,
                            expression=expression,
                        )
                    )
            else:
                # No transform details: create a placeholder column
                col_name = step.columns[0] if step.columns else "new_column"
                result.append(
                    PrepareStep.create_column_grel(column=col_name, expression="")
                )

        elif op == OperationType.SPLIT_COLUMN:
            if step.columns:
                source_col = step.columns[0]
                # Try to find separator from column_transforms parameters
                separator = " "
                for transform in step.column_transforms:
                    sep = transform.parameters.get("separator") or transform.parameters.get("sep")
                    if sep:
                        separator = sep
                        break
                result.append(
                    PrepareStep(
                        processor_type=ProcessorType.SPLIT_COLUMN,
                        params={"column": source_col, "separator": separator},
                    )
                )

        elif op == OperationType.UNPIVOT:
            if step.columns:
                result.append(PrepareStep.fold_multiple_columns(columns=step.columns))

        elif op == OperationType.ENCODE_CATEGORICAL:
            for col in step.columns or [t.column for t in step.column_transforms]:
                if col:
                    result.append(
                        PrepareStep(
                            processor_type=ProcessorType.CATEGORICAL_ENCODER,
                            params={"column": col},
                        )
                    )

        elif op == OperationType.NORMALIZE_SCALE:
            # Pick mode from transform parameters; default to MIN_MAX
            for transform in step.column_transforms:
                params = transform.parameters or {}
                mode_hint = (params.get("mode") or transform.operation or "min_max").lower()
                if mode_hint in ("zscore", "z_score", "standard", "standard_scaler"):
                    mode = "ZSCORE"
                elif mode_hint in ("robust", "robust_scaler"):
                    mode = "ROBUST"
                else:
                    mode = "MIN_MAX"
                result.append(
                    PrepareStep(
                        processor_type=ProcessorType.NORMALIZER,
                        params={"column": transform.column, "mode": mode},
                    )
                )
            # Fallback when LLM only set step.columns
            if not step.column_transforms:
                for col in step.columns:
                    result.append(
                        PrepareStep(
                            processor_type=ProcessorType.NORMALIZER,
                            params={"column": col, "mode": "MIN_MAX"},
                        )
                    )

        elif op == OperationType.GEO_OPERATION:
            for transform in step.column_transforms:
                params = transform.parameters or {}
                op_hint = (params.get("operation") or transform.operation or "").lower()
                if "point" in op_hint or "create_point" in op_hint:
                    result.append(
                        PrepareStep(
                            processor_type=ProcessorType.GEO_POINT_CREATOR,
                            params={
                                "lat_column": params.get("lat") or "",
                                "lon_column": params.get("lon") or "",
                                "output_column": transform.output_column or "geopoint",
                            },
                        )
                    )
                else:
                    result.append(
                        PrepareStep(
                            processor_type=ProcessorType.GEO_ENCODER,
                            params={"column": transform.column},
                        )
                    )

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
            return PrepareStep.create_column_grel(
                column=transform.column,
                expression=f"abs(val(\"{transform.column}\"))",
            )

        # Default: create GREL expression
        return PrepareStep.create_column_grel(
            column=transform.output_column or transform.column,
            expression=f"{transform.column}",  # Placeholder
        )

    def _map_operator(self, operator: str) -> str:
        """Map filter operator to a DSS matchingMode (legacy / unused).

        DEPRECATED: this method was used by the wave-1 LLM-path FILTER
        routing, which emitted invalid matchingMode values for numeric
        comparisons. Wave-8 routed all filter conditions through
        :meth:`PatternMatcher.match_filter` which dispatches by operator
        class to the correct DSS processor (FilterOnValue /
        FilterOnNumericRange / FilterOnFormula). This method is kept for
        backward-compat with any external caller that imported it
        directly; new code should not use it.
        """
        op_map = {
            "equals": "FULL_STRING",
            "not_equals": "FULL_STRING",
            "contains": "SUBSTRING",
            "regex": "PATTERN",
            "in": "FULL_STRING",
        }
        return op_map.get(operator.lower(), "FULL_STRING")

    def _create_grouping_recipe(
        self, step: DataStep, input_dataset: Optional[str]
    ) -> str:
        """Create a Grouping recipe."""
        self.recipe_counter += 1
        output_name = step.output_dataset or f"grouped_{self.recipe_counter}"
        output_name = self._sanitize_name(output_name)

        # Normalize the aggregation function name to DSS canonical form
        # (e.g. "mean" -> "AVG", "std" -> "STDDEV", "nunique" -> "COUNTD").
        # If the LLM emitted an already-canonical DSS name we leave it alone.
        def _canonical(fn: str) -> str:
            return PandasMapper.AGG_MAPPINGS.get(fn.lower(), fn.upper())

        aggregations = [
            Aggregation(
                column=agg.column,
                function=_canonical(agg.function),
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

        # C3 fix: prevent DAG cycle when output would equal input
        if output_name == input_dataset:
            output_name = f"{output_name}_filtered"

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

        # Convert sort_columns ({"column", "order"}) into ordering strings
        order_columns = [sc.get("column", "") for sc in step.sort_columns if sc.get("column")]

        # Build window_aggregations from step.aggregations
        window_aggregations = [
            {
                "column": agg.column,
                "type": agg.function.upper(),
                "outputColumn": agg.output_column or f"{agg.function}_{agg.column}",
            }
            for agg in step.aggregations
        ]

        recipe = DataikuRecipe(
            name=f"window_{self.recipe_counter}",
            recipe_type=RecipeType.WINDOW,
            inputs=[input_dataset or ""],
            outputs=[output_name],
            partition_columns=step.group_by_columns,
            order_columns=order_columns,
            window_aggregations=window_aggregations,
        )

        if not window_aggregations:
            self.flow.warnings.append(
                f"Window step {step.step_number} has no aggregations; "
                "the WINDOW recipe will produce no output columns"
            )

        if step.reasoning:
            recipe.notes.append(step.reasoning)

        self.flow.add_recipe(recipe)
        return output_name

    def _create_statistics_recipe(
        self, step: DataStep, input_dataset: Optional[str]
    ) -> str:
        """Create a Generate Statistics recipe (df.describe / df.info)."""
        self.recipe_counter += 1
        output_name = step.output_dataset or f"statistics_{self.recipe_counter}"
        output_name = self._sanitize_name(output_name)

        recipe = DataikuRecipe(
            name=f"statistics_{self.recipe_counter}",
            recipe_type=RecipeType.GENERATE_STATISTICS,
            inputs=[input_dataset or ""],
            outputs=[output_name],
        )
        if step.reasoning:
            recipe.notes.append(step.reasoning)

        if not self.flow.get_dataset(output_name):
            self.flow.add_dataset(
                DataikuDataset(name=output_name, dataset_type=DatasetType.OUTPUT)
            )

        self.flow.add_recipe(recipe)
        return output_name

    def _create_topn_recipe(
        self, step: DataStep, input_dataset: Optional[str]
    ) -> str:
        """Create a Top-N recipe (df.nlargest / df.nsmallest)."""
        self.recipe_counter += 1
        output_name = step.output_dataset or f"topn_{self.recipe_counter}"
        output_name = self._sanitize_name(output_name)

        # Pick ranking column: prefer first sort_columns entry, else first column
        ranking_column = None
        sort_columns: list[dict[str, str]] = []
        if step.sort_columns:
            ranking_column = step.sort_columns[0].get("column")
            sort_columns = step.sort_columns
        elif step.columns:
            ranking_column = step.columns[0]
            sort_columns = [{"column": ranking_column, "order": "desc"}]

        # n: prefer aggregation-style param, fall back to int in columns/parameters
        top_n = 10
        for transform in step.column_transforms:
            n_param = transform.parameters.get("n") or transform.parameters.get("top_n")
            if isinstance(n_param, int):
                top_n = n_param
                break

        recipe = DataikuRecipe(
            name=f"topn_{self.recipe_counter}",
            recipe_type=RecipeType.TOP_N,
            inputs=[input_dataset or ""],
            outputs=[output_name],
            top_n=top_n,
            ranking_column=ranking_column,
            sort_columns=sort_columns,
        )

        if step.reasoning:
            recipe.notes.append(step.reasoning)

        self.flow.add_recipe(recipe)
        return output_name

    def _create_sampling_recipe(
        self, step: DataStep, input_dataset: Optional[str]
    ) -> str:
        """Create a Sampling recipe (df.sample / df.head / df.tail)."""
        from py2dataiku.models.dataiku_recipe import SamplingMethod

        self.recipe_counter += 1
        output_name = step.output_dataset or f"sampled_{self.recipe_counter}"
        output_name = self._sanitize_name(output_name)

        # Determine sampling method and size from column_transforms parameters
        method = SamplingMethod.RANDOM
        sample_size: Optional[int] = None
        for transform in step.column_transforms:
            params = transform.parameters or {}
            method_hint = (params.get("method") or transform.operation or "").lower()
            if method_hint in ("head", "first", "first_rows"):
                method = SamplingMethod.FIRST_ROWS
            elif method_hint in ("tail", "last", "last_rows"):
                method = SamplingMethod.LAST_ROWS
            elif method_hint in ("stratified",):
                method = SamplingMethod.STRATIFIED
            n = params.get("n") or params.get("size")
            frac = params.get("frac") or params.get("fraction")
            if isinstance(n, int):
                sample_size = n
            elif isinstance(frac, (int, float)):
                method = SamplingMethod.RANDOM_FIXED
                sample_size = int(frac * 100) if frac <= 1 else int(frac)
            break

        recipe = DataikuRecipe(
            name=f"sampling_{self.recipe_counter}",
            recipe_type=RecipeType.SAMPLING,
            inputs=[input_dataset or ""],
            outputs=[output_name],
            sampling_method=method,
            sample_size=sample_size,
        )

        if step.reasoning:
            recipe.notes.append(step.reasoning)

        self.flow.add_recipe(recipe)
        return output_name

    def _create_pivot_recipe(
        self, step: DataStep, input_dataset: Optional[str]
    ) -> str:
        """Create a Pivot recipe (df.pivot / df.pivot_table)."""
        from py2dataiku.models.recipe_settings import PivotSettings

        self.recipe_counter += 1
        output_name = step.output_dataset or f"pivoted_{self.recipe_counter}"
        output_name = self._sanitize_name(output_name)

        # Extract pivot configuration from the step
        # group_by_columns -> row index columns
        # First aggregation -> value/aggregation
        # First column in `columns` (other than index/value) -> pivot column
        row_columns = list(step.group_by_columns)
        column_column = ""
        value_column = ""
        aggregation = "SUM"

        if step.aggregations:
            first_agg = step.aggregations[0]
            value_column = first_agg.column
            aggregation = first_agg.function.upper()

        # Pick the pivot (column-spreading) column from `columns` excluding rows/values
        for col in step.columns:
            if col not in row_columns and col != value_column:
                column_column = col
                break

        settings = PivotSettings(
            row_columns=row_columns,
            column_column=column_column,
            value_column=value_column,
            aggregation=aggregation,
        )

        recipe = DataikuRecipe(
            name=f"pivot_{self.recipe_counter}",
            recipe_type=RecipeType.PIVOT,
            inputs=[input_dataset or ""],
            outputs=[output_name],
            settings=settings,
        )

        if step.reasoning:
            recipe.notes.append(step.reasoning)

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
