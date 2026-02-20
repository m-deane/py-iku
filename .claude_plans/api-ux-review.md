# py-iku API & Developer Experience Review

## Executive Summary

The py-iku library provides a well-structured public API with clear entry points, comprehensive model coverage, and multiple output formats. The library strikes a good balance between simplicity (two convenience functions) and power (full class-based API with plugin system). However, there are several areas where the developer experience can be improved, particularly around error handling consistency, discoverability, type safety, and some API surface inconsistencies.

---

## 1. Current State Assessment

### Strengths

**S1. Clean dual-entry API design**
The library offers three tiers of access that serve different user profiles well:
- `convert()` / `convert_with_llm()` - one-liner convenience functions for quick use
- `Py2Dataiku` class - stateful converter with automatic LLM fallback
- Individual components (`CodeAnalyzer`, `LLMCodeAnalyzer`, `FlowGenerator`, etc.) for advanced use

**S2. Comprehensive `__init__.py` exports**
All key types are importable from the top-level package. The `__all__` list is well-organized with section comments. Users can do `from py2dataiku import convert, DataikuFlow, RecipeType` without knowing internal module structure.

**S3. Rich visualization support**
Five output formats (SVG, HTML, ASCII, PlantUML, Mermaid) accessible via a single `flow.visualize(format=...)` method. The `DataikuFlow` class has dedicated convenience methods (`to_svg()`, `to_html()`, `to_ascii()`, `to_plantuml()`, `to_png()`, `to_pdf()`). Theme support with light/dark modes.

**S4. Well-designed model classes with factory methods**
`DataikuRecipe` provides `create_prepare()`, `create_grouping()`, `create_join()`, `create_python()` factory methods that enforce correct construction. `PrepareStep` has 11 factory class methods (`fill_empty()`, `rename_columns()`, `delete_columns()`, etc.) that simplify step creation.

**S5. Full CLI with four commands**
`py2dataiku convert|visualize|analyze|export` covers all major workflows. Supports stdin, file output, format selection, LLM toggle, and quiet mode.

**S6. Plugin system for extensibility**
The `PluginRegistry` with `@plugin_hook`, `register_recipe_handler`, `register_processor_handler`, `register_pandas_mapping` decorators allows third-party extensions.

**S7. DSS export capability**
The `DSSExporter` generates a complete DSS-compatible project directory structure with `project.json`, `params.json`, dataset configs, recipe configs, and flow zones. Supports zip bundling for direct import.

**S8. Multiple serialization formats**
`DataikuFlow` supports `to_dict()`, `to_json()`, `to_yaml()`, `to_recipe_configs()`, and `export_all()` for comprehensive output flexibility.

### Weaknesses

**W1. Version inconsistency**
`pyproject.toml` says `version = "0.2.0"`, `__init__.py` says `__version__ = "0.3.0"`, and `cli.py` has `version="%(prog)s 0.3.0"`. Only one source of truth should exist.

**W2. Inconsistent error handling and error messages**
- `CodeAnalyzer.analyze()` re-raises `SyntaxError` with context but other errors propagate unhandled
- `LLMCodeAnalyzer.analyze()` silently returns an empty `AnalysisResult` on any error (including API failures, JSON parse errors), rather than raising. The error is buried in the `code_summary` field
- `Py2Dataiku.__init__()` uses `print()` to warn about LLM fallback rather than `warnings.warn()` or logging
- `FlowGenerator` and `LLMFlowGenerator` can produce flows with empty string inputs/outputs (`""`) without warning when dataset references cannot be resolved

**W3. No custom exception hierarchy**
All errors are generic `ValueError`, `ImportError`, `SyntaxError`. A `Py2DataikuError` base class with subclasses like `ConversionError`, `ProviderError`, `ValidationError` would enable better error handling by users.

**W4. `to_json()` naming confusion on `DataikuRecipe`**
`DataikuRecipe.to_dict()` returns the internal representation while `DataikuRecipe.to_json()` returns a Dataiku-API-compatible dict (not a JSON string). This is confusing since every other class's `to_json()` returns a string.

**W5. Silent failures in flow generation**
Both `FlowGenerator` and `LLMFlowGenerator` silently create empty-string dataset names and recipes with no inputs when they cannot resolve references. There are no warnings emitted.

**W6. `_merge_prepare_recipes()` is a no-op**
`FlowGenerator._merge_prepare_recipes()` has a `pass` body with a comment saying "simplified implementation." The `optimize=True` parameter on `convert()` implies optimization happens, but this core optimization step does nothing.

**W7. Missing `convert_file()` convenience function**
Both `convert()` and `convert_with_llm()` require a code string. There is no convenience function to convert from a file path, despite this being the primary CLI use case. Users must always `open()` + `read()` first.

**W8. No progress/status callbacks for LLM analysis**
LLM API calls can take seconds. There are no callbacks, progress indicators, or timeout configuration in `LLMCodeAnalyzer` or `convert_with_llm()`.

**W9. `DataikuFlow.get_column_lineage()` is unimplemented**
Returns `None` always. The method exists in the public API but does nothing. Should either be implemented or removed/marked as experimental.

**W10. `DSSExporter._build_join_payload()` and `_build_grouping_payload()` access non-existent attribute**
Both methods reference `recipe.parameters` which does not exist on `DataikuRecipe` (the attributes are `join_keys`, `join_type`, `group_keys`, `aggregations`, etc.). This means DSS export of join and grouping recipes silently produces incorrect configurations.

---

## 2. Enhancement Recommendations

### Priority 1: High Impact, Addresses Bugs/Correctness

| # | Recommendation | Impact | Complexity | Details |
|---|---------------|--------|------------|---------|
| R1 | **Fix version inconsistency** | High | Small | Use single-source versioning. Read version from `pyproject.toml` in `__init__.py` using `importlib.metadata.version("py-iku")`, remove hardcoded version from `cli.py`. |
| R2 | **Fix DSSExporter recipe payload methods** | High | Small | `_build_join_payload()` and `_build_grouping_payload()` reference `recipe.parameters` which does not exist. Must use `recipe.join_type`, `recipe.join_keys`, `recipe.group_keys`, `recipe.aggregations` instead. This is a bug producing incorrect DSS exports. |
| R3 | **Implement proper error handling strategy** | High | Medium | (1) Create custom exception hierarchy: `Py2DataikuError > ConversionError, ProviderError, ValidationError, ExportError`. (2) Replace `LLMCodeAnalyzer`'s silent error swallowing with raising `ProviderError`. (3) Replace `print()` warnings in `Py2Dataiku.__init__()` with `warnings.warn()`. (4) Add validation/warnings when flow generation produces empty dataset references. |
| R4 | **Fix `DataikuRecipe.to_json()` return type** | Medium | Small | Rename to `to_api_dict()` or similar to avoid confusion with `DataikuFlow.to_json()` which returns a JSON string. Alternatively, make it return a JSON string and add `to_api_dict()` for the dictionary form. |

### Priority 2: Significant UX Improvements

| # | Recommendation | Impact | Complexity | Details |
|---|---------------|--------|------------|---------|
| R5 | **Add `convert_file()` convenience function** | Medium | Small | Add `convert_file(path, ...)` and `convert_file_with_llm(path, ...)` to `__init__.py`. Sets `source_file` on the resulting flow automatically. This is the natural entry point for CLI and scripting users. |
| R6 | **Add timeout and retry to LLM providers** | Medium | Small | Add `timeout` parameter to `AnthropicProvider` and `OpenAIProvider` constructors (default 60s). Add `max_retries` parameter (default 2). These are critical for production usage. |
| R7 | **Implement `_merge_prepare_recipes()` or remove `optimize` param** | Medium | Medium | The `optimize=True` parameter creates an expectation that the library performs meaningful optimization. If full optimization is not planned, document clearly what optimization does/doesn't do. If it is planned, implement merging consecutive prepare recipes (combine their step lists). |
| R8 | **Add type stubs / improve type annotations** | Medium | Medium | While `py.typed` marker exists in `pyproject.toml`, many parameters use loose types like `str` for what should be enum values (e.g., `provider: str = "anthropic"` could be a `Literal["anthropic", "openai"]`). `Aggregation.function` is `str` instead of `AggregationFunction`. `JoinKey.match_type` is `str` instead of an enum. |
| R9 | **Add `DataikuFlow.from_dict()` / `from_json()` / `from_yaml()`** | Medium | Medium | The flow can be serialized with `to_dict()`/`to_json()`/`to_yaml()` but cannot be deserialized back. This breaks round-trip workflows and prevents loading saved flows for further manipulation. |

### Priority 3: Nice-to-Have Enhancements

| # | Recommendation | Impact | Complexity | Details |
|---|---------------|--------|------------|---------|
| R10 | **Remove or mark `get_column_lineage()` as experimental** | Low | Small | The method returns `None` always. Either remove it from the public API, raise `NotImplementedError`, or mark with a "not yet implemented" docstring note. |
| R11 | **Add `DataikuFlow.__len__()` and iteration** | Low | Small | `len(flow)` could return recipe count. `for recipe in flow` could iterate recipes. Pythonic convenience. |
| R12 | **Add `convert()` return type validation** | Low | Small | After flow generation, auto-call `flow.validate()` and emit warnings for any issues found. Currently, users must manually call `validate()` to discover problems. |
| R13 | **Add progress callback parameter to `convert_with_llm()`** | Low | Small | `convert_with_llm(code, on_progress=callback)` where callback receives status strings like "analyzing", "generating flow", etc. Useful for UIs and notebooks. |
| R14 | **Add `DataikuFlow.diff()` method** | Low | Medium | Compare two flows and return differences. Useful when comparing rule-based vs LLM-based conversion results. |
| R15 | **Improve CLI error messages with suggestions** | Low | Small | When `--llm` is used without the package installed, suggest `pip install py-iku[llm]`. When a file has syntax errors, show the specific line. Already partially done but could be more consistent. |
| R16 | **Add `DataikuFlow.add_recipe_from_code()` convenience** | Low | Medium | `flow.add_recipe_from_code("df.groupby('cat').sum()")` that internally parses and adds the appropriate recipe. Convenient for programmatic flow building. |

---

## 3. Import Ergonomics Assessment

### Current State: Good
```python
# Basic usage - clean
from py2dataiku import convert, convert_with_llm

# Model access - clean
from py2dataiku import DataikuFlow, DataikuRecipe, RecipeType, ProcessorType

# Visualization - clean
from py2dataiku import SVGVisualizer, DATAIKU_LIGHT, DATAIKU_DARK

# Plugin system - clean
from py2dataiku import PluginRegistry, plugin_hook, register_recipe_handler

# Export - clean
from py2dataiku import DSSExporter, export_to_dss
```

### Issues Found
1. `Aggregation` and `JoinKey` dataclasses are not exported from `__init__.py` but are needed to construct recipes programmatically. Users must do `from py2dataiku.models.dataiku_recipe import Aggregation, JoinKey`.
2. `ColumnSchema` is not exported but needed for building dataset schemas.
3. `FlowRecommendation` and `ColumnLineage` from `dataiku_flow.py` are not exported.
4. Supporting enums (`JoinType`, `AggregationFunction`, `WindowFunctionType`, `SplitMode`, `SamplingMethod`, `StringTransformerMode`, `NumericalTransformerMode`, `FilterMatchMode`, etc.) are not exported. Users constructing recipes/steps programmatically must import from deep module paths.
5. `InteractiveVisualizer` is in `visualizers/__init__.py` but not in the top-level `__init__.py`.
6. `MockProvider` is useful for testing but not exported.

### Recommendation
Add commonly needed types to `__all__` in `__init__.py`:
```python
# Add to exports
from py2dataiku.models.dataiku_recipe import (
    Aggregation, JoinKey, JoinType, AggregationFunction,
    WindowFunctionType, SplitMode, SamplingMethod,
)
from py2dataiku.models.prepare_step import (
    StringTransformerMode, NumericalTransformerMode,
    FilterMatchMode, DateComponentType, BinningMode,
    NormalizationMode, EncodingType,
)
from py2dataiku.models.dataiku_dataset import ColumnSchema
from py2dataiku.llm.providers import MockProvider
```

---

## 4. Docstring Quality Assessment

### Overall: Good - B+

**Strengths:**
- All public functions and classes have docstrings
- Consistent Google-style Args/Returns format
- `convert_with_llm()` includes an Example section
- Module-level docstrings explain purpose and list capabilities

**Weaknesses:**
- No docstrings on enum members (e.g., what does `RecipeType.GENERATE_FEATURES` do?)
- `DataikuFlow.validate()` docstring doesn't describe return structure
- `DataikuFlow.to_recipe_configs()` docstring says "Dataiku API-compatible" but the method calls `r.to_json()` which returns a dict, not proper API configs
- `PrepareStep` factory methods lack Examples sections
- No Raises documentation on any method (what exceptions can `convert()` throw?)
- `Py2Dataiku.generate_diagram()` and `Py2Dataiku.visualize()` have overlapping purposes without clear guidance on when to use which

---

## 5. Configuration & Defaults Assessment

### Current Defaults: Generally Good

| Configuration | Default | Assessment |
|--------------|---------|------------|
| `optimize` | `True` | Good - users want optimized flows by default |
| `provider` | `"anthropic"` | Reasonable - Anthropic is the primary supported provider |
| `flow_name` | `"converted_flow"` | Fine for quick use |
| `DSSProjectConfig.default_connection` | `"filesystem_managed"` | Good DSS default |
| `DSSProjectConfig.default_format` | `"csv"` | Good - most common format |
| `AnthropicProvider.model` | `"claude-sonnet-4-20250514"` | Good - cost-effective default |
| `OpenAIProvider.model` | `"gpt-4o"` | Good |
| `max_tokens` | `4096` | May be insufficient for large code files with many operations |

### Missing Configuration Options
1. No way to configure dataset naming conventions (currently hardcoded sanitization)
2. No way to set default project key prefix for DSS export
3. No configuration for flow optimization aggressiveness
4. No way to specify which recipe types to prefer or avoid
5. No configuration file support (e.g., `.py2dataikurc` or `py2dataiku.toml`)

---

## 6. Output Format Flexibility Assessment

### Current State: Excellent

The library supports a rich set of output formats:
- **Structured data**: dict, JSON, YAML
- **Visual**: SVG, HTML (interactive), ASCII, PlantUML, Mermaid
- **Image export**: PNG, PDF (via cairosvg)
- **DSS-compatible**: Full project export with zip bundling
- **Summary**: Human-readable text summary

### Gaps
1. No Jupyter notebook widget/display integration (could add `_repr_svg_()` to `DataikuFlow` for automatic rendering)
2. No Graphviz DOT output (though `DiagramGenerator.to_graphviz()` exists, it is not exposed through the `visualize()` unified API)
3. No `to_csv()` or tabular export of the flow metadata (useful for documentation)

---

## 7. Examples Assessment

### Current State: Comprehensive

- `recipe_examples.py`: 35+ examples covering all visual, code, and ML recipe types
- `processor_examples.py`: 60+ examples for every processor type
- `settings_examples.py`: 50+ settings configurations
- `combination_examples.py`: 22+ multi-step pipeline examples
- `basic/intermediate/advanced/complex_pipelines.py`: Progressive complexity examples
- 5 Jupyter notebooks covering basic usage through advanced features

### Gaps
1. No "quick start" example in the module docstring or package README showing 3-line usage
2. No examples of the plugin system in action
3. No examples of DSS export workflow
4. No examples showing error handling patterns
5. No comparison example showing rule-based vs LLM-based conversion of the same code
6. The example registry functions (`get_recipe_example()`, `list_recipe_examples()`) are useful but not documented in the main `__init__.py` or any top-level guide

---

## 8. CLI / Scripting Integration Assessment

### Current State: Good

The CLI (`py2dataiku convert|visualize|analyze|export`) covers the main workflows with:
- Stdin support (`-` for input)
- File output (`-o`)
- Format selection (`-f`)
- LLM toggle (`--llm`)
- Quiet mode (`-q`)

### Gaps
1. No `--validate` flag on `convert` to also run validation
2. No `--diff` command to compare two conversion results
3. No `--watch` mode for iterative development
4. No JSON Schema output command for tooling integration
5. Return codes are 0/1 only - no granular exit codes for scripting
6. No shell completion support (bash/zsh/fish)
7. No `--dry-run` option to show what would be generated without writing files
8. No `--verbose` flag (only `--quiet`; middle ground is default but no verbose)
9. The `visualize` command aliases to `viz` which is good

---

## 9. Awkward Workflows Identified

### AW1: Programmatic recipe building requires deep imports
```python
# Current - awkward
from py2dataiku.models.dataiku_recipe import Aggregation, JoinKey, JoinType
from py2dataiku.models.prepare_step import StringTransformerMode

# Better - if exported from top level
from py2dataiku import Aggregation, JoinKey, JoinType, StringTransformerMode
```

### AW2: No way to inspect what the library detected before generating flow
```python
# Current - must use two separate paths
analyzer = CodeAnalyzer()
transformations = analyzer.analyze(code)  # Inspect these
generator = FlowGenerator()
flow = generator.generate(transformations)  # Then generate

# Better - inspect then generate in one pipeline
flow = convert(code)
# But now you can't see what transformations were detected
```
The `Py2Dataiku.analyze()` method only works in LLM mode. There is no equivalent for rule-based mode.

### AW3: Visualization requires flow object, not code
```python
# Can't do this:
svg = visualize_code("import pandas as pd\n...")

# Must do:
flow = convert(code)
svg = flow.visualize(format="svg")
```

### AW4: DSS export from code requires multiple steps
```python
# Current
flow = convert(code)
exporter = DSSExporter(flow, project_key="MY_PROJECT")
exporter.export("./output")

# Better - single convenience function exists but requires extra import
from py2dataiku.exporters import export_to_dss
flow = convert(code)
export_to_dss(flow, "./output", project_key="MY_PROJECT")
```
The `export_to_dss` convenience function is good but not exported from the top-level package (it IS in `__all__` but under "Exporters" section, could be more prominent).

---

## 10. Summary of Top 5 Recommendations by Impact

1. **Fix DSSExporter recipe payload bugs** (R2) - Currently produces incorrect DSS exports for join and grouping recipes. High impact, small effort.

2. **Fix version inconsistency** (R1) - Three different version strings create confusion and potential packaging issues. High impact, small effort.

3. **Implement custom exception hierarchy and consistent error handling** (R3) - Silent error swallowing in LLM analyzer means users don't know when conversion fails. High impact, medium effort.

4. **Export commonly needed types from top-level `__init__.py`** (Import ergonomics section) - Reduces friction for programmatic recipe building. Medium impact, small effort.

5. **Add `DataikuFlow.from_dict()`/`from_json()` for round-trip serialization** (R9) - Critical for workflows that save and reload flows. Medium impact, medium effort.

---

*Report generated: 2026-02-19*
*Reviewer: API/UX Review Agent*
*Scope: py2dataiku public API, developer experience, and integration points*
