"""Flow optimization utilities."""

from dataclasses import dataclass, field

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
    log: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
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
        self.recommendations: list[FlowRecommendation] = []

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
            self._apply_merge_window_recipes(flow, self.last_result)
            self._apply_remove_orphan_datasets(flow, self.last_result)
        else:
            self._recommend_merge_prepare_recipes(flow)

        self._push_filters_early(flow)
        self._add_recommendations(flow)

        # Store optimization log on the flow
        for entry in self.last_result.log:
            flow.optimization_notes.append(entry)

        return flow

    def _find_merge_pair(
        self,
        flow: DataikuFlow,
        is_eligible,
        can_merge,
    ):
        """DAG-aware lookup of two mergeable recipes.

        For each candidate ``recipe1`` (passed ``is_eligible``), find the
        downstream recipe (matched on shared dataset, regardless of list
        position) for which ``can_merge(recipe1, recipe2)`` returns True.
        Refuses to merge when ``recipe1.outputs[0]`` is consumed by more
        than one downstream recipe (fan-out makes the merge unsafe).

        Returns ``(i, j, recipe1, recipe2)`` indices into ``flow.recipes``
        or ``None`` if no merge candidate exists.
        """
        # Build an "input -> [recipes that consume it]" lookup once.
        consumers: dict[str, list[int]] = {}
        for idx, r in enumerate(flow.recipes):
            for inp in r.inputs:
                consumers.setdefault(inp, []).append(idx)

        for i, recipe1 in enumerate(flow.recipes):
            if not is_eligible(recipe1):
                continue
            if not recipe1.outputs:
                continue
            output_name = recipe1.outputs[0]
            downstream_indices = consumers.get(output_name, [])
            # Fan-out guard: only merge when exactly one downstream consumer.
            if len(downstream_indices) != 1:
                continue
            j = downstream_indices[0]
            if j == i:
                continue
            recipe2 = flow.recipes[j]
            if not is_eligible(recipe2):
                continue
            # The downstream recipe must consume ONLY this dataset (otherwise
            # merging would change its input set).
            if recipe2.inputs != [output_name]:
                continue
            if can_merge(recipe1, recipe2):
                return i, j, recipe1, recipe2
        return None

    def _apply_merge_prepare_recipes(
        self, flow: DataikuFlow, result: OptimizationResult
    ) -> None:
        """Merge mergeable Prepare recipes anywhere in the DAG.

        Was list-position based (only adjacent recipes considered).
        Now scans the dependency graph: if a Prepare recipe's single
        output is consumed by exactly one downstream Prepare recipe
        whose only input is that output, the pair is merged — regardless
        of where they sit in ``flow.recipes``. Fan-out (multiple
        consumers of the intermediate) blocks the merge.
        """
        def is_prepare(r):
            return r.recipe_type == RecipeType.PREPARE

        can_merge = RecipeMerger.can_merge_prepare

        while True:
            pair = self._find_merge_pair(flow, is_prepare, can_merge)
            if pair is None:
                break
            i, j, recipe1, recipe2 = pair

            intermediate_ds = recipe1.outputs[0]
            old_recipe1_output = recipe1.outputs[0]
            merged = RecipeMerger.merge_prepare_recipes([recipe1, recipe2])
            new_output = merged.outputs[0] if merged.outputs else None

            # Replace recipe1 with the merged recipe; remove recipe2.
            flow.recipes[i] = merged
            # Remove recipe2 by index. After pop, indices > j shift down by 1
            # — that's fine because we restart the scan immediately.
            flow.recipes.pop(j)

            # Rewrite any downstream recipe that referenced the absorbed
            # intermediate name to point at the merged output.
            if old_recipe1_output and new_output and old_recipe1_output != new_output:
                for downstream in flow.recipes:
                    if downstream is merged:
                        continue
                    downstream.inputs = [
                        new_output if inp == old_recipe1_output else inp
                        for inp in downstream.inputs
                    ]

            result.recipes_merged += 1
            result.log.append(
                f"Merged '{recipe1.name}' + '{recipe2.name}' -> '{merged.name}'"
            )

            # Drop the now-orphaned intermediate dataset, if any.
            ds = flow.get_dataset(intermediate_ds)
            if ds is not None:
                still_referenced = any(
                    intermediate_ds in r.inputs or intermediate_ds in r.outputs
                    for r in flow.recipes
                )
                if not still_referenced:
                    flow.datasets = [
                        d for d in flow.datasets if d.name != intermediate_ds
                    ]
                    result.datasets_removed += 1
                    result.log.append(
                        f"Removed intermediate dataset '{intermediate_ds}'"
                    )

    def _apply_merge_window_recipes(
        self, flow: DataikuFlow, result: OptimizationResult
    ) -> None:
        """Merge mergeable Window recipes anywhere in the DAG.

        Two WINDOW recipes can be merged when they share the same input
        dataset (chained or sibling) AND the same partition_columns
        AND the same order_columns. Now DAG-aware (was list-position
        based): a WINDOW separated from its merge candidate by an
        unrelated PREPARE/JOIN/etc. is still detected.

        For chained WINDOW pairs (recipe1.outputs[0] == recipe2.inputs[0])
        we additionally enforce the fan-out guard — recipe1's output
        must have exactly one consumer (recipe2). Sibling WINDOW pairs
        (same recipe1.inputs[0] as recipe2.inputs[0]) don't have this
        constraint since the shared input keeps its identity after merge.
        """
        # Build "input -> [consumer indices]" once per pass; recomputed
        # after each merge since indices shift.
        def _consumers(flow_obj: DataikuFlow) -> dict[str, list[int]]:
            c: dict[str, list[int]] = {}
            for idx, r in enumerate(flow_obj.recipes):
                for inp in r.inputs:
                    c.setdefault(inp, []).append(idx)
            return c

        changed = True
        while changed:
            changed = False
            consumers = _consumers(flow)
            window_indices = [
                i for i, r in enumerate(flow.recipes)
                if r.recipe_type == RecipeType.WINDOW
            ]
            merge_pair = None
            for i in window_indices:
                recipe1 = flow.recipes[i]
                if not recipe1.outputs or not recipe1.inputs:
                    continue
                # Try to find a downstream WINDOW (chained merge candidate)
                # with exactly-one fan-out from recipe1.
                output_name = recipe1.outputs[0]
                downstream = consumers.get(output_name, [])
                if len(downstream) == 1:
                    j = downstream[0]
                    if j != i and flow.recipes[j].recipe_type == RecipeType.WINDOW:
                        recipe2 = flow.recipes[j]
                        if (
                            recipe2.inputs == [output_name]
                            and recipe1.partition_columns == recipe2.partition_columns
                            and recipe1.order_columns == recipe2.order_columns
                        ):
                            merge_pair = (i, j, recipe1, recipe2, True)  # True = chained
                            break
                # Otherwise try a sibling WINDOW (same input dataset).
                if recipe1.inputs:
                    input_name = recipe1.inputs[0]
                    siblings = consumers.get(input_name, [])
                    for k in siblings:
                        if k <= i:  # only look forward to avoid duplicate pairs
                            continue
                        recipe2 = flow.recipes[k]
                        if recipe2.recipe_type != RecipeType.WINDOW:
                            continue
                        if (
                            recipe2.inputs[:1] == [input_name]
                            and recipe1.partition_columns == recipe2.partition_columns
                            and recipe1.order_columns == recipe2.order_columns
                        ):
                            merge_pair = (i, k, recipe1, recipe2, False)  # False = sibling
                            break
                    if merge_pair is not None:
                        break

            if merge_pair is None:
                break

            i, j, recipe1, recipe2, same_chain = merge_pair

            old_recipe1_output = recipe1.outputs[0] if recipe1.outputs else None
            new_output = recipe2.outputs[0] if recipe2.outputs else None

            # Build the merged recipe: union of aggregations, output is
            # recipe2.outputs (downstream consumers look there).
            merged = DataikuRecipe(
                name=f"window_merged_{recipe1.name}",
                recipe_type=RecipeType.WINDOW,
                inputs=list(recipe1.inputs),
                outputs=list(recipe2.outputs),
                partition_columns=list(recipe1.partition_columns),
                order_columns=list(recipe1.order_columns),
                window_aggregations=(
                    list(recipe1.window_aggregations)
                    + list(recipe2.window_aggregations)
                ),
                source_lines=list(recipe1.source_lines) + list(recipe2.source_lines),
                notes=list(recipe1.notes) + list(recipe2.notes),
            )

            flow.recipes[i] = merged
            flow.recipes.pop(j)

            # Rewrite any downstream recipe that referenced the absorbed
            # intermediate output so it points at the merged output.
            if (
                old_recipe1_output
                and new_output
                and old_recipe1_output != new_output
            ):
                for downstream in flow.recipes:
                    if downstream is merged:
                        continue
                    downstream.inputs = [
                        new_output if inp == old_recipe1_output else inp
                        for inp in downstream.inputs
                    ]

            result.recipes_merged += 1
            result.log.append(
                f"Merged WINDOW '{recipe1.name}' + '{recipe2.name}' "
                f"-> '{merged.name}'"
            )

            # Remove the now-unreferenced intermediate dataset, if any.
            if (
                same_chain
                and old_recipe1_output
                and old_recipe1_output != new_output
            ):
                intermediate_ds = old_recipe1_output
                still_referenced = any(
                    intermediate_ds in r.inputs or intermediate_ds in r.outputs
                    for r in flow.recipes
                )
                if not still_referenced:
                    flow.datasets = [
                        d for d in flow.datasets if d.name != intermediate_ds
                    ]
                    result.datasets_removed += 1
                    result.log.append(
                        f"Removed intermediate dataset '{intermediate_ds}'"
                    )

            changed = True

    def _apply_remove_orphan_datasets(
        self, flow: DataikuFlow, result: OptimizationResult
    ) -> None:
        """Remove intermediate datasets that are no longer referenced."""
        referenced: set[str] = set()
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
    ) -> list[list[DataikuRecipe]]:
        """Identify recipe sequences that can run in parallel.

        Currently a no-op stub. The previous implementation was an O(R^2 * D)
        hot path that did no useful work (its inner body was ``pass`` and the
        result was never accumulated). On flows with 100+ recipes this
        consumed 99% of conversion time. The stub remains for callers/tests
        that import it directly; a real implementation can be added later
        using cached transitive-closure reachability rather than per-pair BFS.
        """
        return []

    def _build_dependency_graph(self, flow: DataikuFlow) -> dict:
        """Build a dependency graph of recipes."""
        deps: dict[str, set[str]] = {}
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

        visited: set[str] = set()
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
