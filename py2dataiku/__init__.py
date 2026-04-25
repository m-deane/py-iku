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
- Interactive: Enhanced HTML with pan/zoom, search, and export
"""

try:
    from importlib.metadata import version as _get_version
    __version__ = _get_version("py-iku")
except Exception:
    __version__ = "0.3.0"

import warnings
from typing import Optional

# Configuration
from py2dataiku.config import (
    Py2DataikuConfig,
    find_config_file,
    load_config,
)

# Exceptions
from py2dataiku.exceptions import (
    ConfigurationError,
    ConversionError,
    ExportError,
    InvalidPythonCodeError,
    LLMResponseParseError,
    ProviderError,
    Py2DataikuError,
    ValidationError,
)

# Exporters
from py2dataiku.exporters import (
    DSSExporter,
    DSSProjectConfig,
    export_to_dss,
)
from py2dataiku.generators.diagram_generator import DiagramGenerator
from py2dataiku.generators.flow_generator import FlowGenerator
from py2dataiku.generators.llm_flow_generator import LLMFlowGenerator

# Integrations
from py2dataiku.integrations import (
    DeploymentResult,
    DSSFlowDeployer,
    format_mcp_script,
    generate_mcp_tool_calls,
)

# LLM-based components (recommended)
from py2dataiku.llm.analyzer import LLMCodeAnalyzer
from py2dataiku.llm.providers import (
    AnthropicProvider,
    LLMProvider,
    MockProvider,
    OpenAIProvider,
    get_provider,
)
from py2dataiku.llm.schemas import AnalysisResult, DataStep, OperationType
from py2dataiku.models.dataiku_dataset import (
    ColumnSchema,
    DataikuDataset,
    DatasetConnectionType,
    DatasetType,
)

# Core models
from py2dataiku.models.dataiku_flow import DataikuFlow, FlowZone

# Metrics and checks
from py2dataiku.models.dataiku_metrics import (
    CheckCondition,
    CheckSeverity,
    DataikuCheck,
    DataikuMetric,
    DataQualityRule,
    MetricType,
)

# MLOps models
from py2dataiku.models.dataiku_mlops import (
    APIEndpoint,
    DriftConfig,
    DriftMetricType,
    EndpointType,
    ModelFramework,
    ModelVersion,
)
from py2dataiku.models.dataiku_recipe import (
    Aggregation,
    AggregationFunction,
    DataikuRecipe,
    JoinKey,
    JoinType,
    RecipeType,
    SamplingMethod,
    SplitMode,
    WindowFunctionType,
)

# Scenario model
from py2dataiku.models.dataiku_scenario import (
    DataikuScenario,
    ReporterType,
    ScenarioReporter,
    ScenarioStep,
    ScenarioTrigger,
    StepType,
    TriggerType,
)
from py2dataiku.models.prepare_step import (
    FilterMatchMode,
    NumericalTransformerMode,
    PrepareStep,
    ProcessorType,
    StringTransformerMode,
)

# Rule-based components (legacy)
from py2dataiku.parser.ast_analyzer import CodeAnalyzer

# Plugin system
from py2dataiku.plugins import (
    PluginRegistry,
    plugin_hook,
    register_pandas_mapping,
    register_processor_handler,
    register_recipe_handler,
)

# Visualizers
from py2dataiku.visualizers import (
    DATAIKU_DARK,
    DATAIKU_LIGHT,
    ASCIIVisualizer,
    DataikuTheme,
    HTMLVisualizer,
    PlantUMLVisualizer,
    SVGVisualizer,
    visualize_flow,
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
    # Integrations
    "DSSFlowDeployer",
    "DeploymentResult",
    "generate_mcp_tool_calls",
    "format_mcp_script",
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


def convert(code, optimize: bool = True) -> DataikuFlow:
    """
    Convert Python code to a Dataiku flow using rule-based analysis.

    This is the legacy method using AST pattern matching.
    For better results, use convert_with_llm() instead.

    Args:
        code: Either a Python source code string, a ``pathlib.Path`` to a
              ``.py`` file, or a string ending in ``.py`` that exists on disk.
              When given a path, the file is read and converted.
        optimize: Whether to optimize the flow (merge recipes, reorder steps)

    Returns:
        DataikuFlow object representing the converted pipeline
    """
    from pathlib import Path as _Path

    # Polymorphic input: accept Path objects or path-strings to .py files
    if isinstance(code, _Path):
        return convert_file(str(code), optimize=optimize)
    if (
        isinstance(code, str)
        and code.endswith(".py")
        and "\n" not in code
        and _Path(code).is_file()
    ):
        return convert_file(code, optimize=optimize)

    analyzer = CodeAnalyzer()
    transformations = analyzer.analyze(code)

    generator = FlowGenerator()
    flow = generator.generate(transformations, optimize=optimize)

    return flow


def convert_with_llm(
    code,
    provider: str = "anthropic",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    optimize: bool = True,
    flow_name: str = "converted_flow",
    on_progress=None,
) -> DataikuFlow:
    """
    Convert Python code to a Dataiku flow using LLM-based analysis.

    This is the recommended method - uses AI to understand code semantics
    and produces more accurate mappings, especially for complex code.

    Args:
        code: Either a Python source code string or a ``pathlib.Path``/string
              path to a ``.py`` file (file is read for you).
        provider: LLM provider ("anthropic", "openai")
        api_key: API key (uses environment variable if not provided)
        model: Model name (uses provider default if not provided)
        optimize: Whether to optimize the flow
        flow_name: Name for the generated flow
        on_progress: Optional callable invoked at each pipeline phase. Signature
            ``on_progress(phase: str, info: dict) -> None``. Phases: ``"start"``
            (info: ``{"code_size": int}``), ``"analyzing"`` (info: ``{"provider":
            str, "model": str}``), ``"analyzed"`` (info: ``{"steps": int,
            "datasets": int, "complexity": int}``), ``"generating"`` (info:
            ``{"step_count": int}``), ``"optimizing"`` (info: ``{"recipe_count":
            int}``), ``"done"`` (info: ``{"recipes": int, "datasets": int}``).
            Use this to give users feedback during long LLM calls.

    Returns:
        DataikuFlow object representing the converted pipeline

    Example:
        >>> def show(phase, info):
        ...     print(f"[{phase}] {info}")
        >>> flow = convert_with_llm("script.py", on_progress=show)
    """
    from pathlib import Path as _Path

    # Polymorphic input: accept Path objects or path-strings to .py files
    if isinstance(code, _Path):
        return convert_file_with_llm(
            str(code), provider=provider, api_key=api_key, model=model,
            optimize=optimize, flow_name=flow_name, on_progress=on_progress,
        )
    if (
        isinstance(code, str)
        and code.endswith(".py")
        and "\n" not in code
        and _Path(code).is_file()
    ):
        return convert_file_with_llm(
            code, provider=provider, api_key=api_key, model=model,
            optimize=optimize, flow_name=flow_name, on_progress=on_progress,
        )

    def _emit(phase: str, info: dict) -> None:
        if on_progress is None:
            return
        try:
            on_progress(phase, info)
        except Exception:
            # Never let a callback exception break the conversion
            pass

    _emit("start", {"code_size": len(code) if isinstance(code, str) else 0})

    # Initialize LLM analyzer
    llm_provider = get_provider(provider, api_key, model)
    _emit("analyzing", {"provider": provider, "model": llm_provider.model_name})

    analyzer = LLMCodeAnalyzer(provider=llm_provider)
    analysis = analyzer.analyze(code)
    _emit("analyzed", {
        "steps": len(analysis.steps),
        "datasets": len(analysis.datasets),
        "complexity": analysis.complexity_score,
    })

    # Generate flow from analysis
    _emit("generating", {"step_count": len(analysis.steps)})
    generator = LLMFlowGenerator()
    flow = generator.generate(analysis, flow_name=flow_name, optimize=optimize)

    if optimize:
        _emit("optimizing", {"recipe_count": len(flow.recipes)})

    _emit("done", {
        "recipes": len(flow.recipes),
        "datasets": len(flow.datasets),
    })
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
    with open(path, encoding="utf-8") as f:
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
    on_progress=None,
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
        on_progress: See ``convert_with_llm``.

    Returns:
        DataikuFlow object representing the converted pipeline
    """
    import os
    with open(path, encoding="utf-8") as f:
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
        on_progress=on_progress,
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
            except (ConfigurationError, ValueError, ImportError) as e:
                # ConfigurationError = missing API key (typed) or unknown provider.
                # ValueError = legacy unhandled-key paths (kept for backward-compat).
                # ImportError = optional dependency (anthropic / openai) not installed.
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
