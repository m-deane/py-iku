# py-iku

Convert Python data processing code to Dataiku DSS recipes and flows.

## Overview

**py-iku** is a Python library that converts Python data processing code (pandas, numpy, scikit-learn) to Dataiku DSS recipes, flows, and visual diagrams. The library supports two analysis modes:

- **LLM-based (recommended)**: Uses AI (Anthropic/OpenAI) to understand code semantics
- **Rule-based (fallback)**: Uses AST pattern matching for offline conversion

Generates Dataiku DSS 14 compatible configurations with support for:
- 34+ recipe types (visual, code, ML, plugin)
- 76+ processor types (prepare recipe steps)

## Installation

```bash
pip install py-iku
```

For LLM-based analysis:
```bash
pip install py-iku[llm]  # includes anthropic and openai
```

## Quick Start

```python
from py2dataiku import convert, convert_with_llm

# Rule-based conversion (fast, offline)
code = '''
import pandas as pd
df = pd.read_csv('data.csv')
df = df.dropna()
result = df.groupby('category').agg({'amount': 'sum'})
'''
flow = convert(code)

# LLM-based conversion (more accurate, requires API key)
flow = convert_with_llm(code, provider="anthropic")

# Visualize the flow
print(flow.visualize(format="ascii"))
svg_content = flow.visualize(format="svg")
html_content = flow.visualize(format="html")
```

## Supported Conversions

### pandas → Dataiku Recipes

| pandas Operation | Dataiku Recipe |
|-----------------|----------------|
| `df.groupby().agg()` | GROUPING |
| `pd.merge()` / `df.merge()` | JOIN |
| `pd.concat()` | STACK |
| `df.drop_duplicates()` | DISTINCT |
| `df.sort_values()` | SORT |
| `df.pivot()` / `df.pivot_table()` | PIVOT |
| `df.rolling()` / `df.cumsum()` | WINDOW |
| `df[condition]` | SPLIT / FILTER |

### pandas → Dataiku Processors

| pandas Operation | Dataiku Processor |
|-----------------|-------------------|
| `df.rename()` | COLUMN_RENAMER |
| `df.drop()` | COLUMN_DELETER |
| `df.fillna()` | FILL_EMPTY_WITH_VALUE |
| `df.dropna()` | REMOVE_ROWS_ON_EMPTY |
| `df['col'].str.upper()` | STRING_TRANSFORMER |
| `df['col'].astype()` | TYPE_SETTER |
| `pd.to_datetime()` | DATE_PARSER |
| `pd.cut()` / `pd.qcut()` | BINNER |
| `pd.get_dummies()` | CATEGORICAL_ENCODER |

## Output Formats

- **SVG**: Pixel-accurate Dataiku styling
- **HTML**: Interactive canvas with zoom/pan
- **ASCII**: Terminal-friendly text diagrams
- **PlantUML**: UML-compatible diagrams
- **Mermaid**: Markdown-compatible diagrams
- **JSON/YAML**: Machine-readable export

## API Reference

### Main Functions

```python
# Rule-based conversion
convert(code: str) -> DataikuFlow

# LLM-based conversion
convert_with_llm(
    code: str,
    provider: str = "anthropic",  # or "openai"
    model: str = None,  # optional model override
) -> DataikuFlow
```

### DataikuFlow Methods

```python
flow.visualize(format="svg")  # Generate visualization
flow.to_dict()                # Export as dictionary
flow.to_json()                # Export as JSON string
flow.to_yaml()                # Export as YAML string
flow.validate()               # Check flow structure
flow.get_summary()            # Text summary
```

## Examples

The library includes comprehensive examples:

```python
from py2dataiku.examples.recipe_examples import RECIPE_EXAMPLES
from py2dataiku.examples.processor_examples import PROCESSOR_EXAMPLES
from py2dataiku.examples.combination_examples import COMBINATION_EXAMPLES
```

## Development

```bash
# Run tests
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ --cov=py2dataiku --cov-report=html
```

## License

MIT
