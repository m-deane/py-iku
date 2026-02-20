"""Tests for the optimizer module."""

import pytest

from py2dataiku.models.dataiku_flow import DataikuFlow
from py2dataiku.models.dataiku_recipe import DataikuRecipe, RecipeType
from py2dataiku.models.dataiku_dataset import DataikuDataset, DatasetType
from py2dataiku.models.prepare_step import PrepareStep, ProcessorType
from py2dataiku.optimizer.flow_optimizer import FlowOptimizer
from py2dataiku.optimizer.recipe_merger import RecipeMerger


class TestFlowOptimizer:
    """Tests for FlowOptimizer class."""

    def test_init(self):
        """Test FlowOptimizer initialization."""
        optimizer = FlowOptimizer()
        assert optimizer.recommendations == []

    def test_optimize_empty_flow(self):
        """Test optimizing an empty flow."""
        flow = DataikuFlow(name="empty_flow")
        optimizer = FlowOptimizer()

        result = optimizer.optimize(flow)

        assert result is not None
        assert result.name == "empty_flow"
        assert len(result.recipes) == 0

    def test_optimize_single_recipe_flow(self):
        """Test optimizing a flow with single recipe."""
        flow = DataikuFlow(name="single_recipe_flow")
        flow.add_dataset(DataikuDataset(name="input", dataset_type=DatasetType.INPUT))
        flow.add_dataset(DataikuDataset(name="output", dataset_type=DatasetType.OUTPUT))
        flow.add_recipe(DataikuRecipe(
            name="prepare_1",
            recipe_type=RecipeType.PREPARE,
            inputs=["input"],
            outputs=["output"]
        ))

        optimizer = FlowOptimizer()
        result = optimizer.optimize(flow)

        assert result is not None
        assert len(result.recipes) == 1

    def test_apply_merge_consecutive_prepare_recipes(self):
        """Test that consecutive Prepare recipes are merged when apply=True."""
        flow = DataikuFlow(name="consecutive_prepares")
        flow.add_dataset(DataikuDataset(name="input", dataset_type=DatasetType.INPUT))
        flow.add_dataset(DataikuDataset(name="intermediate", dataset_type=DatasetType.INTERMEDIATE))
        flow.add_dataset(DataikuDataset(name="output", dataset_type=DatasetType.OUTPUT))
        flow.add_recipe(DataikuRecipe(
            name="prepare_1",
            recipe_type=RecipeType.PREPARE,
            inputs=["input"],
            outputs=["intermediate"]
        ))
        flow.add_recipe(DataikuRecipe(
            name="prepare_2",
            recipe_type=RecipeType.PREPARE,
            inputs=["intermediate"],
            outputs=["output"]
        ))

        optimizer = FlowOptimizer()
        result = optimizer.optimize(flow, apply=True)

        # Should have merged the two recipes into one
        assert len(result.recipes) == 1
        assert result.recipes[0].inputs == ["input"]
        assert result.recipes[0].outputs == ["output"]
        assert optimizer.last_result.recipes_merged == 1

    def test_recommend_consecutive_prepare_recipes(self):
        """Test recommendation for consecutive Prepare recipes when apply=False."""
        flow = DataikuFlow(name="consecutive_prepares")
        flow.add_dataset(DataikuDataset(name="input", dataset_type=DatasetType.INPUT))
        flow.add_dataset(DataikuDataset(name="intermediate", dataset_type=DatasetType.INTERMEDIATE))
        flow.add_dataset(DataikuDataset(name="output", dataset_type=DatasetType.OUTPUT))
        flow.add_recipe(DataikuRecipe(
            name="prepare_1",
            recipe_type=RecipeType.PREPARE,
            inputs=["input"],
            outputs=["intermediate"]
        ))
        flow.add_recipe(DataikuRecipe(
            name="prepare_2",
            recipe_type=RecipeType.PREPARE,
            inputs=["intermediate"],
            outputs=["output"]
        ))

        optimizer = FlowOptimizer()
        optimizer.optimize(flow, apply=False)

        # Should have recommendation to merge
        consolidation_recs = [r for r in flow.recommendations if r.type == "CONSOLIDATION"]
        assert len(consolidation_recs) >= 1

    def test_detect_filter_after_join(self):
        """Test detection of filter after join pattern."""
        flow = DataikuFlow(name="filter_after_join")
        flow.add_dataset(DataikuDataset(name="left", dataset_type=DatasetType.INPUT))
        flow.add_dataset(DataikuDataset(name="right", dataset_type=DatasetType.INPUT))
        flow.add_dataset(DataikuDataset(name="joined", dataset_type=DatasetType.INTERMEDIATE))
        flow.add_dataset(DataikuDataset(name="filtered", dataset_type=DatasetType.OUTPUT))
        flow.add_recipe(DataikuRecipe(
            name="join_1",
            recipe_type=RecipeType.JOIN,
            inputs=["left", "right"],
            outputs=["joined"]
        ))
        flow.add_recipe(DataikuRecipe(
            name="split_1",
            recipe_type=RecipeType.SPLIT,
            inputs=["joined"],
            outputs=["filtered"]
        ))

        optimizer = FlowOptimizer()
        optimizer.optimize(flow)

        # Should have performance recommendation
        perf_recs = [r for r in flow.recommendations if r.type == "PERFORMANCE"]
        assert len(perf_recs) >= 1

    def test_build_dependency_graph(self):
        """Test dependency graph building."""
        flow = DataikuFlow(name="deps")
        flow.add_recipe(DataikuRecipe(
            name="r1",
            recipe_type=RecipeType.PREPARE,
            inputs=["input"],
            outputs=["middle"]
        ))
        flow.add_recipe(DataikuRecipe(
            name="r2",
            recipe_type=RecipeType.PREPARE,
            inputs=["middle"],
            outputs=["output"]
        ))

        optimizer = FlowOptimizer()
        deps = optimizer._build_dependency_graph(flow)

        assert "r1" in deps
        assert "r2" in deps
        assert "r1" in deps["r2"]
        assert len(deps["r1"]) == 0

    def test_has_dependency_direct(self):
        """Test direct dependency detection."""
        flow = DataikuFlow(name="deps")
        r1 = DataikuRecipe(name="r1", recipe_type=RecipeType.PREPARE, inputs=["a"], outputs=["b"])
        r2 = DataikuRecipe(name="r2", recipe_type=RecipeType.PREPARE, inputs=["b"], outputs=["c"])
        flow.add_recipe(r1)
        flow.add_recipe(r2)

        optimizer = FlowOptimizer()
        deps = optimizer._build_dependency_graph(flow)

        assert optimizer._has_dependency(r1, r2, deps)

    def test_has_dependency_transitive(self):
        """Test transitive dependency detection."""
        flow = DataikuFlow(name="transitive_deps")
        r1 = DataikuRecipe(name="r1", recipe_type=RecipeType.PREPARE, inputs=["a"], outputs=["b"])
        r2 = DataikuRecipe(name="r2", recipe_type=RecipeType.PREPARE, inputs=["b"], outputs=["c"])
        r3 = DataikuRecipe(name="r3", recipe_type=RecipeType.PREPARE, inputs=["c"], outputs=["d"])
        flow.add_recipe(r1)
        flow.add_recipe(r2)
        flow.add_recipe(r3)

        optimizer = FlowOptimizer()
        deps = optimizer._build_dependency_graph(flow)

        # r1 -> r2 -> r3, so r3 depends on r1 (transitively via r2)
        # The _has_dependency checks if recipe2 is in recipe1's dependency chain
        # or if recipe1 is in recipe2's chain
        assert optimizer._has_dependency(r3, r1, deps)

    def test_no_dependency_parallel_branches(self):
        """Test that parallel branches have no dependency."""
        flow = DataikuFlow(name="parallel")
        r1 = DataikuRecipe(name="r1", recipe_type=RecipeType.PREPARE, inputs=["a"], outputs=["b"])
        r2 = DataikuRecipe(name="r2", recipe_type=RecipeType.PREPARE, inputs=["x"], outputs=["y"])
        flow.add_recipe(r1)
        flow.add_recipe(r2)

        optimizer = FlowOptimizer()
        deps = optimizer._build_dependency_graph(flow)

        assert not optimizer._has_dependency(r1, r2, deps)


class TestRecipeMerger:
    """Tests for RecipeMerger class."""

    def test_can_merge_prepare_recipes(self):
        """Test checking if Prepare recipes can be merged."""
        r1 = DataikuRecipe(
            name="prepare_1",
            recipe_type=RecipeType.PREPARE,
            inputs=["input"],
            outputs=["middle"]
        )
        r2 = DataikuRecipe(
            name="prepare_2",
            recipe_type=RecipeType.PREPARE,
            inputs=["middle"],
            outputs=["output"]
        )

        assert RecipeMerger.can_merge_prepare(r1, r2) is True

    def test_cannot_merge_non_consecutive(self):
        """Test that non-consecutive recipes cannot be merged."""
        r1 = DataikuRecipe(
            name="prepare_1",
            recipe_type=RecipeType.PREPARE,
            inputs=["input"],
            outputs=["a"]
        )
        r2 = DataikuRecipe(
            name="prepare_2",
            recipe_type=RecipeType.PREPARE,
            inputs=["b"],  # Different input
            outputs=["output"]
        )

        assert RecipeMerger.can_merge_prepare(r1, r2) is False

    def test_cannot_merge_different_types(self):
        """Test that different recipe types cannot be merged."""
        r1 = DataikuRecipe(
            name="prepare_1",
            recipe_type=RecipeType.PREPARE,
            inputs=["input"],
            outputs=["middle"]
        )
        r2 = DataikuRecipe(
            name="join_1",
            recipe_type=RecipeType.JOIN,
            inputs=["middle"],
            outputs=["output"]
        )

        assert RecipeMerger.can_merge_prepare(r1, r2) is False

    def test_merge_prepare_recipes(self):
        """Test merging multiple Prepare recipes."""
        step1 = PrepareStep(processor_type=ProcessorType.COLUMN_RENAMER, params={"column": "a", "new_name": "b"})
        step2 = PrepareStep(processor_type=ProcessorType.FILL_EMPTY_WITH_VALUE, params={"column": "c", "value": 0})

        r1 = DataikuRecipe(
            name="prepare_1",
            recipe_type=RecipeType.PREPARE,
            inputs=["input"],
            outputs=["middle"],
            steps=[step1]
        )
        r2 = DataikuRecipe(
            name="prepare_2",
            recipe_type=RecipeType.PREPARE,
            inputs=["middle"],
            outputs=["output"],
            steps=[step2]
        )

        merged = RecipeMerger.merge_prepare_recipes([r1, r2])

        assert merged.recipe_type == RecipeType.PREPARE
        assert merged.inputs == ["input"]
        assert merged.outputs == ["output"]
        assert len(merged.steps) == 2

    def test_merge_single_recipe(self):
        """Test merging a single recipe returns itself."""
        r1 = DataikuRecipe(
            name="prepare_1",
            recipe_type=RecipeType.PREPARE,
            inputs=["input"],
            outputs=["output"]
        )

        result = RecipeMerger.merge_prepare_recipes([r1])
        assert result is r1

    def test_merge_empty_list_raises(self):
        """Test merging empty list raises error."""
        with pytest.raises(ValueError, match="No recipes to merge"):
            RecipeMerger.merge_prepare_recipes([])

    def test_merge_non_prepare_raises(self):
        """Test merging non-Prepare recipe raises error."""
        r1 = DataikuRecipe(
            name="prepare_1",
            recipe_type=RecipeType.PREPARE,
            inputs=["a"],
            outputs=["b"]
        )
        r2 = DataikuRecipe(
            name="join_1",
            recipe_type=RecipeType.JOIN,
            inputs=["b", "c"],
            outputs=["d"]
        )

        with pytest.raises(ValueError, match="not a Prepare recipe"):
            RecipeMerger.merge_prepare_recipes([r1, r2])

    def test_optimize_prepare_steps_order(self):
        """Test that step optimization orders correctly."""
        steps = [
            PrepareStep(processor_type=ProcessorType.COLUMN_RENAMER, params={}),
            PrepareStep(processor_type=ProcessorType.COLUMN_DELETER, params={}),
            PrepareStep(processor_type=ProcessorType.TYPE_SETTER, params={}),
            PrepareStep(processor_type=ProcessorType.REMOVE_ROWS_ON_EMPTY, params={}),
        ]

        optimized = RecipeMerger.optimize_prepare_steps(steps)

        # Order should be: deletions, type_setters, row_filters, other, renames
        assert optimized[0].processor_type == ProcessorType.COLUMN_DELETER
        assert optimized[1].processor_type == ProcessorType.TYPE_SETTER
        assert optimized[2].processor_type == ProcessorType.REMOVE_ROWS_ON_EMPTY
        assert optimized[3].processor_type == ProcessorType.COLUMN_RENAMER

    def test_remove_redundant_steps(self):
        """Test removal of redundant steps."""
        steps = [
            PrepareStep(processor_type=ProcessorType.COLUMN_DELETER, params={"columns": ["col_a"]}),
            PrepareStep(processor_type=ProcessorType.FILL_EMPTY_WITH_VALUE, params={"column": "col_a", "value": 0}),
            PrepareStep(processor_type=ProcessorType.FILL_EMPTY_WITH_VALUE, params={"column": "col_b", "value": 0}),
        ]

        optimized = RecipeMerger.remove_redundant_steps(steps)

        # Should remove operation on deleted column
        assert len(optimized) == 2
        assert optimized[0].processor_type == ProcessorType.COLUMN_DELETER
        assert optimized[1].params.get("column") == "col_b"


class TestFlowOptimizerIntegration:
    """Integration tests for flow optimization."""

    def test_optimize_complex_flow_apply(self):
        """Test optimizing a complex flow with apply=True merges recipes."""
        flow = DataikuFlow(name="complex_flow")

        # Create datasets
        for name in ["input1", "input2", "prepared1", "prepared2", "joined", "output"]:
            flow.add_dataset(DataikuDataset(name=name, dataset_type=DatasetType.INTERMEDIATE))

        # Create recipe chain: prepare_1 -> prepare_2 -> join_1 -> prepare_3
        flow.add_recipe(DataikuRecipe(
            name="prepare_1",
            recipe_type=RecipeType.PREPARE,
            inputs=["input1"],
            outputs=["prepared1"]
        ))
        flow.add_recipe(DataikuRecipe(
            name="prepare_2",
            recipe_type=RecipeType.PREPARE,
            inputs=["prepared1"],
            outputs=["prepared2"]
        ))
        flow.add_recipe(DataikuRecipe(
            name="join_1",
            recipe_type=RecipeType.JOIN,
            inputs=["prepared2", "input2"],
            outputs=["joined"]
        ))
        flow.add_recipe(DataikuRecipe(
            name="prepare_3",
            recipe_type=RecipeType.PREPARE,
            inputs=["joined"],
            outputs=["output"]
        ))

        optimizer = FlowOptimizer()
        result = optimizer.optimize(flow, apply=True)

        assert result is not None
        # prepare_1 and prepare_2 should have been merged
        assert optimizer.last_result.recipes_merged >= 1
        # The merged recipe should go from input1 to prepared2
        prepare_recipes = [r for r in result.recipes if r.recipe_type == RecipeType.PREPARE]
        assert len(prepare_recipes) == 2  # merged + prepare_3

    def test_optimize_complex_flow_recommend(self):
        """Test optimizing a complex flow with apply=False generates recommendations."""
        flow = DataikuFlow(name="complex_flow")

        # Create datasets
        for name in ["input1", "input2", "prepared1", "prepared2", "joined", "filtered", "output"]:
            flow.add_dataset(DataikuDataset(name=name, dataset_type=DatasetType.INTERMEDIATE))

        # Create recipe chain with filter-after-join pattern
        flow.add_recipe(DataikuRecipe(
            name="prepare_1",
            recipe_type=RecipeType.PREPARE,
            inputs=["input1"],
            outputs=["prepared1"]
        ))
        flow.add_recipe(DataikuRecipe(
            name="prepare_2",
            recipe_type=RecipeType.PREPARE,
            inputs=["prepared1"],
            outputs=["prepared2"]
        ))
        flow.add_recipe(DataikuRecipe(
            name="join_1",
            recipe_type=RecipeType.JOIN,
            inputs=["prepared2", "input2"],
            outputs=["joined"]
        ))
        flow.add_recipe(DataikuRecipe(
            name="split_1",
            recipe_type=RecipeType.SPLIT,
            inputs=["joined"],
            outputs=["filtered"]
        ))

        optimizer = FlowOptimizer()
        result = optimizer.optimize(flow, apply=False)

        assert result is not None
        # Should have CONSOLIDATION (consecutive prepares) and PERFORMANCE (filter after join)
        assert len(result.recommendations) >= 2


class TestOptimizationResult:
    """Tests for OptimizationResult dataclass."""

    def test_default_values(self):
        from py2dataiku.optimizer.flow_optimizer import OptimizationResult

        result = OptimizationResult()
        assert result.recipes_merged == 0
        assert result.datasets_removed == 0
        assert result.filters_pushed_down == 0
        assert result.log == []

    def test_to_dict(self):
        from py2dataiku.optimizer.flow_optimizer import OptimizationResult

        result = OptimizationResult(
            recipes_merged=2,
            datasets_removed=1,
            filters_pushed_down=0,
            log=["Merged A + B"],
        )
        d = result.to_dict()
        assert d["recipes_merged"] == 2
        assert d["datasets_removed"] == 1
        assert d["log"] == ["Merged A + B"]


class TestFlowOptimizerMerge:
    """Tests for actual recipe merging in FlowOptimizer."""

    def test_merge_removes_intermediate_dataset(self):
        """Merging consecutive prepares should remove the intermediate dataset."""
        flow = DataikuFlow(name="test")
        flow.add_dataset(DataikuDataset(name="input", dataset_type=DatasetType.INPUT))
        flow.add_dataset(DataikuDataset(name="mid", dataset_type=DatasetType.INTERMEDIATE))
        flow.add_dataset(DataikuDataset(name="output", dataset_type=DatasetType.OUTPUT))
        flow.add_recipe(DataikuRecipe(
            name="p1", recipe_type=RecipeType.PREPARE,
            inputs=["input"], outputs=["mid"]
        ))
        flow.add_recipe(DataikuRecipe(
            name="p2", recipe_type=RecipeType.PREPARE,
            inputs=["mid"], outputs=["output"]
        ))

        optimizer = FlowOptimizer()
        result = optimizer.optimize(flow, apply=True)

        assert optimizer.last_result.recipes_merged == 1
        assert optimizer.last_result.datasets_removed >= 1
        # mid should be gone
        assert flow.get_dataset("mid") is None

    def test_merge_preserves_steps(self):
        """Merged recipe should contain steps from both originals."""
        step1 = PrepareStep(processor_type=ProcessorType.COLUMN_RENAMER, params={"column": "a"})
        step2 = PrepareStep(processor_type=ProcessorType.FILL_EMPTY_WITH_VALUE, params={"column": "b"})

        flow = DataikuFlow(name="test")
        flow.add_dataset(DataikuDataset(name="input", dataset_type=DatasetType.INPUT))
        flow.add_dataset(DataikuDataset(name="mid", dataset_type=DatasetType.INTERMEDIATE))
        flow.add_dataset(DataikuDataset(name="output", dataset_type=DatasetType.OUTPUT))
        flow.add_recipe(DataikuRecipe(
            name="p1", recipe_type=RecipeType.PREPARE,
            inputs=["input"], outputs=["mid"], steps=[step1]
        ))
        flow.add_recipe(DataikuRecipe(
            name="p2", recipe_type=RecipeType.PREPARE,
            inputs=["mid"], outputs=["output"], steps=[step2]
        ))

        optimizer = FlowOptimizer()
        optimizer.optimize(flow, apply=True)

        assert len(flow.recipes) == 1
        assert len(flow.recipes[0].steps) == 2

    def test_merge_three_consecutive(self):
        """Three consecutive Prepare recipes should be merged into one."""
        flow = DataikuFlow(name="test")
        flow.add_dataset(DataikuDataset(name="a", dataset_type=DatasetType.INPUT))
        flow.add_dataset(DataikuDataset(name="b", dataset_type=DatasetType.INTERMEDIATE))
        flow.add_dataset(DataikuDataset(name="c", dataset_type=DatasetType.INTERMEDIATE))
        flow.add_dataset(DataikuDataset(name="d", dataset_type=DatasetType.OUTPUT))
        flow.add_recipe(DataikuRecipe(
            name="p1", recipe_type=RecipeType.PREPARE,
            inputs=["a"], outputs=["b"]
        ))
        flow.add_recipe(DataikuRecipe(
            name="p2", recipe_type=RecipeType.PREPARE,
            inputs=["b"], outputs=["c"]
        ))
        flow.add_recipe(DataikuRecipe(
            name="p3", recipe_type=RecipeType.PREPARE,
            inputs=["c"], outputs=["d"]
        ))

        optimizer = FlowOptimizer()
        optimizer.optimize(flow, apply=True)

        assert len(flow.recipes) == 1
        assert optimizer.last_result.recipes_merged == 2

    def test_no_merge_non_consecutive(self):
        """Prepare recipes separated by a Join should not be merged."""
        flow = DataikuFlow(name="test")
        flow.add_dataset(DataikuDataset(name="a", dataset_type=DatasetType.INPUT))
        flow.add_dataset(DataikuDataset(name="b", dataset_type=DatasetType.INTERMEDIATE))
        flow.add_dataset(DataikuDataset(name="c", dataset_type=DatasetType.INPUT))
        flow.add_dataset(DataikuDataset(name="d", dataset_type=DatasetType.INTERMEDIATE))
        flow.add_dataset(DataikuDataset(name="e", dataset_type=DatasetType.OUTPUT))
        flow.add_recipe(DataikuRecipe(
            name="p1", recipe_type=RecipeType.PREPARE,
            inputs=["a"], outputs=["b"]
        ))
        flow.add_recipe(DataikuRecipe(
            name="j1", recipe_type=RecipeType.JOIN,
            inputs=["b", "c"], outputs=["d"]
        ))
        flow.add_recipe(DataikuRecipe(
            name="p2", recipe_type=RecipeType.PREPARE,
            inputs=["d"], outputs=["e"]
        ))

        optimizer = FlowOptimizer()
        optimizer.optimize(flow, apply=True)

        assert len(flow.recipes) == 3
        assert optimizer.last_result.recipes_merged == 0

    def test_optimization_log_stored_on_flow(self):
        """Optimization log entries should be appended to flow.optimization_notes."""
        flow = DataikuFlow(name="test")
        flow.add_dataset(DataikuDataset(name="a", dataset_type=DatasetType.INPUT))
        flow.add_dataset(DataikuDataset(name="b", dataset_type=DatasetType.INTERMEDIATE))
        flow.add_dataset(DataikuDataset(name="c", dataset_type=DatasetType.OUTPUT))
        flow.add_recipe(DataikuRecipe(
            name="p1", recipe_type=RecipeType.PREPARE,
            inputs=["a"], outputs=["b"]
        ))
        flow.add_recipe(DataikuRecipe(
            name="p2", recipe_type=RecipeType.PREPARE,
            inputs=["b"], outputs=["c"]
        ))

        optimizer = FlowOptimizer()
        optimizer.optimize(flow, apply=True)

        assert len(flow.optimization_notes) > 0
        assert any("Merged" in note for note in flow.optimization_notes)


class TestFlowOptimizerOrphanRemoval:
    """Tests for orphan dataset removal."""

    def test_remove_orphan_intermediate(self):
        """Orphaned intermediate datasets should be removed."""
        flow = DataikuFlow(name="test")
        flow.add_dataset(DataikuDataset(name="input", dataset_type=DatasetType.INPUT))
        flow.add_dataset(DataikuDataset(name="orphan", dataset_type=DatasetType.INTERMEDIATE))
        flow.add_dataset(DataikuDataset(name="output", dataset_type=DatasetType.OUTPUT))
        flow.add_recipe(DataikuRecipe(
            name="p1", recipe_type=RecipeType.PREPARE,
            inputs=["input"], outputs=["output"]
        ))

        optimizer = FlowOptimizer()
        optimizer.optimize(flow, apply=True)

        assert flow.get_dataset("orphan") is None
        assert optimizer.last_result.datasets_removed >= 1

    def test_keep_input_datasets(self):
        """Input datasets should not be removed even if unreferenced."""
        flow = DataikuFlow(name="test")
        flow.add_dataset(DataikuDataset(name="unused_input", dataset_type=DatasetType.INPUT))

        optimizer = FlowOptimizer()
        optimizer.optimize(flow, apply=True)

        assert flow.get_dataset("unused_input") is not None
