# Quick Start

## Convert Python Code

```python
from py2dataiku import convert

flow = convert("""
import pandas as pd

# Read data
df = pd.read_csv('customers.csv')
orders = pd.read_csv('orders.csv')

# Clean data
df = df.dropna(subset=['email'])
df['name'] = df['name'].str.strip()

# Join
merged = df.merge(orders, on='customer_id', how='left')

# Aggregate
summary = merged.groupby('region').agg({
    'amount': 'sum',
    'customer_id': 'nunique'
})

# Save
summary.to_csv('regional_summary.csv')
""")

print(flow.get_summary())
```

`convert` is polymorphic on its input — pass a source string, a path
string ending in `.py`, or a `pathlib.Path`:

```python
from pathlib import Path
from py2dataiku import convert

flow = convert("script.py")           # path-string
flow = convert(Path("script.py"))     # Path object
flow = convert(open("script.py").read())  # source string
```

The same applies to `convert_with_llm`.

## Visualize the Flow

```python
# Terminal-friendly
print(flow.visualize(format="ascii"))

# Pixel-accurate Dataiku styling
svg = flow.visualize(format="svg")

# Interactive HTML
html = flow.visualize(format="html")

# GitHub/Notion compatible
mermaid = flow.visualize(format="mermaid")
```

### Saving Visualizations

`flow.save()` auto-detects the format from the file extension, so you
rarely need to call format-specific methods directly:

```python
flow.save("flow.svg")        # SVG
flow.save("flow.html")       # interactive HTML
flow.save("flow.json")       # serialized flow (round-trips with load)
flow.save("flow.yaml")       # serialized flow
flow.save("flow.png")        # PNG (uses cairosvg)
flow.save("flow.md")         # Mermaid (.md/.mermaid)
flow.save("flow.puml")       # PlantUML
```

If you need an explicit format (e.g. saving Mermaid to a `.txt`):

```python
flow.save("diagram.txt", format="mermaid")
```

### PNG Export

There are two PNG paths, optimised for different use cases:

```python
# 1. Publication-quality matplotlib rendering — requires `pip install matplotlib`.
#    Returns PNG bytes, ideal for inline display.
png_bytes = flow.visualize(format="png")

from IPython.display import Image, display
display(Image(png_bytes))

# 2. SVG-to-PNG conversion via cairosvg — requires `pip install cairosvg`.
#    Used by flow.save("flow.png") and flow.to_png().
flow.save("flow.png")
flow.to_png("flow.png", scale=2.0)
```

Use `flow.visualize(format="png")` (matplotlib) when you want
DDODS-styled output for reports/notebooks; use `flow.to_png()` /
`flow.save("flow.png")` (cairosvg) when you want a faithful
pixel rendering of the SVG diagram.

### Jupyter / JupyterLab / VS Code Notebooks

A `DataikuFlow` renders inline as an SVG diagram — just put the flow as
the last expression in a cell:

```python
flow  # renders the SVG diagram in the notebook
```

This works in Classic Jupyter (via `_repr_svg_`) and in JupyterLab 3+
and VS Code notebooks (via `_repr_mimebundle_`); no extra setup is
required.

## Inspect the Flow

```python
# Datasets
for ds in flow.datasets:
    print(f"{ds.name} ({ds.dataset_type.value})")

# Recipes
for recipe in flow.recipes:
    print(f"{recipe.name}: {recipe.recipe_type.value}")
    print(f"  Inputs: {recipe.inputs}")
    print(f"  Outputs: {recipe.outputs}")

# Validate
result = flow.validate()
print(result)
```

## Flow Optimization

The `optimize=True` flag (the default) merges consecutive Prepare recipes, removes orphan intermediate datasets, and reorders steps for efficiency.

```python
# Optimization is on by default
flow = convert(code, optimize=True)

# Check what the optimizer did
for note in flow.optimization_notes:
    print(note)
```

## Export and Round-trip

```python
# Serialize
json_str = flow.to_json()
yaml_str = flow.to_yaml()

# Save and load — extension auto-detected
flow.save("flow.json")

from py2dataiku import DataikuFlow
flow2 = DataikuFlow.load("flow.json")     # round-trip
flow2 = DataikuFlow.load("flow.yaml")     # also works

# DSS project bundle
from py2dataiku import export_to_dss
export_to_dss(flow, "output/my_project", create_zip=True)
```

## Dataiku API Output

Generate payloads compatible with the Dataiku DSS API.

```python
# Per-recipe API dicts
for recipe in flow.recipes:
    api_dict = recipe.to_api_dict()
    print(api_dict)
    # Output uses DSS conventions:
    #   - type "shaker" for PREPARE recipes, "vstack" for STACK
    #   - Nested I/O: {"main": {"items": [{"ref": "dataset_name", "deps": []}]}}
    #   - Settings under "params" key

# All recipes at once
configs = flow.to_recipe_configs()
```

## Use LLM for Better Results

```python
from py2dataiku import convert_with_llm

# Reads ANTHROPIC_API_KEY from the environment
# (load .env.local first — see Installation guide).
# temperature defaults to 0.0, so conversions are deterministic;
# bump it up if you specifically want sampling variability.
flow = convert_with_llm(code, provider="anthropic")

# OpenAI
flow = convert_with_llm(code, provider="openai")

# Pass a key explicitly
flow = convert_with_llm(code, provider="anthropic", api_key="sk-ant-...")
```

### Progress Callback

For long LLM calls, pass an `on_progress` callback to surface progress
to the user. py-iku invokes it at each pipeline phase (`start`,
`analyzing`, `analyzed`, `generating`, `optimizing`, `done`):

```python
def show(phase: str, info: dict) -> None:
    print(f"[{phase}] {info}")

flow = convert_with_llm(code, provider="anthropic", on_progress=show)
```

If the callback raises, the conversion still completes — exceptions
inside `on_progress` are swallowed deliberately so user-facing UI bugs
can never break the conversion itself.

### Prompt Caching

When you use the Anthropic provider, py-iku marks the system prompt
with `cache_control: ephemeral`. Repeat calls within Anthropic's cache
window pay roughly 10% of the input-token cost for the cached portion,
which makes iterative work (and the smoke-test script) materially
cheaper.

### Worked Example

`scripts/llm_smoke_test.py` is a real end-to-end smoke test against the
Anthropic and OpenAI APIs. It loads `ANTHROPIC_API_KEY` (or
`OPENAI_API_KEY`) from `.env.local`, runs `convert_with_llm` against
several representative pandas snippets, and validates the resulting
flows. Use it as a reference for setting up the LLM path locally.

## Convert from File

```python
from py2dataiku import convert_file, convert_file_with_llm

# Rule-based
flow = convert_file("pipeline.py")

# LLM-based
flow = convert_file_with_llm("pipeline.py", provider="anthropic")
```

`convert("pipeline.py")` and `convert(Path("pipeline.py"))` are
shortcuts for the same thing — see the polymorphic input note above.

## Use the Class Interface

```python
from py2dataiku import Py2Dataiku

# LLM mode (falls back to rule-based if no API key)
converter = Py2Dataiku(provider="anthropic")

# Rule-based only
converter = Py2Dataiku(use_llm=False)

# Convert
flow = converter.convert(code)

# Visualize
converter.save_visualization(flow, "output.svg")
converter.save_visualization(flow, "output.html")
converter.save_visualization(flow, "output.png")  # uses cairosvg
```

## CLI

The CLI auto-routes a bare `.py` file to `convert`, so the simplest
form is:

```bash
py2dataiku script.py
py2dataiku script.py --llm anthropic
py2dataiku script.py -o flow.svg
```

These are shorthand for `py2dataiku convert script.py ...`.

## Column Lineage

```python
# Trace a column through the flow
lineage = flow.get_column_lineage("amount")
print(lineage)

# Trace from a specific dataset
lineage = flow.get_column_lineage("amount", dataset="output_data")
print(lineage)
```

## DAG Analysis

```python
graph = flow.graph

# Execution order
order = graph.topological_sort()

# Check for cycles
cycles = graph.detect_cycles()

# Independent sub-pipelines
subgraphs = graph.find_disconnected_subgraphs()
```

## How py-iku Translates Filters

DataFrame filtering maps to one of three Prepare processors depending
on the predicate shape:

- **Numeric comparisons** (`df[df.x > 100]`, `df[df.x.between(1, 5)]`)
  use `FilterOnNumericRange` — the DSS-canonical processor for numeric
  bounds.
- **Equality on a single column** (`df[df.country == "US"]`) uses
  `FilterOnValue`.
- **Compound predicates** (`df[(a > 1) & (b == 2)]`) translate into a
  GREL formula via `FilterOnFormula`.

In all three cases the filter is a step inside a PREPARE recipe — only
mutually-exclusive splits (one input → multiple outputs by predicate)
become standalone SPLIT recipes.

## Configuration

Create a `py2dataiku.toml` in your project root:

```toml
[py2dataiku]
default_provider = "anthropic"
project_key = "MY_PROJECT"
optimize = true
optimization_level = 2
default_format = "svg"
```

Then configuration is auto-discovered:

```python
from py2dataiku import load_config
config = load_config()
```
