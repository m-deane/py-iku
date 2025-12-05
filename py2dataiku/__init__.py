"""
py2dataiku - Convert Python data processing code to Dataiku DSS recipes and flows.

This library analyzes Python code (pandas, numpy, scikit-learn) and generates
equivalent Dataiku DSS recipe configurations, flow structures, and visual diagrams.

Two analysis modes are available:
1. LLM-based (recommended): Uses AI to understand code semantics
2. Rule-based (fallback): Uses AST pattern matching
"""

__version__ = "0.2.0"

# Rule-based components (legacy)
from py2dataiku.parser.ast_analyzer import CodeAnalyzer
from py2dataiku.generators.flow_generator import FlowGenerator
from py2dataiku.generators.diagram_generator import DiagramGenerator

# LLM-based components (recommended)
from py2dataiku.llm.analyzer import LLMCodeAnalyzer
from py2dataiku.llm.providers import (
    LLMProvider,
    AnthropicProvider,
    OpenAIProvider,
    get_provider,
)
from py2dataiku.llm.schemas import AnalysisResult, DataStep, OperationType
from py2dataiku.generators.llm_flow_generator import LLMFlowGenerator

# Core models
from py2dataiku.models.dataiku_flow import DataikuFlow
from py2dataiku.models.dataiku_recipe import DataikuRecipe
from py2dataiku.models.dataiku_dataset import DataikuDataset

__all__ = [
    # LLM-based (recommended)
    "LLMCodeAnalyzer",
    "LLMFlowGenerator",
    "LLMProvider",
    "AnthropicProvider",
    "OpenAIProvider",
    "get_provider",
    "AnalysisResult",
    "DataStep",
    "OperationType",
    # Rule-based (legacy)
    "CodeAnalyzer",
    "FlowGenerator",
    # Shared
    "DiagramGenerator",
    "DataikuFlow",
    "DataikuRecipe",
    "DataikuDataset",
    # Convenience functions
    "convert",
    "convert_with_llm",
]


def convert(code: str, optimize: bool = True) -> DataikuFlow:
    """
    Convert Python code to a Dataiku flow using rule-based analysis.

    This is the legacy method using AST pattern matching.
    For better results, use convert_with_llm() instead.

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


def convert_with_llm(
    code: str,
    provider: str = "anthropic",
    api_key: str = None,
    model: str = None,
    optimize: bool = True,
    flow_name: str = "converted_flow",
) -> DataikuFlow:
    """
    Convert Python code to a Dataiku flow using LLM-based analysis.

    This is the recommended method - uses AI to understand code semantics
    and produces more accurate mappings, especially for complex code.

    Args:
        code: Python source code string
        provider: LLM provider ("anthropic", "openai")
        api_key: API key (uses environment variable if not provided)
        model: Model name (uses provider default if not provided)
        optimize: Whether to optimize the flow
        flow_name: Name for the generated flow

    Returns:
        DataikuFlow object representing the converted pipeline

    Example:
        >>> flow = convert_with_llm('''
        ... import pandas as pd
        ... df = pd.read_csv('data.csv')
        ... df = df.dropna()
        ... result = df.groupby('category').agg({'amount': 'sum'})
        ... ''')
        >>> print(flow.get_summary())
    """
    # Initialize LLM analyzer
    llm_provider = get_provider(provider, api_key, model)
    analyzer = LLMCodeAnalyzer(provider=llm_provider)

    # Analyze code with LLM
    analysis = analyzer.analyze(code)

    # Generate flow from analysis
    generator = LLMFlowGenerator()
    flow = generator.generate(analysis, flow_name=flow_name, optimize=optimize)

    return flow


class Py2Dataiku:
    """
    Main converter class with hybrid LLM + rule-based approach.

    This class provides a unified interface for converting Python code
    to Dataiku flows, with LLM as primary and rule-based as fallback.
    """

    def __init__(
        self,
        provider: str = "anthropic",
        api_key: str = None,
        model: str = None,
        use_llm: bool = True,
    ):
        """
        Initialize the converter.

        Args:
            provider: LLM provider name ("anthropic", "openai")
            api_key: API key for LLM provider
            model: Model name override
            use_llm: Whether to use LLM (True) or rule-based (False)
        """
        self.use_llm = use_llm
        self.provider = provider
        self.api_key = api_key
        self.model = model

        # Initialize components
        self.diagram_generator = DiagramGenerator()

        if use_llm:
            try:
                llm_provider = get_provider(provider, api_key, model)
                self.analyzer = LLMCodeAnalyzer(provider=llm_provider)
                self.flow_generator = LLMFlowGenerator()
            except (ValueError, ImportError) as e:
                print(f"Warning: Could not initialize LLM ({e}). Falling back to rule-based.")
                self.use_llm = False
                self.analyzer = CodeAnalyzer()
                self.flow_generator = FlowGenerator()
        else:
            self.analyzer = CodeAnalyzer()
            self.flow_generator = FlowGenerator()

    def convert(
        self,
        code: str,
        flow_name: str = "converted_flow",
        optimize: bool = True,
    ) -> DataikuFlow:
        """
        Convert Python code to a Dataiku flow.

        Args:
            code: Python source code
            flow_name: Name for the generated flow
            optimize: Whether to optimize the flow

        Returns:
            DataikuFlow object
        """
        if self.use_llm:
            analysis = self.analyzer.analyze(code)
            return self.flow_generator.generate(
                analysis, flow_name=flow_name, optimize=optimize
            )
        else:
            transformations = self.analyzer.analyze(code)
            return self.flow_generator.generate(
                transformations, flow_name=flow_name, optimize=optimize
            )

    def analyze(self, code: str) -> AnalysisResult:
        """
        Analyze code without generating flow (LLM mode only).

        Args:
            code: Python source code

        Returns:
            AnalysisResult with extracted steps and metadata
        """
        if not self.use_llm:
            raise ValueError("analyze() requires LLM mode. Initialize with use_llm=True")
        return self.analyzer.analyze(code)

    def generate_diagram(self, flow: DataikuFlow, format: str = "mermaid") -> str:
        """
        Generate a diagram for a flow.

        Args:
            flow: DataikuFlow to visualize
            format: Diagram format ("mermaid", "graphviz", "ascii", "plantuml")

        Returns:
            Diagram string in specified format
        """
        if format == "mermaid":
            return self.diagram_generator.to_mermaid(flow)
        elif format == "graphviz":
            return self.diagram_generator.to_graphviz(flow)
        elif format == "ascii":
            return self.diagram_generator.to_ascii(flow)
        elif format == "plantuml":
            return self.diagram_generator.to_plantuml(flow)
        else:
            raise ValueError(f"Unknown format: {format}")
