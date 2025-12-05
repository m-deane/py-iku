"""
py2dataiku - Convert Python data processing code to Dataiku DSS recipes and flows.

This library analyzes Python code (pandas, numpy, scikit-learn) and generates
equivalent Dataiku DSS recipe configurations, flow structures, and visual diagrams.
"""

__version__ = "0.1.0"

from py2dataiku.parser.ast_analyzer import CodeAnalyzer
from py2dataiku.generators.flow_generator import FlowGenerator
from py2dataiku.generators.diagram_generator import DiagramGenerator
from py2dataiku.models.dataiku_flow import DataikuFlow
from py2dataiku.models.dataiku_recipe import DataikuRecipe
from py2dataiku.models.dataiku_dataset import DataikuDataset

__all__ = [
    "CodeAnalyzer",
    "FlowGenerator",
    "DiagramGenerator",
    "DataikuFlow",
    "DataikuRecipe",
    "DataikuDataset",
]


def convert(code: str, optimize: bool = True) -> "DataikuFlow":
    """
    Convert Python code to a Dataiku flow.

    Args:
        code: Python source code string
        optimize: Whether to optimize the flow (merge recipes, reorder steps)

    Returns:
        DataikuFlow object representing the converted pipeline
    """
    analyzer = CodeAnalyzer()
    transformations = analyzer.analyze(code)

    generator = FlowGenerator()
    flow = generator.generate(transformations, optimize=optimize)

    return flow
