# py-iku

Convert Python data processing code to Dataiku DSS recipes and flows.

## Overview

**py-iku** is a Python library that converts Python data processing code (pandas, numpy, scikit-learn) to Dataiku DSS recipes, flows, and visual diagrams. The library supports two analysis modes:

- **LLM-based (recommended)**: Uses AI (Anthropic/OpenAI) to understand code semantics
- **Rule-based (fallback)**: Uses AST pattern matching for offline conversion

Generates Dataiku DSS 14 compatible configurations with support for:
- 37 recipe types (visual, code, ML, plugin)
- 122 processor types (prepare recipe steps)

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

# Rule-based conversion (fast, offline) — accepts a code string OR a .py path
flow = convert("script.py")           # path-string
flow = convert(Path("script.py"))     # pathlib.Path
flow = convert("""                    # inline code
import pandas as pd
df = pd.read_csv('data.csv').dropna()
result = df.groupby('category').agg({'amount': 'sum'})
""")

# LLM-based conversion (more accurate, requires API key)
# Runs at temperature=0.0 by default for deterministic output.
# Store ANTHROPIC_API_KEY in .env.local (gitignored) or as an env var.
flow = convert_with_llm("script.py", provider="anthropic")

# Optional progress callback — useful for long-running LLM calls
def show_progress(phase, info):
    print(f"[{phase}] {info}")

flow = convert_with_llm("script.py", on_progress=show_progress)

# Save in any format — extension auto-detects
flow.save("flow.json")
flow.save("flow.yaml")
flow.save("flow.svg")
flow.save("flow.html")
flow.save("flow.png")
flow.save("flow.pdf")
flow.save("flow.puml")   # PlantUML
flow.save("flow.txt")    # ASCII
flow.save("flow.md")     # Mermaid

# Load back from JSON or YAML
flow2 = DataikuFlow.load("flow.json")

# Compare two flows (e.g. rule-based vs LLM output)
delta = flow.diff(flow2)

# Or render directly
print(flow.visualize(format="ascii"))
flow                                  # renders inline in Jupyter / JupyterLab
```

CLI:

```bash
py2dataiku script.py                  # bare-file invocation (rule-based)
py2dataiku script.py --llm            # use LLM (default provider: anthropic)
py2dataiku convert script.py --provider openai
```

## Supported Conversions

### pandas -> Dataiku Recipes

| pandas Operation | Dataiku Recipe |
|-----------------|----------------|
| `df.groupby().agg()` | GROUPING |
| `pd.merge()` / `df.merge()` | JOIN |
| `pd.concat()` | STACK |
| `df.drop_duplicates()` | DISTINCT |
| `df.sort_values()` | SORT |
| `df.pivot()` / `df.pivot_table()` | PIVOT |
| `df.rolling()` / `df.cumsum()` / `df.expanding()` | WINDOW |
| `df[cond]` and `df[~cond]` (boolean pair) | SPLIT (multi-output) |
| `df[condition]` (single branch) | FILTER (in PREPARE recipe) |
| `df.nlargest()` / `df.nsmallest()` | TOP_N |
| `df.describe()` / `df.info()` | GENERATE_STATISTICS |

### pandas -> Dataiku Processors (inside PREPARE recipes)

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
| `df.round()` / `df.abs()` / `df.clip()` | NUMERIC_TRANSFORM processors |
| `df[col] > value` / `< value` / etc. | FilterOnNumericRange |
| `df[col] == value` / `!= value` | FilterOnValue (FULL_STRING) |
| compound predicate `(a > 5) & (b < 10)` | FilterOnFormula (GREL) |

## Output Formats

`flow.save(path)` and `flow.visualize(format=...)` support the following formats:

| Extension / format name | Description |
|------------------------|-------------|
| `.json` / `json` | Machine-readable JSON export (round-trip with `DataikuFlow.load`) |
| `.yaml` / `.yml` / `yaml` | Machine-readable YAML export (round-trip with `DataikuFlow.load`) |
| `.svg` / `svg` | Pixel-accurate Dataiku-style vector diagram |
| `.html` / `html` | Interactive canvas with zoom/pan |
| `.png` / `png` | Raster image via matplotlib |
| `.pdf` / `pdf` | PDF via cairosvg |
| `.puml` / `plantuml` | PlantUML diagram |
| `.txt` / `ascii` | Terminal-friendly ASCII diagram |
| `.md` / `mermaid` | Mermaid diagram (GitHub/Notion compatible) |

## API Reference

### Main Functions

```python
# Rule-based conversion — accepts str, pathlib.Path, or path-string to .py file
convert(code: str | Path, optimize: bool = True) -> DataikuFlow

# LLM-based conversion
convert_with_llm(
    code: str | Path,
    provider: str = "anthropic",   # or "openai"
    api_key: str = None,           # falls back to ANTHROPIC_API_KEY / OPENAI_API_KEY env var
    model: str = None,             # uses provider default if omitted
    optimize: bool = True,
    flow_name: str = "converted_flow",
    on_progress=None,              # callable(phase: str, info: dict) -> None
    temperature: float = 0.0,      # 0.0 = deterministic; raise for more variety
) -> DataikuFlow

# File-path variants (same parameters as above)
convert_file(path: str, optimize: bool = True) -> DataikuFlow
convert_file_with_llm(path: str, ..., on_progress=None, temperature: float = 0.0) -> DataikuFlow
```

`on_progress` phases: `"start"`, `"analyzing"`, `"analyzed"`, `"generating"`, `"optimizing"`, `"done"`.

### DataikuFlow Methods

```python
# Visualization
flow.visualize(format="svg")          # returns string (or bytes for png)
flow.to_ascii()                       # shorthand
flow.to_svg(output_path=None)         # shorthand, returns SVG string
flow.to_html(output_path=None)        # shorthand, returns HTML string

# Serialization
flow.to_dict(include_timestamp=True)  # dict; pass False when diffing
flow.to_json()                        # JSON string
flow.to_yaml()                        # YAML string

# File I/O (format auto-detected from extension)
flow.save(path, format=None)          # write to file
DataikuFlow.load(path, format=None)   # classmethod — reads .json or .yaml/.yml

# Comparison
flow.diff(other)                      # structural diff; returns dict with added/removed/changed/equivalent

# Inspection
flow.validate()                       # returns {valid, errors, warnings, info}
flow.get_summary()                    # text summary string
flow.graph                            # FlowGraph DAG (topological sort, cycle detection)
```

### LLM Provider Notes

- `AnthropicProvider` defaults to `temperature=0.0` for deterministic output.
- Anthropic prompt caching is enabled by default (pass `disable_cache=True` to opt out). Caching reduces token cost by ~70-80% across repeated calls with the same system prompt within a 5-minute window.
- A missing API key raises `ConfigurationError` (not `ValueError`).
- Store credentials in `.env.local` (gitignored) and load with `python-dotenv` or similar.

## Examples

```python
from py2dataiku.examples.recipe_examples import RECIPE_EXAMPLES
from py2dataiku.examples.processor_examples import PROCESSOR_EXAMPLES
from py2dataiku.examples.combination_examples import COMBINATION_EXAMPLES
```

## Development

```bash
# Run tests (1807 tests)
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ --cov=py2dataiku --cov-report=html

# Lint / format
ruff check py2dataiku/
black py2dataiku/ tests/
```

## License

MIT
