"""Tests for FlowGraph DAG data structure."""

import pytest

from py2dataiku.models.flow_graph import FlowGraph, FlowNode, NodeType
from py2dataiku.models.dataiku_flow import DataikuFlow
from py2dataiku.models.dataiku_dataset import DataikuDataset, DatasetType
from py2dataiku.models.dataiku_recipe import DataikuRecipe, RecipeType


class TestFlowGraphBasic:
    """Tests for basic FlowGraph operations."""

    def test_add_node(self):
        g = FlowGraph()
        node = g.add_node("ds1", NodeType.DATASET)
        assert node.name == "ds1"
        assert node.node_type == NodeType.DATASET
        assert "ds1" in g
        assert len(g) == 1

    def test_add_edge(self):
        g = FlowGraph()
        g.add_node("ds1", NodeType.DATASET)
        g.add_node("r1", NodeType.RECIPE)
        g.add_edge("ds1", "r1")
        assert g.get_successors("ds1") == ["r1"]
        assert g.get_predecessors("r1") == ["ds1"]

    def test_add_edge_missing_node_raises(self):
        g = FlowGraph()
        g.add_node("ds1", NodeType.DATASET)
        with pytest.raises(ValueError, match="not found"):
            g.add_edge("ds1", "missing")

    def test_get_node(self):
        g = FlowGraph()
        g.add_node("ds1", NodeType.DATASET, metadata={"key": "value"})
        node = g.get_node("ds1")
        assert node is not None
        assert node.metadata == {"key": "value"}
        assert g.get_node("missing") is None

    def test_nodes_property(self):
        g = FlowGraph()
        g.add_node("ds1", NodeType.DATASET)
        g.add_node("r1", NodeType.RECIPE)
        assert len(g.nodes) == 2

    def test_dataset_nodes(self):
        g = FlowGraph()
        g.add_node("ds1", NodeType.DATASET)
        g.add_node("ds2", NodeType.DATASET)
        g.add_node("r1", NodeType.RECIPE)
        assert len(g.dataset_nodes) == 2

    def test_recipe_nodes(self):
        g = FlowGraph()
        g.add_node("ds1", NodeType.DATASET)
        g.add_node("r1", NodeType.RECIPE)
        g.add_node("r2", NodeType.RECIPE)
        assert len(g.recipe_nodes) == 2

    def test_edges_property(self):
        g = FlowGraph()
        g.add_node("ds1", NodeType.DATASET)
        g.add_node("r1", NodeType.RECIPE)
        g.add_node("ds2", NodeType.DATASET)
        g.add_edge("ds1", "r1")
        g.add_edge("r1", "ds2")
        assert len(g.edges) == 2
        assert ("ds1", "r1") in g.edges
        assert ("r1", "ds2") in g.edges

    def test_duplicate_edge_not_added(self):
        g = FlowGraph()
        g.add_node("a", NodeType.DATASET)
        g.add_node("b", NodeType.RECIPE)
        g.add_edge("a", "b")
        g.add_edge("a", "b")  # duplicate
        assert g.get_successors("a") == ["b"]

    def test_repr(self):
        g = FlowGraph()
        g.add_node("a", NodeType.DATASET)
        assert "nodes=1" in repr(g)

    def test_contains(self):
        g = FlowGraph()
        g.add_node("a", NodeType.DATASET)
        assert "a" in g
        assert "b" not in g


class TestFlowGraphTopologicalSort:
    """Tests for topological sorting."""

    def test_simple_linear(self):
        g = FlowGraph()
        g.add_node("ds1", NodeType.DATASET)
        g.add_node("r1", NodeType.RECIPE)
        g.add_node("ds2", NodeType.DATASET)
        g.add_edge("ds1", "r1")
        g.add_edge("r1", "ds2")
        order = g.topological_sort()
        assert order.index("ds1") < order.index("r1")
        assert order.index("r1") < order.index("ds2")

    def test_diamond_dag(self):
        g = FlowGraph()
        for n in ["a", "b", "c", "d"]:
            g.add_node(n, NodeType.DATASET)
        g.add_edge("a", "b")
        g.add_edge("a", "c")
        g.add_edge("b", "d")
        g.add_edge("c", "d")
        order = g.topological_sort()
        assert order.index("a") < order.index("b")
        assert order.index("a") < order.index("c")
        assert order.index("b") < order.index("d")
        assert order.index("c") < order.index("d")

    def test_empty_graph(self):
        g = FlowGraph()
        assert g.topological_sort() == []

    def test_single_node(self):
        g = FlowGraph()
        g.add_node("a", NodeType.DATASET)
        assert g.topological_sort() == ["a"]


class TestFlowGraphCycleDetection:
    """Tests for cycle detection."""

    def test_no_cycles(self):
        g = FlowGraph()
        g.add_node("a", NodeType.DATASET)
        g.add_node("b", NodeType.RECIPE)
        g.add_node("c", NodeType.DATASET)
        g.add_edge("a", "b")
        g.add_edge("b", "c")
        assert g.detect_cycles() == []

    def test_simple_cycle(self):
        g = FlowGraph()
        g.add_node("a", NodeType.DATASET)
        g.add_node("b", NodeType.RECIPE)
        g.add_edge("a", "b")
        g.add_edge("b", "a")
        cycles = g.detect_cycles()
        assert len(cycles) > 0

    def test_cycle_in_topological_sort(self):
        g = FlowGraph()
        g.add_node("a", NodeType.DATASET)
        g.add_node("b", NodeType.RECIPE)
        g.add_edge("a", "b")
        g.add_edge("b", "a")
        with pytest.raises(ValueError, match="cycle"):
            g.topological_sort()


class TestFlowGraphDisconnected:
    """Tests for disconnected subgraph detection."""

    def test_single_component(self):
        g = FlowGraph()
        g.add_node("a", NodeType.DATASET)
        g.add_node("b", NodeType.RECIPE)
        g.add_edge("a", "b")
        components = g.find_disconnected_subgraphs()
        assert len(components) == 1

    def test_two_components(self):
        g = FlowGraph()
        g.add_node("a", NodeType.DATASET)
        g.add_node("b", NodeType.RECIPE)
        g.add_edge("a", "b")
        g.add_node("c", NodeType.DATASET)
        g.add_node("d", NodeType.RECIPE)
        g.add_edge("c", "d")
        components = g.find_disconnected_subgraphs()
        assert len(components) == 2

    def test_isolated_node(self):
        g = FlowGraph()
        g.add_node("a", NodeType.DATASET)
        g.add_node("b", NodeType.DATASET)
        components = g.find_disconnected_subgraphs()
        assert len(components) == 2

    def test_empty_graph(self):
        g = FlowGraph()
        assert g.find_disconnected_subgraphs() == []


class TestFlowGraphPathFinding:
    """Tests for path finding."""

    def test_direct_path(self):
        g = FlowGraph()
        g.add_node("a", NodeType.DATASET)
        g.add_node("b", NodeType.RECIPE)
        g.add_edge("a", "b")
        path = g.get_path("a", "b")
        assert path == ["a", "b"]

    def test_multi_hop_path(self):
        g = FlowGraph()
        g.add_node("a", NodeType.DATASET)
        g.add_node("r1", NodeType.RECIPE)
        g.add_node("b", NodeType.DATASET)
        g.add_node("r2", NodeType.RECIPE)
        g.add_node("c", NodeType.DATASET)
        g.add_edge("a", "r1")
        g.add_edge("r1", "b")
        g.add_edge("b", "r2")
        g.add_edge("r2", "c")
        path = g.get_path("a", "c")
        assert path == ["a", "r1", "b", "r2", "c"]

    def test_no_path(self):
        g = FlowGraph()
        g.add_node("a", NodeType.DATASET)
        g.add_node("b", NodeType.DATASET)
        assert g.get_path("a", "b") is None

    def test_same_node(self):
        g = FlowGraph()
        g.add_node("a", NodeType.DATASET)
        assert g.get_path("a", "a") == ["a"]

    def test_missing_node(self):
        g = FlowGraph()
        g.add_node("a", NodeType.DATASET)
        assert g.get_path("a", "missing") is None


class TestFlowGraphRootsLeaves:
    """Tests for root and leaf detection."""

    def test_roots(self):
        g = FlowGraph()
        g.add_node("a", NodeType.DATASET)
        g.add_node("r", NodeType.RECIPE)
        g.add_node("b", NodeType.DATASET)
        g.add_edge("a", "r")
        g.add_edge("r", "b")
        roots = g.get_roots()
        assert "a" in roots
        assert "r" not in roots

    def test_leaves(self):
        g = FlowGraph()
        g.add_node("a", NodeType.DATASET)
        g.add_node("r", NodeType.RECIPE)
        g.add_node("b", NodeType.DATASET)
        g.add_edge("a", "r")
        g.add_edge("r", "b")
        leaves = g.get_leaves()
        assert "b" in leaves
        assert "a" not in leaves


class TestFlowGraphFromFlow:
    """Tests for building FlowGraph from DataikuFlow."""

    def test_simple_flow(self):
        flow = DataikuFlow(name="test")
        flow.add_dataset(DataikuDataset(name="input", dataset_type=DatasetType.INPUT))
        flow.add_recipe(DataikuRecipe(
            name="prep", recipe_type=RecipeType.PREPARE,
            inputs=["input"], outputs=["output"],
        ))

        graph = flow.graph
        assert "input" in graph
        assert "recipe:prep" in graph
        assert "output" in graph
        assert graph.get_successors("input") == ["recipe:prep"]
        assert graph.get_successors("recipe:prep") == ["output"]

    def test_join_flow(self):
        flow = DataikuFlow(name="test")
        flow.add_dataset(DataikuDataset(name="left", dataset_type=DatasetType.INPUT))
        flow.add_dataset(DataikuDataset(name="right", dataset_type=DatasetType.INPUT))
        flow.add_recipe(DataikuRecipe(
            name="join", recipe_type=RecipeType.JOIN,
            inputs=["left", "right"], outputs=["joined"],
        ))

        graph = flow.graph
        assert graph.get_predecessors("recipe:join") == ["left", "right"]
        assert graph.get_successors("recipe:join") == ["joined"]

    def test_graph_topological_sort_from_flow(self):
        flow = DataikuFlow(name="test")
        flow.add_dataset(DataikuDataset(name="raw", dataset_type=DatasetType.INPUT))
        flow.add_recipe(DataikuRecipe(
            name="clean", recipe_type=RecipeType.PREPARE,
            inputs=["raw"], outputs=["cleaned"],
        ))
        flow.add_recipe(DataikuRecipe(
            name="group", recipe_type=RecipeType.GROUPING,
            inputs=["cleaned"], outputs=["grouped"],
        ))

        graph = flow.graph
        order = graph.topological_sort()
        assert order.index("raw") < order.index("recipe:clean")
        assert order.index("recipe:clean") < order.index("cleaned")
        assert order.index("cleaned") < order.index("recipe:group")
        assert order.index("recipe:group") < order.index("grouped")


class TestFlowValidationWithDAG:
    """Tests for DataikuFlow.validate() using DAG analysis."""

    def test_valid_flow(self):
        flow = DataikuFlow(name="test")
        flow.add_dataset(DataikuDataset(name="input", dataset_type=DatasetType.INPUT))
        flow.add_recipe(DataikuRecipe(
            name="prep", recipe_type=RecipeType.PREPARE,
            inputs=["input"], outputs=["output"],
        ))
        result = flow.validate()
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_orphan_dataset_warning(self):
        flow = DataikuFlow(name="test")
        flow.add_dataset(DataikuDataset(name="orphan", dataset_type=DatasetType.INPUT))
        # No recipes reference this dataset
        result = flow.validate()
        orphan_warnings = [w for w in result["warnings"] if isinstance(w, dict) and w.get("type") == "ORPHAN_DATASET"]
        assert len(orphan_warnings) == 1

    def test_disconnected_flow_warning(self):
        flow = DataikuFlow(name="test")
        flow.add_dataset(DataikuDataset(name="a", dataset_type=DatasetType.INPUT))
        flow.add_recipe(DataikuRecipe(
            name="r1", recipe_type=RecipeType.PREPARE,
            inputs=["a"], outputs=["b"],
        ))
        flow.add_dataset(DataikuDataset(name="c", dataset_type=DatasetType.INPUT))
        flow.add_recipe(DataikuRecipe(
            name="r2", recipe_type=RecipeType.PREPARE,
            inputs=["c"], outputs=["d"],
        ))
        result = flow.validate()
        disconnect_warnings = [w for w in result["warnings"] if isinstance(w, dict) and w.get("type") == "DISCONNECTED_FLOW"]
        assert len(disconnect_warnings) == 1


class TestFlowNodeEquality:
    """Tests for FlowNode equality and hashing."""

    def test_equal_nodes(self):
        a = FlowNode("ds1", NodeType.DATASET)
        b = FlowNode("ds1", NodeType.DATASET)
        assert a == b

    def test_unequal_nodes_name(self):
        a = FlowNode("ds1", NodeType.DATASET)
        b = FlowNode("ds2", NodeType.DATASET)
        assert a != b

    def test_unequal_nodes_type(self):
        a = FlowNode("x", NodeType.DATASET)
        b = FlowNode("x", NodeType.RECIPE)
        assert a != b

    def test_hash_consistency(self):
        a = FlowNode("ds1", NodeType.DATASET)
        b = FlowNode("ds1", NodeType.DATASET)
        assert hash(a) == hash(b)

    def test_not_equal_to_other_type(self):
        a = FlowNode("ds1", NodeType.DATASET)
        assert a != "ds1"
