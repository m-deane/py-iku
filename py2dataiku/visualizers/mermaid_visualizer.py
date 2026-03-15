"""Mermaid diagram visualizer for Dataiku flows."""

from collections import defaultdict
from typing import Optional

from py2dataiku.visualizers.base import FlowVisualizer
from py2dataiku.visualizers.themes import DataikuTheme


class MermaidVisualizer(FlowVisualizer):
    """Generate Mermaid diagram syntax for Dataiku flows.

    Supports FlowZone-based subgraph grouping when zones are present.
    Falls back to the DiagramGenerator for basic rendering when no
    zone-aware output is needed.
    """

    def __init__(self, theme: Optional[DataikuTheme] = None):
        super().__init__(theme=theme)

    def render(self, flow) -> str:
        """Render the flow as a Mermaid diagram with zone subgraphs."""
        lines = ["graph LR"]

        # Build zone membership lookup
        zone_datasets = {}  # dataset_name -> zone_name
        zone_recipes = {}   # recipe_name -> zone_name
        has_zones = hasattr(flow, 'zones') and flow.zones

        if has_zones:
            for zone in flow.zones:
                for d in zone.datasets:
                    zone_datasets[d] = zone.name
                for r in zone.recipes:
                    zone_recipes[r] = zone.name

        # Collect nodes into zone groups
        zone_nodes = defaultdict(list)  # zone_name -> list of mermaid node strings

        for dataset in flow.datasets:
            node_str = self._dataset_node(dataset)
            zone = zone_datasets.get(dataset.name, "__unzoned__")
            zone_nodes[zone].append(node_str)

        for recipe in flow.recipes:
            node_str = self._recipe_node(recipe)
            zone = zone_recipes.get(recipe.name, "__unzoned__")
            zone_nodes[zone].append(node_str)

        # Emit subgraphs for named zones
        if has_zones:
            for zone in flow.zones:
                safe_id = zone.name.replace(" ", "_")
                lines.append(f"  subgraph {safe_id}[{zone.name}]")
                for node in zone_nodes.get(zone.name, []):
                    lines.append(f"    {node}")
                lines.append("  end")

        # Emit unzoned nodes at top level
        for node in zone_nodes.get("__unzoned__", []):
            lines.append(f"  {node}")

        # Emit edges
        for recipe in flow.recipes:
            recipe_id = self._safe_id(recipe.name)
            for inp in recipe.inputs:
                inp_ref = inp.get("ref", inp) if isinstance(inp, dict) else inp
                lines.append(f"  {self._safe_id(inp_ref)} --> {recipe_id}")
            for out in recipe.outputs:
                out_ref = out.get("ref", out) if isinstance(out, dict) else out
                lines.append(f"  {recipe_id} --> {self._safe_id(out_ref)}")

        return "\n".join(lines)

    def _safe_id(self, name: str) -> str:
        """Sanitize a name for use as a Mermaid node ID."""
        return name.replace(" ", "_").replace("-", "_")

    def _dataset_node(self, dataset) -> str:
        """Generate Mermaid node declaration for a dataset."""
        safe = self._safe_id(dataset.name)
        return f'{safe}["{dataset.name}"]'

    def _recipe_node(self, recipe) -> str:
        """Generate Mermaid node declaration for a recipe."""
        safe = self._safe_id(recipe.name)
        recipe_type = recipe.recipe_type.value if hasattr(recipe.recipe_type, 'value') else str(recipe.recipe_type)
        return f'{safe}{{"{recipe.name}\\n{recipe_type}"}}'
