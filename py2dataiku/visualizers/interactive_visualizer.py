"""
Interactive HTML visualizer for Dataiku flows.

Enhanced visualization with:
- Pan and zoom (mouse wheel + drag)
- Click to show details panel
- Search/filter nodes
- Export buttons (SVG, PNG download)
- Keyboard shortcuts
- Node highlighting
- Flow statistics
"""

from typing import Optional
import json
from py2dataiku.visualizers.base import FlowVisualizer
from py2dataiku.visualizers.layout_engine import LayoutEngine
from py2dataiku.visualizers.themes import DataikuTheme, DATAIKU_LIGHT
from py2dataiku.visualizers.icons import RecipeIcons


class InteractiveVisualizer(FlowVisualizer):
    """Generate interactive HTML visualization with enhanced features."""

    def __init__(self, theme: Optional[DataikuTheme] = None):
        super().__init__(theme)

    def render(self, flow) -> str:
        """Render flow as interactive HTML with enhanced features."""
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

        # Build enhanced node data
        nodes_json = self._build_nodes_json(flow, positions)
        edges_json = self._edges_to_json(edges)
        theme_json = self._theme_to_json()
        stats_json = self._build_stats_json(flow)

        flow_name = getattr(flow, 'name', 'Dataiku Flow')

        return self._generate_interactive_html(
            flow_name=flow_name,
            width=width,
            height=height,
            nodes_json=nodes_json,
            edges_json=edges_json,
            theme_json=theme_json,
            stats_json=stats_json,
        )

    def _build_nodes_json(self, flow, positions) -> str:
        """Build enhanced node JSON with recipe details."""
        nodes = []

        # Build recipe lookup
        recipe_map = {r.name: r for r in flow.recipes}
        dataset_map = {d.name: d for d in flow.datasets}

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
                dataset = dataset_map.get(node_id)
                if dataset:
                    node["schema"] = [{"name": c.get("name", ""), "type": c.get("type", "")}
                                     for c in (dataset.schema or [])]
                    node["sourceLine"] = dataset.source_line
                    node["notes"] = dataset.notes or []
            else:
                node["recipeType"] = pos.extra.get("recipe_type", "default")
                node["details"] = pos.extra.get("details", "")
                node["icon"] = RecipeIcons.get_unicode(pos.extra.get("recipe_type", "default"))

                # Find recipe for extra details
                recipe = recipe_map.get(node_id)
                if recipe:
                    node["inputs"] = recipe.inputs
                    node["outputs"] = recipe.outputs
                    node["stepCount"] = len(recipe.steps) if hasattr(recipe, 'steps') else 0
                    node["sourceLines"] = recipe.source_lines or []
                    node["notes"] = recipe.notes or []
                    if recipe.steps:
                        node["steps"] = [
                            {"type": str(s.processor_type.value) if hasattr(s.processor_type, 'value') else str(s.processor_type),
                             "params": s.params}
                            for s in recipe.steps[:5]  # First 5 steps
                        ]

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

    def _build_stats_json(self, flow) -> str:
        """Build flow statistics JSON."""
        stats = {
            "totalDatasets": len(flow.datasets),
            "totalRecipes": len(flow.recipes),
            "inputDatasets": len([d for d in flow.datasets if d.dataset_type.value == "input"]),
            "outputDatasets": len([d for d in flow.datasets if d.dataset_type.value == "output"]),
            "recipeTypes": {},
        }

        for recipe in flow.recipes:
            rt = recipe.recipe_type.value
            stats["recipeTypes"][rt] = stats["recipeTypes"].get(rt, 0) + 1

        return json.dumps(stats, indent=2)

    def _generate_interactive_html(
        self,
        flow_name: str,
        width: int,
        height: int,
        nodes_json: str,
        edges_json: str,
        theme_json: str,
        stats_json: str,
    ) -> str:
        """Generate complete interactive HTML document."""
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{flow_name} - Interactive Flow Visualization</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: {self.theme.font_family};
            background: #1a1a2e;
            color: #eee;
            height: 100vh;
            overflow: hidden;
        }}

        /* Header */
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 20px;
            background: #16213e;
            border-bottom: 1px solid #0f3460;
        }}
        .header h1 {{
            font-size: 18px;
            font-weight: 500;
        }}
        .header-controls {{
            display: flex;
            gap: 12px;
            align-items: center;
        }}

        /* Search */
        .search-box {{
            position: relative;
        }}
        .search-box input {{
            padding: 8px 12px 8px 36px;
            border: 1px solid #0f3460;
            border-radius: 6px;
            background: #1a1a2e;
            color: #eee;
            font-size: 13px;
            width: 200px;
        }}
        .search-box input:focus {{
            outline: none;
            border-color: #e94560;
        }}
        .search-box::before {{
            content: '🔍';
            position: absolute;
            left: 10px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 14px;
        }}

        /* Buttons */
        .btn {{
            padding: 8px 14px;
            border: none;
            border-radius: 6px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .btn-primary {{
            background: #e94560;
            color: white;
        }}
        .btn-primary:hover {{ background: #d63355; }}
        .btn-secondary {{
            background: #0f3460;
            color: #eee;
        }}
        .btn-secondary:hover {{ background: #16417a; }}

        /* Main content */
        .main {{
            display: flex;
            height: calc(100vh - 56px);
        }}

        /* Canvas container */
        .canvas-container {{
            flex: 1;
            position: relative;
            overflow: hidden;
        }}
        canvas {{
            background: {self.theme.background_color};
        }}

        /* Zoom controls */
        .zoom-controls {{
            position: absolute;
            bottom: 20px;
            right: 20px;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}
        .zoom-btn {{
            width: 36px;
            height: 36px;
            border: none;
            border-radius: 6px;
            background: #16213e;
            color: #eee;
            font-size: 18px;
            cursor: pointer;
            transition: background 0.2s;
        }}
        .zoom-btn:hover {{ background: #0f3460; }}
        .zoom-level {{
            text-align: center;
            font-size: 11px;
            color: #888;
            margin: 4px 0;
        }}

        /* Details panel */
        .details-panel {{
            width: 320px;
            background: #16213e;
            border-left: 1px solid #0f3460;
            overflow-y: auto;
            display: none;
        }}
        .details-panel.visible {{ display: block; }}
        .panel-header {{
            padding: 16px;
            border-bottom: 1px solid #0f3460;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .panel-header h2 {{
            font-size: 14px;
            font-weight: 500;
        }}
        .close-btn {{
            background: none;
            border: none;
            color: #888;
            font-size: 20px;
            cursor: pointer;
        }}
        .close-btn:hover {{ color: #eee; }}
        .panel-content {{ padding: 16px; }}
        .detail-section {{
            margin-bottom: 16px;
        }}
        .detail-section h3 {{
            font-size: 11px;
            text-transform: uppercase;
            color: #888;
            margin-bottom: 8px;
        }}
        .detail-value {{
            font-size: 13px;
            color: #eee;
        }}
        .detail-list {{
            list-style: none;
        }}
        .detail-list li {{
            padding: 4px 0;
            font-size: 12px;
            color: #ccc;
            border-bottom: 1px solid #0f3460;
        }}
        .badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            margin-right: 4px;
        }}
        .badge-input {{ background: #2d5a27; }}
        .badge-output {{ background: #5a2727; }}
        .badge-prepare {{ background: #2d4a5a; }}
        .badge-grouping {{ background: #5a4a2d; }}

        /* Stats bar */
        .stats-bar {{
            position: absolute;
            top: 10px;
            left: 10px;
            display: flex;
            gap: 16px;
            background: rgba(22, 33, 62, 0.9);
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 12px;
        }}
        .stat-item {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .stat-value {{
            font-weight: 600;
            color: #e94560;
        }}

        /* Tooltip */
        #tooltip {{
            position: fixed;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 10px 14px;
            border-radius: 6px;
            font-size: 12px;
            pointer-events: none;
            display: none;
            z-index: 1000;
            max-width: 250px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }}

        /* Keyboard shortcuts help */
        .shortcuts-help {{
            position: fixed;
            bottom: 20px;
            left: 20px;
            font-size: 11px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 {flow_name}</h1>
        <div class="header-controls">
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="Search nodes..." />
            </div>
            <button class="btn btn-secondary" onclick="resetView()">Reset View</button>
            <button class="btn btn-secondary" onclick="exportSVG()">Export SVG</button>
            <button class="btn btn-primary" onclick="exportPNG()">Export PNG</button>
        </div>
    </div>

    <div class="main">
        <div class="canvas-container" id="canvasContainer">
            <canvas id="flowCanvas"></canvas>

            <div class="stats-bar">
                <div class="stat-item">
                    <span>Datasets:</span>
                    <span class="stat-value" id="statDatasets">-</span>
                </div>
                <div class="stat-item">
                    <span>Recipes:</span>
                    <span class="stat-value" id="statRecipes">-</span>
                </div>
                <div class="stat-item">
                    <span>Inputs:</span>
                    <span class="stat-value" id="statInputs">-</span>
                </div>
            </div>

            <div class="zoom-controls">
                <button class="zoom-btn" onclick="zoomIn()">+</button>
                <div class="zoom-level" id="zoomLevel">100%</div>
                <button class="zoom-btn" onclick="zoomOut()">-</button>
                <button class="zoom-btn" onclick="fitToScreen()">⊡</button>
            </div>
        </div>

        <div class="details-panel" id="detailsPanel">
            <div class="panel-header">
                <h2 id="panelTitle">Node Details</h2>
                <button class="close-btn" onclick="closePanel()">×</button>
            </div>
            <div class="panel-content" id="panelContent"></div>
        </div>
    </div>

    <div id="tooltip"></div>

    <div class="shortcuts-help">
        Scroll to zoom • Drag to pan • Click node for details • Esc to close • / to search
    </div>

    <script>
        // Data
        const nodes = {nodes_json};
        const edges = {edges_json};
        const theme = {theme_json};
        const stats = {stats_json};

        // Canvas setup
        const container = document.getElementById('canvasContainer');
        const canvas = document.getElementById('flowCanvas');
        const ctx = canvas.getContext('2d');
        const tooltip = document.getElementById('tooltip');

        // View state
        let scale = 1;
        let offsetX = 0;
        let offsetY = 0;
        let isDragging = false;
        let dragStartX = 0;
        let dragStartY = 0;
        let selectedNode = null;
        let highlightedNodes = new Set();
        let searchTerm = '';

        // Original dimensions
        const originalWidth = {width};
        const originalHeight = {height};

        // Node lookup
        const nodeMap = new Map();
        nodes.forEach(n => nodeMap.set(n.id, n));

        // Initialize
        function init() {{
            resizeCanvas();
            updateStats();
            drawFlow();

            // Event listeners
            window.addEventListener('resize', resizeCanvas);
            canvas.addEventListener('wheel', handleWheel, {{ passive: false }});
            canvas.addEventListener('mousedown', handleMouseDown);
            canvas.addEventListener('mousemove', handleMouseMove);
            canvas.addEventListener('mouseup', handleMouseUp);
            canvas.addEventListener('mouseleave', handleMouseLeave);
            canvas.addEventListener('click', handleClick);
            canvas.addEventListener('dblclick', handleDoubleClick);

            document.getElementById('searchInput').addEventListener('input', handleSearch);
            document.addEventListener('keydown', handleKeyboard);
        }}

        function resizeCanvas() {{
            canvas.width = container.clientWidth;
            canvas.height = container.clientHeight;
            drawFlow();
        }}

        function updateStats() {{
            document.getElementById('statDatasets').textContent = stats.totalDatasets;
            document.getElementById('statRecipes').textContent = stats.totalRecipes;
            document.getElementById('statInputs').textContent = stats.inputDatasets;
        }}

        // Drawing functions
        function drawFlow() {{
            ctx.save();
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // Apply transforms
            ctx.translate(offsetX, offsetY);
            ctx.scale(scale, scale);

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
                const isHighlighted = highlightedNodes.has(node.id);
                const isSelected = selectedNode && selectedNode.id === node.id;
                const isFiltered = searchTerm && !node.label.toLowerCase().includes(searchTerm.toLowerCase());

                if (node.type === 'dataset') {{
                    drawDataset(node, isHighlighted, isSelected, isFiltered);
                }} else {{
                    drawRecipe(node, isHighlighted, isSelected, isFiltered);
                }}
            }});

            ctx.restore();
            updateZoomLevel();
        }}

        function drawEdge(source, target) {{
            const x1 = source.x + source.width;
            const y1 = source.y + source.height / 2;
            const x2 = target.x;
            const y2 = target.y + target.height / 2;

            ctx.beginPath();
            ctx.moveTo(x1, y1);
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

        function drawDataset(node, highlighted, selected, filtered) {{
            const colors = theme[node.datasetType] || theme.intermediate;
            const alpha = filtered ? 0.3 : 1;

            ctx.globalAlpha = alpha;

            // Shadow/glow for selected
            if (selected) {{
                ctx.shadowColor = '#e94560';
                ctx.shadowBlur = 15;
            }} else if (highlighted) {{
                ctx.shadowColor = colors.border;
                ctx.shadowBlur = 10;
            }}

            // Background
            ctx.beginPath();
            roundRect(ctx, node.x, node.y, node.width, node.height, theme.datasetRadius);
            ctx.fillStyle = colors.bg;
            ctx.fill();
            ctx.strokeStyle = selected ? '#e94560' : colors.border;
            ctx.lineWidth = selected ? 3 : 1.5;
            ctx.stroke();

            ctx.shadowBlur = 0;

            // Icon
            ctx.fillStyle = colors.border;
            ctx.font = '16px Arial';
            ctx.fillText('📊', node.x + 10, node.y + node.height / 2 + 5);

            // Label
            ctx.fillStyle = colors.text;
            ctx.font = `${{theme.datasetFontSize}}px ${{theme.fontFamily}}`;
            ctx.fillText(truncate(node.label, 16), node.x + 35, node.y + node.height / 2 - 2);

            // Type label
            if (node.datasetType !== 'intermediate') {{
                ctx.font = `${{theme.datasetFontSize - 3}}px ${{theme.fontFamily}}`;
                ctx.globalAlpha = alpha * 0.7;
                ctx.fillText(`[${{node.datasetType.toUpperCase()}}]`, node.x + 35, node.y + node.height / 2 + 14);
            }}

            ctx.globalAlpha = 1;
        }}

        function drawRecipe(node, highlighted, selected, filtered) {{
            const recipeType = node.recipeType || 'default';
            const colors = theme.recipes[recipeType] || theme.recipes.default;
            const alpha = filtered ? 0.3 : 1;

            ctx.globalAlpha = alpha;

            if (selected) {{
                ctx.shadowColor = '#e94560';
                ctx.shadowBlur = 15;
            }} else if (highlighted) {{
                ctx.shadowColor = colors.border;
                ctx.shadowBlur = 10;
            }}

            ctx.beginPath();
            roundRect(ctx, node.x, node.y, node.width, node.height, theme.recipeRadius);
            ctx.fillStyle = colors.bg;
            ctx.fill();
            ctx.strokeStyle = selected ? '#e94560' : colors.border;
            ctx.lineWidth = selected ? 3 : 2;
            ctx.stroke();

            ctx.shadowBlur = 0;

            // Icon
            ctx.fillStyle = colors.text;
            ctx.font = `${{theme.iconFontSize}}px Arial`;
            ctx.textAlign = 'center';
            ctx.fillText(node.icon || '■', node.x + node.width / 2, node.y + node.height / 2 - 5);

            // Label
            ctx.font = `bold ${{theme.recipeFontSize}}px ${{theme.fontFamily}}`;
            ctx.fillText(recipeType.charAt(0).toUpperCase() + recipeType.slice(1),
                        node.x + node.width / 2, node.y + node.height / 2 + 12);

            // Step count badge
            if (node.stepCount > 0) {{
                ctx.font = '10px Arial';
                ctx.fillStyle = colors.border;
                const badgeX = node.x + node.width - 18;
                const badgeY = node.y + 10;
                ctx.beginPath();
                ctx.arc(badgeX, badgeY, 10, 0, Math.PI * 2);
                ctx.fill();
                ctx.fillStyle = colors.bg;
                ctx.fillText(node.stepCount, badgeX, badgeY + 4);
            }}

            ctx.textAlign = 'left';
            ctx.globalAlpha = 1;
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

        // Event handlers
        function handleWheel(e) {{
            e.preventDefault();
            const rect = canvas.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;

            const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1;
            const newScale = Math.max(0.1, Math.min(5, scale * zoomFactor));

            // Zoom towards mouse position
            offsetX = mouseX - (mouseX - offsetX) * (newScale / scale);
            offsetY = mouseY - (mouseY - offsetY) * (newScale / scale);
            scale = newScale;

            drawFlow();
        }}

        function handleMouseDown(e) {{
            isDragging = true;
            dragStartX = e.clientX - offsetX;
            dragStartY = e.clientY - offsetY;
            canvas.style.cursor = 'grabbing';
        }}

        function handleMouseMove(e) {{
            const rect = canvas.getBoundingClientRect();
            const x = (e.clientX - rect.left - offsetX) / scale;
            const y = (e.clientY - rect.top - offsetY) / scale;

            if (isDragging) {{
                offsetX = e.clientX - dragStartX;
                offsetY = e.clientY - dragStartY;
                drawFlow();
                return;
            }}

            // Find hovered node
            let hoveredNode = findNodeAt(x, y);

            if (hoveredNode) {{
                let info = hoveredNode.type === 'dataset'
                    ? `<strong>${{hoveredNode.label}}</strong><br/>Type: ${{hoveredNode.datasetType}}`
                    : `<strong>${{hoveredNode.recipeType}}</strong><br/>` +
                      (hoveredNode.stepCount > 0 ? `Steps: ${{hoveredNode.stepCount}}<br/>` : '') +
                      (hoveredNode.inputs ? `In: ${{hoveredNode.inputs.join(', ')}}` : '');

                tooltip.innerHTML = info;
                tooltip.style.display = 'block';
                tooltip.style.left = (e.clientX + 15) + 'px';
                tooltip.style.top = (e.clientY + 15) + 'px';
                canvas.style.cursor = 'pointer';
            }} else {{
                tooltip.style.display = 'none';
                canvas.style.cursor = isDragging ? 'grabbing' : 'grab';
            }}
        }}

        function handleMouseUp() {{
            isDragging = false;
            canvas.style.cursor = 'grab';
        }}

        function handleMouseLeave() {{
            isDragging = false;
            tooltip.style.display = 'none';
        }}

        function handleClick(e) {{
            const rect = canvas.getBoundingClientRect();
            const x = (e.clientX - rect.left - offsetX) / scale;
            const y = (e.clientY - rect.top - offsetY) / scale;

            const node = findNodeAt(x, y);
            if (node) {{
                selectedNode = node;
                showDetailsPanel(node);
            }} else {{
                selectedNode = null;
            }}
            drawFlow();
        }}

        function handleDoubleClick(e) {{
            const rect = canvas.getBoundingClientRect();
            const x = (e.clientX - rect.left - offsetX) / scale;
            const y = (e.clientY - rect.top - offsetY) / scale;

            const node = findNodeAt(x, y);
            if (node) {{
                // Center on node
                offsetX = canvas.width / 2 - (node.x + node.width / 2) * scale;
                offsetY = canvas.height / 2 - (node.y + node.height / 2) * scale;
                drawFlow();
            }}
        }}

        function handleSearch(e) {{
            searchTerm = e.target.value;
            drawFlow();
        }}

        function handleKeyboard(e) {{
            if (e.key === 'Escape') {{
                closePanel();
                selectedNode = null;
                searchTerm = '';
                document.getElementById('searchInput').value = '';
                drawFlow();
            }} else if (e.key === '/' && document.activeElement !== document.getElementById('searchInput')) {{
                e.preventDefault();
                document.getElementById('searchInput').focus();
            }} else if (e.key === '0') {{
                resetView();
            }}
        }}

        function findNodeAt(x, y) {{
            for (const node of nodes) {{
                if (x >= node.x && x <= node.x + node.width &&
                    y >= node.y && y <= node.y + node.height) {{
                    return node;
                }}
            }}
            return null;
        }}

        // Panel functions
        function showDetailsPanel(node) {{
            const panel = document.getElementById('detailsPanel');
            const title = document.getElementById('panelTitle');
            const content = document.getElementById('panelContent');

            panel.classList.add('visible');
            title.textContent = node.type === 'dataset' ? '📊 ' + node.label : '⚙️ ' + (node.recipeType || 'Recipe');

            let html = '';

            if (node.type === 'dataset') {{
                html = `
                    <div class="detail-section">
                        <h3>Type</h3>
                        <span class="badge badge-${{node.datasetType}}">${{node.datasetType.toUpperCase()}}</span>
                    </div>
                    ${{node.schema && node.schema.length > 0 ? `
                    <div class="detail-section">
                        <h3>Schema (${{node.schema.length}} columns)</h3>
                        <ul class="detail-list">
                            ${{node.schema.map(c => `<li>${{c.name}} <span style="color:#888">(${{c.type || 'string'}})</span></li>`).join('')}}
                        </ul>
                    </div>` : ''}}
                    ${{node.sourceLine ? `<div class="detail-section"><h3>Source Line</h3><div class="detail-value">${{node.sourceLine}}</div></div>` : ''}}
                `;
            }} else {{
                html = `
                    <div class="detail-section">
                        <h3>Recipe Type</h3>
                        <span class="badge badge-${{node.recipeType}}">${{node.recipeType?.toUpperCase()}}</span>
                    </div>
                    <div class="detail-section">
                        <h3>Inputs</h3>
                        <ul class="detail-list">
                            ${{(node.inputs || []).map(i => `<li>${{i}}</li>`).join('') || '<li>None</li>'}}
                        </ul>
                    </div>
                    <div class="detail-section">
                        <h3>Outputs</h3>
                        <ul class="detail-list">
                            ${{(node.outputs || []).map(o => `<li>${{o}}</li>`).join('') || '<li>None</li>'}}
                        </ul>
                    </div>
                    ${{node.steps && node.steps.length > 0 ? `
                    <div class="detail-section">
                        <h3>Steps (${{node.stepCount}})</h3>
                        <ul class="detail-list">
                            ${{node.steps.map(s => `<li>${{s.type}}</li>`).join('')}}
                            ${{node.stepCount > 5 ? '<li style="color:#888">... and more</li>' : ''}}
                        </ul>
                    </div>` : ''}}
                    ${{node.sourceLines && node.sourceLines.length > 0 ? `<div class="detail-section"><h3>Source Lines</h3><div class="detail-value">${{node.sourceLines.join(', ')}}</div></div>` : ''}}
                `;
            }}

            if (node.notes && node.notes.length > 0) {{
                html += `
                    <div class="detail-section">
                        <h3>Notes</h3>
                        <ul class="detail-list">
                            ${{node.notes.map(n => `<li>${{n}}</li>`).join('')}}
                        </ul>
                    </div>
                `;
            }}

            content.innerHTML = html;
        }}

        function closePanel() {{
            document.getElementById('detailsPanel').classList.remove('visible');
            selectedNode = null;
            drawFlow();
        }}

        // Zoom functions
        function zoomIn() {{
            scale = Math.min(5, scale * 1.2);
            drawFlow();
        }}

        function zoomOut() {{
            scale = Math.max(0.1, scale / 1.2);
            drawFlow();
        }}

        function fitToScreen() {{
            const scaleX = (canvas.width - 40) / originalWidth;
            const scaleY = (canvas.height - 40) / originalHeight;
            scale = Math.min(scaleX, scaleY, 1);
            offsetX = (canvas.width - originalWidth * scale) / 2;
            offsetY = (canvas.height - originalHeight * scale) / 2;
            drawFlow();
        }}

        function resetView() {{
            scale = 1;
            offsetX = 0;
            offsetY = 0;
            searchTerm = '';
            document.getElementById('searchInput').value = '';
            selectedNode = null;
            closePanel();
            drawFlow();
        }}

        function updateZoomLevel() {{
            document.getElementById('zoomLevel').textContent = Math.round(scale * 100) + '%';
        }}

        // Export functions
        function exportSVG() {{
            // Convert canvas to SVG approximation
            const svg = generateSVGContent();
            downloadFile(svg, 'flow.svg', 'image/svg+xml');
        }}

        function exportPNG() {{
            // Create high-res canvas
            const exportCanvas = document.createElement('canvas');
            const exportCtx = exportCanvas.getContext('2d');
            const dpr = 2;
            exportCanvas.width = originalWidth * dpr;
            exportCanvas.height = originalHeight * dpr;

            exportCtx.scale(dpr, dpr);
            exportCtx.fillStyle = theme.background;
            exportCtx.fillRect(0, 0, originalWidth, originalHeight);

            // Draw edges
            edges.forEach(edge => {{
                const source = nodeMap.get(edge.source);
                const target = nodeMap.get(edge.target);
                if (source && target) {{
                    drawEdgeToCtx(exportCtx, source, target);
                }}
            }});

            // Draw nodes
            nodes.forEach(node => {{
                if (node.type === 'dataset') {{
                    drawDatasetToCtx(exportCtx, node);
                }} else {{
                    drawRecipeToCtx(exportCtx, node);
                }}
            }});

            exportCanvas.toBlob(blob => {{
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'flow.png';
                a.click();
                URL.revokeObjectURL(url);
            }});
        }}

        function drawEdgeToCtx(ctx, source, target) {{
            const x1 = source.x + source.width;
            const y1 = source.y + source.height / 2;
            const x2 = target.x;
            const y2 = target.y + target.height / 2;

            ctx.beginPath();
            ctx.moveTo(x1, y1);
            const cp1x = x1 + (x2 - x1) / 2;
            ctx.bezierCurveTo(cp1x, y1, cp1x, y2, x2, y2);
            ctx.strokeStyle = theme.connectionColor;
            ctx.lineWidth = theme.connectionWidth;
            ctx.stroke();
        }}

        function drawDatasetToCtx(ctx, node) {{
            const colors = theme[node.datasetType] || theme.intermediate;
            ctx.beginPath();
            roundRect(ctx, node.x, node.y, node.width, node.height, theme.datasetRadius);
            ctx.fillStyle = colors.bg;
            ctx.fill();
            ctx.strokeStyle = colors.border;
            ctx.lineWidth = 1.5;
            ctx.stroke();
            ctx.fillStyle = colors.text;
            ctx.font = `${{theme.datasetFontSize}}px ${{theme.fontFamily}}`;
            ctx.fillText(truncate(node.label, 18), node.x + 10, node.y + node.height / 2 + 4);
        }}

        function drawRecipeToCtx(ctx, node) {{
            const colors = theme.recipes[node.recipeType] || theme.recipes.default;
            ctx.beginPath();
            roundRect(ctx, node.x, node.y, node.width, node.height, theme.recipeRadius);
            ctx.fillStyle = colors.bg;
            ctx.fill();
            ctx.strokeStyle = colors.border;
            ctx.lineWidth = 2;
            ctx.stroke();
            ctx.fillStyle = colors.text;
            ctx.font = `bold ${{theme.recipeFontSize}}px ${{theme.fontFamily}}`;
            ctx.textAlign = 'center';
            ctx.fillText(node.recipeType?.toUpperCase() || 'RECIPE', node.x + node.width / 2, node.y + node.height / 2 + 4);
            ctx.textAlign = 'left';
        }}

        function generateSVGContent() {{
            // Simple SVG generation
            let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${{originalWidth}}" height="${{originalHeight}}" style="background:${{theme.background}}">`;

            // Edges
            edges.forEach(edge => {{
                const source = nodeMap.get(edge.source);
                const target = nodeMap.get(edge.target);
                if (source && target) {{
                    const x1 = source.x + source.width;
                    const y1 = source.y + source.height / 2;
                    const x2 = target.x;
                    const y2 = target.y + target.height / 2;
                    const cpx = x1 + (x2 - x1) / 2;
                    svg += `<path d="M${{x1}},${{y1}} C${{cpx}},${{y1}} ${{cpx}},${{y2}} ${{x2}},${{y2}}" fill="none" stroke="${{theme.connectionColor}}" stroke-width="${{theme.connectionWidth}}"/>`;
                }}
            }});

            // Nodes
            nodes.forEach(node => {{
                const colors = node.type === 'dataset'
                    ? (theme[node.datasetType] || theme.intermediate)
                    : (theme.recipes[node.recipeType] || theme.recipes.default);
                svg += `<rect x="${{node.x}}" y="${{node.y}}" width="${{node.width}}" height="${{node.height}}" rx="6" fill="${{colors.bg}}" stroke="${{colors.border}}" stroke-width="2"/>`;
                svg += `<text x="${{node.x + node.width/2}}" y="${{node.y + node.height/2 + 4}}" text-anchor="middle" fill="${{colors.text}}" font-family="${{theme.fontFamily}}" font-size="12">${{node.label}}</text>`;
            }});

            svg += '</svg>';
            return svg;
        }}

        function downloadFile(content, filename, type) {{
            const blob = new Blob([content], {{ type }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();
            URL.revokeObjectURL(url);
        }}

        // Start
        init();
        fitToScreen();
    </script>
</body>
</html>'''
