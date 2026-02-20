"""
Layout engine for Dataiku flow visualization.

Implements a simplified Sugiyama algorithm for hierarchical graph layout:
1. Assign nodes to layers (topological ordering)
2. Minimize edge crossings
3. Assign x, y coordinates
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict


@dataclass
class NodePosition:
    """Position and dimensions of a node."""
    x: float
    y: float
    width: float
    height: float
    layer: int
    node_type: str  # "dataset" or "recipe"
    node_id: str
    label: str
    extra: Dict = field(default_factory=dict)

    @property
    def center_x(self) -> float:
        return self.x + self.width / 2

    @property
    def center_y(self) -> float:
        return self.y + self.height / 2

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height


@dataclass
class Edge:
    """Edge between two nodes."""
    source: str
    target: str
    label: Optional[str] = None


class LayoutEngine:
    """
    Calculates node positions for a Dataiku flow using hierarchical layout.

    Uses a simplified Sugiyama algorithm:
    1. Topological sort to assign layers
    2. Barycenter heuristic to minimize crossings
    3. Coordinate assignment with proper spacing
    """

    def __init__(
        self,
        layer_spacing: int = 180,
        node_spacing: int = 100,
        dataset_width: int = 160,
        dataset_height: int = 50,
        recipe_size: int = 70,
        padding: int = 40,
    ):
        self.layer_spacing = layer_spacing
        self.node_spacing = node_spacing
        self.dataset_width = dataset_width
        self.dataset_height = dataset_height
        self.recipe_size = recipe_size
        self.padding = padding

        # Internal state
        self.nodes: Dict[str, dict] = {}
        self.edges: List[Edge] = []
        self.layers: List[List[str]] = []
        self.positions: Dict[str, NodePosition] = {}

    def calculate_layout(self, flow) -> Dict[str, NodePosition]:
        """
        Calculate positions for all nodes in the flow.

        Args:
            flow: DataikuFlow object

        Returns:
            Dictionary mapping node IDs to NodePosition objects
        """
        self._extract_graph(flow)
        self._assign_layers()
        self._minimize_crossings()
        self._assign_coordinates()
        return self.positions

    def get_edges(self) -> List[Edge]:
        """Get all edges after layout calculation."""
        return self.edges

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get bounding box (min_x, min_y, max_x, max_y)."""
        if not self.positions:
            return (0, 0, 100, 100)

        min_x = min(p.x for p in self.positions.values())
        min_y = min(p.y for p in self.positions.values())
        max_x = max(p.right for p in self.positions.values())
        max_y = max(p.bottom for p in self.positions.values())

        return (min_x, min_y, max_x, max_y)

    def get_canvas_size(self) -> Tuple[int, int]:
        """Get required canvas size with padding."""
        min_x, min_y, max_x, max_y = self.get_bounds()
        width = int(max_x - min_x + 2 * self.padding)
        height = int(max_y - min_y + 2 * self.padding)
        return (max(width, 400), max(height, 200))

    def _extract_graph(self, flow):
        """Extract nodes and edges from the flow."""
        self.nodes = {}
        self.edges = []

        # Add datasets as nodes
        for ds in flow.datasets:
            ds_type = "input"
            if hasattr(ds, 'is_output') and ds.is_output:
                ds_type = "output"
            elif hasattr(ds, 'is_input') and ds.is_input:
                ds_type = "input"
            else:
                ds_type = "intermediate"

            self.nodes[ds.name] = {
                "type": "dataset",
                "label": ds.name,
                "dataset_type": ds_type,
            }

        # Add recipes as nodes and extract edges
        for i, recipe in enumerate(flow.recipes):
            recipe_id = f"recipe_{i}"
            recipe_type = recipe.recipe_type.value if hasattr(recipe.recipe_type, 'value') else str(recipe.recipe_type)

            self.nodes[recipe_id] = {
                "type": "recipe",
                "label": recipe.name,
                "recipe_type": recipe_type,
                "details": self._get_recipe_details(recipe),
            }

            # Connect inputs to recipe
            for inp in recipe.inputs:
                ref = inp.get("ref", inp) if isinstance(inp, dict) else inp
                if ref in self.nodes:
                    self.edges.append(Edge(source=ref, target=recipe_id))

            # Connect recipe to outputs
            for out in recipe.outputs:
                ref = out.get("ref", out) if isinstance(out, dict) else out
                if ref in self.nodes:
                    self.edges.append(Edge(source=recipe_id, target=ref))

    def _get_recipe_details(self, recipe) -> str:
        """Get details string for a recipe."""
        recipe_type = recipe.recipe_type.value if hasattr(recipe.recipe_type, 'value') else str(recipe.recipe_type)

        if recipe_type == "prepare":
            steps = getattr(recipe, 'steps', [])
            return f"{len(steps)} steps"
        elif recipe_type == "join":
            join_type = getattr(recipe, 'join_type', None)
            if join_type and hasattr(join_type, 'value'):
                return join_type.value
            return "INNER"
        elif recipe_type == "grouping":
            aggs = getattr(recipe, 'aggregations', [])
            return f"{len(aggs)} aggs"
        elif recipe_type == "split":
            return "filter"

        return ""

    def _assign_layers(self):
        """Assign nodes to layers using topological sort."""
        # Build adjacency lists
        outgoing: Dict[str, List[str]] = defaultdict(list)
        incoming: Dict[str, List[str]] = defaultdict(list)

        for edge in self.edges:
            outgoing[edge.source].append(edge.target)
            incoming[edge.target].append(edge.source)

        # Find nodes with no incoming edges (sources)
        in_degree = {node: len(incoming[node]) for node in self.nodes}
        sources = [node for node, deg in in_degree.items() if deg == 0]

        # Assign layers using BFS
        layer_assignment: Dict[str, int] = {}
        current_layer = 0
        current_nodes = sources

        while current_nodes:
            for node in current_nodes:
                layer_assignment[node] = current_layer

            # Find next layer nodes
            next_nodes = set()
            for node in current_nodes:
                for target in outgoing[node]:
                    in_degree[target] -= 1
                    if in_degree[target] == 0:
                        next_nodes.add(target)

            current_nodes = list(next_nodes)
            current_layer += 1

        # Handle any remaining nodes (cycles or disconnected)
        for node in self.nodes:
            if node not in layer_assignment:
                layer_assignment[node] = current_layer

        # Group nodes by layer
        max_layer = max(layer_assignment.values()) if layer_assignment else 0
        self.layers = [[] for _ in range(max_layer + 1)]
        for node, layer in layer_assignment.items():
            self.layers[layer].append(node)

    def _minimize_crossings(self):
        """Minimize edge crossings using barycenter heuristic."""
        # Build adjacency for barycenter calculation
        outgoing: Dict[str, List[str]] = defaultdict(list)
        incoming: Dict[str, List[str]] = defaultdict(list)

        for edge in self.edges:
            outgoing[edge.source].append(edge.target)
            incoming[edge.target].append(edge.source)

        # Iterate to minimize crossings
        for _ in range(4):  # Few iterations usually enough
            # Forward pass
            for i in range(1, len(self.layers)):
                self._order_layer_by_barycenter(i, incoming, forward=True)

            # Backward pass
            for i in range(len(self.layers) - 2, -1, -1):
                self._order_layer_by_barycenter(i, outgoing, forward=False)

    def _order_layer_by_barycenter(
        self, layer_idx: int, adjacency: Dict[str, List[str]], forward: bool
    ):
        """Order nodes in a layer by barycenter of connected nodes."""
        if layer_idx < 0 or layer_idx >= len(self.layers):
            return

        ref_layer_idx = layer_idx - 1 if forward else layer_idx + 1
        if ref_layer_idx < 0 or ref_layer_idx >= len(self.layers):
            return

        ref_layer = self.layers[ref_layer_idx]
        ref_positions = {node: i for i, node in enumerate(ref_layer)}

        def barycenter(node: str) -> float:
            connected = adjacency.get(node, [])
            positions = [ref_positions[n] for n in connected if n in ref_positions]
            if not positions:
                return float('inf')
            return sum(positions) / len(positions)

        self.layers[layer_idx].sort(key=barycenter)

    def _assign_coordinates(self):
        """Assign x, y coordinates to all nodes."""
        self.positions = {}

        for layer_idx, layer_nodes in enumerate(self.layers):
            x = self.padding + layer_idx * self.layer_spacing

            # Calculate total height of this layer
            layer_height = 0
            for node_id in layer_nodes:
                node = self.nodes[node_id]
                if node["type"] == "dataset":
                    layer_height += self.dataset_height
                else:
                    layer_height += self.recipe_size
                layer_height += self.node_spacing

            layer_height -= self.node_spacing  # Remove last spacing

            # Start y position (centered)
            y = self.padding

            for node_id in layer_nodes:
                node = self.nodes[node_id]

                if node["type"] == "dataset":
                    width = self.dataset_width
                    height = self.dataset_height
                    node_type = "dataset"
                else:
                    width = self.recipe_size
                    height = self.recipe_size
                    node_type = "recipe"

                self.positions[node_id] = NodePosition(
                    x=x,
                    y=y,
                    width=width,
                    height=height,
                    layer=layer_idx,
                    node_type=node_type,
                    node_id=node_id,
                    label=node["label"],
                    extra=node,
                )

                y += height + self.node_spacing
