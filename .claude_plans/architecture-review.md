# Architecture Review: py-iku (py2dataiku)

**Date:** 2026-02-19
**Reviewer:** Architecture Review Agent
**Library Version:** 0.3.0
**Total Source Files:** 52 Python files in py2dataiku/
**Total Tests:** 843

---

## Executive Summary

py-iku is a well-structured Python library that converts pandas/numpy/scikit-learn code to Dataiku DSS recipes and flows. The architecture follows a clean pipeline pattern: **Parse -> Intermediate Representation -> Generate -> Visualize/Export**. The dual-mode design (rule-based AST analysis vs. LLM-based semantic analysis) is a sound architectural decision that provides both offline capability and AI-enhanced accuracy. The codebase demonstrates strong separation of concerns across its modules, with a comprehensive model layer at the core. Key areas for improvement include reducing code duplication between the two analysis paths, strengthening the optimizer module, and tightening the interface contracts between pipeline stages.

---

## Current Architecture Strengths

### 1. Clean Pipeline Architecture
The library follows a clear data transformation pipeline:
```
Input Code -> [Parser/LLM Analyzer] -> [Intermediate Representation] -> [Flow Generator] -> [DataikuFlow] -> [Visualizer/Exporter]
```
Each stage has well-defined inputs and outputs. The `Transformation` class (rule-based) and `AnalysisResult`/`DataStep` classes (LLM-based) serve as clean intermediate representations between parsing and generation.

### 2. Strong Model Layer (`models/`)
The `models/` package is the strongest module in the codebase:
- **DataikuFlow** (`dataiku_flow.py`): Central output class with comprehensive serialization (JSON, YAML, dict), validation, and visualization dispatch. Uses dataclasses effectively.
- **DataikuRecipe** (`dataiku_recipe.py`): Rich enum types (`RecipeType` with 34+ types, `JoinType`, `AggregationFunction`, `WindowFunctionType`, etc.) that accurately model DSS 14 concepts. Factory methods (`create_prepare`, `create_grouping`, `create_join`, `create_python`) provide a clean construction API.
- **PrepareStep** (`prepare_step.py`): 76+ `ProcessorType` enum values with supporting mode enums (`StringTransformerMode`, `NumericalTransformerMode`, `FilterMatchMode`, etc.) and convenience factory methods.
- **Transformation** (`transformation.py`): Clean intermediate representation with factory methods for common operations.

The model layer correctly uses Python dataclasses, enums, and type hints throughout.

### 3. Dual-Mode Analysis Design
The rule-based (`parser/`) and LLM-based (`llm/`) analysis paths are cleanly separated:
- **Rule-based path:** `CodeAnalyzer` -> `List[Transformation]` -> `FlowGenerator` -> `DataikuFlow`
- **LLM-based path:** `LLMCodeAnalyzer` -> `AnalysisResult` -> `LLMFlowGenerator` -> `DataikuFlow`

Both paths converge on the same output type (`DataikuFlow`), which is excellent for downstream consumers. The `Py2Dataiku` class provides a unified facade with automatic LLM-to-rule-based fallback.

### 4. Extensible Plugin System (`plugins/`)
The `PluginRegistry` class with its class-level dictionaries allows runtime extension without modifying core code:
- Custom pandas method -> RecipeType/ProcessorType mappings
- Custom AST node handlers
- Decorator-based registration (`@plugin_hook`, `@register_recipe_handler`)
- Plugin base class with `activate()`/`deactivate()` lifecycle

This is well-designed for a library that needs to support custom Dataiku plugins and domain-specific transformations.

### 5. Comprehensive Visualization System (`visualizers/`)
Five output format engines (SVG, HTML, ASCII, PlantUML, Interactive) share a common `FlowVisualizer` base class and `LayoutEngine`. The theme system (`DATAIKU_LIGHT`, `DATAIKU_DARK`) and icon registry (`RecipeIcons`) provide consistent Dataiku-style rendering across formats.

### 6. Production-Ready Exporter (`exporters/`)
The `DSSExporter` generates real DSS project bundles with proper directory structure (`project.json`, `params.json`, `datasets/`, `recipes/`, `flow/zones.json`). This is a significant differentiator from a toy project -- it produces import-ready artifacts.

### 7. Well-Designed Public API (`__init__.py`)
The top-level API surface is clean:
- `convert(code)` -- simple rule-based conversion
- `convert_with_llm(code)` -- LLM-based conversion
- `Py2Dataiku` class -- unified interface with fallback
- Explicit `__all__` list

The convenience functions have sensible defaults and the progressive disclosure from simple functions to the full class API is well done.

### 8. Comprehensive CLI (`cli.py`)
Four subcommands (`convert`, `visualize`, `analyze`, `export`) with consistent argument patterns, stdin support, and proper error handling. Mirrors the programmatic API well.

---

## Current Architecture Weaknesses

### 1. Code Duplication Between Analysis Paths (HIGH Impact)
The two analysis paths have significant structural duplication:
- `FlowGenerator` and `LLMFlowGenerator` share ~60% identical code for recipe creation (`_create_join_recipe`, `_create_grouping_recipe`, `_create_stack_recipe`, `_create_split_recipe`, `_create_sort_recipe`, `_create_python_recipe`, `_optimize_flow`, `_sanitize_name`).
- `ast_analyzer.py` and `llm/analyzer.py` both maintain recipe-type inference maps.
- `pattern_matcher.py` and `pandas_mappings.py` duplicate string method mappings, aggregation mappings, and join type mappings.

This creates maintenance burden and risks the two paths drifting out of sync.

### 2. Incomplete Intermediate Representation Alignment
The rule-based path uses `Transformation` (from `models/transformation.py`) while the LLM path uses `DataStep` (from `llm/schemas.py`). These serve the same purpose but have different field names and structures:
- `Transformation.source_dataframe` vs `DataStep.input_datasets`
- `Transformation.suggested_recipe` (string) vs `DataStep.suggested_recipe` (string) -- same but different surrounding context
- `Transformation.parameters` (generic dict) vs `DataStep` (typed fields like `filter_conditions`, `aggregations`, etc.)

The LLM schema is more structured, but having two incompatible IRs makes it harder to share downstream logic.

### 3. DataikuRecipe is a God Object
`DataikuRecipe` carries fields for every recipe type (prepare steps, group keys, aggregations, join keys, join type, window aggregations, partition columns, sort columns, split condition, top_n, code, etc.) rather than using composition or a type hierarchy. While this works at the current scale, it will become unwieldy as more recipe types are fully implemented. The `_build_settings()` method is already a long if/elif chain mapping recipe types to their configuration.

### 4. Shallow Optimizer Implementation
The `FlowOptimizer` and `RecipeMerger` classes are structurally sound but functionally incomplete:
- `_merge_prepare_recipes` in `FlowGenerator` is a no-op (`pass`).
- `FlowOptimizer.optimize()` only generates recommendations -- it does not actually modify the flow.
- `RecipeMerger.merge()` exists but is never called from the main pipeline.
- The flow graph is stored as flat lists (`flow.recipes`, `flow.datasets`) rather than an explicit DAG, making graph traversal and optimization harder.

### 5. Weak Error Handling in LLM Path
The `LLMCodeAnalyzer.analyze()` method catches all exceptions and returns an `AnalysisResult` with empty steps and a warning message. This makes it impossible for callers to distinguish between:
- Invalid Python code
- LLM API errors (network, auth, rate limits)
- Malformed LLM responses
- Analysis that legitimately found no operations

The `Py2Dataiku` class swallows initialization errors with a `print()` statement and silently falls back.

### 6. PluginRegistry Uses Class-Level Mutable State
`PluginRegistry` stores all state in class variables (`_recipe_mappings`, `_processor_mappings`, etc.). This is effectively a global singleton, which causes issues:
- Tests can leak state between test cases unless `PluginRegistry.clear()` is called in teardown.
- Multiple independent converter instances cannot have different plugin configurations.
- Thread safety is not considered.

### 7. Missing Abstract Base for Generators
`FlowGenerator` and `LLMFlowGenerator` have no common base class or protocol despite sharing the pattern `generate(...) -> DataikuFlow`. This makes it harder to write code that works with either generator polymorphically.

### 8. Visualization Dispatch is Fragmented
Flow visualization is dispatched from three different places:
- `DataikuFlow.visualize()` delegates to `visualizers.visualize_flow()` for most formats, but handles `"mermaid"` separately via `DiagramGenerator`.
- `Py2Dataiku.generate_diagram()` uses `DiagramGenerator` directly for mermaid/graphviz/ascii/plantuml.
- `Py2Dataiku.visualize()` delegates to `flow.visualize()`.

The legacy `DiagramGenerator` and the newer `visualizers/` system overlap in functionality (both can produce ASCII and PlantUML output), creating confusion about which to use.

---

## Enhancement Recommendations

### R1: Extract Shared Recipe Creation into a Base Generator
**Impact:** HIGH | **Complexity:** MEDIUM

Create a `BaseFlowGenerator` abstract class that contains the shared recipe creation methods (`_create_join_recipe`, `_create_grouping_recipe`, etc.) and `_sanitize_name`. Both `FlowGenerator` and `LLMFlowGenerator` would inherit from it, only overriding the analysis-specific logic. This eliminates ~300 lines of duplication and ensures both paths produce consistent Dataiku configurations.

### R2: Unify Mapping Dictionaries
**Impact:** MEDIUM | **Complexity:** SMALL

Consolidate the duplicated mapping dictionaries (string methods, aggregation functions, join types, recipe inference) into the existing `mappings/pandas_mappings.py` module. The `PandasMapper` class already has the right structure. Have `PatternMatcher`, `CodeAnalyzer`, and `LLMFlowGenerator` reference this single source of truth instead of maintaining their own copies.

### R3: Refactor DataikuRecipe Using Composition
**Impact:** MEDIUM | **Complexity:** LARGE

Replace the monolithic `DataikuRecipe` with a base class + recipe-specific settings classes:
```python
@dataclass
class RecipeSettings(ABC):
    pass

@dataclass
class PrepareSettings(RecipeSettings):
    steps: List[PrepareStep]

@dataclass
class GroupingSettings(RecipeSettings):
    keys: List[str]
    aggregations: List[Aggregation]

@dataclass
class DataikuRecipe:
    name: str
    recipe_type: RecipeType
    inputs: List[str]
    outputs: List[str]
    settings: RecipeSettings
```

This eliminates unused fields per recipe instance and replaces the `_build_settings()` if/elif chain with polymorphic dispatch. The factory methods can remain as convenience constructors.

### R4: Implement DAG Data Structure for Flow
**Impact:** HIGH | **Complexity:** MEDIUM

Replace the flat `List[DataikuRecipe]` and `List[DataikuDataset]` with an explicit DAG representation (adjacency list or similar). This would:
- Enable the optimizer to actually perform graph transformations (merging, reordering)
- Support topological sorting for execution order
- Make `validate()` and column lineage tracking more robust
- Enable detection of disconnected subgraphs and cycles

### R5: Add Typed Error Hierarchy for LLM Path
**Impact:** MEDIUM | **Complexity:** SMALL

Introduce specific exception types:
```python
class Py2DataikuError(Exception): ...
class AnalysisError(Py2DataikuError): ...
class LLMProviderError(AnalysisError): ...
class LLMResponseParseError(AnalysisError): ...
class InvalidPythonCodeError(AnalysisError): ...
```

Replace the blanket `except Exception` in `LLMCodeAnalyzer.analyze()` with specific handlers. Let callers decide how to handle different failure modes instead of silently degrading.

### R6: Make PluginRegistry Instance-Based
**Impact:** MEDIUM | **Complexity:** MEDIUM

Convert `PluginRegistry` from class-level state to instance-based state. Inject the registry into `CodeAnalyzer` and generators via constructor parameters. Provide a default global instance for backward compatibility. This improves testability and allows multiple independent converter configurations.

### R7: Consolidate Visualization Dispatch
**Impact:** LOW | **Complexity:** SMALL

- Move mermaid generation into the `visualizers/` module (create `MermaidVisualizer` following the existing pattern).
- Deprecate `DiagramGenerator` or make it delegate to the visualizer system.
- Remove the special-case mermaid handling from `DataikuFlow.visualize()`.
- Remove `Py2Dataiku.generate_diagram()` or have it delegate to `flow.visualize()`.

### R8: Implement Column Lineage Tracking
**Impact:** MEDIUM | **Complexity:** LARGE

The `DataFlowTracker` in `parser/dataflow_tracker.py` exists but is not integrated into the main pipeline. The `DataikuFlow.get_column_lineage()` method returns `None` (placeholder). Integrate `DataFlowTracker` into the rule-based analysis path and implement a schema-propagation system that tracks how columns flow through recipes. This would be a significant feature for users auditing their converted flows.

### R9: Add Protocol/Interface for Analyzers
**Impact:** LOW | **Complexity:** SMALL

Define a `Protocol` (or ABC) for code analyzers:
```python
class CodeAnalyzerProtocol(Protocol):
    def analyze(self, code: str) -> AnalysisResult: ...
```

This would require either unifying the IR types or making the protocol generic. The benefit is that `Py2Dataiku` and the CLI can work with any analyzer implementation without knowing its concrete type.

### R10: Strengthen the Optimizer Module
**Impact:** HIGH | **Complexity:** MEDIUM

The optimizer has the right structure but needs implementation:
1. Actually merge consecutive Prepare recipes (not just recommend it).
2. Implement filter pushdown (move filters before joins).
3. Eliminate redundant intermediate datasets when recipes are merged.
4. Provide a before/after summary of optimizations applied.

This is closely tied to R4 (DAG data structure) -- implementing the DAG first would make optimization transformations much cleaner.

---

## Module Dependency Analysis

```
__init__.py (public API facade)
  |
  +-- parser/ (rule-based analysis)
  |     +-- ast_analyzer.py -> models/transformation.py, plugins/registry.py
  |     +-- pattern_matcher.py -> models/prepare_step.py
  |     +-- dataflow_tracker.py (standalone, not integrated)
  |
  +-- llm/ (LLM-based analysis)
  |     +-- analyzer.py -> llm/providers.py, llm/schemas.py
  |     +-- providers.py (standalone, optional deps: anthropic, openai)
  |     +-- schemas.py (standalone)
  |
  +-- generators/ (flow generation)
  |     +-- flow_generator.py -> models/*
  |     +-- llm_flow_generator.py -> models/*, llm/schemas.py
  |     +-- recipe_generator.py -> models/dataiku_recipe.py, models/prepare_step.py
  |     +-- diagram_generator.py -> models/dataiku_flow.py (LEGACY)
  |
  +-- models/ (core data models, no external deps)
  |     +-- dataiku_flow.py -> dataiku_dataset.py, dataiku_recipe.py
  |     +-- dataiku_recipe.py -> prepare_step.py
  |     +-- dataiku_dataset.py (standalone)
  |     +-- prepare_step.py (standalone)
  |     +-- transformation.py (standalone)
  |
  +-- visualizers/ (visualization engines)
  |     +-- base.py, layout_engine.py, themes.py, icons.py
  |     +-- svg_visualizer.py, ascii_visualizer.py, html_visualizer.py
  |     +-- plantuml_visualizer.py, interactive_visualizer.py
  |     All depend on models/dataiku_flow.py
  |
  +-- plugins/ (extension system)
  |     +-- registry.py -> models/dataiku_recipe.py, models/prepare_step.py, models/transformation.py
  |
  +-- exporters/ (DSS project export)
  |     +-- dss_exporter.py -> models/dataiku_flow.py, models/dataiku_recipe.py, models/dataiku_dataset.py
  |
  +-- optimizer/ (flow optimization)
  |     +-- flow_optimizer.py -> models/dataiku_flow.py, models/dataiku_recipe.py
  |     +-- recipe_merger.py (in same file, same deps)
  |
  +-- mappings/ (pandas -> Dataiku mappings)
  |     +-- pandas_mappings.py -> models/prepare_step.py, models/dataiku_recipe.py
  |     +-- processor_catalog.py
  |
  +-- cli.py -> __init__.py (convert, DataikuFlow, CodeAnalyzer)
```

**Dependency direction is generally clean:** models have no outward dependencies, analyzers depend on models, generators depend on models and analyzer output types, visualizers depend on models only. The one concern is `parser/ast_analyzer.py` depending on `plugins/registry.py` -- this creates a coupling between the parser and the extension system that could be inverted via dependency injection.

---

## Summary of Recommendations by Priority

| Priority | Recommendation | Impact | Complexity |
|----------|---------------|--------|------------|
| 1 | R1: Extract shared generator base class | HIGH | MEDIUM |
| 2 | R4: Implement DAG data structure | HIGH | MEDIUM |
| 3 | R10: Strengthen optimizer | HIGH | MEDIUM |
| 4 | R2: Unify mapping dictionaries | MEDIUM | SMALL |
| 5 | R5: Add typed error hierarchy | MEDIUM | SMALL |
| 6 | R3: Refactor DataikuRecipe via composition | MEDIUM | LARGE |
| 7 | R6: Instance-based PluginRegistry | MEDIUM | MEDIUM |
| 8 | R8: Implement column lineage | MEDIUM | LARGE |
| 9 | R7: Consolidate visualization dispatch | LOW | SMALL |
| 10 | R9: Add analyzer protocol/interface | LOW | SMALL |
