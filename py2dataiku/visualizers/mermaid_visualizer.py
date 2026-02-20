"""Mermaid diagram visualizer for Dataiku flows."""

from typing import Optional

from py2dataiku.visualizers.base import FlowVisualizer
from py2dataiku.visualizers.themes import DataikuTheme


class MermaidVisualizer(FlowVisualizer):
    """Generate Mermaid diagram syntax for Dataiku flows.

    This wraps the existing DiagramGenerator.to_mermaid() method
    within the standard visualizer interface.
    """

    def __init__(self, theme: Optional[DataikuTheme] = None):
        super().__init__(theme=theme)

    def render(self, flow) -> str:
        """Render the flow as a Mermaid diagram."""
        from py2dataiku.generators.diagram_generator import DiagramGenerator
        gen = DiagramGenerator()
        return gen.to_mermaid(flow)
