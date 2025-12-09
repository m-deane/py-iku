# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Repository Overview

**py-iku** is a Python library that converts Python data processing code (pandas, numpy, scikit-learn) to Dataiku DSS recipes, flows, and visual diagrams. The library supports two analysis modes:

1. **LLM-based (recommended)**: Uses AI (Anthropic/OpenAI) to understand code semantics
2. **Rule-based (fallback)**: Uses AST pattern matching for offline conversion

The library generates Dataiku DSS 14 compatible configurations with support for 34+ recipe types and 76+ processor types.

## Quick Reference

### Running Tests
```bash
# All tests (843 tests)
python -m pytest tests/ -v

# Specific test modules
python -m pytest tests/test_py2dataiku/test_recipe_examples.py -v
python -m pytest tests/test_py2dataiku/test_processor_examples.py -v
python -m pytest tests/test_py2dataiku/test_combination_examples.py -v

# With coverage
python -m pytest tests/ --cov=py2dataiku --cov-report=html
```

### Basic Usage
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

## Architecture

```
py2dataiku/
├── __init__.py          # Public API: convert(), convert_with_llm(), Py2Dataiku class
├── parser/              # Code analysis
│   ├── ast_analyzer.py  # Rule-based AST pattern matching
│   ├── pattern_matcher.py
│   └── dataflow_tracker.py
├── llm/                 # LLM-based analysis
│   ├── analyzer.py      # LLMCodeAnalyzer
│   ├── providers.py     # AnthropicProvider, OpenAIProvider
│   └── schemas.py       # AnalysisResult, DataStep, OperationType
├── generators/          # Flow generation
│   ├── flow_generator.py     # Rule-based FlowGenerator
│   ├── llm_flow_generator.py # LLM-based LLMFlowGenerator
│   ├── recipe_generator.py
│   └── diagram_generator.py  # Mermaid/Graphviz diagrams
├── models/              # Core data models
│   ├── dataiku_flow.py     # DataikuFlow - main output class
│   ├── dataiku_recipe.py   # DataikuRecipe, RecipeType enum (34+ types)
│   ├── dataiku_dataset.py  # DataikuDataset, DatasetType
│   ├── prepare_step.py     # PrepareStep, ProcessorType enum (76+ types)
│   └── transformation.py
├── visualizers/         # Visualization engines
│   ├── svg_visualizer.py     # Pixel-accurate Dataiku styling
│   ├── html_visualizer.py    # Interactive canvas
│   ├── ascii_visualizer.py   # Terminal-friendly
│   ├── plantuml_visualizer.py
│   ├── themes.py             # DATAIKU_LIGHT, DATAIKU_DARK
│   ├── icons.py              # Recipe/dataset icons
│   └── layout_engine.py      # DAG layout algorithm
├── mappings/            # pandas → Dataiku mappings
│   ├── pandas_mappings.py
│   └── processor_catalog.py
├── optimizer/           # Flow optimization
│   ├── flow_optimizer.py
│   └── recipe_merger.py
├── utils/
│   └── validation.py
└── examples/            # Comprehensive examples library
    ├── recipe_examples.py       # 35+ recipe examples
    ├── processor_examples.py    # 60+ processor examples
    ├── settings_examples.py     # 50+ settings examples
    ├── combination_examples.py  # 22+ combination examples
    ├── basic_pipelines.py
    ├── intermediate_pipelines.py
    ├── advanced_pipelines.py
    └── complex_pipelines.py
```

## Key Concepts

### RecipeType (Dataiku DSS 14)
Visual recipes: `PREPARE`, `SYNC`, `JOIN`, `STACK`, `SPLIT`, `GROUPING`, `WINDOW`, `PIVOT`, `SORT`, `DISTINCT`, `TOP_N`, `SAMPLING`, `DOWNLOAD`, `UPLOAD`

Code recipes: `PYTHON`, `R`, `SQL`, `PYSPARK`, `SPARKSQL`, `SPARK_SCALA`, `HIVE`, `IMPALA`, `SHELL`

ML recipes: `PREDICTION_SCORING`, `CLUSTERING_SCORING`, `EVALUATION`, `STANDALONE_EVALUATION`

Plugin recipes: `UPSERT`, `SYNC_DATASETS`, `GENERATE_FEATURES`

### ProcessorType (76+ types)
Column manipulation: `COLUMN_RENAMER`, `COLUMN_COPIER`, `COLUMN_DELETER`, `COLUMNS_SELECTOR`, `COLUMN_REORDER`

String transformations: `STRING_TRANSFORMER`, `TOKENIZER`, `REGEXP_EXTRACTOR`, `FIND_REPLACE`, `TEXT_SIMPLIFIER`, `LANGUAGE_DETECTOR`

Numeric operations: `NUMERICAL_TRANSFORMER`, `ROUND_COLUMN`, `ABS_COLUMN`, `CLIP_COLUMN`, `BINNER`, `NORMALIZER`

Missing values: `FILL_EMPTY_WITH_VALUE`, `FILL_EMPTY_WITH_PREVIOUS_NEXT`, `REMOVE_ROWS_ON_EMPTY`, `FILL_EMPTY_WITH_COMPUTED_VALUE`

Date/time: `DATE_PARSER`, `DATE_FORMATTER`, `DATE_COMPONENTS_EXTRACTOR`, `DATE_DIFFERENCE`, `DATE_AGGREGATOR`

Filtering: `FILTER_ON_VALUE`, `FILTER_ON_FORMULA`, `FILTER_ON_DATE_RANGE`, `FILTER_ON_NUMERIC_RANGE`, `FILTER_ON_BAD_TYPE`

Flagging: `FLAG_ON_VALUE`, `FLAG_ON_FORMULA`, `FLAG_ON_DATE_RANGE`, `FLAG_ON_NUMERIC_RANGE`, `FLAG_EMPTY`

Categorical: `CATEGORICAL_ENCODER`, `TARGET_ENCODER`, `MERGE_LONG_TAIL_VALUES`

### DataikuFlow
The main output class representing a complete Dataiku pipeline:
- `datasets`: List of DataikuDataset (INPUT, OUTPUT, INTERMEDIATE)
- `recipes`: List of DataikuRecipe with configurations
- `visualize(format)`: Generate SVG, HTML, ASCII, PlantUML, or Mermaid output
- `to_dict()`, `to_json()`, `to_yaml()`: Export formats
- `validate()`: Check flow structure for errors
- `get_summary()`: Text summary of flow

## Examples Registry

The library includes comprehensive examples for testing and documentation:

```python
from py2dataiku.examples.recipe_examples import (
    RECIPE_EXAMPLES,           # Dict of 35+ recipe examples
    get_recipe_example,        # Get example by name
    list_recipe_examples,      # List all example names
)

from py2dataiku.examples.processor_examples import (
    PROCESSOR_EXAMPLES,        # Dict of 60+ processor examples
    get_processor_example,
    list_processor_examples,
)

from py2dataiku.examples.settings_examples import (
    SETTINGS_EXAMPLES,         # Dict of 50+ settings examples
)

from py2dataiku.examples.combination_examples import (
    COMBINATION_EXAMPLES,      # Dict of 22+ combination examples
)
```

## Development Guidelines

### Adding New Recipe Types
1. Add to `RecipeType` enum in `py2dataiku/models/dataiku_recipe.py`
2. Add pandas mapping in `py2dataiku/mappings/pandas_mappings.py`
3. Add example in `py2dataiku/examples/recipe_examples.py`
4. Add test in `tests/test_py2dataiku/test_recipe_examples.py`

### Adding New Processor Types
1. Add to `ProcessorType` enum in `py2dataiku/models/prepare_step.py`
2. Add any related enums (modes, options)
3. Add example in `py2dataiku/examples/processor_examples.py`
4. Add test in `tests/test_py2dataiku/test_processor_examples.py`

### Common Patterns

**pandas → Dataiku Recipe Mapping:**
- `df.groupby().agg()` → GROUPING recipe
- `pd.merge()` / `df.merge()` → JOIN recipe
- `pd.concat()` → STACK recipe
- `df.drop_duplicates()` → DISTINCT recipe
- `df.sort_values()` → SORT recipe
- `df.pivot()` / `df.pivot_table()` → PIVOT recipe
- `df.rolling()` / `df.cumsum()` → WINDOW recipe
- `df[condition]` (boolean indexing) → SPLIT recipe or FILTER processor
- Other transformations → PREPARE recipe with appropriate processors

**pandas → Dataiku Processor Mapping:**
- `df.rename()` → COLUMN_RENAMER processor
- `df.drop()` → COLUMN_DELETER processor
- `df.fillna()` → FILL_EMPTY_WITH_VALUE processor
- `df.dropna()` → REMOVE_ROWS_ON_EMPTY processor
- `df['col'].str.upper()` → STRING_TRANSFORMER (mode: TO_UPPER)
- `df['col'].str.strip()` → STRING_TRANSFORMER (mode: TRIM)
- `df['col'].astype()` → TYPE_SETTER processor
- `pd.to_datetime()` → DATE_PARSER processor
- `df['col'].dt.strftime()` → DATE_FORMATTER processor
- `pd.cut()` / `pd.qcut()` → BINNER processor
- `pd.get_dummies()` → CATEGORICAL_ENCODER processor

## Dependencies

- **pandas**: Primary data processing library being converted
- **pyyaml**: YAML export
- **anthropic** (optional): LLM analysis with Claude
- **openai** (optional): LLM analysis with GPT
- **cairosvg** (optional): PNG/PDF export from SVG

## File Organization Rules

- All source code in `py2dataiku/`
- All tests in `tests/test_py2dataiku/`
- Examples in `py2dataiku/examples/`
- Plans and analysis documents in `.claude_plans/`

## Testing Philosophy

- All tests use pytest framework
- Tests verify both success and failure cases
- Run all tests before committing changes
- Current test count: 843 tests (all should pass)

## Common Gotchas

1. **Visualization formats**: SVG is pixel-accurate Dataiku styling; ASCII is terminal-friendly
2. **LLM vs Rule-based**: LLM mode requires API key but produces better results for complex code
3. **Recipe vs Processor**: Recipes are top-level flow nodes; processors are steps within PREPARE recipes
4. **Enums**: Always use enum values from models, not raw strings
