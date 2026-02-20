"""DAG representation for Dataiku flows."""

from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


class NodeType(Enum):
    """Type of node in the flow graph."""

    DATASET = "dataset"
    RECIPE = "recipe"


@dataclass
class FlowNode:
    """A node in the flow graph (dataset or recipe)."""

    name: str
    node_type: NodeType
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash((self.name, self.node_type))

    def __eq__(self, other):
        if not isinstance(other, FlowNode):
            return NotImplemented
        return self.name == other.name and self.node_type == other.node_type


class FlowGraph:
    """
    Directed Acyclic Graph representation of a Dataiku flow.

    Nodes are datasets and recipes. Edges represent data flow:
    dataset -> recipe (recipe reads from dataset)
    recipe -> dataset (recipe writes to dataset)

    This provides graph-based operations like topological sorting,
    cycle detection, and path finding.
    """

    def __init__(self):
        self._nodes: Dict[str, FlowNode] = {}
        self._successors: Dict[str, List[str]] = defaultdict(list)
        self._predecessors: Dict[str, List[str]] = defaultdict(list)

    def add_node(
        self,
        name: str,
        node_type: NodeType,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FlowNode:
        """Add a node to the graph."""
        node = FlowNode(name=name, node_type=node_type, metadata=metadata or {})
        self._nodes[name] = node
        return node

    def add_edge(self, source: str, target: str) -> None:
        """Add a directed edge from source to target."""
        if source not in self._nodes:
            raise ValueError(f"Source node '{source}' not found in graph")
        if target not in self._nodes:
            raise ValueError(f"Target node '{target}' not found in graph")
        if target not in self._successors[source]:
            self._successors[source].append(target)
        if source not in self._predecessors[target]:
            self._predecessors[target].append(source)

    def get_node(self, name: str) -> Optional[FlowNode]:
        """Get a node by name."""
        return self._nodes.get(name)

    @property
    def nodes(self) -> List[FlowNode]:
        """Get all nodes."""
        return list(self._nodes.values())

    @property
    def dataset_nodes(self) -> List[FlowNode]:
        """Get all dataset nodes."""
        return [n for n in self._nodes.values() if n.node_type == NodeType.DATASET]

    @property
    def recipe_nodes(self) -> List[FlowNode]:
        """Get all recipe nodes."""
        return [n for n in self._nodes.values() if n.node_type == NodeType.RECIPE]

    @property
    def edges(self) -> List[Tuple[str, str]]:
        """Get all edges as (source, target) tuples."""
        result = []
        for source, targets in self._successors.items():
            for target in targets:
                result.append((source, target))
        return result

    def get_successors(self, name: str) -> List[str]:
        """Get direct successor node names."""
        return list(self._successors.get(name, []))

    def get_predecessors(self, name: str) -> List[str]:
        """Get direct predecessor node names."""
        return list(self._predecessors.get(name, []))

    def topological_sort(self) -> List[str]:
        """
        Return nodes in topological order (Kahn's algorithm).

        Raises ValueError if the graph contains a cycle.
        """
        in_degree: Dict[str, int] = {name: 0 for name in self._nodes}
        for targets in self._successors.values():
            for t in targets:
                in_degree[t] += 1

        queue = deque(name for name, deg in in_degree.items() if deg == 0)
        result = []

        while queue:
            node = queue.popleft()
            result.append(node)
            for successor in self._successors.get(node, []):
                in_degree[successor] -= 1
                if in_degree[successor] == 0:
                    queue.append(successor)

        if len(result) != len(self._nodes):
            raise ValueError("Graph contains a cycle")

        return result

    def detect_cycles(self) -> List[List[str]]:
        """
        Detect all cycles in the graph using DFS.

        Returns a list of cycles, where each cycle is a list of node names.
        Returns an empty list if the graph is acyclic.
        """
        WHITE, GRAY, BLACK = 0, 1, 2
        color: Dict[str, int] = {name: WHITE for name in self._nodes}
        path: List[str] = []
        cycles: List[List[str]] = []

        def dfs(node: str) -> None:
            color[node] = GRAY
            path.append(node)

            for successor in self._successors.get(node, []):
                if color[successor] == GRAY:
                    # Found a cycle
                    cycle_start = path.index(successor)
                    cycles.append(path[cycle_start:] + [successor])
                elif color[successor] == WHITE:
                    dfs(successor)

            path.pop()
            color[node] = BLACK

        for name in self._nodes:
            if color[name] == WHITE:
                dfs(name)

        return cycles

    def find_disconnected_subgraphs(self) -> List[Set[str]]:
        """
        Find disconnected subgraphs (connected components) in the undirected sense.

        Returns a list of sets, where each set contains node names in a component.
        """
        visited: Set[str] = set()
        components: List[Set[str]] = []

        def bfs(start: str) -> Set[str]:
            component: Set[str] = set()
            queue = deque([start])
            while queue:
                node = queue.popleft()
                if node in component:
                    continue
                component.add(node)
                # Traverse both directions (undirected connectivity)
                for successor in self._successors.get(node, []):
                    if successor not in component:
                        queue.append(successor)
                for predecessor in self._predecessors.get(node, []):
                    if predecessor not in component:
                        queue.append(predecessor)
            return component

        for name in self._nodes:
            if name not in visited:
                component = bfs(name)
                visited.update(component)
                components.append(component)

        return components

    def get_path(self, source: str, target: str) -> Optional[List[str]]:
        """
        Find a path from source to target using BFS.

        Returns the shortest path as a list of node names, or None if no path exists.
        """
        if source not in self._nodes or target not in self._nodes:
            return None

        if source == target:
            return [source]

        visited: Set[str] = set()
        queue: deque[Tuple[str, List[str]]] = deque([(source, [source])])

        while queue:
            current, path = queue.popleft()
            if current == target:
                return path

            if current in visited:
                continue
            visited.add(current)

            for successor in self._successors.get(current, []):
                if successor not in visited:
                    queue.append((successor, path + [successor]))

        return None

    def get_roots(self) -> List[str]:
        """Get nodes with no predecessors (source nodes)."""
        return [
            name for name in self._nodes
            if not self._predecessors.get(name)
        ]

    def get_leaves(self) -> List[str]:
        """Get nodes with no successors (sink nodes)."""
        return [
            name for name in self._nodes
            if not self._successors.get(name)
        ]

    @classmethod
    def from_flow(cls, flow) -> "FlowGraph":
        """
        Build a FlowGraph from a DataikuFlow's datasets and recipes.

        Args:
            flow: A DataikuFlow instance

        Returns:
            A FlowGraph representing the flow's structure
        """
        graph = cls()

        # Add dataset nodes
        for ds in flow.datasets:
            graph.add_node(
                ds.name,
                NodeType.DATASET,
                metadata={"dataset_type": ds.dataset_type.value},
            )

        # Add recipe nodes and edges
        for recipe in flow.recipes:
            recipe_node_name = f"recipe:{recipe.name}"
            graph.add_node(
                recipe_node_name,
                NodeType.RECIPE,
                metadata={"recipe_type": recipe.recipe_type.value},
            )

            # dataset -> recipe edges (inputs)
            for inp in recipe.inputs:
                if inp not in graph._nodes:
                    graph.add_node(inp, NodeType.DATASET)
                graph.add_edge(inp, recipe_node_name)

            # recipe -> dataset edges (outputs)
            for out in recipe.outputs:
                if out not in graph._nodes:
                    graph.add_node(out, NodeType.DATASET)
                graph.add_edge(recipe_node_name, out)

        return graph

    def __len__(self) -> int:
        return len(self._nodes)

    def __contains__(self, name: str) -> bool:
        return name in self._nodes

    def __repr__(self) -> str:
        return (
            f"FlowGraph(nodes={len(self._nodes)}, edges={len(self.edges)})"
        )
