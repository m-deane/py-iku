"""
Matplotlib-based PNG/PDF visualizer for Dataiku flows.

Produces publication-quality raster diagrams that mirror the Dataiku DSS flow
view: recipes are solid colored circles with white icon glyphs, datasets are
rounded rectangles with a colored connection-type stripe on the left edge.

When ``cairosvg`` is available, the SVG icon paths from
:class:`RecipeIcons.SVG_PATHS` are rasterized and composed onto the recipe
circles via :func:`Axes.imshow`. When it is not, we fall back to the unicode
glyph (`RecipeIcons.get_glyph`) rendered as text — this is enough to remain
recognizable without a hard cairosvg dependency.
"""

import io
import math
from typing import Optional

from py2dataiku.visualizers.base import FlowVisualizer
from py2dataiku.visualizers.icons import RecipeIcons
from py2dataiku.visualizers.layout_engine import LayoutEngine
from py2dataiku.visualizers.themes import DataikuTheme

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import cairosvg  # noqa: F401
    HAS_CAIROSVG = True
except ImportError:
    HAS_CAIROSVG = False


# Cache rasterized icons across renders so the same flow doesn't re-rasterize
# the same SVG path data on every call.
_ICON_CACHE: dict[tuple[str, str, int], object] = {}


def _rasterize_icon(recipe_type: str, color: str, size_px: int = 96):
    """Rasterize a recipe icon SVG path to an RGBA numpy array.

    Returns ``None`` if cairosvg is unavailable or rasterization fails — the
    caller falls back to a unicode glyph rendered as text.
    """
    if not HAS_CAIROSVG:
        return None

    cache_key = (recipe_type, color, size_px)
    if cache_key in _ICON_CACHE:
        return _ICON_CACHE[cache_key]

    try:
        import numpy as np
        from PIL import Image
        path_d = RecipeIcons.get_svg_path(recipe_type)
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
            f'width="{size_px}" height="{size_px}">'
            f'<path d="{path_d}" fill="{color}" stroke="{color}" '
            f'stroke-width="0.5" stroke-linejoin="round" stroke-linecap="round"/>'
            f'</svg>'
        )
        png_bytes = cairosvg.svg2png(
            bytestring=svg.encode("utf-8"), output_width=size_px, output_height=size_px
        )
        img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
        arr = np.asarray(img)
        _ICON_CACHE[cache_key] = arr
        return arr
    except Exception:
        _ICON_CACHE[cache_key] = None
        return None


class MatplotlibVisualizer(FlowVisualizer):
    """Generate PNG/PDF visualization of Dataiku flows using matplotlib."""

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

    def _setup_style(self, bg='white'):
        plt.rcParams.update({
            'font.family': 'sans-serif',
            'font.size': 10,
            'axes.spines.top': False,
            'axes.spines.right': False,
            'figure.facecolor': bg,
            'axes.facecolor': bg,
        })

    @staticmethod
    def _truncate_label(label: str, max_chars: int = 16) -> str:
        if len(label) <= max_chars:
            return label
        keep = (max_chars - 1) // 2
        return label[:keep] + "…" + label[-(max_chars - keep - 1):]

    def render(self, flow) -> bytes:
        """Render flow as PNG bytes."""
        if not HAS_MATPLOTLIB:
            raise ImportError(
                "matplotlib is required for PNG visualization. "
                "Install with: pip install matplotlib"
            )

        bg = self.theme.background_color
        self._setup_style(bg)

        positions = self.layout_engine.calculate_layout(flow)
        edges = self.layout_engine.get_edges()
        canvas_width, canvas_height = self.layout_engine.get_canvas_size()

        # Build dataset lookup for connection-type / column-count info.
        ds_lookup = {ds.name: ds for ds in getattr(flow, "datasets", [])}

        n_layers = self.layout_engine.get_layer_count()
        max_per_layer = self.layout_engine.get_max_nodes_per_layer()

        fig_width = max(10, min(22, n_layers * 2.8))
        fig_height = max(5, min(14, max_per_layer * 1.8))

        logical_width = fig_width
        logical_height = fig_height
        scale_x = logical_width / max(canvas_width, 1)
        scale_y = logical_height / max(canvas_height, 1)

        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        ax.set_xlim(0, logical_width)
        ax.set_ylim(0, logical_height)
        ax.axis('off')
        fig.patch.set_facecolor(bg)
        ax.set_facecolor(bg)

        ax.set_title(
            flow.name,
            fontsize=14,
            fontweight='bold',
            color='#2C3E50',
            pad=15,
        )

        self._draw_zones(ax, flow, positions, scale_x, scale_y)

        for edge in edges:
            if edge.source in positions and edge.target in positions:
                self._draw_arrow(ax, positions[edge.source], positions[edge.target], scale_x, scale_y)

        for _node_id, pos in positions.items():
            if pos.node_type == "dataset":
                self._draw_dataset(ax, pos, scale_x, scale_y, ds_lookup.get(pos.label))
            else:
                self._draw_recipe(ax, pos, scale_x, scale_y)

        buf = io.BytesIO()
        fig.savefig(
            buf, format='png', dpi=self.dpi, bbox_inches='tight',
            pad_inches=0.3, facecolor=bg,
        )
        plt.close(fig)
        buf.seek(0)
        return buf.read()

    def render_to_file(self, flow, path: str) -> None:
        png_bytes = self.render(flow)
        with open(path, 'wb') as f:
            f.write(png_bytes)

    def render_pdf(self, flow) -> bytes:
        """Render flow as PDF bytes."""
        if not HAS_MATPLOTLIB:
            raise ImportError("matplotlib is required for PDF visualization")
        # Reuse the PNG pipeline but emit PDF via savefig(format='pdf').
        bg = self.theme.background_color
        self._setup_style(bg)
        positions = self.layout_engine.calculate_layout(flow)
        edges = self.layout_engine.get_edges()
        canvas_width, canvas_height = self.layout_engine.get_canvas_size()
        ds_lookup = {ds.name: ds for ds in getattr(flow, "datasets", [])}
        n_layers = self.layout_engine.get_layer_count()
        max_per_layer = self.layout_engine.get_max_nodes_per_layer()
        fig_width = max(10, min(22, n_layers * 2.8))
        fig_height = max(5, min(14, max_per_layer * 1.8))
        scale_x = fig_width / max(canvas_width, 1)
        scale_y = fig_height / max(canvas_height, 1)
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        ax.set_xlim(0, fig_width)
        ax.set_ylim(0, fig_height)
        ax.axis('off')
        fig.patch.set_facecolor(bg)
        ax.set_facecolor(bg)
        ax.set_title(flow.name, fontsize=14, fontweight='bold', color='#2C3E50', pad=15)
        self._draw_zones(ax, flow, positions, scale_x, scale_y)
        for edge in edges:
            if edge.source in positions and edge.target in positions:
                self._draw_arrow(ax, positions[edge.source], positions[edge.target], scale_x, scale_y)
        for _node_id, pos in positions.items():
            if pos.node_type == "dataset":
                self._draw_dataset(ax, pos, scale_x, scale_y, ds_lookup.get(pos.label))
            else:
                self._draw_recipe(ax, pos, scale_x, scale_y)
        buf = io.BytesIO()
        fig.savefig(buf, format='pdf', bbox_inches='tight', pad_inches=0.3, facecolor=bg)
        plt.close(fig)
        buf.seek(0)
        return buf.read()

    def _to_logical(self, pos, scale_x, scale_y):
        lx = pos.x * scale_x
        ly = pos.y * scale_y
        lw = pos.width * scale_x
        lh = pos.height * scale_y
        return lx, ly, lw, lh

    def _draw_dataset(self, ax, pos, scale_x, scale_y, dataset=None):
        """Draw a dataset card with connection-type stripe on the left."""
        lx, ly, lw, lh = self._to_logical(pos, scale_x, scale_y)
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

        # Connection-type stripe colour
        stripe_color = edgecolor
        col_count = None
        if dataset is not None:
            ct = getattr(dataset, "connection_type", None)
            if ct is not None:
                ct_value = ct.value if hasattr(ct, "value") else str(ct)
                stripe_color = self.theme.get_connection_stripe(ct_value)
            schema = getattr(dataset, "schema", None) or getattr(dataset, "columns", None)
            if schema is not None:
                try:
                    col_count = len(schema)
                except TypeError:
                    col_count = None

        box = FancyBboxPatch(
            (lx, fy), lw, lh,
            boxstyle="round,pad=0.05",
            facecolor=facecolor,
            edgecolor=edgecolor,
            linewidth=linewidth,
            zorder=2,
        )
        ax.add_patch(box)

        # Stripe — a thin coloured rectangle on the left edge.
        stripe_w = lw * 0.06
        stripe = Rectangle(
            (lx, fy), stripe_w, lh,
            facecolor=stripe_color, edgecolor="none", zorder=3,
        )
        ax.add_patch(stripe)

        label = self._truncate_label(pos.label, max_chars=16)
        cx = lx + lw / 2
        cy = fy + lh / 2

        ax.text(
            cx + stripe_w / 2, cy + lh * 0.1, label,
            ha='center', va='center', fontsize=9, fontweight='bold',
            color='#2C3E50', zorder=4,
        )

        # Subtitle: type label or column count
        sub = ""
        if ds_type != "intermediate":
            sub = ds_type.upper()
        if col_count is not None:
            sub = (sub + " " if sub else "") + f"{col_count} cols"
        if sub:
            ax.text(
                cx + stripe_w / 2, cy - lh * 0.2, sub,
                ha='center', va='center', fontsize=7,
                color='#95A5A6', zorder=4,
            )

    def _draw_recipe(self, ax, pos, scale_x, scale_y):
        """Draw a recipe node — solid colored circle with icon."""
        lx, ly, lw, lh = self._to_logical(pos, scale_x, scale_y)
        fig_height = ax.get_ylim()[1]
        fy = fig_height - ly - lh

        extra = pos.extra
        recipe_type = extra.get("recipe_type", "default")

        # DSS-fidelity solid palette
        fill, stroke, icon_color = self.theme.get_recipe_palette(recipe_type)

        # Use the smaller dimension as diameter so the node is a true circle
        diameter = min(lw, lh)
        cx = lx + lw / 2
        cy = fy + lh / 2
        radius = diameter / 2 - 0.02

        circle = Circle(
            (cx, cy), radius,
            facecolor=fill, edgecolor=stroke, linewidth=2, zorder=2,
        )
        ax.add_patch(circle)

        # Icon — try to rasterize the SVG; fall back to the unicode glyph.
        icon_size = radius * 1.0
        icon_arr = _rasterize_icon(recipe_type, icon_color, size_px=96)
        if icon_arr is not None:
            ax.imshow(
                icon_arr,
                extent=(cx - icon_size, cx + icon_size, cy - icon_size, cy + icon_size),
                zorder=3,
                interpolation='bilinear',
            )
        else:
            glyph = RecipeIcons.get_glyph(recipe_type)
            ax.text(
                cx, cy, glyph,
                ha='center', va='center', fontsize=int(diameter * 6),
                color=icon_color, zorder=3,
            )

        # Label below the circle
        label = RecipeIcons.get_label(recipe_type)
        ax.text(
            cx, fy - 0.05, label,
            ha='center', va='top', fontsize=8, fontweight='600',
            color='#2C3E50', zorder=3,
        )

    def _draw_arrow(self, ax, source, target, scale_x, scale_y):
        fig_height = ax.get_ylim()[1]

        s_cx = source.x + source.width / 2
        s_cy = source.y + source.height / 2
        t_cx = target.x + target.width / 2
        t_cy = target.y + target.height / 2

        dx = t_cx - s_cx
        dy = t_cy - s_cy

        if abs(dx) >= abs(dy):
            if dx >= 0:
                sx = (source.x + source.width) * scale_x
                sy = fig_height - s_cy * scale_y
                tx = target.x * scale_x
                ty = fig_height - t_cy * scale_y
            else:
                sx = source.x * scale_x
                sy = fig_height - s_cy * scale_y
                tx = (target.x + target.width) * scale_x
                ty = fig_height - t_cy * scale_y
        else:
            if dy >= 0:
                sx = s_cx * scale_x
                sy = fig_height - (source.y + source.height) * scale_y
                tx = t_cx * scale_x
                ty = fig_height - target.y * scale_y
            else:
                sx = s_cx * scale_x
                sy = fig_height - source.y * scale_y
                tx = t_cx * scale_x
                ty = fig_height - (target.y + target.height) * scale_y

        arrow = FancyArrowPatch(
            (sx, sy), (tx, ty),
            arrowstyle='->', mutation_scale=12,
            color='#95A5A6', lw=1.5, zorder=1,
            connectionstyle='arc3,rad=0.05',
        )
        ax.add_patch(arrow)

    def _draw_zones(self, ax, flow, positions, scale_x, scale_y):
        if not flow.zones:
            return
        fig_height = ax.get_ylim()[1]
        logical_width = ax.get_xlim()[1]
        logical_height = fig_height

        for i, zone in enumerate(flow.zones):
            zone_node_ids = set()
            for node_id, pos in positions.items():
                if pos.node_type == "dataset" and pos.label in zone.datasets:
                    zone_node_ids.add(node_id)
                elif pos.node_type == "recipe" and pos.label in zone.recipes:
                    zone_node_ids.add(node_id)

            if not zone_node_ids:
                continue

            min_x = min(positions[nid].x for nid in zone_node_ids)
            min_y = min(positions[nid].y for nid in zone_node_ids)
            max_x = max(positions[nid].x + positions[nid].width for nid in zone_node_ids)
            max_y = max(positions[nid].y + positions[nid].height for nid in zone_node_ids)

            pad = self.theme.zone_padding
            min_x -= pad
            min_y -= pad
            max_x += pad
            max_y += pad

            lx = min_x * scale_x
            ly = min_y * scale_y
            lw = (max_x - min_x) * scale_x
            lh = (max_y - min_y) * scale_y

            fy = fig_height - ly - lh
            lx = max(0.05, lx)
            fy = max(0.05, fy)
            lw = min(lw, logical_width - lx - 0.05)
            lh = min(lh, logical_height - fy - 0.05)
            if lw <= 0 or lh <= 0:
                continue

            zone_color = self.theme.zone_colors[i % len(self.theme.zone_colors)]
            zone_border = self.theme.zone_border_colors[i % len(self.theme.zone_border_colors)]

            zone_box = FancyBboxPatch(
                (lx, fy), lw, lh,
                boxstyle="round,pad=0.1",
                facecolor=zone_color, edgecolor=zone_border,
                linewidth=1.5, linestyle='--', alpha=0.4, zorder=0,
            )
            ax.add_patch(zone_box)

            label_y = min(fy + lh - 0.15, fig_height - 0.25)
            label_x = max(lx + 0.1, 0.05)
            label_y = max(label_y, fy + 0.05)

            ax.text(
                label_x, label_y, zone.name,
                fontsize=self.theme.zone_label_size,
                fontweight='bold', color=zone_border, zorder=1,
            )
