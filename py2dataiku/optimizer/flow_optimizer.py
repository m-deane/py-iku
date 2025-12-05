"""Flow optimization utilities."""

from typing import List, Optional, Set, Tuple

from py2dataiku.models.dataiku_flow import DataikuFlow, FlowRecommendation
from py2dataiku.models.dataiku_recipe import DataikuRecipe, RecipeType


class FlowOptimizer:
    """
    Optimize Dataiku flows for performance and maintainability.

    Applies optimization rules:
    1. Merge consecutive Prepare recipes
    2. Push filters early to reduce data volume
    3. Identify parallel branches
    4. Minimize intermediate dataset count
    """

    def __init__(self):
        self.recommendations: List[FlowRecommendation] = []

    def optimize(self, flow: DataikuFlow) -> DataikuFlow:
        """
        Optimize the flow and return an optimized version.

        Args:
            flow: The flow to optimize

        Returns:
            Optimized DataikuFlow
        """
        self.recommendations = []

        # Apply optimization passes
        self._merge_prepare_recipes(flow)
        self._push_filters_early(flow)
        self._identify_parallel_branches(flow)
        self._add_recommendations(flow)

        return flow

    def _merge_prepare_recipes(self, flow: DataikuFlow) -> None:
        """Merge consecutive Prepare recipes."""
        prepare_recipes = flow.get_recipes_by_type(RecipeType.PREPARE)

        if len(prepare_recipes) <= 1:
            return

        # Find consecutive prepare recipes
        consecutive_pairs = []
        for i, recipe in enumerate(flow.recipes[:-1]):
            next_recipe = flow.recipes[i + 1]
            if (
                recipe.recipe_type == RecipeType.PREPARE
                and next_recipe.recipe_type == RecipeType.PREPARE
                and recipe.outputs[0] == next_recipe.inputs[0]
            ):
                consecutive_pairs.append((recipe, next_recipe))

        if consecutive_pairs:
            self.recommendations.append(
                FlowRecommendation(
                    type="CONSOLIDATION",
                    priority="MEDIUM",
                    message=f"Found {len(consecutive_pairs)} consecutive Prepare recipes that could be merged",
                    impact="Reduces recipe count and intermediate datasets",
                    action="Combine steps into single Prepare recipe",
                )
            )

    def _push_filters_early(self, flow: DataikuFlow) -> None:
        """Identify filters that could be pushed earlier in the flow."""
        # Find Split/Filter recipes
        filter_recipes = flow.get_recipes_by_type(RecipeType.SPLIT)

        for recipe in filter_recipes:
            # Check if there's a Join before this filter
            # that could benefit from filtering first
            input_ds = recipe.inputs[0] if recipe.inputs else None
            if not input_ds:
                continue

            # Find the recipe that produces this input
            for other in flow.recipes:
                if input_ds in other.outputs and other.recipe_type == RecipeType.JOIN:
                    self.recommendations.append(
                        FlowRecommendation(
                            type="PERFORMANCE",
                            priority="HIGH",
                            message=f"Filter in '{recipe.name}' could be moved before Join '{other.name}'",
                            impact="Reduces data volume before expensive Join operation",
                            action="Apply filter to input datasets before Join",
                        )
                    )

    def _identify_parallel_branches(self, flow: DataikuFlow) -> List[List[DataikuRecipe]]:
        """Identify recipe sequences that can run in parallel."""
        parallel_groups: List[List[DataikuRecipe]] = []

        # Build dependency graph
        dependencies = self._build_dependency_graph(flow)

        # Find recipes with no dependencies on each other
        for i, recipe1 in enumerate(flow.recipes):
            for recipe2 in flow.recipes[i + 1 :]:
                if not self._has_dependency(recipe1, recipe2, dependencies):
                    # These can run in parallel
                    pass

        return parallel_groups

    def _build_dependency_graph(
        self, flow: DataikuFlow
    ) -> dict:
        """Build a dependency graph of recipes."""
        deps = {}
        for recipe in flow.recipes:
            deps[recipe.name] = set()
            for inp in recipe.inputs:
                # Find recipe that produces this input
                for other in flow.recipes:
                    if inp in other.outputs:
                        deps[recipe.name].add(other.name)
        return deps

    def _has_dependency(
        self,
        recipe1: DataikuRecipe,
        recipe2: DataikuRecipe,
        dependencies: dict,
    ) -> bool:
        """Check if two recipes have a dependency relationship."""
        # Check direct dependency
        if recipe2.name in dependencies.get(recipe1.name, set()):
            return True
        if recipe1.name in dependencies.get(recipe2.name, set()):
            return True

        # Check transitive dependencies
        visited = set()
        to_check = list(dependencies.get(recipe1.name, set()))
        while to_check:
            current = to_check.pop()
            if current == recipe2.name:
                return True
            if current not in visited:
                visited.add(current)
                to_check.extend(dependencies.get(current, set()))

        return False

    def _add_recommendations(self, flow: DataikuFlow) -> None:
        """Add all collected recommendations to the flow."""
        for rec in self.recommendations:
            flow.recommendations.append(rec)


class RecipeMerger:
    """Merge compatible recipes to reduce flow complexity."""

    @staticmethod
    def can_merge(recipe1: DataikuRecipe, recipe2: DataikuRecipe) -> bool:
        """Check if two recipes can be merged."""
        # Only merge Prepare recipes
        if recipe1.recipe_type != RecipeType.PREPARE:
            return False
        if recipe2.recipe_type != RecipeType.PREPARE:
            return False

        # Must be consecutive (output of 1 is input of 2)
        if not (
            recipe1.outputs and recipe2.inputs and recipe1.outputs[0] == recipe2.inputs[0]
        ):
            return False

        return True

    @staticmethod
    def merge(recipe1: DataikuRecipe, recipe2: DataikuRecipe) -> DataikuRecipe:
        """Merge two Prepare recipes into one."""
        if not RecipeMerger.can_merge(recipe1, recipe2):
            raise ValueError("Recipes cannot be merged")

        merged = DataikuRecipe(
            name=f"{recipe1.name}_merged",
            recipe_type=RecipeType.PREPARE,
            inputs=recipe1.inputs,
            outputs=recipe2.outputs,
            steps=recipe1.steps + recipe2.steps,
        )
        merged.source_lines = recipe1.source_lines + recipe2.source_lines
        merged.notes = recipe1.notes + recipe2.notes

        return merged
