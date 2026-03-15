"""
Matplotlib-based PNG visualizer for Dataiku flows.

Produces publication-quality PNG diagrams following the DDODS visual design language.
Requires matplotlib (optional dependency).
"""

import io
from typing import Optional

from py2dataiku.visualizers.base import FlowVisualizer
from py2dataiku.visualizers.layout_engine import LayoutEngine
from py2dataiku.visualizers.themes import DataikuTheme, DATAIKU_LIGHT

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class MatplotlibVisualizer(FlowVisualizer):
    """Generate PNG visualization of Dataiku flows using matplotlib."""

    def __init__(self, theme: Optional[DataikuTheme] = None, dpi: int = 150):
        super().__init__(theme)
        self.dpi = dpi
        self.layout_engine = LayoutEngine(
            layer_spacing=self.theme.layer_spacing,
            node_spacing=self.theme.node_spacing,
            dataset_width=self.theme.dataset_width,
            dataset_height=self.theme.dataset_height,
            recipe_size=self.theme.recipe_size,
            padding=self.theme.padding,
        )

    def _setup_style(self):
        """Configure matplotlib rcParams for DDODS style."""
        plt.rcParams.update({
            'font.family': 'sans-serif',
            'font.size': 10,
            'axes.spines.top': False,
            'axes.spines.right': False,
            'figure.facecolor': 'white',
            'axes.facecolor': 'white',
        })

    def render(self, flow) -> bytes:
        """
        Render flow as PNG bytes.

        Args:
            flow: DataikuFlow object to visualize

        Returns:
            PNG image as bytes
        """
        if not HAS_MATPLOTLIB:
            raise ImportError(
                "matplotlib is required for PNG visualization. "
                "Install with: pip install matplotlib"
            )

        self._setup_style()

        # Calculate layout
        positions = self.layout_engine.calculate_layout(flow)
        edges = self.layout_engine.get_edges()
        canvas_width, canvas_height = self.layout_engine.get_canvas_size()

        # Determine figure size based on node count
        n_nodes = len(flow.datasets) + len(flow.recipes)
        fig_width = max(10, min(20, n_nodes * 1.5))
        fig_height = max(5, min(12, n_nodes * 0.8))

        # Scale factors: map pixel positions to logical coordinates
        logical_width = fig_width
        logical_height = fig_height
        scale_x = logical_width / max(canvas_width, 1)
        scale_y = logical_height / max(canvas_height, 1)

        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        ax.set_xlim(0, logical_width)
        ax.set_ylim(0, logical_height)
        ax.axis('off')
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')

        # Title
        ax.set_title(
            flow.name,
            fontsize=14,
            fontweight='bold',
            color='#2C3E50',
            pad=15,
        )

        # Draw zones BEFORE nodes (background layer)
        self._draw_zones(ax, flow, positions, scale_x, scale_y)

        # Draw arrows (behind nodes)
        for edge in edges:
            if edge.source in positions and edge.target in positions:
                self._draw_arrow(ax, positions[edge.source], positions[edge.target], scale_x, scale_y)

        # Draw nodes
        for node_id, pos in positions.items():
            if pos.node_type == "dataset":
                self._draw_dataset(ax, pos, scale_x, scale_y)
            else:
                self._draw_recipe(ax, pos, scale_x, scale_y)

        # Render to bytes
        buf = io.BytesIO()
        fig.savefig(
            buf,
            format='png',
            dpi=self.dpi,
            bbox_inches='tight',
            pad_inches=0.3,
            facecolor='white',
        )
        plt.close(fig)
        buf.seek(0)
        return buf.read()

    def render_to_file(self, flow, path: str) -> None:
        """
        Render flow and save as PNG file.

        Args:
            flow: DataikuFlow object to visualize
            path: File path to save the PNG
        """
        png_bytes = self.render(flow)
        with open(path, 'wb') as f:
            f.write(png_bytes)

    def _to_logical(self, pos, scale_x, scale_y):
        """Convert pixel position to logical coordinates."""
        lx = pos.x * scale_x
        ly = pos.y * scale_y
        lw = pos.width * scale_x
        lh = pos.height * scale_y
        return lx, ly, lw, lh

    def _draw_dataset(self, ax, pos, scale_x, scale_y):
        """Draw a dataset node."""
        lx, ly, lw, lh = self._to_logical(pos, scale_x, scale_y)
        # Flip y so top of layout is top of figure
        fig_height = ax.get_ylim()[1]
        fy = fig_height - ly - lh

        extra = pos.extra
        ds_type = extra.get("dataset_type", "intermediate")

        if ds_type == "input":
            facecolor = "#B2DFDB"
            edgecolor = "#009688"
            linewidth = 2
        elif ds_type == "output":
            facecolor = "#C8E6C9"
            edgecolor = "#2ECC71"
            linewidth = 2
        else:
            facecolor = "#F8F9FA"
            edgecolor = "#95A5A6"
            linewidth = 1.5

        box = FancyBboxPatch(
            (lx, fy), lw, lh,
            boxstyle="round,pad=0.1",
            facecolor=facecolor,
            edgecolor=edgecolor,
            linewidth=linewidth,
            zorder=2,
        )
        ax.add_patch(box)

        # Label
        label = pos.label
        if len(label) > 18:
            label = label[:16] + "..."

        cx = lx + lw / 2
        cy = fy + lh / 2

        ax.text(
            cx, cy + lh * 0.1,
            label,
            ha='center', va='center',
            fontsize=9, fontweight='bold',
            color='#2C3E50',
            zorder=3,
        )

        # Type label below name
        type_label = ds_type.upper() if ds_type != "intermediate" else ""
        if type_label:
            ax.text(
                cx, cy - lh * 0.2,
                type_label,
                ha='center', va='center',
                fontsize=7,
                color='#95A5A6',
                zorder=3,
            )

    def _draw_recipe(self, ax, pos, scale_x, scale_y):
        """Draw a recipe node."""
        lx, ly, lw, lh = self._to_logical(pos, scale_x, scale_y)
        fig_height = ax.get_ylim()[1]
        fy = fig_height - ly - lh

        extra = pos.extra
        recipe_type = extra.get("recipe_type", "default")

        bg, border, text_color = self.theme.get_recipe_colors(recipe_type)

        # DDODS palette overrides for key recipe types
        ddods_map = {
            "prepare": ("#009688", "#00796B", "white"),
            "join": ("#5B8DEF", "#3D6FCC", "white"),
            "grouping": ("#2ECC71", "#27AE60", "white"),
            "split": ("#FF6B6B", "#E55555", "white"),
            "window": ("#9B59B6", "#8E44AD", "white"),
            "sort": ("#F5A623", "#D4891A", "white"),
            "stack": ("#9B59B6", "#8E44AD", "white"),
            "distinct": ("#795548", "#5D4037", "white"),
            "python": ("#3F51B5", "#303F9F", "white"),
        }

        if recipe_type in ddods_map:
            bg, border, text_color = ddods_map[recipe_type]

        box = FancyBboxPatch(
            (lx, fy), lw, lh,
            boxstyle="round,pad=0.1",
            facecolor=bg,
            edgecolor=border,
            linewidth=2,
            zorder=2,
        )
        ax.add_patch(box)

        # Recipe name (truncated)
        label = pos.label
        if len(label) > 12:
            label = label[:10] + ".."

        cx = lx + lw / 2
        cy = fy + lh / 2

        ax.text(
            cx, cy + lh * 0.1,
            label,
            ha='center', va='center',
            fontsize=9, fontweight='bold',
            color=text_color,
            zorder=3,
        )

        # Recipe type label below
        from py2dataiku.visualizers.icons import RecipeIcons
        type_label = RecipeIcons.get_label(recipe_type)
        ax.text(
            cx, cy - lh * 0.2,
            type_label,
            ha='center', va='center',
            fontsize=7,
            color=text_color,
            alpha=0.8,
            zorder=3,
        )

    def _draw_arrow(self, ax, source, target, scale_x, scale_y):
        """Draw an arrow between two nodes."""
        fig_height = ax.get_ylim()[1]

        # Source: right edge center
        sx = (source.x + source.width) * scale_x
        sy = fig_height - (source.y + source.height / 2) * scale_y

        # Target: left edge center
        tx = target.x * scale_x
        ty = fig_height - (target.y + target.height / 2) * scale_y

        arrow = FancyArrowPatch(
            (sx, sy), (tx, ty),
            arrowstyle='->',
            mutation_scale=12,
            color='#95A5A6',
            lw=1.5,
            zorder=1,
        )
        ax.add_patch(arrow)

    def _draw_zones(self, ax, flow, positions, scale_x, scale_y):
        """Draw flow zones as background rectangles."""
        if not flow.zones:
            return

        fig_height = ax.get_ylim()[1]

        for i, zone in enumerate(flow.zones):
            # Find bounding box of all nodes in this zone
            zone_node_ids = set()

            # Match zone datasets/recipes to position keys
            for node_id, pos in positions.items():
                if pos.node_type == "dataset" and pos.label in zone.datasets:
                    zone_node_ids.add(node_id)
                elif pos.node_type == "recipe" and pos.label in zone.recipes:
                    zone_node_ids.add(node_id)

            if not zone_node_ids:
                continue

            # Compute bounding box in pixel space
            min_x = min(positions[nid].x for nid in zone_node_ids)
            min_y = min(positions[nid].y for nid in zone_node_ids)
            max_x = max(positions[nid].x + positions[nid].width for nid in zone_node_ids)
            max_y = max(positions[nid].y + positions[nid].height for nid in zone_node_ids)

            # Add zone padding in pixel space
            pad = self.theme.zone_padding
            min_x -= pad
            min_y -= pad
            max_x += pad
            max_y += pad

            # Convert to logical coordinates
            lx = min_x * scale_x
            ly = min_y * scale_y
            lw = (max_x - min_x) * scale_x
            lh = (max_y - min_y) * scale_y

            # Flip y
            fy = fig_height - ly - lh

            zone_color = self.theme.zone_colors[i % len(self.theme.zone_colors)]
            zone_border = self.theme.zone_border_colors[i % len(self.theme.zone_border_colors)]

            zone_box = FancyBboxPatch(
                (lx, fy), lw, lh,
                boxstyle="round,pad=0.1",
                facecolor=zone_color,
                edgecolor=zone_border,
                linewidth=1.5,
                linestyle='--',
                alpha=0.4,
                zorder=0,
            )
            ax.add_patch(zone_box)

            # Zone label in top-left
            ax.text(
                lx + 0.1, fy + lh - 0.1,
                zone.name,
                fontsize=self.theme.zone_label_size,
                fontweight='bold',
                color=zone_border,
                zorder=1,
            )
