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

# Save to file
flow.to_svg("flow.svg")
flow.to_html("flow.html")
```

### PNG Export

The `"png"` format produces a publication-quality diagram using the DDODS visual design language (requires `pip install matplotlib`):

```python
# Returns PNG bytes
png_bytes = flow.visualize(format="png")

# Display in Jupyter
from IPython.display import Image, display
display(Image(png_bytes))

# Save to file
from py2dataiku.visualizers import MatplotlibVisualizer
MatplotlibVisualizer().render_to_file(flow, "flow_diagram.png")
```

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

## Export

```python
# JSON
json_str = flow.to_json()

# YAML
yaml_str = flow.to_yaml()

# Round-trip
from py2dataiku import DataikuFlow
flow2 = DataikuFlow.from_json(json_str)

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

# Requires ANTHROPIC_API_KEY environment variable
flow = convert_with_llm(code, provider="anthropic")

# Or with OpenAI
flow = convert_with_llm(code, provider="openai")

# With explicit API key
flow = convert_with_llm(code, provider="anthropic", api_key="sk-...")
```

## Convert from File

```python
from py2dataiku import convert_file, convert_file_with_llm

# Rule-based
flow = convert_file("pipeline.py")

# LLM-based
flow = convert_file_with_llm("pipeline.py", provider="anthropic")
```

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
converter.save_visualization(flow, "output.png")  # Requires cairosvg
```

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
