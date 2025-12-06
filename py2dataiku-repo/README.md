# py2dataiku

Convert Python data processing code to Dataiku DSS recipes and flows.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

**py2dataiku** analyzes Python code (pandas, numpy, scikit-learn) and generates equivalent Dataiku DSS recipe configurations, flow structures, and visual diagrams. It helps data teams migrate Python pipelines to Dataiku's visual interface or understand how Python operations map to Dataiku recipes.

### Key Features

- **LLM-powered analysis** (recommended): Uses Claude or GPT to semantically understand code intent
- **Rule-based fallback**: AST pattern matching for offline use
- **Multiple output formats**: JSON configs, YAML, Mermaid diagrams, GraphViz, ASCII art
- **Comprehensive recipe mapping**: Supports Prepare, Join, Grouping, Window, Split, Stack, Sort, Distinct, Top N, Sampling, Pivot, and Python recipes
- **30+ Prepare processors**: FillEmptyWithValue, ColumnRenamer, FilterOnValue, StringTransformer, TypeSetter, DateParser, and more

## Installation

```bash
pip install py2dataiku
```

Or install from source:

```bash
git clone https://github.com/YOUR_USERNAME/py2dataiku.git
cd py2dataiku
pip install -e .
```

## Quick Start

### LLM-based Conversion (Recommended)

```python
from py2dataiku import convert_with_llm

code = """
import pandas as pd

df = pd.read_csv('sales.csv')
df['date'] = pd.to_datetime(df['date'])
df = df.dropna(subset=['amount'])
df['amount'] = df['amount'].clip(lower=0)

summary = df.groupby('category').agg({
    'amount': 'sum',
    'quantity': 'mean'
}).reset_index()

summary.to_csv('sales_summary.csv')
"""

# Convert using Claude (requires ANTHROPIC_API_KEY env var)
flow = convert_with_llm(code, provider="anthropic")

# Or use OpenAI (requires OPENAI_API_KEY env var)
flow = convert_with_llm(code, provider="openai")

# View the generated flow
print(flow.get_summary())
print(flow.to_yaml())
```

### Rule-based Conversion (Offline)

```python
from py2dataiku import convert

code = """
import pandas as pd
df = pd.read_csv('data.csv')
df = df.dropna()
df['name'] = df['name'].str.lower()
result = df.groupby('category').agg({'value': 'sum'})
"""

flow = convert(code)
print(flow.get_summary())
```

### Generate Diagrams

```python
from py2dataiku import Py2Dataiku

converter = Py2Dataiku(provider="anthropic")
flow = converter.convert(code)

# Mermaid diagram (for GitHub, Notion, etc.)
print(converter.generate_diagram(flow, format="mermaid"))

# GraphViz DOT format
print(converter.generate_diagram(flow, format="graphviz"))

# ASCII art (for terminals)
print(converter.generate_diagram(flow, format="ascii"))
```

## Supported Mappings

### Python to Dataiku Recipe Types

| Python Pattern | Dataiku Recipe |
|---------------|----------------|
| `df['col'].fillna()`, `df['col'].str.lower()` | Prepare |
| `pd.merge(df1, df2)`, `df1.join(df2)` | Join |
| `pd.concat([df1, df2])` | Stack |
| `df.groupby().agg()` | Grouping |
| `df.rolling().mean()`, `df.cumsum()` | Window |
| `df.pivot()`, `df.melt()` | Pivot |
| `df[df['col'] > 0]`, `df.query()` | Split |
| `df.sort_values()` | Sort |
| `df.drop_duplicates()` | Distinct |
| `df.head()`, `df.nlargest()` | Top N |
| `df.sample()` | Sampling |
| Complex functions, ML code | Python Recipe |

### Prepare Recipe Processors

| Processor | Python Pattern |
|-----------|---------------|
| `FillEmptyWithValue` | `df['col'].fillna(value)` |
| `ColumnRenamer` | `df.rename(columns={...})` |
| `FilterOnValue` | `df[df['col'] == val]` |
| `RemoveRowsOnEmpty` | `df.dropna(subset=['col'])` |
| `ColumnCopier` | `df['new'] = df['old']` |
| `ColumnDeleter` | `df.drop(columns=['col'])` |
| `StringTransformer` | `df['col'].str.upper()` |
| `TypeSetter` | `df['col'].astype(int)` |
| `DateParser` | `pd.to_datetime(df['col'])` |
| `RoundColumn` | `df['col'].round(2)` |
| `ClipColumn` | `df['col'].clip(lower, upper)` |

See [full processor catalog](docs/processors.md) for all 30+ supported processors.

## API Reference

### Main Functions

```python
# LLM-based conversion (recommended)
convert_with_llm(
    code: str,
    provider: str = "anthropic",  # or "openai"
    api_key: str = None,          # uses env var if not provided
    model: str = None,            # uses provider default
    optimize: bool = True,
    flow_name: str = "converted_flow"
) -> DataikuFlow

# Rule-based conversion (offline)
convert(
    code: str,
    optimize: bool = True
) -> DataikuFlow
```

### Py2Dataiku Class

```python
from py2dataiku import Py2Dataiku

converter = Py2Dataiku(
    provider="anthropic",
    api_key=None,        # uses env var
    model=None,          # uses default
    use_llm=True         # set False for rule-based
)

# Convert code
flow = converter.convert(code, flow_name="my_flow")

# Get LLM analysis details
analysis = converter.analyze(code)
print(analysis.steps)
print(analysis.recommendations)

# Generate diagrams
diagram = converter.generate_diagram(flow, format="mermaid")
```

### DataikuFlow Object

```python
flow.get_summary()      # Human-readable summary
flow.to_json()          # JSON configuration
flow.to_yaml()          # YAML configuration
flow.to_dict()          # Python dictionary
flow.validate()         # Validate configuration
flow.recipes            # List of DataikuRecipe objects
flow.datasets           # List of DataikuDataset objects
```

## Configuration

### Environment Variables

```bash
# For Anthropic Claude
export ANTHROPIC_API_KEY="your-api-key"

# For OpenAI GPT
export OPENAI_API_KEY="your-api-key"
```

### Custom LLM Provider

```python
from py2dataiku import LLMCodeAnalyzer
from py2dataiku.llm.providers import AnthropicProvider

provider = AnthropicProvider(
    api_key="your-key",
    model="claude-sonnet-4-20250514",
    max_tokens=4096
)

analyzer = LLMCodeAnalyzer(provider=provider)
analysis = analyzer.analyze(code)
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=py2dataiku --cov-report=html

# Run specific test file
pytest tests/test_py2dataiku/test_llm.py -v
```

## Project Structure

```
py2dataiku/
├── __init__.py              # Main entry point
├── llm/                     # LLM-based analysis (recommended)
│   ├── analyzer.py          # LLMCodeAnalyzer
│   ├── providers.py         # Anthropic, OpenAI, Mock providers
│   └── schemas.py           # DataStep, AnalysisResult models
├── parser/                  # Rule-based analysis (fallback)
│   ├── ast_analyzer.py      # AST parsing
│   ├── pattern_matcher.py   # Operation patterns
│   └── dataflow_tracker.py  # Data lineage tracking
├── generators/              # Output generation
│   ├── flow_generator.py    # Rule-based flow generation
│   ├── llm_flow_generator.py # LLM-based flow generation
│   ├── diagram_generator.py # Mermaid, GraphViz, ASCII
│   └── recipe_generator.py  # Recipe configurations
├── models/                  # Data models
│   ├── dataiku_flow.py      # Flow representation
│   ├── dataiku_recipe.py    # Recipe types
│   ├── dataiku_dataset.py   # Dataset nodes
│   └── prepare_step.py      # Prepare processors
├── mappings/                # Pattern mappings
│   ├── pandas_mappings.py   # pandas operations
│   └── processor_catalog.py # Dataiku processors
├── optimizer/               # Flow optimization
│   ├── flow_optimizer.py    # Recipe ordering
│   └── recipe_merger.py     # Merge compatible ops
└── examples/                # Demo scripts
    ├── demo.py              # Rule-based demo
    └── llm_demo.py          # LLM-based demo
```

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Dataiku DSS](https://www.dataiku.com/) for the recipe/flow paradigm
- [Anthropic Claude](https://www.anthropic.com/) and [OpenAI](https://openai.com/) for LLM capabilities
- The Python AST module for code analysis capabilities
