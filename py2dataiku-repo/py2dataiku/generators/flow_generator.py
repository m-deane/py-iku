"""Generate Dataiku flows from transformations."""

from typing import Dict, List, Optional

from py2dataiku.models.dataiku_flow import DataikuFlow
from py2dataiku.models.dataiku_recipe import (
    Aggregation,
    DataikuRecipe,
    JoinKey,
    JoinType,
    RecipeType,
)
from py2dataiku.models.dataiku_dataset import DataikuDataset, DatasetType
from py2dataiku.models.prepare_step import PrepareStep
from py2dataiku.models.transformation import Transformation, TransformationType


class FlowGenerator:
    """
    Generate Dataiku flows from analyzed transformations.

    This class takes the intermediate Transformation objects from
    the CodeAnalyzer and converts them into a complete DataikuFlow
    with datasets and recipes.
    """

    def __init__(self):
        self.flow: Optional[DataikuFlow] = None
        self.dataset_counter = 0
        self.recipe_counter = 0
        self.current_dataset: Dict[str, str] = {}  # variable -> dataset name

    def generate(
        self,
        transformations: List[Transformation],
        flow_name: str = "converted_flow",
        optimize: bool = True,
    ) -> DataikuFlow:
        """
        Generate a Dataiku flow from transformations.

        Args:
            transformations: List of Transformation objects
            flow_name: Name for the generated flow
            optimize: Whether to optimize the flow

        Returns:
            DataikuFlow object
        """
        self.flow = DataikuFlow(name=flow_name)
        self.dataset_counter = 0
        self.recipe_counter = 0
        self.current_dataset = {}

        # Group transformations by target variable
        groups = self._group_transformations(transformations)

        # Process each group
        for var_name, trans_list in groups.items():
            self._process_transformation_group(var_name, trans_list)

        # Optimize if requested
        if optimize:
            self._optimize_flow()

        return self.flow

    def _group_transformations(
        self, transformations: List[Transformation]
    ) -> Dict[str, List[Transformation]]:
        """Group transformations by target DataFrame variable."""
        groups: Dict[str, List[Transformation]] = {}

        for trans in transformations:
            target = trans.target_dataframe or "unknown"
            if target not in groups:
                groups[target] = []
            groups[target].append(trans)

        return groups

    def _process_transformation_group(
        self, var_name: str, transformations: List[Transformation]
    ) -> None:
        """Process a group of transformations for a single variable."""
        prepare_steps: List[PrepareStep] = []
        current_input: Optional[str] = None

        for trans in transformations:
            # Handle data reading
            if trans.transformation_type == TransformationType.READ_DATA:
                dataset = self._create_input_dataset(var_name, trans)
                current_input = dataset.name
                self.current_dataset[var_name] = dataset.name
                continue

            # Get input dataset
            if not current_input and trans.source_dataframe:
                current_input = self.current_dataset.get(trans.source_dataframe)

            # Route to appropriate handler
            if trans.transformation_type in self._prepare_types():
                step = self._transform_to_prepare_step(trans)
                if step:
                    prepare_steps.append(step)

            elif trans.transformation_type == TransformationType.MERGE:
                # Flush any pending prepare steps first
                if prepare_steps and current_input:
                    current_input = self._create_prepare_recipe(
                        current_input, prepare_steps
                    )
                    prepare_steps = []

                current_input = self._create_join_recipe(trans, current_input)
                self.current_dataset[var_name] = current_input

            elif trans.transformation_type == TransformationType.GROUPBY:
                if prepare_steps and current_input:
                    current_input = self._create_prepare_recipe(
                        current_input, prepare_steps
                    )
                    prepare_steps = []

                current_input = self._create_grouping_recipe(trans, current_input)
                self.current_dataset[var_name] = current_input

            elif trans.transformation_type == TransformationType.CONCAT:
                if prepare_steps and current_input:
                    current_input = self._create_prepare_recipe(
                        current_input, prepare_steps
                    )
                    prepare_steps = []

                current_input = self._create_stack_recipe(trans)
                self.current_dataset[var_name] = current_input

            elif trans.transformation_type == TransformationType.FILTER:
                if prepare_steps and current_input:
                    current_input = self._create_prepare_recipe(
                        current_input, prepare_steps
                    )
                    prepare_steps = []

                current_input = self._create_split_recipe(trans, current_input)
                self.current_dataset[trans.target_dataframe or var_name] = current_input

            elif trans.transformation_type == TransformationType.SORT:
                if prepare_steps and current_input:
                    current_input = self._create_prepare_recipe(
                        current_input, prepare_steps
                    )
                    prepare_steps = []

                current_input = self._create_sort_recipe(trans, current_input)
                self.current_dataset[var_name] = current_input

            elif trans.transformation_type == TransformationType.WRITE_DATA:
                # Flush prepare steps
                if prepare_steps and current_input:
                    current_input = self._create_prepare_recipe(
                        current_input, prepare_steps
                    )
                    prepare_steps = []

                # Mark as output
                if current_input:
                    ds = self.flow.get_dataset(current_input)
                    if ds:
                        ds.dataset_type = DatasetType.OUTPUT

            elif trans.requires_python_recipe:
                # Create Python recipe
                if prepare_steps and current_input:
                    current_input = self._create_prepare_recipe(
                        current_input, prepare_steps
                    )
                    prepare_steps = []

                current_input = self._create_python_recipe(trans, current_input)
                self.current_dataset[var_name] = current_input

        # Flush remaining prepare steps
        if prepare_steps and current_input:
            output = self._create_prepare_recipe(current_input, prepare_steps)
            self.current_dataset[var_name] = output

    def _prepare_types(self) -> set:
        """Transformation types that map to Prepare recipe steps."""
        return {
            TransformationType.FILL_NA,
            TransformationType.DROP_NA,
            TransformationType.DROP_DUPLICATES,
            TransformationType.COLUMN_RENAME,
            TransformationType.COLUMN_DROP,
            TransformationType.COLUMN_CREATE,
            TransformationType.STRING_TRANSFORM,
            TransformationType.TYPE_CAST,
            TransformationType.DATE_PARSE,
        }

    def _transform_to_prepare_step(
        self, trans: Transformation
    ) -> Optional[PrepareStep]:
        """Convert a transformation to a PrepareStep."""
        ttype = trans.transformation_type

        if ttype == TransformationType.FILL_NA:
            column = trans.columns[0] if trans.columns else "unknown"
            value = trans.parameters.get("value", "")
            return PrepareStep.fill_empty(column, value, trans.source_line)

        elif ttype == TransformationType.DROP_NA:
            columns = trans.columns or trans.parameters.get("subset", [])
            return PrepareStep.remove_rows_on_empty(columns, False, trans.source_line)

        elif ttype == TransformationType.DROP_DUPLICATES:
            columns = trans.columns or trans.parameters.get("subset")
            return PrepareStep.remove_duplicates(columns, trans.source_line)

        elif ttype == TransformationType.COLUMN_RENAME:
            mapping = trans.parameters.get("mapping", {})
            return PrepareStep.rename_columns(mapping, trans.source_line)

        elif ttype == TransformationType.COLUMN_DROP:
            return PrepareStep.delete_columns(trans.columns, trans.source_line)

        elif ttype == TransformationType.TYPE_CAST:
            column = trans.columns[0] if trans.columns else "unknown"
            dtype = trans.parameters.get("dtype", "string")
            return PrepareStep.set_type(column, dtype, trans.source_line)

        elif ttype == TransformationType.DATE_PARSE:
            column = trans.columns[0] if trans.columns else "unknown"
            return PrepareStep.parse_date(column, source_line=trans.source_line)

        return None

    def _create_input_dataset(
        self, var_name: str, trans: Transformation
    ) -> DataikuDataset:
        """Create an input dataset."""
        filepath = trans.parameters.get("filepath", "unknown")
        # Use filename as dataset name
        name = filepath.split("/")[-1].split(".")[0] if "/" in filepath else var_name
        name = self._sanitize_name(name)

        dataset = DataikuDataset(
            name=name,
            dataset_type=DatasetType.INPUT,
            source_variable=var_name,
            source_line=trans.source_line,
        )
        self.flow.add_dataset(dataset)
        return dataset

    def _create_prepare_recipe(
        self, input_dataset: str, steps: List[PrepareStep]
    ) -> str:
        """Create a Prepare recipe and return output dataset name."""
        self.recipe_counter += 1
        output_name = f"{input_dataset}_prepared"

        recipe = DataikuRecipe.create_prepare(
            name=f"prepare_{self.recipe_counter}",
            input_dataset=input_dataset,
            output_dataset=output_name,
            steps=steps,
        )

        self.flow.add_recipe(recipe)
        return output_name

    def _create_join_recipe(
        self, trans: Transformation, left_input: Optional[str]
    ) -> str:
        """Create a Join recipe and return output dataset name."""
        self.recipe_counter += 1

        right = trans.parameters.get("right", "")
        right_input = self.current_dataset.get(right, right)
        how = trans.parameters.get("how", "inner")

        output_name = f"{trans.target_dataframe or 'joined'}"

        # Determine join keys
        join_keys = []
        on = trans.parameters.get("on")
        left_on = trans.parameters.get("left_on")
        right_on = trans.parameters.get("right_on")

        if on:
            for col in (on if isinstance(on, list) else [on]):
                join_keys.append(JoinKey(left_column=col, right_column=col))
        elif left_on and right_on:
            left_cols = left_on if isinstance(left_on, list) else [left_on]
            right_cols = right_on if isinstance(right_on, list) else [right_on]
            for lc, rc in zip(left_cols, right_cols):
                join_keys.append(JoinKey(left_column=lc, right_column=rc))

        join_type = {
            "inner": JoinType.INNER,
            "left": JoinType.LEFT,
            "right": JoinType.RIGHT,
            "outer": JoinType.OUTER,
        }.get(how, JoinType.INNER)

        recipe = DataikuRecipe.create_join(
            name=f"join_{self.recipe_counter}",
            left_dataset=left_input or "",
            right_dataset=right_input,
            output_dataset=output_name,
            join_keys=join_keys,
            join_type=join_type,
        )
        recipe.source_lines = [trans.source_line] if trans.source_line else []

        self.flow.add_recipe(recipe)
        return output_name

    def _create_grouping_recipe(
        self, trans: Transformation, input_dataset: Optional[str]
    ) -> str:
        """Create a Grouping recipe and return output dataset name."""
        self.recipe_counter += 1

        keys = trans.parameters.get("keys", [])
        aggs_dict = trans.parameters.get("aggregations", {})
        output_name = f"{trans.target_dataframe or 'aggregated'}"

        aggregations = []
        for col, func in aggs_dict.items():
            agg_func = {
                "sum": "SUM",
                "mean": "AVG",
                "avg": "AVG",
                "count": "COUNT",
                "min": "MIN",
                "max": "MAX",
            }.get(func.lower() if isinstance(func, str) else "count", "COUNT")
            aggregations.append(Aggregation(column=col, function=agg_func))

        recipe = DataikuRecipe.create_grouping(
            name=f"grouping_{self.recipe_counter}",
            input_dataset=input_dataset or "",
            output_dataset=output_name,
            keys=keys,
            aggregations=aggregations,
        )
        recipe.source_lines = [trans.source_line] if trans.source_line else []

        self.flow.add_recipe(recipe)
        return output_name

    def _create_stack_recipe(self, trans: Transformation) -> str:
        """Create a Stack recipe and return output dataset name."""
        self.recipe_counter += 1

        dataframes = trans.parameters.get("dataframes", [])
        inputs = [self.current_dataset.get(df, df) for df in dataframes]
        output_name = f"{trans.target_dataframe or 'stacked'}"

        recipe = DataikuRecipe(
            name=f"stack_{self.recipe_counter}",
            recipe_type=RecipeType.STACK,
            inputs=inputs,
            outputs=[output_name],
        )
        recipe.source_lines = [trans.source_line] if trans.source_line else []

        self.flow.add_recipe(recipe)
        return output_name

    def _create_split_recipe(
        self, trans: Transformation, input_dataset: Optional[str]
    ) -> str:
        """Create a Split recipe and return output dataset name."""
        self.recipe_counter += 1

        condition = trans.parameters.get("condition", "")
        output_name = f"{trans.target_dataframe or 'filtered'}"

        recipe = DataikuRecipe(
            name=f"split_{self.recipe_counter}",
            recipe_type=RecipeType.SPLIT,
            inputs=[input_dataset or ""],
            outputs=[output_name],
            split_condition=condition,
        )
        recipe.source_lines = [trans.source_line] if trans.source_line else []

        self.flow.add_recipe(recipe)
        return output_name

    def _create_sort_recipe(
        self, trans: Transformation, input_dataset: Optional[str]
    ) -> str:
        """Create a Sort recipe and return output dataset name."""
        self.recipe_counter += 1

        columns = trans.columns
        ascending = trans.parameters.get("ascending", True)
        output_name = f"{input_dataset}_sorted"

        sort_columns = [
            {"column": col, "order": "ASC" if ascending else "DESC"}
            for col in columns
        ]

        recipe = DataikuRecipe(
            name=f"sort_{self.recipe_counter}",
            recipe_type=RecipeType.SORT,
            inputs=[input_dataset or ""],
            outputs=[output_name],
            sort_columns=sort_columns,
        )
        recipe.source_lines = [trans.source_line] if trans.source_line else []

        self.flow.add_recipe(recipe)
        return output_name

    def _create_python_recipe(
        self, trans: Transformation, input_dataset: Optional[str]
    ) -> str:
        """Create a Python recipe for complex operations."""
        self.recipe_counter += 1

        output_name = f"{trans.target_dataframe or 'processed'}"
        code = trans.parameters.get("code", "# Complex operation")

        recipe = DataikuRecipe.create_python(
            name=f"python_{self.recipe_counter}",
            inputs=[input_dataset] if input_dataset else [],
            outputs=[output_name],
            code=code,
        )
        recipe.source_lines = [trans.source_line] if trans.source_line else []
        recipe.notes = trans.notes.copy()

        self.flow.add_recipe(recipe)
        self.flow.add_recommendation(
            type="PYTHON_FALLBACK",
            priority="MEDIUM",
            message=f"Recipe '{recipe.name}' requires Python due to complex operation",
            action="Review if visual recipe alternative exists",
        )

        return output_name

    def _optimize_flow(self) -> None:
        """Optimize the generated flow."""
        # Merge consecutive Prepare recipes
        self._merge_prepare_recipes()

        # Add optimization notes
        prepare_count = len(self.flow.get_recipes_by_type(RecipeType.PREPARE))
        if prepare_count > 1:
            self.flow.optimization_notes.append(
                f"Flow contains {prepare_count} Prepare recipes"
            )

    def _merge_prepare_recipes(self) -> None:
        """Merge consecutive Prepare recipes when possible."""
        # This is a simplified implementation
        # Full implementation would rebuild the flow graph
        pass

    def _sanitize_name(self, name: str) -> str:
        """Sanitize a name for use as a dataset/recipe name."""
        return name.replace(" ", "_").replace("-", "_").replace(".", "_")
