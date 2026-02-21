# py-iku API Reference

API documentation for **py-iku** v0.3.0 - Convert Python data processing code to Dataiku DSS recipes and flows.

## Modules

| Module | Description |
|--------|-------------|
| [Core Functions](core-functions.md) | Top-level convenience functions: `convert()`, `convert_with_llm()`, `convert_file()` |
| [Py2Dataiku Class](py2dataiku-class.md) | Main converter class with hybrid LLM + rule-based approach |
| [Models](models.md) | Core data models: `DataikuFlow`, `DataikuRecipe`, `DataikuDataset`, `PrepareStep` |
| [Enums](enums.md) | All enum types: `RecipeType`, `ProcessorType`, `DatasetType`, and 25+ more |
| [LLM Providers](llm-providers.md) | LLM integration: `AnthropicProvider`, `OpenAIProvider`, `LLMCodeAnalyzer` |
| [Visualizers](visualizers.md) | Visualization engines: SVG, HTML, ASCII, Mermaid, PlantUML |
| [Exporters](exporters.md) | DSS project export: `DSSExporter`, `DSSProjectConfig` |
| [Plugin System](plugins.md) | Extension system: `PluginRegistry`, decorators, custom handlers |
| [Configuration](configuration.md) | Config system: `Py2DataikuConfig`, file discovery, environment variables |
| [Exceptions](exceptions.md) | Exception hierarchy: `Py2DataikuError` and subclasses |
| [Graph](graph.md) | DAG operations: `FlowGraph`, topological sort, cycle detection |
| [Scenarios & Metrics](scenarios-metrics.md) | Automation: scenarios, triggers, metrics, checks, data quality rules |
| [MLOps](mlops.md) | ML operations: API endpoints, model versions, drift detection |
| [Recipe Settings](recipe-settings.md) | Typed settings: `RecipeSettings` ABC with 12 subclasses |

## Quick Start

```python
from py2dataiku import convert, convert_with_llm

# Rule-based conversion (fast, offline)
flow = convert("""
import pandas as pd
df = pd.read_csv('data.csv')
df = df.dropna()
result = df.groupby('category').agg({'amount': 'sum'})
""")

# LLM-based conversion (more accurate)
flow = convert_with_llm(code, provider="anthropic")

# Inspect the result
print(flow.get_summary())
print(flow.visualize(format="ascii"))

# Export
flow.to_json()
flow.to_yaml()
```

## Package Structure

```
py2dataiku
├── convert()                    # Rule-based conversion
├── convert_with_llm()           # LLM-based conversion
├── convert_file()               # File-based rule conversion
├── convert_file_with_llm()      # File-based LLM conversion
├── Py2Dataiku                   # Main converter class
├── models
│   ├── DataikuFlow              # Flow container
│   ├── DataikuRecipe            # Recipe node
│   ├── DataikuDataset           # Dataset node
│   ├── PrepareStep              # Processor step
│   ├── FlowGraph                # DAG representation
│   ├── RecipeSettings           # Typed settings (ABC)
│   ├── DataikuScenario          # Automation
│   ├── DataikuMetric            # Metrics
│   └── APIEndpoint              # MLOps
├── llm
│   ├── LLMCodeAnalyzer          # AI analysis
│   ├── AnthropicProvider        # Claude integration
│   └── OpenAIProvider           # GPT integration
├── visualizers
│   ├── SVGVisualizer            # Pixel-accurate
│   ├── HTMLVisualizer           # Interactive
│   ├── ASCIIVisualizer          # Terminal
│   ├── MermaidVisualizer        # GitHub/Notion
│   └── PlantUMLVisualizer       # Documentation
├── exporters
│   └── DSSExporter              # DSS project export
├── plugins
│   └── PluginRegistry           # Extension system
├── config
│   └── Py2DataikuConfig         # Configuration
└── exceptions
    └── Py2DataikuError          # Error hierarchy
```
