"""
Dataiku flow visualization module.

Provides multiple output formats for visualizing Dataiku DSS flows:
- SVG: Scalable vector graphics (primary format)
- ASCII: Terminal-friendly text art
- PlantUML: Documentation-ready diagrams
- HTML: Interactive canvas-based visualization
- Interactive: Enhanced HTML with pan/zoom, search, and export
"""

from py2dataiku.visualizers.base import FlowVisualizer
from py2dataiku.visualizers.layout_engine import LayoutEngine, NodePosition
from py2dataiku.visualizers.themes import DataikuTheme, DATAIKU_LIGHT, DATAIKU_DARK
from py2dataiku.visualizers.icons import RecipeIcons
from py2dataiku.visualizers.svg_visualizer import SVGVisualizer
from py2dataiku.visualizers.ascii_visualizer import ASCIIVisualizer
from py2dataiku.visualizers.plantuml_visualizer import PlantUMLVisualizer
from py2dataiku.visualizers.html_visualizer import HTMLVisualizer
from py2dataiku.visualizers.interactive_visualizer import InteractiveVisualizer

__all__ = [
    "FlowVisualizer",
    "LayoutEngine",
    "NodePosition",
    "DataikuTheme",
    "DATAIKU_LIGHT",
    "DATAIKU_DARK",
    "RecipeIcons",
    "SVGVisualizer",
    "ASCIIVisualizer",
    "PlantUMLVisualizer",
    "HTMLVisualizer",
    "InteractiveVisualizer",
    "visualize_flow",
]


def visualize_flow(flow, format: str = "svg", **kwargs) -> str:
    """
    Generate a visual representation of a Dataiku flow.

    Args:
        flow: DataikuFlow object to visualize
        format: Output format - "svg", "ascii", "plantuml", "html", "interactive"
        **kwargs: Additional arguments passed to the visualizer

    Returns:
        String containing the visualization in the requested format
    """
    visualizers = {
        "svg": SVGVisualizer,
        "ascii": ASCIIVisualizer,
        "plantuml": PlantUMLVisualizer,
        "html": HTMLVisualizer,
        "interactive": InteractiveVisualizer,
    }

    if format not in visualizers:
        raise ValueError(f"Unknown format: {format}. Choose from: {list(visualizers.keys())}")

    visualizer = visualizers[format](**kwargs)
    return visualizer.render(flow)
