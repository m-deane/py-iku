"""
SVG visualizer for Dataiku flows.

Generates scalable vector graphics that match the Dataiku DSS interface.
"""

from typing import Dict, List, Optional
from py2dataiku.visualizers.base import FlowVisualizer
from py2dataiku.visualizers.layout_engine import LayoutEngine, NodePosition, Edge
from py2dataiku.visualizers.themes import DataikuTheme, DATAIKU_LIGHT
from py2dataiku.visualizers.icons import RecipeIcons

# Zone styling colors
ZONE_FILLS = ["#E3F2FD", "#F3E5F5", "#E8F5E9", "#FFF3E0", "#FCE4EC", "#E0F7FA", "#FFF8E1", "#EFEBE9"]
ZONE_BORDERS = ["#90CAF9", "#CE93D8", "#A5D6A7", "#FFCC80", "#F48FB1", "#80DEEA", "#FFD54F", "#BCAAA4"]


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

        # Draw zones behind everything
        svg_parts.append(self._draw_zones(flow, positions))

        # Draw connections (behind nodes)
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
        defs_parts = ['''  <defs>
    <!-- Drop shadow filter -->
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="1" dy="2" stdDeviation="2" flood-opacity="0.15"/>
    </filter>

    <!-- Text shadow filter -->
    <filter id="text-shadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="1" stdDeviation="0.5" flood-opacity="0.3"/>
    </filter>''']

        defs_parts.append(f'''
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
    </symbol>''')

        # Add gradient definitions for each recipe type
        for recipe_type, colors in self.theme.recipe_colors.items():
            bg_color = colors[0]
            defs_parts.append(f'''
    <linearGradient id="grad-{recipe_type}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{bg_color}" stop-opacity="1"/>
      <stop offset="100%" stop-color="{bg_color}" stop-opacity="0.7"/>
    </linearGradient>''')

        defs_parts.append('  </defs>')
        return "\n".join(defs_parts)

    def _draw_zones(self, flow, positions: Dict[str, NodePosition]) -> str:
        """Draw flow zone backgrounds behind all nodes."""
        if not hasattr(flow, 'zones') or not flow.zones:
            return ""

        zone_parts = []
        zone_padding = 20

        for i, zone in enumerate(flow.zones):
            # Collect positions of nodes belonging to this zone
            zone_positions = []

            # Build a lookup from node label to position
            label_to_pos = {}
            for node_id, pos in positions.items():
                label_to_pos[pos.label] = pos
                # Also map by node_id for recipe nodes
                label_to_pos[node_id] = pos

            for ds_name in zone.datasets:
                if ds_name in label_to_pos:
                    zone_positions.append(label_to_pos[ds_name])

            for recipe_name in zone.recipes:
                if recipe_name in label_to_pos:
                    zone_positions.append(label_to_pos[recipe_name])

            if not zone_positions:
                # Draw an empty zone badge at a default position
                fill = ZONE_FILLS[i % len(ZONE_FILLS)]
                border = ZONE_BORDERS[i % len(ZONE_BORDERS)]
                zone_parts.append(f'''  <text x="12" y="{22 + i * 30}" font-family="Arial,Helvetica,sans-serif"
        font-size="11" font-weight="bold" fill="{border}">{zone.name}</text>''')
                continue

            # Compute bounding box
            min_x = min(p.x for p in zone_positions) - zone_padding
            min_y = min(p.y for p in zone_positions) - zone_padding
            max_x = max(p.right for p in zone_positions) + zone_padding
            max_y = max(p.bottom for p in zone_positions) + zone_padding
            w = max_x - min_x
            h = max_y - min_y

            fill = ZONE_FILLS[i % len(ZONE_FILLS)]
            border = ZONE_BORDERS[i % len(ZONE_BORDERS)]

            zone_parts.append(f'''  <rect x="{min_x}" y="{min_y}" width="{w}" height="{h}" rx="12" ry="12"
        fill="{fill}" fill-opacity="0.15" stroke="{border}" stroke-width="1.5"
        stroke-dasharray="6,3"/>
  <text x="{min_x + 12}" y="{min_y + 22}" font-family="Arial,Helvetica,sans-serif"
        font-size="11" font-weight="bold" fill="{border}">{zone.name}</text>''')

        return "\n".join(zone_parts)

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

        # Inner border inset values
        inset = 2

        return f'''  <g class="dataset {ds_type}" transform="translate({pos.x}, {pos.y})">
    <rect width="{pos.width}" height="{pos.height}"
          rx="{self.theme.dataset_radius}" ry="{self.theme.dataset_radius}"
          fill="{bg}" stroke="{border}" stroke-width="1.5"
          filter="url(#shadow)"/>
    <rect x="{inset}" y="{inset}" width="{pos.width - 2 * inset}" height="{pos.height - 2 * inset}"
          rx="{max(self.theme.dataset_radius - 1, 2)}" ry="{max(self.theme.dataset_radius - 1, 2)}"
          fill="none" stroke="{border}" stroke-width="0.5" stroke-opacity="0.2"/>
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

        # Use gradient fill if available, fall back to flat fill
        fill_attr = f'url(#grad-{recipe_type})' if recipe_type in self.theme.recipe_colors else bg

        return f'''  <g class="recipe {recipe_type}" transform="translate({pos.x}, {pos.y})">
    <rect width="{pos.width}" height="{pos.height}"
          rx="{self.theme.recipe_radius}" ry="{self.theme.recipe_radius}"
          fill="{fill_attr}" stroke="{border}" stroke-width="2"
          filter="url(#shadow)"/>
    <text x="{pos.width/2}" y="{pos.height/2 - 8}"
          text-anchor="middle"
          font-family="{self.theme.font_family}"
          font-size="{self.theme.icon_font_size}"
          fill="{text_color}"
          filter="url(#text-shadow)">{icon}</text>
    <text x="{pos.width/2}" y="{pos.height/2 + 10}"
          text-anchor="middle"
          font-family="{self.theme.font_family}"
          font-size="{self.theme.recipe_font_size}"
          font-weight="600"
          fill="{text_color}"
          filter="url(#text-shadow)">{label}</text>
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

        dx = x2 - x1

        # Use bezier S-curve for connections spanning columns, straight for close nodes
        if dx > 60:
            path = f"M {x1} {y1} C {x1 + dx * 0.4} {y1}, {x2 - dx * 0.4} {y2}, {x2} {y2}"
        else:
            path = f"M {x1} {y1} C {x1 + dx / 2} {y1}, {x2 - dx / 2} {y2}, {x2} {y2}"

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
