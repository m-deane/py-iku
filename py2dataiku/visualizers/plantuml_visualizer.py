"""
PlantUML visualizer for Dataiku flows.

Generates PlantUML code that can be rendered by PlantUML servers.
"""

from typing import Optional

from py2dataiku.visualizers.base import FlowVisualizer
from py2dataiku.visualizers.icons import RecipeIcons
from py2dataiku.visualizers.layout_engine import LayoutEngine, NodePosition
from py2dataiku.visualizers.themes import DataikuTheme


class PlantUMLVisualizer(FlowVisualizer):
    """Generate PlantUML visualization of Dataiku flows."""

    def __init__(self, theme: Optional[DataikuTheme] = None):
        super().__init__(theme)

    def render(self, flow) -> str:
        """Render flow as PlantUML code."""
        lines = ["@startuml"]

        # Theme and styling
        lines.extend(self._generate_style())

        # Get layout
        layout = LayoutEngine()
        positions = layout.calculate_layout(flow)
        edges = layout.get_edges()

        # Declare nodes
        lines.append("")
        lines.append("' Datasets")
        for node_id, pos in positions.items():
            if pos.node_type == "dataset":
                lines.append(self._declare_dataset(node_id, pos))

        lines.append("")
        lines.append("' Recipes")
        for node_id, pos in positions.items():
            if pos.node_type == "recipe":
                lines.append(self._declare_recipe(node_id, pos))

        # Declare edges
        lines.append("")
        lines.append("' Connections")
        for edge in edges:
            if edge.source in positions and edge.target in positions:
                lines.append(f"{self._sanitize_id(edge.source)} --> {self._sanitize_id(edge.target)}")

        lines.append("")
        lines.append("@enduml")

        return "\n".join(lines)

    def _generate_style(self) -> list[str]:
        """Generate PlantUML styling directives.

        Emits per-recipe-type ``BackgroundColor<<recipe_type>>`` /
        ``BorderColor<<recipe_type>>`` skinparam declarations using the
        DSS-fidelity recipe palette (`theme.get_recipe_palette`). Every key
        in ``recipe_palette`` produces a stereotype.
        """
        out: list[str] = [
            "!theme plain",
            f"skinparam backgroundColor {self.theme.background_color}",
            "skinparam defaultFontName Arial",
            "skinparam defaultFontSize 12",
            "",
            "' Dataset styles",
            "skinparam rectangle {",
            f"  BackgroundColor<<input>> {self.theme.input_bg}",
            f"  BorderColor<<input>> {self.theme.input_border}",
            f"  FontColor<<input>> {self.theme.input_text}",
            f"  BackgroundColor<<output>> {self.theme.output_bg}",
            f"  BorderColor<<output>> {self.theme.output_border}",
            f"  FontColor<<output>> {self.theme.output_text}",
            f"  BackgroundColor<<intermediate>> {self.theme.intermediate_bg}",
            f"  BorderColor<<intermediate>> {self.theme.intermediate_border}",
            f"  FontColor<<intermediate>> {self.theme.intermediate_text}",
            "}",
            "",
            "' Recipe styles (per-type, DSS-palette)",
            "skinparam card {",
        ]
        # Emit per-recipe-type colors using the high-fidelity palette.
        for recipe_type in self.theme.recipe_palette:
            fill, stroke, font = self.theme.get_recipe_palette(recipe_type)
            out.append(f"  BackgroundColor<<{recipe_type}>> {fill}")
            out.append(f"  BorderColor<<{recipe_type}>> {stroke}")
            out.append(f"  FontColor<<{recipe_type}>> {font}")
        out.extend([
            "}",
            "",
            "' Arrow style",
            "skinparam arrow {",
            f"  Color {self.theme.connection_color}",
            f"  Thickness {self.theme.connection_width}",
            "}",
        ])
        return out

    def _declare_dataset(self, node_id: str, pos: NodePosition) -> str:
        """Declare a dataset node."""
        extra = pos.extra
        ds_type = extra.get("dataset_type", "intermediate")
        safe_id = self._sanitize_id(node_id)

        return f'rectangle "{pos.label}" <<{ds_type}>> as {safe_id}'

    def _declare_recipe(self, node_id: str, pos: NodePosition) -> str:
        """Declare a recipe node."""
        extra = pos.extra
        recipe_type = extra.get("recipe_type", "default")
        safe_id = self._sanitize_id(node_id)

        icon = RecipeIcons.get_unicode(recipe_type)
        label = RecipeIcons.get_label(recipe_type)

        return f'card "{icon} {label}" <<{recipe_type}>> as {safe_id}'

    def _sanitize_id(self, node_id: str) -> str:
        """Sanitize node ID for PlantUML."""
        # Replace invalid characters
        safe = node_id.replace("-", "_").replace(".", "_").replace(" ", "_")
        # Ensure it starts with a letter
        if safe and safe[0].isdigit():
            safe = "n_" + safe
        return safe

    def get_render_url(self, flow, server: str = "http://www.plantuml.com/plantuml") -> str:
        """
        Get URL to render the PlantUML diagram.

        Args:
            flow: DataikuFlow to visualize
            server: PlantUML server URL

        Returns:
            URL that renders the diagram as PNG
        """
        import base64
        import zlib

        content = self.render(flow)

        # PlantUML encoding
        compressed = zlib.compress(content.encode('utf-8'))[2:-4]
        encoded = base64.b64encode(compressed).decode('ascii')

        # PlantUML uses a custom base64 alphabet
        plantuml_alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
        base64_alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

        translated = encoded.translate(str.maketrans(base64_alphabet, plantuml_alphabet))

        return f"{server}/png/{translated}"
