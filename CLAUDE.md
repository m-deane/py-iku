# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

**py-iku** is a Python library that converts Python data processing code (pandas, numpy, scikit-learn) to Dataiku DSS recipes, flows, and visual diagrams. Two analysis modes:

1. **LLM-based (recommended)**: Uses AI (Anthropic/OpenAI) to understand code semantics
2. **Rule-based (fallback)**: Uses AST pattern matching for offline conversion

Targets Dataiku DSS 14 with 37 recipe types, 122 processor types, and 122 processor catalog entries.

## Quick Reference

### Running Tests
```bash
# All tests (1693 tests)
python -m pytest tests/ -v

# Single test file
python -m pytest tests/test_py2dataiku/test_recipe_examples.py -v

# Single test function
python -m pytest tests/test_py2dataiku/test_api.py::test_convert_basic -v

# With coverage
python -m pytest tests/ --cov=py2dataiku --cov-report=html
```

### Basic Usage
```python
from py2dataiku import convert, convert_with_llm, convert_file

# Rule-based conversion
flow = convert("import pandas as pd\ndf = pd.read_csv('data.csv')\ndf = df.dropna()")

# LLM-based conversion (requires API key)
flow = convert_with_llm(code, provider="anthropic")

# File-based conversion
flow = convert_file("pipeline.py")

# Visualization (svg, html, ascii, plantuml, mermaid)
print(flow.visualize(format="ascii"))

# Serialization round-trip
d = flow.to_dict()
flow2 = DataikuFlow.from_dict(d)
```

## Architecture

```
py2dataiku/
├── __init__.py              # Public API: convert(), convert_with_llm(), convert_file(), Py2Dataiku
├── exceptions.py            # Py2DataikuError hierarchy (7 exception types)
├── config.py                # Py2DataikuConfig, supports toml/yaml/rc config files + env vars
├── cli.py                   # CLI entry point (py2dataiku command)
├── parser/                  # Rule-based code analysis
│   ├── ast_analyzer.py      # CodeAnalyzer - AST pattern matching
│   ├── pattern_matcher.py   # PatternMatcher
│   └── dataflow_tracker.py  # DataflowTracker - variable lineage
├── llm/                     # LLM-based analysis
│   ├── analyzer.py          # LLMCodeAnalyzer
│   ├── providers.py         # AnthropicProvider, OpenAIProvider, MockProvider
│   └── schemas.py           # AnalysisResult, DataStep, OperationType
├── generators/              # Flow generation
│   ├── base_generator.py    # BaseFlowGenerator ABC (shared logic)
│   ├── flow_generator.py    # FlowGenerator (rule-based, extends BaseFlowGenerator)
│   ├── llm_flow_generator.py # LLMFlowGenerator (LLM-based, extends BaseFlowGenerator)
│   ├── recipe_generator.py
│   └── diagram_generator.py # Mermaid/Graphviz diagrams
├── models/                  # Core data models
│   ├── dataiku_flow.py      # DataikuFlow (main output), FlowZone, DAG graph property
│   ├── dataiku_recipe.py    # DataikuRecipe, RecipeType (37 types)
│   ├── dataiku_dataset.py   # DataikuDataset, DatasetType, DatasetConnectionType (13 types)
│   ├── prepare_step.py      # PrepareStep, ProcessorType (122 types)
│   ├── recipe_settings.py   # RecipeSettings ABC with 12 subclasses (composition pattern)
│   ├── flow_graph.py        # FlowGraph DAG: topological_sort, detect_cycles, subgraphs
│   ├── dataiku_scenario.py  # DataikuScenario, triggers, steps, reporters
│   ├── dataiku_metrics.py   # DataikuMetric, DataikuCheck, DataQualityRule
│   ├── dataiku_mlops.py     # APIEndpoint, ModelVersion, DriftConfig
│   └── transformation.py
├── visualizers/             # Visualization engines
│   ├── svg_visualizer.py    # Pixel-accurate Dataiku styling
│   ├── html_visualizer.py   # Interactive canvas
│   ├── ascii_visualizer.py  # Terminal-friendly
│   ├── mermaid_visualizer.py # GitHub/Notion compatible
│   ├── plantuml_visualizer.py
│   ├── themes.py            # DATAIKU_LIGHT, DATAIKU_DARK
│   ├── icons.py             # Recipe/dataset icons
│   └── layout_engine.py     # DAG layout algorithm
├── mappings/                # pandas/numpy → Dataiku mappings
│   ├── pandas_mappings.py   # Method-level mapping rules
│   └── processor_catalog.py # ProcessorCatalog class (122 entries)
├── optimizer/               # Flow optimization
│   ├── flow_optimizer.py    # Merges consecutive Prepare recipes, removes orphan datasets
│   └── recipe_merger.py
├── exporters/               # DSS project export
│   └── dss_exporter.py      # DSSExporter, DSSProjectConfig
├── plugins/                 # Extension system
│   └── registry.py          # PluginRegistry (instance-based with global default)
├── utils/
│   └── validation.py
└── examples/                # Comprehensive examples library
    ├── recipe_examples.py       # 35+ recipe examples
    ├── processor_examples.py    # 60+ processor examples
    ├── settings_examples.py     # 50+ settings examples
    ├── combination_examples.py  # 22+ combination examples
    └── *_pipelines.py           # basic, intermediate, advanced, complex
```

## Key Design Patterns

### Exception Hierarchy
```
Py2DataikuError
├── ConversionError
│   └── InvalidPythonCodeError
├── ProviderError
│   └── LLMResponseParseError
├── ValidationError
├── ExportError
└── ConfigurationError
```

### Generator Inheritance
`BaseFlowGenerator` (ABC) provides shared `_sanitize_name()`, `_optimize_flow()`, `_merge_prepare_recipes()`. Both `FlowGenerator` and `LLMFlowGenerator` extend it, eliminating code duplication.

### DataikuFlow Features
- **DAG graph**: `flow.graph` returns a `FlowGraph` with topological sort, cycle detection, disconnected subgraph discovery
- **Round-trip serialization**: `to_dict()`/`from_dict()`, `to_json()`/`from_json()`, `to_yaml()`/`from_yaml()`
- **Iteration protocol**: `len(flow)`, `for recipe in flow`
- **Jupyter integration**: `_repr_svg_()` for inline display
- **Column lineage**: `get_column_lineage()` traces columns through recipes
- **Flow zones**: Logical grouping via `FlowZone` dataclass

### Recipe Settings (Composition)
`RecipeSettings` ABC with typed subclasses: `PrepareSettings`, `GroupingSettings`, `JoinSettings`, `WindowSettings`, `PivotSettings`, `SplitSettings`, `SortSettings`, `StackSettings`, `SamplingSettings`, `TopNSettings`, `DistinctSettings`, `PythonSettings`. Composed into `DataikuRecipe.settings`.

### ProcessorCatalog
Instance-based `ProcessorCatalog` class (not a flat dict). Access via:
```python
from py2dataiku.mappings.processor_catalog import ProcessorCatalog
catalog = ProcessorCatalog()
catalog.list_processors()  # all 122 entries
catalog.get_processor("COLUMN_RENAMER")
```

### PluginRegistry
Instance-based with backward-compatible global default:
```python
from py2dataiku.plugins import PluginRegistry, register_recipe_handler
# Global convenience functions still work
register_recipe_handler("custom", handler_fn)
# Or use instance
registry = PluginRegistry()
registry.register_recipe_handler("custom", handler_fn)
```

## Development Guidelines

### Adding New Recipe Types
1. Add to `RecipeType` enum in `models/dataiku_recipe.py`
2. Add pandas mapping in `mappings/pandas_mappings.py`
3. Add `RecipeSettings` subclass in `models/recipe_settings.py`
4. Add example in `examples/recipe_examples.py`
5. Add test in `tests/test_py2dataiku/test_recipe_examples.py`

### Adding New Processor Types
1. Add to `ProcessorType` enum in `models/prepare_step.py`
2. Add entry in `ProcessorCatalog` in `mappings/processor_catalog.py`
3. Add example in `examples/processor_examples.py`
4. Add test in `tests/test_py2dataiku/test_processor_examples.py`

### pandas → Dataiku Mapping Quick Reference

**Recipes:**
- `df.groupby().agg()` → GROUPING
- `pd.merge()` / `df.merge()` → JOIN
- `pd.concat()` → STACK
- `df.drop_duplicates()` → DISTINCT
- `df.sort_values()` → SORT
- `df.pivot()` / `df.pivot_table()` → PIVOT
- `df.rolling()` / `df.cumsum()` → WINDOW
- `df.nlargest()` / `df.nsmallest()` → TOP_N
- `df[condition]` → SPLIT or FILTER processor
- Other transformations → PREPARE recipe with processors

**Processors (selected):**
- `df.rename()` → COLUMN_RENAMER
- `df.fillna()` → FILL_EMPTY_WITH_VALUE
- `df.dropna()` → REMOVE_ROWS_ON_EMPTY
- `df['col'].str.upper()` → STRING_TRANSFORMER (TO_UPPER)
- `df['col'].astype()` → TYPE_SETTER
- `pd.to_datetime()` → DATE_PARSER
- `pd.cut()` / `pd.qcut()` → BINNER
- `pd.get_dummies()` → CATEGORICAL_ENCODER

## Examples Registry

```python
from py2dataiku.examples.recipe_examples import RECIPE_EXAMPLES, get_recipe_example
from py2dataiku.examples.processor_examples import PROCESSOR_EXAMPLES, get_processor_example
from py2dataiku.examples.settings_examples import SETTINGS_EXAMPLES
from py2dataiku.examples.combination_examples import COMBINATION_EXAMPLES
```

## File Organization Rules

- All source code in `py2dataiku/`
- All tests in `tests/test_py2dataiku/`
- Examples in `py2dataiku/examples/`
- Plans and analysis documents in `.claude_plans/`

## Dependencies

- **pyyaml**: YAML export (required)
- **anthropic** (optional): LLM analysis with Claude
- **openai** (optional): LLM analysis with GPT
- **cairosvg** (optional): PNG/PDF export from SVG

## Common Gotchas

1. **Version**: Resolved via `importlib.metadata` at runtime; fallback `0.3.0` in `__init__.py`. Canonical version is in `pyproject.toml`.
2. **LLM vs Rule-based**: LLM mode requires API key but handles complex/ambiguous code better. Rule-based is fast, offline, deterministic.
3. **Recipe vs Processor**: Recipes are top-level flow nodes; processors are steps within PREPARE recipes.
4. **Enums**: Always use enum values from models, not raw strings.
5. **BaseFlowGenerator**: Both generators inherit from this ABC. Shared logic lives here, not duplicated.
6. **ProcessorCatalog**: Class-based (not dict). Use `ProcessorCatalog()` instance methods.
7. **FlowGraph**: Access via `flow.graph`. Supports topological sort, cycle detection. Don't manipulate the adjacency list directly.
