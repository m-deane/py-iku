# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

**py-iku** is a Python library that converts Python data processing code (pandas, numpy, scikit-learn) to Dataiku DSS recipes, flows, and visual diagrams. Two analysis modes:

1. **LLM-based (recommended)**: Uses AI (Anthropic/OpenAI) to understand code semantics
2. **Rule-based (fallback)**: Uses AST pattern matching for offline conversion

Targets Dataiku DSS 14 with 37 recipe types, 100 processor types (with phantom-name aliases collapsing to canonical DSS values), and 101 processor catalog entries.

## Commands

```bash
# Install
pip install -e ".[dev]"         # dev dependencies (pytest, black, ruff, mypy)
pip install -e ".[llm]"         # LLM providers (anthropic, openai)
pip install -e ".[all]"         # everything

# Tests (~2381 tests)
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

# LLM credentials & smoke test
# Put ANTHROPIC_API_KEY / OPENAI_API_KEY in `.env.local` (gitignored).
python scripts/llm_smoke_test.py         # round-trip a small snippet through the LLM provider
```

## Architecture

### Conversion Pipeline

The two analysis modes share a common output model but use different parsing and generation paths:

```
Rule-based:  Python code → CodeAnalyzer (AST) → FlowGenerator → DataikuFlow
LLM-based:   Python code → LLMCodeAnalyzer → LLMFlowGenerator → DataikuFlow
```

Both `FlowGenerator` and `LLMFlowGenerator` extend `BaseFlowGenerator` (ABC), which provides shared `_sanitize_name()`, `_optimize_flow()`, `_merge_prepare_recipes()`. The optimizer's PREPARE/WINDOW merging is DAG-aware (not list-position based) and skips merges across fan-out points.

### Public API (LLM)

```python
convert_with_llm(code, provider="anthropic", api_key=None, model=None,
                 optimize=True, flow_name="converted_flow",
                 on_progress=None, temperature=0.0)
convert_file_with_llm(path, ...)  # same kwargs
```

`on_progress` is an optional callback (status-string updates). `temperature=0.0` is the default for determinism — pass e.g. `temperature=0.7` for non-deterministic output. The Anthropic system prompt is auto-generated from `ProcessorCatalog` (~89 processors across 17 categories) plus mapping rules and few-shot examples; **prompt caching is enabled by default** (~80% input-cost savings on repeat calls — pass `disable_cache=True` on the analyzer to opt out). `AnalysisResult.usage` surfaces token counts including `cache_read_input_tokens`. Processor names returned by the LLM are validated against `ProcessorCatalog` post-parse.

### Key Distinction: Recipes vs Processors

- **Recipes** are top-level flow nodes (GROUPING, JOIN, SORT, etc.) — each becomes a node in the DAG
- **Processors** are steps *within* a PREPARE recipe (COLUMN_RENAMER, FILL_EMPTY_WITH_VALUE, etc.)
- Most simple pandas transforms become processors inside a PREPARE recipe; only structural operations (groupby, merge, concat, etc.) become their own recipe types

### Core Models

- `DataikuFlow` — main output container. `graph` property returns a `FlowGraph` DAG (topological sort, cycle detection, subgraph discovery). Round-trip serialization: `to_dict(include_timestamp=True)`/`from_dict`, `to_json`/`from_json`, `to_yaml`/`from_yaml`, plus `flow.save(path)` / `DataikuFlow.load(path)` with format auto-detect from extension. `flow.diff(other)` returns a structured comparison dict. Renders inline in Classic Jupyter (`_repr_svg_`), Jupyter notebooks via HTML (`_repr_html_`), and JupyterLab/VS Code (`_repr_mimebundle_`).
- `DataikuRecipe` — a single recipe node. `RecipeType` enum has 37 types. Settings use composition: `RecipeSettings` ABC with 12 typed subclasses (`PrepareSettings`, `GroupingSettings`, `JoinSettings`, etc.) composed into `recipe.settings`.
- `DataikuDataset` — input/output datasets. `DatasetType` and `DatasetConnectionType` enums.
- `PrepareStep` — a step within a PREPARE recipe. `ProcessorType` enum has 100 canonical types (phantom names alias to canonical members — see Gotchas).
- `FlowGraph` — DAG representation. Access via `flow.graph`. Don't manipulate the adjacency list directly.

### ProcessorCatalog

Instance-based class (not a flat dict):
```python
from py2dataiku.mappings.processor_catalog import ProcessorCatalog
catalog = ProcessorCatalog()
catalog.list_processors()       # 101 entries
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
- `df[df.x > N]` (numeric comparison) → PREPARE with `FilterOnNumericRange`
- `df[df.x == 'foo']` (equality) → PREPARE with `FilterOnValue` using `FULL_STRING` match
- `df[(a > 5) & (b < 10)]` (compound) → PREPARE with `FilterOnFormula` using a GREL expression
- `df[cond]` + `df[~cond]` (complementary) → ONE multi-output `SPLIT` recipe (not two filters)
- `df[cond]` alone → SPLIT recipe *or* FILTER processor depending on context
- `df.describe()` / `df.info()` → `GENERATE_STATISTICS` recipe (a real DSS recipe, not a Python recipe)
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
7. **Phantom enum aliases**: 19 `ProcessorType` and 4 `AggregationFunction` phantom names are aliased to canonical DSS values, so identity checks collapse:
   `ProcessorType.ABS_COLUMN is ProcessorType.CREATE_COLUMN_WITH_GREL` evaluates `True`; `AggregationFunction.MEAN is AggregationFunction.AVG`, `NUNIQUE is COUNTD`, etc. Treat the canonical name as the source of truth.
8. **LLM prompt caching**: enabled by default on the Anthropic path — pass `disable_cache=True` to opt out. Inspect `AnalysisResult.usage["cache_read_input_tokens"]` to confirm cache hits.
9. **LLM determinism**: `temperature=0.0` is the default for `convert_with_llm` / `convert_file_with_llm`. Pass `temperature=0.7` (or similar) for non-deterministic output.
10. **`ConfigurationError`**: raised for missing API keys; multi-inherits from `ValueError` for backward compatibility (older code catching `ValueError` still works).
11. **Jupyter rendering**: `_repr_svg_` (Classic Jupyter) and `_repr_mimebundle_` (JupyterLab / VS Code) are both implemented; `_repr_html_` is also available.
12. **Filter routing**: see the pandas-mapping section — equality, numeric range, and compound conditions each route to a *different* `Filter*` processor; do not collapse them.
