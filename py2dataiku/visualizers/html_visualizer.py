"""
HTML/Canvas visualizer for Dataiku flows.

Generates interactive HTML visualization with hover and click support.
"""

from typing import Optional
import json
from py2dataiku.visualizers.base import FlowVisualizer
from py2dataiku.visualizers.layout_engine import LayoutEngine
from py2dataiku.visualizers.themes import DataikuTheme, DATAIKU_LIGHT
from py2dataiku.visualizers.icons import RecipeIcons


class HTMLVisualizer(FlowVisualizer):
    """Generate interactive HTML visualization of Dataiku flows."""

    def __init__(self, theme: Optional[DataikuTheme] = None):
        super().__init__(theme)

    def render(self, flow) -> str:
        """Render flow as interactive HTML."""
        # Get layout
        layout = LayoutEngine(
            layer_spacing=self.theme.layer_spacing,
            node_spacing=self.theme.node_spacing,
            dataset_width=self.theme.dataset_width,
            dataset_height=self.theme.dataset_height,
            recipe_size=self.theme.recipe_size,
            padding=self.theme.padding,
        )
        positions = layout.calculate_layout(flow)
        edges = layout.get_edges()
        width, height = layout.get_canvas_size()

        # Convert to JSON for JavaScript
        nodes_json = self._positions_to_json(positions)
        edges_json = self._edges_to_json(edges)
        theme_json = self._theme_to_json()

        flow_name = getattr(flow, 'name', 'Dataiku Flow')

        return self._generate_html(
            flow_name=flow_name,
            width=width,
            height=height,
            nodes_json=nodes_json,
            edges_json=edges_json,
            theme_json=theme_json,
        )

    def _positions_to_json(self, positions) -> str:
        """Convert positions to JSON."""
        nodes = []
        for node_id, pos in positions.items():
            node = {
                "id": node_id,
                "x": pos.x,
                "y": pos.y,
                "width": pos.width,
                "height": pos.height,
                "type": pos.node_type,
                "label": pos.label,
                "layer": pos.layer,
            }

            if pos.node_type == "dataset":
                node["datasetType"] = pos.extra.get("dataset_type", "intermediate")
            else:
                node["recipeType"] = pos.extra.get("recipe_type", "default")
                node["details"] = pos.extra.get("details", "")
                node["icon"] = RecipeIcons.get_unicode(pos.extra.get("recipe_type", "default"))

            nodes.append(node)

        return json.dumps(nodes, indent=2)

    def _edges_to_json(self, edges) -> str:
        """Convert edges to JSON."""
        edge_list = [{"source": e.source, "target": e.target} for e in edges]
        return json.dumps(edge_list, indent=2)

    def _theme_to_json(self) -> str:
        """Convert theme to JSON."""
        theme_dict = {
            "background": self.theme.background_color,
            "connectionColor": self.theme.connection_color,
            "connectionWidth": self.theme.connection_width,
            "fontFamily": self.theme.font_family,
            "datasetFontSize": self.theme.dataset_font_size,
            "recipeFontSize": self.theme.recipe_font_size,
            "iconFontSize": self.theme.icon_font_size,
            "datasetRadius": self.theme.dataset_radius,
            "recipeRadius": self.theme.recipe_radius,
            "input": {
                "bg": self.theme.input_bg,
                "border": self.theme.input_border,
                "text": self.theme.input_text,
            },
            "output": {
                "bg": self.theme.output_bg,
                "border": self.theme.output_border,
                "text": self.theme.output_text,
            },
            "intermediate": {
                "bg": self.theme.intermediate_bg,
                "border": self.theme.intermediate_border,
                "text": self.theme.intermediate_text,
            },
            "recipes": {},
        }

        for recipe_type, colors in self.theme.recipe_colors.items():
            theme_dict["recipes"][recipe_type] = {
                "bg": colors[0],
                "border": colors[1],
                "text": colors[2],
            }

        return json.dumps(theme_dict, indent=2)

    def _generate_html(
        self,
        flow_name: str,
        width: int,
        height: int,
        nodes_json: str,
        edges_json: str,
        theme_json: str,
    ) -> str:
        """Generate complete HTML document."""
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{flow_name} - Dataiku Flow</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: {self.theme.font_family};
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 100%;
            overflow: auto;
        }}
        h1 {{
            margin-bottom: 20px;
            color: #333;
            font-size: 24px;
        }}
        canvas {{
            border: 1px solid #ddd;
            border-radius: 8px;
            background: {self.theme.background_color};
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        #tooltip {{
            position: absolute;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
            pointer-events: none;
            display: none;
            z-index: 1000;
        }}
        .legend {{
            margin-top: 20px;
            display: flex;
            flex-wrap: wrap;
            gap: 16px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
        }}
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 4px;
            border: 2px solid;
        }}
    </style>
</head>
<body>
    <h1>{flow_name}</h1>
    <div class="container">
        <canvas id="flowCanvas" width="{width}" height="{height}"></canvas>
    </div>
    <div id="tooltip"></div>
    <div class="legend" id="legend"></div>

    <script>
        const nodes = {nodes_json};
        const edges = {edges_json};
        const theme = {theme_json};

        const canvas = document.getElementById('flowCanvas');
        const ctx = canvas.getContext('2d');
        const tooltip = document.getElementById('tooltip');

        // Position lookup
        const nodeMap = new Map();
        nodes.forEach(n => nodeMap.set(n.id, n));

        function drawFlow() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // Draw edges
            edges.forEach(edge => {{
                const source = nodeMap.get(edge.source);
                const target = nodeMap.get(edge.target);
                if (source && target) {{
                    drawEdge(source, target);
                }}
            }});

            // Draw nodes
            nodes.forEach(node => {{
                if (node.type === 'dataset') {{
                    drawDataset(node);
                }} else {{
                    drawRecipe(node);
                }}
            }});
        }}

        function drawEdge(source, target) {{
            const x1 = source.x + source.width;
            const y1 = source.y + source.height / 2;
            const x2 = target.x;
            const y2 = target.y + target.height / 2;

            ctx.beginPath();
            ctx.moveTo(x1, y1);

            // Bezier curve
            const cp1x = x1 + (x2 - x1) / 2;
            const cp2x = x2 - (x2 - x1) / 2;
            ctx.bezierCurveTo(cp1x, y1, cp2x, y2, x2, y2);

            ctx.strokeStyle = theme.connectionColor;
            ctx.lineWidth = theme.connectionWidth;
            ctx.stroke();

            // Arrow
            const angle = Math.atan2(y2 - y1, x2 - x1);
            const arrowSize = 8;
            ctx.beginPath();
            ctx.moveTo(x2, y2);
            ctx.lineTo(x2 - arrowSize * Math.cos(angle - Math.PI / 6),
                       y2 - arrowSize * Math.sin(angle - Math.PI / 6));
            ctx.lineTo(x2 - arrowSize * Math.cos(angle + Math.PI / 6),
                       y2 - arrowSize * Math.sin(angle + Math.PI / 6));
            ctx.closePath();
            ctx.fillStyle = theme.connectionColor;
            ctx.fill();
        }}

        function drawDataset(node) {{
            const colors = theme[node.datasetType] || theme.intermediate;

            // Background
            ctx.beginPath();
            roundRect(ctx, node.x, node.y, node.width, node.height, theme.datasetRadius);
            ctx.fillStyle = colors.bg;
            ctx.fill();
            ctx.strokeStyle = colors.border;
            ctx.lineWidth = 1.5;
            ctx.stroke();

            // Icon
            ctx.fillStyle = colors.border;
            ctx.font = '16px Arial';
            ctx.fillText('📊', node.x + 10, node.y + node.height / 2 + 5);

            // Label
            ctx.fillStyle = colors.text;
            ctx.font = `${{theme.datasetFontSize}}px ${{theme.fontFamily}}`;
            const label = truncate(node.label, 16);
            ctx.fillText(label, node.x + 35, node.y + node.height / 2 - 2);

            // Type label
            if (node.datasetType !== 'intermediate') {{
                ctx.font = `${{theme.datasetFontSize - 3}}px ${{theme.fontFamily}}`;
                ctx.globalAlpha = 0.7;
                ctx.fillText(`[${{node.datasetType.toUpperCase()}}]`, node.x + 35, node.y + node.height / 2 + 14);
                ctx.globalAlpha = 1;
            }}
        }}

        function drawRecipe(node) {{
            const recipeType = node.recipeType || 'default';
            const colors = theme.recipes[recipeType] || theme.recipes.default;

            // Background
            ctx.beginPath();
            roundRect(ctx, node.x, node.y, node.width, node.height, theme.recipeRadius);
            ctx.fillStyle = colors.bg;
            ctx.fill();
            ctx.strokeStyle = colors.border;
            ctx.lineWidth = 2;
            ctx.stroke();

            // Icon
            ctx.fillStyle = colors.text;
            ctx.font = `${{theme.iconFontSize}}px Arial`;
            ctx.textAlign = 'center';
            ctx.fillText(node.icon || '■', node.x + node.width / 2, node.y + node.height / 2 - 5);

            // Label
            ctx.font = `bold ${{theme.recipeFontSize}}px ${{theme.fontFamily}}`;
            const label = recipeType.charAt(0).toUpperCase() + recipeType.slice(1);
            ctx.fillText(label, node.x + node.width / 2, node.y + node.height / 2 + 12);

            // Details
            if (node.details) {{
                ctx.font = `${{theme.recipeFontSize - 2}}px ${{theme.fontFamily}}`;
                ctx.globalAlpha = 0.7;
                ctx.fillText(node.details, node.x + node.width / 2, node.y + node.height / 2 + 24);
                ctx.globalAlpha = 1;
            }}

            ctx.textAlign = 'left';
        }}

        function roundRect(ctx, x, y, width, height, radius) {{
            ctx.moveTo(x + radius, y);
            ctx.lineTo(x + width - radius, y);
            ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
            ctx.lineTo(x + width, y + height - radius);
            ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
            ctx.lineTo(x + radius, y + height);
            ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
            ctx.lineTo(x, y + radius);
            ctx.quadraticCurveTo(x, y, x + radius, y);
        }}

        function truncate(str, len) {{
            return str.length > len ? str.substring(0, len - 2) + '...' : str;
        }}

        // Tooltip handling
        canvas.addEventListener('mousemove', (e) => {{
            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            let hoveredNode = null;
            for (const node of nodes) {{
                if (x >= node.x && x <= node.x + node.width &&
                    y >= node.y && y <= node.y + node.height) {{
                    hoveredNode = node;
                    break;
                }}
            }}

            if (hoveredNode) {{
                let info = hoveredNode.type === 'dataset'
                    ? `Dataset: ${{hoveredNode.label}}\\nType: ${{hoveredNode.datasetType}}`
                    : `Recipe: ${{hoveredNode.recipeType}}\\n${{hoveredNode.details || ''}}`;

                tooltip.textContent = info;
                tooltip.style.display = 'block';
                tooltip.style.left = (e.clientX + 10) + 'px';
                tooltip.style.top = (e.clientY + 10) + 'px';
                canvas.style.cursor = 'pointer';
            }} else {{
                tooltip.style.display = 'none';
                canvas.style.cursor = 'default';
            }}
        }});

        canvas.addEventListener('mouseleave', () => {{
            tooltip.style.display = 'none';
        }});

        // Build legend
        function buildLegend() {{
            const legend = document.getElementById('legend');
            const items = [
                {{ label: 'Input Dataset', colors: theme.input }},
                {{ label: 'Output Dataset', colors: theme.output }},
                {{ label: 'Intermediate', colors: theme.intermediate }},
            ];

            Object.entries(theme.recipes).forEach(([type, colors]) => {{
                if (type !== 'default') {{
                    items.push({{ label: type.charAt(0).toUpperCase() + type.slice(1), colors }});
                }}
            }});

            items.slice(0, 8).forEach(item => {{
                const div = document.createElement('div');
                div.className = 'legend-item';
                div.innerHTML = `
                    <div class="legend-color" style="background: ${{item.colors.bg}}; border-color: ${{item.colors.border}}"></div>
                    <span>${{item.label}}</span>
                `;
                legend.appendChild(div);
            }});
        }}

        // Initialize
        drawFlow();
        buildLegend();
    </script>
</body>
</html>'''
