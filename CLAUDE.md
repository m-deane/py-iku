# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

**py-iku** is a Python library that converts Python data processing code (pandas, numpy, scikit-learn) to Dataiku DSS recipes, flows, and visual diagrams. Two analysis modes:

1. **LLM-based (recommended)**: Uses AI (Anthropic/OpenAI) to understand code semantics
2. **Rule-based (fallback)**: Uses AST pattern matching for offline conversion

Targets Dataiku DSS 14 with 37 recipe types, 122 processor types, and 122 processor catalog entries.

## Commands

```bash
# Install
pip install -e ".[dev]"         # dev dependencies (pytest, black, ruff, mypy)
pip install -e ".[llm]"         # LLM providers (anthropic, openai)
pip install -e ".[all]"         # everything

# Tests (1807 tests)
python -m pytest tests/ -v
python -m pytest tests/test_py2dataiku/test_recipe_examples.py -v      # single file
python -m pytest tests/test_py2dataiku/test_api.py::test_convert_basic -v  # single test
python -m pytest tests/ --cov=py2dataiku --cov-report=html             # with coverage

# Linting & formatting
ruff check py2dataiku/                   # lint
black py2dataiku/ tests/                 # format
isort py2dataiku/ tests/                 # sort imports
mypy py2dataiku/                         # type check

# CLI
py2dataiku script.py                     # convert a file (rule-based; bare-file form auto-routes to convert)
py2dataiku script.py --llm               # convert with LLM (default provider: anthropic)
py2dataiku convert script.py --llm --provider openai   # explicit provider
```

## Architecture

### Conversion Pipeline

The two analysis modes share a common output model but use different parsing and generation paths:

```
Rule-based:  Python code → CodeAnalyzer (AST) → FlowGenerator → DataikuFlow
LLM-based:   Python code → LLMCodeAnalyzer → LLMFlowGenerator → DataikuFlow
```

Both `FlowGenerator` and `LLMFlowGenerator` extend `BaseFlowGenerator` (ABC), which provides shared `_sanitize_name()`, `_optimize_flow()`, `_merge_prepare_recipes()`.

### Key Distinction: Recipes vs Processors

- **Recipes** are top-level flow nodes (GROUPING, JOIN, SORT, etc.) — each becomes a node in the DAG
- **Processors** are steps *within* a PREPARE recipe (COLUMN_RENAMER, FILL_EMPTY_WITH_VALUE, etc.)
- Most simple pandas transforms become processors inside a PREPARE recipe; only structural operations (groupby, merge, concat, etc.) become their own recipe types

### Core Models

- `DataikuFlow` — main output container. Has a `graph` property returning a `FlowGraph` DAG (topological sort, cycle detection, subgraph discovery). Supports round-trip serialization (`to_dict`/`from_dict`, `to_json`/`from_json`, `to_yaml`/`from_yaml`) plus `flow.save(path)` / `DataikuFlow.load(path)` with format auto-detect from extension. Renders inline in Classic Jupyter (`_repr_svg_`) and JupyterLab/VS Code (`_repr_mimebundle_`).
- `DataikuRecipe` — a single recipe node. `RecipeType` enum has 37 types. Settings use composition: `RecipeSettings` ABC with 12 typed subclasses (`PrepareSettings`, `GroupingSettings`, `JoinSettings`, etc.) composed into `recipe.settings`.
- `DataikuDataset` — input/output datasets. `DatasetType` and `DatasetConnectionType` enums.
- `PrepareStep` — a step within a PREPARE recipe. `ProcessorType` enum has 122 types.
- `FlowGraph` — DAG representation. Access via `flow.graph`. Don't manipulate the adjacency list directly.

### ProcessorCatalog

Instance-based class (not a flat dict):
```python
from py2dataiku.mappings.processor_catalog import ProcessorCatalog
catalog = ProcessorCatalog()
catalog.list_processors()       # all 122 entries
catalog.get_processor("COLUMN_RENAMER")
```

### PluginRegistry

Instance-based with backward-compatible global convenience functions:
```python
from py2dataiku.plugins import PluginRegistry, register_recipe_handler
register_recipe_handler("custom", handler_fn)  # global shorthand
```

### Exception Hierarchy
```
Py2DataikuError
├── ConversionError → InvalidPythonCodeError
├── ProviderError → LLMResponseParseError
├── ValidationError
├── ExportError
└── ConfigurationError
```

### Visualizers

`flow.visualize(format=...)` dispatches to format-specific visualizer classes in `visualizers/`. The `layout_engine.py` handles DAG positioning; `themes.py` defines DATAIKU_LIGHT/DATAIKU_DARK; `icons.py` provides recipe/dataset SVG icons.

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

### pandas → Dataiku Mapping (Non-Obvious Cases)

These mappings are less intuitive and worth knowing upfront:
- `pd.melt()` / `df.melt()` → PREPARE recipe with FOLD_MULTIPLE_COLUMNS processor (not its own recipe type)
- `df[condition]` → SPLIT recipe *or* FILTER processor depending on context
- `df.rolling()` / `df.cumsum()` / `df.expanding()` → WINDOW recipe
- `df.nlargest()` / `df.nsmallest()` → TOP_N recipe
- `df.round()` / `df.abs()` / `df.clip()` → PREPARE recipe with NUMERIC_TRANSFORM processors
- Other simple transforms → PREPARE recipe with corresponding processors

Full mapping tables are in `mappings/pandas_mappings.py`.

## File Organization

- Source code: `py2dataiku/`
- Tests: `tests/test_py2dataiku/`
- Examples library: `py2dataiku/examples/` (recipe, processor, settings, combination, pipeline examples)
- Plans and analysis: `.claude_plans/`
- Do not leave files in the root directory — organize into appropriate locations

## Gotchas

1. **Version**: Resolved via `importlib.metadata` at runtime; fallback `0.3.0` in `__init__.py`. Canonical version is in `pyproject.toml`.
2. **Enums**: Always use enum values from models (`RecipeType.GROUPING`), not raw strings.
3. **BaseFlowGenerator**: Shared logic lives in this ABC. Don't duplicate it into subclasses.
4. **ProcessorCatalog**: Class-based, not a dict. Use `ProcessorCatalog()` instance methods.
5. **FlowGraph**: Access via `flow.graph`. Supports topological sort, cycle detection. Don't touch the adjacency list directly.
6. **Config**: `Py2DataikuConfig` supports toml/yaml/rc config files and environment variables.
