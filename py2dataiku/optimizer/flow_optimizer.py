"""Flow optimization utilities."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from py2dataiku.models.dataiku_dataset import DatasetType
from py2dataiku.models.dataiku_flow import DataikuFlow, FlowRecommendation
from py2dataiku.models.dataiku_recipe import DataikuRecipe, RecipeType
from py2dataiku.optimizer.recipe_merger import RecipeMerger


@dataclass
class OptimizationResult:
    """Summary of optimizations applied to a flow."""

    recipes_merged: int = 0
    datasets_removed: int = 0
    filters_pushed_down: int = 0
    log: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "recipes_merged": self.recipes_merged,
            "datasets_removed": self.datasets_removed,
            "filters_pushed_down": self.filters_pushed_down,
            "log": self.log,
        }


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

    def optimize(
        self, flow: DataikuFlow, apply: bool = True
    ) -> DataikuFlow:
        """
        Optimize the flow and return it.

        Args:
            flow: The flow to optimize
            apply: If True, actually apply transformations.
                   If False, only generate recommendations.

        Returns:
            The optimized DataikuFlow (same object, mutated in place)
        """
        self.recommendations = []
        self.last_result = OptimizationResult()

        if apply:
            self._apply_merge_prepare_recipes(flow, self.last_result)
            self._apply_remove_orphan_datasets(flow, self.last_result)
        else:
            self._recommend_merge_prepare_recipes(flow)

        self._push_filters_early(flow)
        self._identify_parallel_branches(flow)
        self._add_recommendations(flow)

        # Store optimization log on the flow
        for entry in self.last_result.log:
            flow.optimization_notes.append(entry)

        return flow

    def _apply_merge_prepare_recipes(
        self, flow: DataikuFlow, result: OptimizationResult
    ) -> None:
        """Find and merge consecutive Prepare recipes."""
        changed = True
        while changed:
            changed = False
            for i in range(len(flow.recipes) - 1):
                recipe1 = flow.recipes[i]
                recipe2 = flow.recipes[i + 1]

                if not RecipeMerger.can_merge_prepare(recipe1, recipe2):
                    continue

                # Merge
                intermediate_ds = recipe1.outputs[0]
                merged = RecipeMerger.merge_prepare_recipes([recipe1, recipe2])

                # Replace the two recipes with the merged one
                flow.recipes[i] = merged
                flow.recipes.pop(i + 1)

                result.recipes_merged += 1
                result.log.append(
                    f"Merged '{recipe1.name}' + '{recipe2.name}' -> '{merged.name}'"
                )

                # Mark intermediate dataset for removal
                # (it's no longer needed between the two recipes)
                ds = flow.get_dataset(intermediate_ds)
                if ds is not None:
                    # Check no other recipe references this dataset
                    still_referenced = False
                    for r in flow.recipes:
                        if intermediate_ds in r.inputs or intermediate_ds in r.outputs:
                            still_referenced = True
                            break
                    if not still_referenced:
                        flow.datasets = [
                            d for d in flow.datasets if d.name != intermediate_ds
                        ]
                        result.datasets_removed += 1
                        result.log.append(
                            f"Removed intermediate dataset '{intermediate_ds}'"
                        )

                changed = True
                break  # Restart scan from beginning

    def _apply_remove_orphan_datasets(
        self, flow: DataikuFlow, result: OptimizationResult
    ) -> None:
        """Remove intermediate datasets that are no longer referenced."""
        referenced: Set[str] = set()
        for recipe in flow.recipes:
            referenced.update(recipe.inputs)
            referenced.update(recipe.outputs)

        to_remove = []
        for ds in flow.datasets:
            if ds.name not in referenced and ds.dataset_type == DatasetType.INTERMEDIATE:
                to_remove.append(ds.name)

        for name in to_remove:
            flow.datasets = [d for d in flow.datasets if d.name != name]
            result.datasets_removed += 1
            result.log.append(f"Removed orphaned intermediate dataset '{name}'")

    def _recommend_merge_prepare_recipes(self, flow: DataikuFlow) -> None:
        """Generate recommendations for merging consecutive Prepare recipes."""
        prepare_recipes = flow.get_recipes_by_type(RecipeType.PREPARE)

        if len(prepare_recipes) <= 1:
            return

        consecutive_pairs = []
        for i in range(len(flow.recipes) - 1):
            recipe = flow.recipes[i]
            next_recipe = flow.recipes[i + 1]
            if (
                recipe.recipe_type == RecipeType.PREPARE
                and next_recipe.recipe_type == RecipeType.PREPARE
                and recipe.outputs
                and next_recipe.inputs
                and recipe.outputs[0] == next_recipe.inputs[0]
            ):
                consecutive_pairs.append((recipe, next_recipe))

        if consecutive_pairs:
            self.recommendations.append(
                FlowRecommendation(
                    type="CONSOLIDATION",
                    priority="MEDIUM",
                    message=(
                        f"Found {len(consecutive_pairs)} consecutive Prepare "
                        f"recipes that could be merged"
                    ),
                    impact="Reduces recipe count and intermediate datasets",
                    action="Combine steps into single Prepare recipe",
                )
            )

    def _push_filters_early(self, flow: DataikuFlow) -> None:
        """Identify filters that could be pushed earlier in the flow."""
        filter_recipes = flow.get_recipes_by_type(RecipeType.SPLIT)

        for recipe in filter_recipes:
            input_ds = recipe.inputs[0] if recipe.inputs else None
            if not input_ds:
                continue

            for other in flow.recipes:
                if input_ds in other.outputs and other.recipe_type == RecipeType.JOIN:
                    self.recommendations.append(
                        FlowRecommendation(
                            type="PERFORMANCE",
                            priority="HIGH",
                            message=(
                                f"Filter in '{recipe.name}' could be moved "
                                f"before Join '{other.name}'"
                            ),
                            impact="Reduces data volume before expensive Join operation",
                            action="Apply filter to input datasets before Join",
                        )
                    )

    def _identify_parallel_branches(
        self, flow: DataikuFlow
    ) -> List[List[DataikuRecipe]]:
        """Identify recipe sequences that can run in parallel."""
        parallel_groups: List[List[DataikuRecipe]] = []

        dependencies = self._build_dependency_graph(flow)

        for i, recipe1 in enumerate(flow.recipes):
            for recipe2 in flow.recipes[i + 1:]:
                if not self._has_dependency(recipe1, recipe2, dependencies):
                    pass

        return parallel_groups

    def _build_dependency_graph(self, flow: DataikuFlow) -> dict:
        """Build a dependency graph of recipes."""
        deps: Dict[str, Set[str]] = {}
        for recipe in flow.recipes:
            deps[recipe.name] = set()
            for inp in recipe.inputs:
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
        if recipe2.name in dependencies.get(recipe1.name, set()):
            return True
        if recipe1.name in dependencies.get(recipe2.name, set()):
            return True

        visited: Set[str] = set()
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
