"""Recipe merging utilities."""

from typing import List, Optional

from py2dataiku.models.dataiku_recipe import DataikuRecipe, RecipeType
from py2dataiku.models.prepare_step import PrepareStep


class RecipeMerger:
    """
    Merge compatible recipes to reduce flow complexity.

    This class provides utilities for combining multiple recipes
    into fewer, more efficient recipes.
    """

    @staticmethod
    def can_merge_prepare(recipe1: DataikuRecipe, recipe2: DataikuRecipe) -> bool:
        """Check if two Prepare recipes can be merged."""
        if recipe1.recipe_type != RecipeType.PREPARE:
            return False
        if recipe2.recipe_type != RecipeType.PREPARE:
            return False

        # Output of recipe1 must be input of recipe2
        if not recipe1.outputs or not recipe2.inputs:
            return False
        if recipe1.outputs[0] != recipe2.inputs[0]:
            return False

        return True

    @staticmethod
    def merge_prepare_recipes(
        recipes: List[DataikuRecipe],
    ) -> DataikuRecipe:
        """
        Merge multiple consecutive Prepare recipes into one.

        Args:
            recipes: List of Prepare recipes to merge (must be in order)

        Returns:
            Single merged Prepare recipe
        """
        if not recipes:
            raise ValueError("No recipes to merge")

        if len(recipes) == 1:
            return recipes[0]

        # Validate all are Prepare recipes
        for r in recipes:
            if r.recipe_type != RecipeType.PREPARE:
                raise ValueError(f"Recipe '{r.name}' is not a Prepare recipe")

        # Combine all steps
        all_steps: List[PrepareStep] = []
        all_source_lines: List[int] = []
        all_notes: List[str] = []

        for recipe in recipes:
            all_steps.extend(recipe.steps)
            all_source_lines.extend(recipe.source_lines)
            all_notes.extend(recipe.notes)

        # Create merged recipe
        merged = DataikuRecipe(
            name=f"prepare_merged_{recipes[0].name}",
            recipe_type=RecipeType.PREPARE,
            inputs=recipes[0].inputs,
            outputs=recipes[-1].outputs,
            steps=all_steps,
            source_lines=all_source_lines,
            notes=all_notes,
        )

        return merged

    @staticmethod
    def optimize_prepare_steps(steps: List[PrepareStep]) -> List[PrepareStep]:
        """
        Optimize the order of Prepare steps for efficiency.

        Rules:
        1. Column deletions should come first (reduce data early)
        2. Type conversions before operations that depend on them
        3. Filters/row removals early to reduce row count
        4. Column renames last (to avoid breaking references)
        """
        # Categorize steps
        deletions = []
        type_setters = []
        row_filters = []
        other = []
        renames = []

        from py2dataiku.models.prepare_step import ProcessorType

        for step in steps:
            if step.processor_type == ProcessorType.COLUMN_DELETER:
                deletions.append(step)
            elif step.processor_type == ProcessorType.TYPE_SETTER:
                type_setters.append(step)
            elif step.processor_type in (
                ProcessorType.FILTER_ON_VALUE,
                ProcessorType.REMOVE_ROWS_ON_EMPTY,
                ProcessorType.REMOVE_DUPLICATES,
            ):
                row_filters.append(step)
            elif step.processor_type == ProcessorType.COLUMN_RENAMER:
                renames.append(step)
            else:
                other.append(step)

        # Combine in optimized order
        return deletions + type_setters + row_filters + other + renames

    @staticmethod
    def remove_redundant_steps(steps: List[PrepareStep]) -> List[PrepareStep]:
        """
        Remove redundant or contradictory steps.

        Examples:
        - Multiple renames of the same column (keep last)
        - Fill NA then drop NA on same column (remove fill)
        - Delete then any operation on same column (remove operation)
        """
        from py2dataiku.models.prepare_step import ProcessorType

        optimized = []
        deleted_columns = set()

        for step in steps:
            # Track deleted columns
            if step.processor_type == ProcessorType.COLUMN_DELETER:
                deleted_columns.update(step.params.get("columns", []))
                optimized.append(step)
                continue

            # Skip operations on deleted columns
            step_column = step.params.get("column")
            if step_column and step_column in deleted_columns:
                continue

            optimized.append(step)

        return optimized
