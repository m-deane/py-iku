"""
py2dataiku - Convert Python data processing code to Dataiku DSS recipes and flows.

This library analyzes Python code (pandas, numpy, scikit-learn) and generates
equivalent Dataiku DSS recipe configurations, flow structures, and visual diagrams.

Two analysis modes are available:
1. LLM-based (recommended): Uses AI to understand code semantics
2. Rule-based (fallback): Uses AST pattern matching

Visualization formats:
- SVG: Scalable vector graphics (pixel-accurate Dataiku styling)
- HTML: Interactive canvas with hover/click
- ASCII: Terminal-friendly text art
- PlantUML: Documentation-ready diagrams
- Mermaid: GitHub/Notion compatible
"""

try:
    from importlib.metadata import version as _get_version
    __version__ = _get_version("py-iku")
except Exception:
    __version__ = "0.3.0"

import warnings
from typing import Optional

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
    MockProvider,
    get_provider,
)
from py2dataiku.llm.schemas import AnalysisResult, DataStep, OperationType
from py2dataiku.generators.llm_flow_generator import LLMFlowGenerator

# Core models
from py2dataiku.models.dataiku_flow import DataikuFlow, FlowZone
from py2dataiku.models.dataiku_recipe import (
    DataikuRecipe,
    RecipeType,
    Aggregation,
    JoinKey,
    JoinType,
    AggregationFunction,
    WindowFunctionType,
    SplitMode,
    SamplingMethod,
)
from py2dataiku.models.dataiku_dataset import (
    DataikuDataset,
    DatasetType,
    DatasetConnectionType,
    ColumnSchema,
)
from py2dataiku.models.prepare_step import (
    PrepareStep,
    ProcessorType,
    StringTransformerMode,
    NumericalTransformerMode,
    FilterMatchMode,
)

# Scenario model
from py2dataiku.models.dataiku_scenario import (
    DataikuScenario,
    ScenarioTrigger,
    ScenarioStep,
    ScenarioReporter,
    TriggerType,
    StepType,
    ReporterType,
)

# Metrics and checks
from py2dataiku.models.dataiku_metrics import (
    DataikuMetric,
    DataikuCheck,
    DataQualityRule,
    MetricType,
    CheckCondition,
    CheckSeverity,
)

# MLOps models
from py2dataiku.models.dataiku_mlops import (
    APIEndpoint,
    ModelVersion,
    DriftConfig,
    EndpointType,
    ModelFramework,
    DriftMetricType,
)

# Configuration
from py2dataiku.config import (
    Py2DataikuConfig,
    load_config,
    find_config_file,
)

# Visualizers
from py2dataiku.visualizers import (
    SVGVisualizer,
    ASCIIVisualizer,
    PlantUMLVisualizer,
    HTMLVisualizer,
    visualize_flow,
    DataikuTheme,
    DATAIKU_LIGHT,
    DATAIKU_DARK,
)

# Plugin system
from py2dataiku.plugins import (
    PluginRegistry,
    plugin_hook,
    register_recipe_handler,
    register_processor_handler,
    register_pandas_mapping,
)

# Exporters
from py2dataiku.exporters import (
    DSSExporter,
    DSSProjectConfig,
    export_to_dss,
)

# Exceptions
from py2dataiku.exceptions import (
    Py2DataikuError,
    ConversionError,
    ProviderError,
    LLMResponseParseError,
    InvalidPythonCodeError,
    ValidationError,
    ExportError,
    ConfigurationError,
)

__all__ = [
    # LLM-based (recommended)
    "LLMCodeAnalyzer",
    "LLMFlowGenerator",
    "LLMProvider",
    "AnthropicProvider",
    "OpenAIProvider",
    "MockProvider",
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
    "PrepareStep",
    "RecipeType",
    "ProcessorType",
    "DatasetType",
    "DatasetConnectionType",
    "Aggregation",
    "JoinKey",
    "JoinType",
    "AggregationFunction",
    "WindowFunctionType",
    "SplitMode",
    "SamplingMethod",
    "StringTransformerMode",
    "NumericalTransformerMode",
    "FilterMatchMode",
    "ColumnSchema",
    "FlowZone",
    # Scenario
    "DataikuScenario",
    "ScenarioTrigger",
    "ScenarioStep",
    "ScenarioReporter",
    "TriggerType",
    "StepType",
    "ReporterType",
    # Metrics and checks
    "DataikuMetric",
    "DataikuCheck",
    "DataQualityRule",
    "MetricType",
    "CheckCondition",
    "CheckSeverity",
    # MLOps
    "APIEndpoint",
    "ModelVersion",
    "DriftConfig",
    "EndpointType",
    "ModelFramework",
    "DriftMetricType",
    # Configuration
    "Py2DataikuConfig",
    "load_config",
    "find_config_file",
    # Visualizers
    "SVGVisualizer",
    "ASCIIVisualizer",
    "PlantUMLVisualizer",
    "HTMLVisualizer",
    "visualize_flow",
    "DataikuTheme",
    "DATAIKU_LIGHT",
    "DATAIKU_DARK",
    # Convenience functions
    "convert",
    "convert_with_llm",
    "convert_file",
    "convert_file_with_llm",
    # Plugin system
    "PluginRegistry",
    "plugin_hook",
    "register_recipe_handler",
    "register_processor_handler",
    "register_pandas_mapping",
    # Exporters
    "DSSExporter",
    "DSSProjectConfig",
    "export_to_dss",
    # Exceptions
    "Py2DataikuError",
    "ConversionError",
    "ProviderError",
    "LLMResponseParseError",
    "InvalidPythonCodeError",
    "ValidationError",
    "ExportError",
    "ConfigurationError",
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
    api_key: Optional[str] = None,
    model: Optional[str] = None,
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


def convert_file(path: str, optimize: bool = True) -> DataikuFlow:
    """
    Convert a Python file to a Dataiku flow using rule-based analysis.

    Args:
        path: Path to a Python file
        optimize: Whether to optimize the flow

    Returns:
        DataikuFlow object representing the converted pipeline
    """
    with open(path, "r", encoding="utf-8") as f:
        code = f.read()
    flow = convert(code, optimize=optimize)
    flow.source_file = path
    return flow


def convert_file_with_llm(
    path: str,
    provider: str = "anthropic",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    optimize: bool = True,
    flow_name: Optional[str] = None,
) -> DataikuFlow:
    """
    Convert a Python file to a Dataiku flow using LLM-based analysis.

    Args:
        path: Path to a Python file
        provider: LLM provider ("anthropic", "openai")
        api_key: API key (uses environment variable if not provided)
        model: Model name (uses provider default if not provided)
        optimize: Whether to optimize the flow
        flow_name: Name for the generated flow (defaults to filename)

    Returns:
        DataikuFlow object representing the converted pipeline
    """
    import os
    with open(path, "r", encoding="utf-8") as f:
        code = f.read()
    if flow_name is None:
        flow_name = os.path.splitext(os.path.basename(path))[0]
    flow = convert_with_llm(
        code,
        provider=provider,
        api_key=api_key,
        model=model,
        optimize=optimize,
        flow_name=flow_name,
    )
    flow.source_file = path
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
        api_key: Optional[str] = None,
        model: Optional[str] = None,
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
                warnings.warn(
                    f"Could not initialize LLM ({e}). Falling back to rule-based.",
                    stacklevel=2,
                )
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
        Generate a diagram for a flow (legacy method).

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

    def visualize(self, flow: DataikuFlow, format: str = "svg", **kwargs) -> str:
        """
        Generate Dataiku-style visualization of a flow.

        This method produces pixel-accurate representations matching
        the Dataiku DSS interface styling.

        Args:
            flow: DataikuFlow to visualize
            format: Output format ("svg", "html", "ascii", "plantuml")
            **kwargs: Additional arguments for the visualizer

        Returns:
            Visualization string in the specified format
        """
        return flow.visualize(format=format, **kwargs)

    def save_visualization(
        self,
        flow: DataikuFlow,
        output_path: str,
        format: str = None,
    ) -> None:
        """
        Save flow visualization to a file.

        Args:
            flow: DataikuFlow to visualize
            output_path: Path to save the file
            format: Output format (auto-detected from extension if not provided)
        """
        if format is None:
            # Auto-detect from extension
            ext = output_path.rsplit('.', 1)[-1].lower()
            format_map = {
                'svg': 'svg',
                'html': 'html',
                'htm': 'html',
                'txt': 'ascii',
                'puml': 'plantuml',
                'plantuml': 'plantuml',
                'png': 'png',
                'pdf': 'pdf',
            }
            format = format_map.get(ext, 'svg')

        if format == 'png':
            flow.to_png(output_path)
        elif format == 'pdf':
            flow.to_pdf(output_path)
        else:
            content = flow.visualize(format=format)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
