"""
Base class for flow visualizers.
"""

from abc import ABC, abstractmethod
from typing import Optional
from py2dataiku.visualizers.themes import DataikuTheme, DATAIKU_LIGHT


class FlowVisualizer(ABC):
    """Abstract base class for flow visualizers."""

    def __init__(self, theme: Optional[DataikuTheme] = None):
        """
        Initialize the visualizer.

        Args:
            theme: Visual theme to use. Defaults to DATAIKU_LIGHT.
        """
        self.theme = theme or DATAIKU_LIGHT

    @abstractmethod
    def render(self, flow) -> str:
        """
        Render the flow to the target format.

        Args:
            flow: DataikuFlow object to visualize

        Returns:
            String containing the visualization
        """
        pass

    def save(self, flow, output_path: str) -> None:
        """
        Render and save the flow to a file.

        Args:
            flow: DataikuFlow object to visualize
            output_path: Path to save the output file
        """
        content = self.render(flow)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
