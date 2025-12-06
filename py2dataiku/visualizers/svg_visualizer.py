"""
SVG visualizer for Dataiku flows.

Generates scalable vector graphics that match the Dataiku DSS interface.
"""

from typing import Optional, List
from py2dataiku.visualizers.base import FlowVisualizer
from py2dataiku.visualizers.layout_engine import LayoutEngine, NodePosition, Edge
from py2dataiku.visualizers.themes import DataikuTheme, DATAIKU_LIGHT
from py2dataiku.visualizers.icons import RecipeIcons


class SVGVisualizer(FlowVisualizer):
    """Generate SVG visualization of Dataiku flows."""

    def __init__(self, theme: Optional[DataikuTheme] = None):
        super().__init__(theme)
        self.layout_engine = LayoutEngine(
            layer_spacing=self.theme.layer_spacing,
            node_spacing=self.theme.node_spacing,
            dataset_width=self.theme.dataset_width,
            dataset_height=self.theme.dataset_height,
            recipe_size=self.theme.recipe_size,
            padding=self.theme.padding,
        )

    def render(self, flow) -> str:
        """Render flow as SVG."""
        # Calculate layout
        positions = self.layout_engine.calculate_layout(flow)
        edges = self.layout_engine.get_edges()
        width, height = self.layout_engine.get_canvas_size()

        # Build SVG
        svg_parts = [self._svg_header(width, height)]
        svg_parts.append(self._svg_defs())

        # Draw connections first (behind nodes)
        for edge in edges:
            if edge.source in positions and edge.target in positions:
                svg_parts.append(self._draw_connection(
                    positions[edge.source],
                    positions[edge.target]
                ))

        # Draw nodes
        for node_id, pos in positions.items():
            if pos.node_type == "dataset":
                svg_parts.append(self._draw_dataset(pos))
            else:
                svg_parts.append(self._draw_recipe(pos))

        svg_parts.append("</svg>")
        return "\n".join(svg_parts)

    def _svg_header(self, width: int, height: int) -> str:
        """Generate SVG header."""
        return f'''<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 {width} {height}"
     width="{width}" height="{height}"
     style="background-color: {self.theme.background_color}">'''

    def _svg_defs(self) -> str:
        """Generate SVG definitions (filters, markers, gradients)."""
        return f'''  <defs>
    <!-- Drop shadow filter -->
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="1" dy="2" stdDeviation="2" flood-opacity="0.15"/>
    </filter>

    <!-- Arrow marker -->
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5"
            markerWidth="{self.theme.arrow_size}" markerHeight="{self.theme.arrow_size}"
            orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="{self.theme.connection_color}"/>
    </marker>

    <!-- Dataset icon -->
    <symbol id="dataset-icon" viewBox="0 0 24 24">
      <ellipse cx="12" cy="6" rx="8" ry="3" fill="currentColor" opacity="0.3"/>
      <path d="M4 6v12c0 1.66 3.58 3 8 3s8-1.34 8-3V6"
            fill="none" stroke="currentColor" stroke-width="1.5"/>
      <ellipse cx="12" cy="6" rx="8" ry="3" fill="none" stroke="currentColor" stroke-width="1.5"/>
    </symbol>
  </defs>'''

    def _draw_dataset(self, pos: NodePosition) -> str:
        """Draw a dataset node."""
        extra = pos.extra
        ds_type = extra.get("dataset_type", "intermediate")

        if ds_type == "input":
            bg = self.theme.input_bg
            border = self.theme.input_border
            text_color = self.theme.input_text
        elif ds_type == "output":
            bg = self.theme.output_bg
            border = self.theme.output_border
            text_color = self.theme.output_text
        else:
            bg = self.theme.intermediate_bg
            border = self.theme.intermediate_border
            text_color = self.theme.intermediate_text

        # Truncate long labels
        label = pos.label
        if len(label) > 18:
            label = label[:16] + "..."

        type_label = f"[{ds_type.upper()}]" if ds_type != "intermediate" else ""

        return f'''  <g class="dataset {ds_type}" transform="translate({pos.x}, {pos.y})">
    <rect width="{pos.width}" height="{pos.height}"
          rx="{self.theme.dataset_radius}" ry="{self.theme.dataset_radius}"
          fill="{bg}" stroke="{border}" stroke-width="1.5"
          filter="url(#shadow)"/>
    <use href="#dataset-icon" x="8" y="{pos.height/2 - 10}" width="20" height="20"
         style="color: {border}"/>
    <text x="32" y="{pos.height/2 - 2}"
          font-family="{self.theme.font_family}"
          font-size="{self.theme.dataset_font_size}"
          font-weight="500"
          fill="{text_color}">{label}</text>
    <text x="32" y="{pos.height/2 + 12}"
          font-family="{self.theme.font_family}"
          font-size="{self.theme.dataset_font_size - 3}"
          fill="{text_color}" opacity="0.7">{type_label}</text>
  </g>'''

    def _draw_recipe(self, pos: NodePosition) -> str:
        """Draw a recipe node."""
        extra = pos.extra
        recipe_type = extra.get("recipe_type", "default")
        details = extra.get("details", "")

        bg, border, text_color = self.theme.get_recipe_colors(recipe_type)
        icon = RecipeIcons.get_unicode(recipe_type)
        label = RecipeIcons.get_label(recipe_type)

        return f'''  <g class="recipe {recipe_type}" transform="translate({pos.x}, {pos.y})">
    <rect width="{pos.width}" height="{pos.height}"
          rx="{self.theme.recipe_radius}" ry="{self.theme.recipe_radius}"
          fill="{bg}" stroke="{border}" stroke-width="2"
          filter="url(#shadow)"/>
    <text x="{pos.width/2}" y="{pos.height/2 - 8}"
          text-anchor="middle"
          font-family="{self.theme.font_family}"
          font-size="{self.theme.icon_font_size}"
          fill="{text_color}">{icon}</text>
    <text x="{pos.width/2}" y="{pos.height/2 + 10}"
          text-anchor="middle"
          font-family="{self.theme.font_family}"
          font-size="{self.theme.recipe_font_size}"
          font-weight="500"
          fill="{text_color}">{label}</text>
    <text x="{pos.width/2}" y="{pos.height/2 + 22}"
          text-anchor="middle"
          font-family="{self.theme.font_family}"
          font-size="{self.theme.recipe_font_size - 2}"
          fill="{text_color}" opacity="0.7">{details}</text>
  </g>'''

    def _draw_connection(self, source: NodePosition, target: NodePosition) -> str:
        """Draw a connection line between two nodes."""
        # Calculate connection points
        x1 = source.right
        y1 = source.center_y
        x2 = target.x
        y2 = target.center_y

        # Create bezier curve for smooth connection
        control_offset = (x2 - x1) / 2
        path = f"M {x1} {y1} C {x1 + control_offset} {y1}, {x2 - control_offset} {y2}, {x2} {y2}"

        return f'''  <path d="{path}"
        fill="none"
        stroke="{self.theme.connection_color}"
        stroke-width="{self.theme.connection_width}"
        marker-end="url(#arrow)"/>'''

    def export_png(self, flow, output_path: str, scale: float = 2.0) -> None:
        """Export flow as PNG (requires cairosvg)."""
        try:
            import cairosvg
            svg_content = self.render(flow)
            cairosvg.svg2png(
                bytestring=svg_content.encode('utf-8'),
                write_to=output_path,
                scale=scale
            )
        except ImportError:
            raise ImportError("cairosvg is required for PNG export. Install with: pip install cairosvg")

    def export_pdf(self, flow, output_path: str) -> None:
        """Export flow as PDF (requires cairosvg)."""
        try:
            import cairosvg
            svg_content = self.render(flow)
            cairosvg.svg2pdf(
                bytestring=svg_content.encode('utf-8'),
                write_to=output_path
            )
        except ImportError:
            raise ImportError("cairosvg is required for PDF export. Install with: pip install cairosvg")
