"""
ASCII art visualizer for Dataiku flows.

Generates terminal-friendly text representations of flows.
"""

from typing import Optional, List, Dict
from py2dataiku.visualizers.base import FlowVisualizer
from py2dataiku.visualizers.layout_engine import LayoutEngine, NodePosition
from py2dataiku.visualizers.themes import DataikuTheme, DATAIKU_LIGHT
from py2dataiku.visualizers.icons import RecipeIcons


class ASCIIVisualizer(FlowVisualizer):
    """Generate ASCII art visualization of Dataiku flows."""

    # Box drawing characters
    H_LINE = "\u2500"       # ─
    V_LINE = "\u2502"       # │
    TL_CORNER = "\u250c"    # ┌
    TR_CORNER = "\u2510"    # ┐
    BL_CORNER = "\u2514"    # └
    BR_CORNER = "\u2518"    # ┘
    T_DOWN = "\u252c"       # ┬
    T_UP = "\u2534"         # ┴
    T_RIGHT = "\u251c"      # ├
    T_LEFT = "\u2524"       # ┤
    CROSS = "\u253c"        # ┼
    ARROW_DOWN = "\u25bc"   # ▼
    ARROW_RIGHT = "\u25b6"  # ▶
    D_H_LINE = "\u2550"     # ═
    DATASET_ICON = "\U0001F4CA"  # 📊

    def __init__(
        self,
        theme: Optional[DataikuTheme] = None,
        width: int = 80,
        show_details: bool = True,
    ):
        super().__init__(theme)
        self.width = width
        self.show_details = show_details

    def render(self, flow) -> str:
        """Render flow as ASCII art."""
        lines = []

        # Header
        flow_name = getattr(flow, 'name', 'Dataiku Flow')
        lines.append(self._header(flow_name))
        lines.append("")

        # Get flow structure
        layout = LayoutEngine()
        positions = layout.calculate_layout(flow)
        edges = layout.get_edges()

        # Group by layers
        layers: Dict[int, List[NodePosition]] = {}
        for pos in positions.values():
            if pos.layer not in layers:
                layers[pos.layer] = []
            layers[pos.layer].append(pos)

        # Sort layers
        sorted_layers = sorted(layers.keys())

        # Render each layer
        prev_layer_nodes = []
        for layer_idx in sorted_layers:
            layer_nodes = layers[layer_idx]

            # Draw connections from previous layer
            if prev_layer_nodes:
                lines.extend(self._draw_connections(prev_layer_nodes, layer_nodes, edges))

            # Draw nodes in this layer
            for pos in layer_nodes:
                lines.extend(self._draw_node(pos))
                lines.append("")

            prev_layer_nodes = layer_nodes

        # Footer
        lines.append(self._footer())
        lines.append("")
        lines.append(self._legend())

        return "\n".join(lines)

    def _header(self, title: str) -> str:
        """Generate header line."""
        title_line = f"  DATAIKU FLOW: {title}  "
        padding = (self.width - len(title_line)) // 2
        return (
            self.D_H_LINE * self.width + "\n" +
            " " * padding + title_line + "\n" +
            self.D_H_LINE * self.width
        )

    def _footer(self) -> str:
        """Generate footer line."""
        return self.D_H_LINE * self.width

    def _legend(self) -> str:
        """Generate legend."""
        icons = [
            f"{self.DATASET_ICON} Dataset",
            f"{RecipeIcons.get_unicode('prepare')} Prepare",
            f"{RecipeIcons.get_unicode('join')} Join",
            f"{RecipeIcons.get_unicode('grouping')} Grouping",
            f"{RecipeIcons.get_unicode('split')} Split",
            f"{RecipeIcons.get_unicode('sort')} Sort",
        ]
        return "Legend: " + "  ".join(icons)

    def _draw_node(self, pos: NodePosition) -> List[str]:
        """Draw a single node."""
        lines = []

        if pos.node_type == "dataset":
            lines.extend(self._draw_dataset_box(pos))
        else:
            lines.extend(self._draw_recipe_box(pos))

        return lines

    def _draw_dataset_box(self, pos: NodePosition) -> List[str]:
        """Draw a dataset box."""
        extra = pos.extra
        ds_type = extra.get("dataset_type", "intermediate")
        label = pos.label

        # Determine width
        box_width = max(len(label) + 6, 20)

        # Build box
        lines = []
        lines.append(self._center(self.TL_CORNER + self.H_LINE * (box_width - 2) + self.TR_CORNER))
        lines.append(self._center(f"{self.V_LINE} {self.DATASET_ICON} {label:<{box_width - 6}} {self.V_LINE}"))

        if ds_type != "intermediate":
            type_label = f"[{ds_type.upper()}]"
            lines.append(self._center(f"{self.V_LINE}    {type_label:<{box_width - 6}} {self.V_LINE}"))

        lines.append(self._center(self.BL_CORNER + self.H_LINE * (box_width - 2) + self.BR_CORNER))

        return lines

    def _draw_recipe_box(self, pos: NodePosition) -> List[str]:
        """Draw a recipe box."""
        extra = pos.extra
        recipe_type = extra.get("recipe_type", "default")
        details = extra.get("details", "")

        icon = RecipeIcons.get_unicode(recipe_type)
        label = RecipeIcons.get_label(recipe_type).upper()

        # Determine width
        box_width = max(len(label) + 6, len(details) + 4, 16)

        # Build box
        lines = []
        lines.append(self._center(self.TL_CORNER + self.H_LINE * (box_width - 2) + self.TR_CORNER))
        lines.append(self._center(f"{self.V_LINE}   {icon} {label:<{box_width - 7}} {self.V_LINE}"))
        lines.append(self._center(f"{self.V_LINE} {self.H_LINE * (box_width - 4)} {self.V_LINE}"))

        if self.show_details and details:
            lines.append(self._center(f"{self.V_LINE} {details:<{box_width - 4}} {self.V_LINE}"))

        lines.append(self._center(self.BL_CORNER + self.H_LINE * (box_width - 2) + self.BR_CORNER))

        return lines

    def _draw_connections(
        self,
        prev_nodes: List[NodePosition],
        curr_nodes: List[NodePosition],
        edges: List
    ) -> List[str]:
        """Draw connection arrows between layers."""
        lines = []

        # Simple vertical arrow for now
        lines.append(self._center(self.V_LINE))
        lines.append(self._center(self.ARROW_DOWN))
        lines.append("")

        return lines

    def _center(self, text: str) -> str:
        """Center text within the width."""
        padding = (self.width - len(text)) // 2
        return " " * max(0, padding) + text

    def render_compact(self, flow) -> str:
        """Render a compact single-line representation."""
        layout = LayoutEngine()
        positions = layout.calculate_layout(flow)

        # Group by layers
        layers: Dict[int, List[NodePosition]] = {}
        for pos in positions.values():
            if pos.layer not in layers:
                layers[pos.layer] = []
            layers[pos.layer].append(pos)

        # Build compact representation
        parts = []
        for layer_idx in sorted(layers.keys()):
            layer_nodes = layers[layer_idx]
            layer_parts = []
            for pos in layer_nodes:
                if pos.node_type == "dataset":
                    layer_parts.append(f"[{pos.label}]")
                else:
                    recipe_type = pos.extra.get("recipe_type", "default")
                    icon = RecipeIcons.get_unicode(recipe_type)
                    layer_parts.append(f"({icon})")
            parts.append(" + ".join(layer_parts) if len(layer_parts) > 1 else layer_parts[0])

        return " --> ".join(parts)
