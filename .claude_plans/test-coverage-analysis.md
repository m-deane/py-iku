# Test Coverage Analysis - py-iku Library

**Date**: 2026-02-19
**Test Suite**: 1000 tests (all passing)
**Overall Coverage**: 71%

---

## 1. Coverage Statistics by Module

### Summary Table

| Module | Stmts | Miss | Cover | Priority |
|--------|-------|------|-------|----------|
| `py2dataiku/examples/demo.py` | 71 | 71 | **0%** | LOW (demo only) |
| `py2dataiku/examples/llm_demo.py` | 100 | 100 | **0%** | LOW (demo only) |
| `py2dataiku/mappings/__init__.py` | 3 | 3 | **0%** | MEDIUM |
| `py2dataiku/mappings/pandas_mappings.py` | 55 | 55 | **0%** | HIGH |
| `py2dataiku/mappings/processor_catalog.py` | 31 | 31 | **0%** | HIGH |
| `py2dataiku/utils/__init__.py` | 2 | 2 | **0%** | MEDIUM |
| `py2dataiku/utils/validation.py` | 110 | 110 | **0%** | HIGH |
| `py2dataiku/parser/dataflow_tracker.py` | 65 | 43 | **23%** | HIGH |
| `py2dataiku/visualizers/interactive_visualizer.py` | 63 | 49 | **18%** | MEDIUM |
| `py2dataiku/llm/analyzer.py` | 75 | 37 | **46%** | HIGH |
| `py2dataiku/llm/providers.py` | 126 | 57 | **52%** | HIGH |
| `py2dataiku/__init__.py` | 82 | 35 | **48%** | HIGH |
| `py2dataiku/parser/pattern_matcher.py` | 52 | 24 | **50%** | HIGH |
| `py2dataiku/generators/llm_flow_generator.py` | 257 | 114 | **51%** | HIGH |
| `py2dataiku/generators/recipe_generator.py` | 34 | 10 | **71%** | MEDIUM |
| `py2dataiku/models/dataiku_dataset.py` | 46 | 11 | **67%** | MEDIUM |
| `py2dataiku/visualizers/base.py` | 13 | 4 | **69%** | LOW |
| `py2dataiku/models/dataiku_flow.py` | 168 | 37 | **76%** | MEDIUM |
| `py2dataiku/parser/ast_analyzer.py` | 643 | 124 | **75%** | HIGH |
| `py2dataiku/optimizer/flow_optimizer.py` | 86 | 15 | **80%** | MEDIUM |
| `py2dataiku/exporters/dss_exporter.py` | 166 | 11 | **90%** | LOW |
| `py2dataiku/generators/flow_generator.py` | 215 | 10 | **95%** | LOW |
| `py2dataiku/plugins/registry.py` | 169 | 19 | **84%** | MEDIUM |
| `py2dataiku/models/dataiku_recipe.py` | 259 | 29 | **82%** | MEDIUM |
| `py2dataiku/models/prepare_step.py` | 310 | 29 | **86%** | MEDIUM |
| `py2dataiku/visualizers/svg_visualizer.py` | 77 | 12 | **86%** | MEDIUM |
| `py2dataiku/visualizers/ascii_visualizer.py` | 124 | 0 | **99%** | DONE |
| `py2dataiku/visualizers/html_visualizer.py` | 40 | 0 | **100%** | DONE |
| `py2dataiku/visualizers/themes.py` | 42 | 0 | **100%** | DONE |
| `py2dataiku/llm/schemas.py` | 105 | 0 | **100%** | DONE |

---

## 2. Specific Gaps Identified

### Gap 1: Validation Module - 0% Coverage (CRITICAL)
**File**: `py2dataiku/utils/validation.py`

The entire validation module (110 statements) has zero test coverage. This is critical because it validates recipe and flow configurations that users will export to Dataiku DSS.

**Missing tests**:
- `validate_recipe_config()` - tests with valid/invalid recipe configs
- `_validate_prepare_settings()` - various prepare step configurations
- `_validate_prepare_step()` - individual step validation with known/unknown processors
- `_validate_join_settings()` - join type validation, missing join conditions
- `_validate_grouping_settings()` - aggregation type validation
- `validate_flow()` - complete flow validation with cross-reference checks
- Error path: recipes referencing non-existent datasets

### Gap 2: PandasMapper - 0% Coverage (CRITICAL)
**File**: `py2dataiku/mappings/pandas_mappings.py`

The `PandasMapper` class (55 statements) has zero coverage. This is the core mapping logic used in the rule-based conversion path.

**Missing tests**:
- `get_recipe_type()` - for each recipe mapping
- `get_processor_type()` - for each processor mapping
- `get_string_mode()` - for all string accessor methods
- `get_agg_function()` - for all aggregation function mappings
- `get_join_type()` - for each join type
- `map_fillna()` with value, ffill, and bfill methods
- `map_dropna()` with and without subset
- `map_rename()` with various column mappings
- `map_drop_columns()` with single and multiple columns
- `map_astype()` for each dtype in the type_map
- `map_string_method()` for all string methods including replace, split, extract, contains
- `requires_python_recipe()` for python-only methods
- `get_alternative_suggestion()` for methods with suggestions

### Gap 3: ProcessorCatalog - 0% Coverage (HIGH)
**File**: `py2dataiku/mappings/processor_catalog.py`

Zero test coverage for the processor catalog that provides metadata used by the validation module.

**Missing tests**:
- `get_processor()` with valid and invalid processor names
- `list_processors()` with and without category filter
- `list_categories()` for all categories
- `get_required_params()` for processors with and without required params
- `get_example()` for valid and unknown processors

### Gap 4: DataFlowTracker - 23% Coverage (HIGH)
**File**: `py2dataiku/parser/dataflow_tracker.py`

Most of the DataFlowTracker class is untested. This tracks column lineage through pandas transformations.

**Missing tests**:
- `register_read()` - with and without columns
- `register_transformation()` - when source exists vs when it doesn't
- `register_column_add()` - adding new and existing columns
- `register_column_drop()` - dropping existing and non-existent columns
- `register_column_rename()` - renaming with mapping
- `register_merge()` - merging DataFrames with and without tracked columns
- `get_columns()` / `get_lineage()` / `get_source()` - for tracked and unknown variables
- `resolve_alias()` - including chained aliases

### Gap 5: PatternMatcher - 50% Coverage (HIGH)
**File**: `py2dataiku/parser/pattern_matcher.py`

Half the methods are not tested. Used internally by AST analysis.

**Missing tests**:
- `match_drop_duplicates()` with and without columns
- `match_rename()` with various mappings
- `match_drop_columns()` with multiple columns
- `match_astype()` for each dtype mapping
- `match_to_datetime()`
- `match_filter()` for each operator mapping
- `match_aggregation()` for all aggregation functions
- `match_join_type()` for all join types
- `match_regex_extract()` with and without output columns
- `match_split()` with various separators
- `requires_python_recipe()` for python-only methods

### Gap 6: LLM Analyzer Error Paths - 46% Coverage (HIGH)
**File**: `py2dataiku/llm/analyzer.py`

The LLM analyzer has many untested code paths, particularly error handling and edge cases.

**Missing tests**:
- `analyze()` with empty code string
- `analyze()` with code containing no recognizable operations
- `_build_prompt()` - prompt construction
- `_parse_response()` - response parsing with missing fields
- `_post_process()` - post-processing with various analysis results
- Error path: malformed JSON with nested structure
- Retry logic when JSON parsing fails

### Gap 7: LLM Flow Generator - 51% Coverage (HIGH)
**File**: `py2dataiku/generators/llm_flow_generator.py`

About half the code paths in the LLM flow generator are not tested.

**Missing tests**:
- `_generate_sort_recipe()` - SORT recipe generation
- `_generate_split_recipe()` - SPLIT recipe generation
- `_generate_distinct_recipe()` - DISTINCT recipe generation
- `_generate_pivot_recipe()` - PIVOT recipe generation
- `_generate_stack_recipe()` - STACK recipe generation
- `_generate_window_recipe()` - WINDOW recipe generation
- `_generate_python_recipe()` - code extraction and Python recipe creation
- Error handling: unknown operation types
- Multiple consecutive operations on same dataset
- Complex multi-step pipelines with branching

### Gap 8: Convenience API - 48% Coverage (HIGH)
**File**: `py2dataiku/__init__.py`

The top-level `convert()`, `convert_with_llm()`, and `Py2Dataiku` class have partial coverage.

**Missing tests**:
- `convert()` with `optimize=False`
- `convert_with_llm()` with mock provider
- `Py2Dataiku` class with `use_llm=False`
- `Py2Dataiku.convert()` with LLM fallback when API key is missing
- `Py2Dataiku.analyze()` when not in LLM mode (should raise ValueError)
- `Py2Dataiku.generate_diagram()` for all format types
- `Py2Dataiku.save_visualization()` for all formats and auto-detection

### Gap 9: LLM Providers Real API Paths - 52% Coverage (MEDIUM)
**File**: `py2dataiku/llm/providers.py`

The real `AnthropicProvider` and `OpenAIProvider` API call code paths are untested (expected without API keys, but error handling paths should be tested).

**Missing tests**:
- `AnthropicProvider.complete()` error handling (rate limits, API errors)
- `AnthropicProvider.complete_json()` JSON parsing failure paths
- `OpenAIProvider.complete()` error handling
- `MockProvider` with empty responses dictionary (default fallback)
- `MockProvider.complete_json()` with non-JSON custom response

### Gap 10: DataikuFlow Advanced Methods - 76% Coverage (MEDIUM)
**File**: `py2dataiku/models/dataiku_flow.py`

Several methods in `DataikuFlow` are partially covered.

**Missing tests**:
- `get_input_datasets()` - filtering input datasets
- `get_output_datasets()` - filtering output datasets
- `get_intermediate_datasets()` - filtering intermediate datasets
- `remove_dataset()` - dataset removal
- `remove_recipe()` - recipe removal
- `clone()` - flow cloning
- `validate()` with flows that have errors (isolated datasets, cycles)
- `merge()` - merging two flows
- Export methods: `to_png()` and `to_pdf()` (require cairosvg)
- `to_json()` full structure verification

### Gap 11: DataikuRecipe Advanced Configurations - 82% Coverage (MEDIUM)
**File**: `py2dataiku/models/dataiku_recipe.py`

Recipe types with complex configurations are not fully tested.

**Missing tests**:
- `create_stack()` - STACK recipe creation and JSON structure
- `create_split()` - SPLIT recipe with conditions
- `create_sort()` - SORT recipe with multiple columns/directions
- `create_distinct()` - DISTINCT recipe
- `create_pivot()` - PIVOT recipe configuration
- `create_window()` - WINDOW recipe with window functions
- `create_python()` - PYTHON recipe with code
- Recipe `to_json()` for JOIN with multiple keys and conditions
- Recipe `to_json()` for GROUPING with all aggregation types

### Gap 12: Interactive Visualizer - 18% Coverage (MEDIUM)
**File**: `py2dataiku/visualizers/interactive_visualizer.py`

The interactive visualizer is almost entirely untested.

**Missing tests**:
- `render()` - basic rendering produces valid HTML
- `render()` output contains node data, edge data, theme data
- `_build_nodes_json()` - dataset nodes include schema information
- `_build_nodes_json()` - recipe nodes include step count
- `_build_stats_json()` - statistics count correctly
- With dark theme
- With complex multi-input flows

### Gap 13: AST Analyzer Edge Cases - 75% Coverage (MEDIUM)
**File**: `py2dataiku/parser/ast_analyzer.py`

The AST analyzer has significant branches that are not covered.

**Missing tests**:
- Chained method calls: `df.str.upper().strip()`
- NumPy-based filtering: `df[np.where(...)]`
- Multiple assignment: `a = b = df.fillna(0)`
- Augmented assignment: `df['col'] += 1`
- Complex boolean filters: `df[(df['a'] > 1) & (df['b'] < 2)]`
- List comprehension in column operations
- Function definitions wrapping pandas operations
- `df.assign()` with multiple columns
- `df.pipe()` calls
- `df.loc[]` and `df.iloc[]` indexing
- `df.where()` and `df.mask()` operations
- Walrus operator (`:=`) assignments

---

## 3. Recommendations Ranked by Importance

### Priority 1: CRITICAL - Zero Coverage Modules

#### 1.1 Add `test_validation.py` (Complexity: Small)
```
tests/test_py2dataiku/test_validation.py
```
- Tests for `validate_recipe_config()` with all recipe types
- Tests for `validate_flow()` with complete and broken flows
- Tests for each private validation helper
- Error message verification for invalid configs
- Estimated: ~40 new test cases

#### 1.2 Add `test_pandas_mapper.py` (Complexity: Small)
```
tests/test_py2dataiku/test_pandas_mapper.py
```
- Unit tests for each mapping method in `PandasMapper`
- Tests for all string method mappings
- Tests for all aggregation function mappings
- Tests for all join type mappings
- Tests for `map_fillna()` with ffill, bfill, and value
- Estimated: ~50 new test cases

#### 1.3 Add `test_processor_catalog.py` (Complexity: Small)
```
tests/test_py2dataiku/test_processor_catalog.py
```
- Tests for `get_processor()` with valid/invalid names
- Tests for `list_processors()` with/without category
- Tests for `list_categories()`
- Verification that all processors have complete metadata
- Estimated: ~20 new test cases

### Priority 2: HIGH - Untested Core Logic

#### 2.1 Add `test_dataflow_tracker.py` (Complexity: Small)
```
tests/test_py2dataiku/test_dataflow_tracker.py
```
- Unit tests for each tracker method
- Tests for column lineage through transformations
- Tests for alias resolution chains
- Tests for merge tracking with unknown variables
- Estimated: ~30 new test cases

#### 2.2 Add `test_pattern_matcher.py` (Complexity: Small)
```
tests/test_py2dataiku/test_pattern_matcher.py
```
- Unit tests for each match method
- Tests for all filter operators
- Tests for string method dispatch
- Tests for `requires_python_recipe()` with all python-only methods
- Estimated: ~35 new test cases

#### 2.3 Expand `test_llm.py` with Error Paths (Complexity: Medium)
```
tests/test_py2dataiku/test_llm.py - additional test classes
```
- `TestLLMAnalyzerEdgeCases`: empty code, no-op code
- `TestLLMFlowGeneratorRecipeTypes`: SORT, SPLIT, DISTINCT, PIVOT, STACK, WINDOW
- `TestLLMProviderErrorHandling`: API error simulation, JSON parse failures
- Estimated: ~40 new test cases

#### 2.4 Expand Public API Tests (Complexity: Small)
```
tests/test_py2dataiku/test_api.py (new file)
```
- Tests for `convert()` and `convert_with_llm()` convenience functions
- Tests for `Py2Dataiku` class in both LLM and rule-based modes
- Tests for fallback when LLM initialization fails
- Tests for `save_visualization()` auto-format detection
- Estimated: ~25 new test cases

### Priority 3: MEDIUM - Incomplete Coverage

#### 3.1 Expand `test_models.py` with Advanced Recipe Types (Complexity: Medium)
- Add tests for `create_stack()`, `create_split()`, `create_sort()`, `create_distinct()`
- Add tests for `create_pivot()`, `create_window()`, `create_python()`
- Verify `to_json()` structure for each recipe type
- Add tests for `DataikuFlow.validate()` with error conditions
- Add tests for `DataikuFlow.get_input_datasets()`, `get_output_datasets()`
- Estimated: ~35 new test cases

#### 3.2 Add `test_interactive_visualizer.py` (Complexity: Small)
```
tests/test_py2dataiku/test_interactive_visualizer.py
```
- Test render produces valid HTML with canvas element
- Verify nodes JSON is embedded
- Verify edges JSON is embedded
- Verify theme JSON is embedded
- Test with dark theme
- Test with flow containing schema-aware datasets
- Estimated: ~15 new test cases

#### 3.3 Expand `test_integration.py` with Complex Patterns (Complexity: Medium)
- Add tests for chained pandas operations
- Add tests for complex boolean filter expressions
- Add tests for combined operations (read + filter + join + groupby)
- Add tests for code with function definitions
- Add tests for `df.loc[]` and `df.iloc[]` access patterns
- Estimated: ~20 new test cases

#### 3.4 Add `test_ast_edge_cases.py` (Complexity: Large)
```
tests/test_py2dataiku/test_ast_edge_cases.py
```
- Tests for complex method chaining
- Tests for multiple assignment targets
- Tests for augmented assignments
- Tests for list comprehension operations
- Tests for context manager patterns (`with`)
- Tests for exception handling around data operations
- Estimated: ~30 new test cases

### Priority 4: LOW - Demo Files and Niche Cases

#### 4.1 `demo.py` and `llm_demo.py` (0% coverage)
These are runnable demo scripts, not library code. Consider:
- Adding smoke tests that import and run the demo functions (with mocking)
- Or marking them to be excluded from coverage requirements

#### 4.2 `visualizers/base.py` (69% coverage)
- Add tests for the abstract base class with a concrete implementation
- Test that visualization returns strings
- Estimated: ~5 new test cases

---

## 4. Implementation Complexity Estimates

| Test Addition | New Tests | Complexity | Coverage Gain |
|--------------|-----------|------------|---------------|
| `test_validation.py` | ~40 | Small | +2.5% |
| `test_pandas_mapper.py` | ~50 | Small | +1.5% |
| `test_processor_catalog.py` | ~20 | Small | +0.5% |
| `test_dataflow_tracker.py` | ~30 | Small | +1.3% |
| `test_pattern_matcher.py` | ~35 | Small | +1.0% |
| `test_api.py` | ~25 | Small | +1.5% |
| `test_interactive_visualizer.py` | ~15 | Small | +1.2% |
| Expand `test_llm.py` | ~40 | Medium | +2.0% |
| Expand `test_models.py` | ~35 | Medium | +1.5% |
| Expand `test_integration.py` | ~20 | Medium | +1.0% |
| `test_ast_edge_cases.py` | ~30 | Large | +1.5% |
| **TOTAL** | **~340** | | **+15.5%** |

**Projected coverage after all additions: ~86%**

---

## 5. Shallow Test Analysis

Beyond raw coverage, several existing tests are shallow and should be strengthened:

### 5.1 `test_integration.py::TestCodeAnalyzer`
Most assertions check `len(transformations) >= 1` rather than verifying the specific transformation type, parameters, and values. These tests would pass even if the wrong transformation type was detected.

**Recommendation**: Add assertions for `transformation_type.value`, specific `parameters` keys, and `suggested_recipe`/`suggested_processor` values.

### 5.2 `test_cli.py::TestMainCommand`
Tests like `test_analyze_text` assert `len(captured.out) > 0` which is trivially true. The output content itself is not verified.

**Recommendation**: Verify the actual structure of CLI output (number of transformations, transformation types in text output).

### 5.3 `test_llm.py::TestLLMFlowGenerator::test_generate_python_fallback`
The test `assert any("PYTHON" in r.type for r in flow.recommendations)` may be fragile - `r.type` for recommendations might not be a string. Should verify the recommendation category attribute instead.

### 5.4 `test_models.py::TestDataikuFlow::test_validate`
Only tests the happy path. No tests for validation failures like cycles, dangling references, or empty flows.

### 5.5 `test_optimizer.py::TestFlowOptimizerIntegration::test_optimize_complex_flow`
Checks `len(result.recommendations) > 0` without verifying the content of recommendations or that optimization actually merged anything.

---

## 6. Missing Edge Case Tests

### 6.1 Recipe Type Coverage
These recipe types are in `RecipeType` enum but have no dedicated test for their complete JSON configuration:
- `STACK` - concatenation configuration
- `SPLIT` - condition-based splitting
- `SORT` - multi-column sort with directions
- `DISTINCT` - deduplication
- `TOP_N` - top N configuration
- `SAMPLING` - sampling configuration
- `PIVOT` - pivot configuration with aggregations
- `WINDOW` - window function configuration
- `PYTHON`, `R`, `SQL` - code recipe configurations
- ML recipes: `PREDICTION_SCORING`, `CLUSTERING_SCORING`, `EVALUATION`

### 6.2 Processor Type Coverage
Several ProcessorType values appear in enums but have no direct tests:
- `CLIP_COLUMN` - numeric clipping
- `BINNER` - binning with different modes
- `NORMALIZER` - normalization modes
- `FLAG_EMPTY` - empty flagging
- `FLAG_ON_DATE_RANGE` - date-based flagging
- `DATE_DIFFERENCE` - date arithmetic
- `DATE_AGGREGATOR` - date aggregation
- `TARGET_ENCODER` - ML encoding
- `CATEGORICAL_ENCODER` with specific modes

### 6.3 Error Propagation Tests
- `CodeAnalyzer.analyze()` with Unicode/non-ASCII code
- `CodeAnalyzer.analyze()` with very large code files (performance)
- `DataikuFlow.validate()` with circular dependencies
- `DSSExporter.export()` to a read-only directory (permission error)
- `LLMCodeAnalyzer.analyze()` with extremely long code

---

## 7. Test Pattern Observations

### What Existing Tests Do Well:
1. **Example libraries**: `recipe_examples`, `processor_examples`, `combination_examples` have comprehensive test coverage via dedicated test files
2. **Visualizers**: Core SVG, ASCII, PlantUML, HTML visualizers are well-tested with both happy paths and edge cases
3. **Optimizer**: `FlowOptimizer` and `RecipeMerger` have thorough unit and integration tests
4. **CLI**: Argument parsing and basic command execution are well covered

### Test Patterns to Replicate:
1. Class-level grouping with descriptive test class names (`TestClassName`)
2. Fixtures for reusable flow/dataset setups
3. Both positive and negative assertions in each test
4. Error path testing with `pytest.raises`

---

## 8. Quick Wins (Highest Impact, Lowest Effort)

1. **Create `test_validation.py`**: Zero coverage, pure Python logic, no dependencies - highest impact for effort ratio
2. **Create `test_pandas_mapper.py`**: Zero coverage, pure mapping logic - straightforward unit tests
3. **Create `test_processor_catalog.py`**: Zero coverage, static data structure tests
4. **Create `test_dataflow_tracker.py`**: Low coverage, stateful but simple class
5. **Create `test_pattern_matcher.py`**: 50% coverage, simple method dispatch tests

Together these 5 files would add ~175 tests and increase coverage by approximately +8%.
