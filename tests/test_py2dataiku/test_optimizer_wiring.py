"""Tests for C5: FlowOptimizer wired into convert() pipeline."""

import pytest

from py2dataiku import convert, DataikuFlow
from py2dataiku.generators.base_generator import BaseFlowGenerator
from py2dataiku.generators.flow_generator import FlowGenerator
from py2dataiku.models.dataiku_recipe import DataikuRecipe, RecipeType
from py2dataiku.models.dataiku_dataset import DataikuDataset, DatasetType
from py2dataiku.models.prepare_step import PrepareStep, ProcessorType
from py2dataiku.optimizer.flow_optimizer import FlowOptimizer, OptimizationResult
from py2dataiku.optimizer.recipe_merger import RecipeMerger


# ---------------------------------------------------------------------------
# FlowOptimizer is called during convert()
# ---------------------------------------------------------------------------

class TestFlowOptimizerWiring:
    """Verify FlowOptimizer is actually invoked when optimize=True."""

    def test_optimize_true_adds_optimization_notes(self):
        """convert(optimize=True) should produce optimization_notes on the flow."""
        code = """
import pandas as pd
df = pd.read_csv('data.csv')
df = df.dropna()
"""
        flow = convert(code, optimize=True)
        # FlowOptimizer and _optimize_flow both add notes
        assert len(flow.optimization_notes) > 0

    def test_optimize_false_no_optimization_notes(self):
        """convert(optimize=False) should not produce optimization notes."""
        code = """
import pandas as pd
df = pd.read_csv('data.csv')
df = df.dropna()
"""
        flow = convert(code, optimize=False)
        assert len(flow.optimization_notes) == 0


# ---------------------------------------------------------------------------
# Consecutive Prepare recipe merging
# ---------------------------------------------------------------------------

class TestPrepareRecipeMerging:
    """Verify that consecutive Prepare recipes get merged."""

    def _build_flow_with_consecutive_prepares(self) -> DataikuFlow:
        """Build a flow with two consecutive Prepare recipes manually."""
        flow = DataikuFlow(name="test")

        # Input dataset
        flow.add_dataset(DataikuDataset(name="input", dataset_type=DatasetType.INPUT))

        # First Prepare recipe: input -> intermediate
        recipe1 = DataikuRecipe.create_prepare(
            "prepare_1", "input", "intermediate",
            steps=[PrepareStep.fill_empty("col1", 0)],
        )
        flow.add_recipe(recipe1)

        # Intermediate dataset
        flow.add_dataset(
            DataikuDataset(name="intermediate", dataset_type=DatasetType.INTERMEDIATE)
        )

        # Second Prepare recipe: intermediate -> output
        recipe2 = DataikuRecipe.create_prepare(
            "prepare_2", "intermediate", "output",
            steps=[PrepareStep.remove_rows_on_empty(["col2"])],
        )
        flow.add_recipe(recipe2)

        # Output dataset
        flow.add_dataset(DataikuDataset(name="output", dataset_type=DatasetType.OUTPUT))

        return flow

    def test_flow_optimizer_merges_consecutive_prepares(self):
        """FlowOptimizer.optimize() should merge consecutive Prepare recipes."""
        flow = self._build_flow_with_consecutive_prepares()
        assert len(flow.recipes) == 2

        optimizer = FlowOptimizer()
        optimizer.optimize(flow, apply=True)

        # After merging, should have 1 recipe instead of 2
        assert len(flow.recipes) == 1
        merged = flow.recipes[0]
        assert merged.recipe_type == RecipeType.PREPARE
        # Merged recipe should contain steps from both originals
        assert len(merged.steps) == 2

    def test_flow_optimizer_removes_intermediate_dataset(self):
        """FlowOptimizer should remove the intermediate dataset after merge."""
        flow = self._build_flow_with_consecutive_prepares()
        assert any(d.name == "intermediate" for d in flow.datasets)

        optimizer = FlowOptimizer()
        optimizer.optimize(flow, apply=True)

        # Intermediate dataset should be removed
        assert not any(d.name == "intermediate" for d in flow.datasets)

    def test_flow_optimizer_preserves_io(self):
        """Merged recipe should use the original input and final output."""
        flow = self._build_flow_with_consecutive_prepares()

        optimizer = FlowOptimizer()
        optimizer.optimize(flow, apply=True)

        merged = flow.recipes[0]
        assert merged.inputs == ["input"]
        assert merged.outputs == ["output"]

    def test_base_generator_calls_optimizer(self):
        """BaseFlowGenerator._optimize_flow() should invoke FlowOptimizer."""

        class _TestGen(BaseFlowGenerator):
            def generate(self, *a, **kw):
                pass

        gen = _TestGen()
        gen.flow = self._build_flow_with_consecutive_prepares()
        assert len(gen.flow.recipes) == 2

        gen._optimize_flow()

        # Should have merged the two recipes
        assert len(gen.flow.recipes) == 1

    def test_convert_merges_when_applicable(self):
        """convert() with multi-step code should produce fewer recipes with optimize=True."""
        code = """
import pandas as pd
df = pd.read_csv('data.csv')
df['name'] = df['name'].str.strip()
df = df.dropna(subset=['id'])
df = df.drop_duplicates()
"""
        flow_opt = convert(code, optimize=True)
        flow_no_opt = convert(code, optimize=False)

        # With optimization, recipe count should be <= without optimization
        assert len(flow_opt.recipes) <= len(flow_no_opt.recipes)


# ---------------------------------------------------------------------------
# RecipeMerger step optimization
# ---------------------------------------------------------------------------

class TestStepOptimization:
    """Verify RecipeMerger.optimize_prepare_steps() and remove_redundant_steps()."""

    def test_optimize_step_order(self):
        """Column deletions should come before other operations."""
        steps = [
            PrepareStep(processor_type=ProcessorType.FILL_EMPTY_WITH_VALUE,
                        params={"column": "a", "value": 0}),
            PrepareStep(processor_type=ProcessorType.COLUMN_DELETER,
                        params={"columns": ["b"]}),
            PrepareStep(processor_type=ProcessorType.COLUMN_RENAMER,
                        params={"column": "c", "new_name": "d"}),
            PrepareStep(processor_type=ProcessorType.REMOVE_ROWS_ON_EMPTY,
                        params={"column": "e"}),
        ]

        optimized = RecipeMerger.optimize_prepare_steps(steps)
        # Deletions first, then row filters, then other, then renames
        assert optimized[0].processor_type == ProcessorType.COLUMN_DELETER
        assert optimized[-1].processor_type == ProcessorType.COLUMN_RENAMER

    def test_remove_redundant_steps_deleted_column(self):
        """Operations on a deleted column should be removed."""
        steps = [
            PrepareStep(processor_type=ProcessorType.COLUMN_DELETER,
                        params={"columns": ["x"]}),
            PrepareStep(processor_type=ProcessorType.FILL_EMPTY_WITH_VALUE,
                        params={"column": "x", "value": 0}),
            PrepareStep(processor_type=ProcessorType.FILL_EMPTY_WITH_VALUE,
                        params={"column": "y", "value": 1}),
        ]

        result = RecipeMerger.remove_redundant_steps(steps)
        # Fill on column "x" should be removed (column was deleted)
        assert len(result) == 2
        # Remaining: delete "x" and fill "y"
        columns_affected = [s.params.get("column") or s.params.get("columns")
                            for s in result]
        assert ["x"] in columns_affected  # delete step
        assert "y" in columns_affected    # fill step

    def test_optimize_steps_called_during_convert(self):
        """After optimization, Prepare steps should be in optimal order."""
        code = """
import pandas as pd
df = pd.read_csv('data.csv')
df['name'] = df['name'].str.strip()
df = df.dropna(subset=['id'])
df = df.drop(columns=['temp'])
"""
        flow = convert(code, optimize=True)
        prepare_recipes = flow.get_recipes_by_type(RecipeType.PREPARE)

        for recipe in prepare_recipes:
            if len(recipe.steps) >= 2:
                # Verify deletions come before row filters
                deletion_idx = None
                filter_idx = None
                for i, step in enumerate(recipe.steps):
                    if step.processor_type == ProcessorType.COLUMN_DELETER:
                        deletion_idx = i
                    if step.processor_type == ProcessorType.REMOVE_ROWS_ON_EMPTY:
                        filter_idx = i
                if deletion_idx is not None and filter_idx is not None:
                    assert deletion_idx < filter_idx


# ---------------------------------------------------------------------------
# OptimizationResult tracking
# ---------------------------------------------------------------------------

class TestOptimizationResult:
    """Verify OptimizationResult correctly tracks operations."""

    def test_result_tracks_merged_count(self):
        """OptimizationResult should count merged recipes."""
        flow = DataikuFlow(name="test")
        flow.add_dataset(DataikuDataset(name="in", dataset_type=DatasetType.INPUT))
        flow.add_dataset(
            DataikuDataset(name="mid", dataset_type=DatasetType.INTERMEDIATE)
        )
        flow.add_dataset(DataikuDataset(name="out", dataset_type=DatasetType.OUTPUT))

        flow.add_recipe(DataikuRecipe.create_prepare(
            "p1", "in", "mid", steps=[PrepareStep.fill_empty("a", 0)]
        ))
        flow.add_recipe(DataikuRecipe.create_prepare(
            "p2", "mid", "out", steps=[PrepareStep.fill_empty("b", 1)]
        ))

        optimizer = FlowOptimizer()
        optimizer.optimize(flow, apply=True)

        assert optimizer.last_result.recipes_merged >= 1
        assert len(optimizer.last_result.log) > 0

    def test_result_to_dict(self):
        """OptimizationResult.to_dict() should return a valid dictionary."""
        result = OptimizationResult(recipes_merged=2, datasets_removed=1)
        d = result.to_dict()
        assert d["recipes_merged"] == 2
        assert d["datasets_removed"] == 1


# ---------------------------------------------------------------------------
# Recommendations (apply=False mode)
# ---------------------------------------------------------------------------

class TestOptimizationRecommendations:
    """Verify FlowOptimizer generates recommendations without applying."""

    def test_recommend_mode_does_not_merge(self):
        """optimize(apply=False) should not alter the flow."""
        flow = DataikuFlow(name="test")
        flow.add_dataset(DataikuDataset(name="in", dataset_type=DatasetType.INPUT))
        flow.add_dataset(
            DataikuDataset(name="mid", dataset_type=DatasetType.INTERMEDIATE)
        )
        flow.add_dataset(DataikuDataset(name="out", dataset_type=DatasetType.OUTPUT))

        flow.add_recipe(DataikuRecipe.create_prepare(
            "p1", "in", "mid", steps=[PrepareStep.fill_empty("a", 0)]
        ))
        flow.add_recipe(DataikuRecipe.create_prepare(
            "p2", "mid", "out", steps=[PrepareStep.fill_empty("b", 1)]
        ))

        optimizer = FlowOptimizer()
        optimizer.optimize(flow, apply=False)

        # Recipes should NOT be merged
        assert len(flow.recipes) == 2
        # But should have recommendations
        assert len(flow.recommendations) > 0

    def test_filter_push_recommendation(self):
        """Optimizer should recommend pushing filters before joins."""
        flow = DataikuFlow(name="test")
        flow.add_dataset(DataikuDataset(name="left", dataset_type=DatasetType.INPUT))
        flow.add_dataset(DataikuDataset(name="right", dataset_type=DatasetType.INPUT))
        flow.add_dataset(
            DataikuDataset(name="joined", dataset_type=DatasetType.INTERMEDIATE)
        )
        flow.add_dataset(DataikuDataset(name="filtered", dataset_type=DatasetType.OUTPUT))

        join_recipe = DataikuRecipe(
            name="join_1", recipe_type=RecipeType.JOIN,
            inputs=["left", "right"], outputs=["joined"],
        )
        flow.add_recipe(join_recipe)

        split_recipe = DataikuRecipe(
            name="split_1", recipe_type=RecipeType.SPLIT,
            inputs=["joined"], outputs=["filtered"],
        )
        flow.add_recipe(split_recipe)

        optimizer = FlowOptimizer()
        optimizer.optimize(flow, apply=False)

        perf_recs = [r for r in flow.recommendations if r.type == "PERFORMANCE"]
        assert len(perf_recs) >= 1
        assert "filter" in perf_recs[0].message.lower() or "Filter" in perf_recs[0].message


# ---------------------------------------------------------------------------
# RecipeMerger.can_merge_prepare
# ---------------------------------------------------------------------------

class TestCanMergePrepare:
    """Tests for RecipeMerger.can_merge_prepare()."""

    def test_can_merge_consecutive(self):
        r1 = DataikuRecipe.create_prepare("p1", "in", "mid")
        r2 = DataikuRecipe.create_prepare("p2", "mid", "out")
        assert RecipeMerger.can_merge_prepare(r1, r2) is True

    def test_cannot_merge_different_types(self):
        r1 = DataikuRecipe.create_prepare("p1", "in", "mid")
        r2 = DataikuRecipe(
            name="j", recipe_type=RecipeType.JOIN,
            inputs=["mid"], outputs=["out"],
        )
        assert RecipeMerger.can_merge_prepare(r1, r2) is False

    def test_cannot_merge_disconnected(self):
        r1 = DataikuRecipe.create_prepare("p1", "in1", "out1")
        r2 = DataikuRecipe.create_prepare("p2", "in2", "out2")
        assert RecipeMerger.can_merge_prepare(r1, r2) is False

    def test_merge_preserves_all_steps(self):
        step1 = PrepareStep.fill_empty("a", 0)
        step2 = PrepareStep.fill_empty("b", 1)
        step3 = PrepareStep.fill_empty("c", 2)

        r1 = DataikuRecipe.create_prepare("p1", "in", "mid", steps=[step1])
        r2 = DataikuRecipe.create_prepare("p2", "mid", "out", steps=[step2, step3])

        merged = RecipeMerger.merge_prepare_recipes([r1, r2])
        assert len(merged.steps) == 3
        assert merged.inputs == ["in"]
        assert merged.outputs == ["out"]
