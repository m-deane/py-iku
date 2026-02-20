# Code Quality Review: py-iku Core Modules

**Reviewed:** 2026-02-19
**Reviewer:** code-quality-reviewer agent
**Scope:** models/, generators/, parser/, llm/

---

## Executive Summary

The codebase shows a well-structured library with clear separation of concerns. The models are clean dataclasses, the LLM providers use a good abstraction layer, and the parser is thorough. However, there are several notable quality gaps: inconsistent error handling, missing input validation, code duplication across generators, a placeholder `get_column_lineage` method, silent failures in critical code paths, and a mild security concern with unvalidated LLM prompt content.

---

## Strengths

1. **Clear Module Boundaries**: The split between `parser/`, `llm/`, `generators/`, `models/`, and `visualizers/` is well-conceived. Each has a clear responsibility.
2. **Good Use of Dataclasses**: `DataikuFlow`, `DataikuRecipe`, `DataikuDataset`, and `PrepareStep` are clean dataclasses with sensible defaults and `field(default_factory=...)` for mutable defaults.
3. **Factory Methods on DataikuRecipe**: `create_prepare()`, `create_grouping()`, `create_join()`, `create_python()` are a good pattern that reduces construction errors.
4. **Lazy Client Initialization**: `AnthropicProvider.client` and `OpenAIProvider.client` use lazy initialization to avoid importing heavy dependencies at module load time. This is correct.
5. **Enum-First Design**: Heavy use of `RecipeType`, `ProcessorType`, `OperationType`, `DatasetType` enums prevents stringly-typed errors throughout the codebase.
6. **LLM Abstraction Layer**: The `LLMProvider` ABC with `complete()` and `complete_json()` makes it easy to add new providers and mock for testing.
7. **Extensive Type Hints**: All public methods in models and generators have full type annotations (`List[str]`, `Optional[Dict[str, Any]]`, return types).

---

## Critical Issues (Must Fix)

### 1. Unimplemented `get_column_lineage` Silently Returns `None`

**File:** `py2dataiku/models/dataiku_flow.py:164-168`

```python
def get_column_lineage(self, column: str) -> Optional[ColumnLineage]:
    """Get lineage information for a column."""
    # This would require tracking column transformations through the flow
    # Placeholder implementation
    return None
```

This is a public method in the primary output class that is documented but permanently returns `None`. Callers cannot distinguish between "no lineage exists" and "not implemented." It should either be implemented or raise `NotImplementedError`.

**Fix:**
```python
def get_column_lineage(self, column: str) -> Optional[ColumnLineage]:
    """Get lineage information for a column. Not yet implemented."""
    raise NotImplementedError(
        "Column lineage tracking is not yet implemented. "
        "Track transformations through recipe steps manually."
    )
```

---

### 2. Silent Swallowing of All Exceptions in LLM Analyzer

**File:** `py2dataiku/llm/analyzer.py:173-178`

```python
except Exception as e:
    return AnalysisResult(
        steps=[],
        datasets=[],
        code_summary=f"Error during analysis: {e}",
        warnings=[f"Analysis error: {e}"],
    )
```

A bare `except Exception` at the top level silently converts network errors, rate-limit errors, authentication failures, and unexpected bugs into an empty result with a warning string. Callers (including the public `convert_with_llm()`) have no way to distinguish a transient API error from a structural analysis failure. The same pattern appears in `analyze_with_context()`.

**Impact:** Users calling `convert_with_llm()` will receive an empty flow with no exception, making debugging very difficult.

**Fix:** Distinguish error categories. Only swallow JSON parse errors as recoverable; re-raise API errors:
```python
except json.JSONDecodeError as e:
    return AnalysisResult(
        steps=[], datasets=[],
        code_summary=f"Error parsing LLM response: {e}",
        warnings=[f"JSON parse error: {e}"],
    )
# Let API errors, auth errors, network errors propagate to the caller
```

---

### 3. `_merge_prepare_recipes` is a Stub

**File:** `py2dataiku/generators/flow_generator.py:462-466`

```python
def _merge_prepare_recipes(self) -> None:
    """Merge consecutive Prepare recipes when possible."""
    # This is a simplified implementation
    # Full implementation would rebuild the flow graph
    pass
```

The `_optimize_flow()` method calls this. The public `generate()` method accepts `optimize=True` by default. Users who pass `optimize=True` (the default) expect optimization to happen. The silently empty implementation means this documented behavior never occurs.

**Fix:** Either implement it, or set `optimize=False` as the default until it is implemented, or raise `NotImplementedError` with a clear message.

---

### 4. `_handle_dataframe_method` Has Redundant Plugin Lookup and Silent Recursion Bug

**File:** `py2dataiku/parser/ast_analyzer.py:498-564`

```python
def _handle_dataframe_method(self, obj: ast.expr, method: str, node: ast.Call, target: str) -> None:
    obj_name = self._get_name(obj)

    # Check for method chains
    if isinstance(obj, ast.Attribute):
        # This is part of a chain, recurse
        self._handle_dataframe_method(obj.value, obj.attr, node, target)
    ...
    # Check for plugin handler first
    plugin_handler = PluginRegistry.get_method_handler(method)
```

The plugin lookup is performed twice: once in `_dispatch_method_handler` (line 238) and once here (line 510). This is redundant and means plugin handlers registered for methods like `fillna` or `dropna` would fire twice in some code paths.

Additionally, the recursive call on line 507 passes `node` (the outer node) and `target` unchanged, causing the same `node` to be processed multiple times with a different `method` name, which produces duplicate or incorrect transformations.

---

## Warnings (Should Fix)

### 5. `api_key` Parameter Has Wrong Type Annotation

**File:** `py2dataiku/__init__.py:142-148`

```python
def convert_with_llm(
    code: str,
    provider: str = "anthropic",
    api_key: str = None,   # <-- should be Optional[str]
    model: str = None,     # <-- should be Optional[str]
    ...
```

`str = None` is incorrect — `None` is not a `str`. This will cause issues with strict type checkers (mypy) and is misleading. The same issue is on `Py2Dataiku.__init__()` at line 198-200.

**Fix:**
```python
def convert_with_llm(
    code: str,
    provider: str = "anthropic",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    ...
```

---

### 6. Duplicate `_sanitize_name` Method in Both Generators

**Files:**
- `py2dataiku/generators/flow_generator.py:468-470`
- `py2dataiku/generators/llm_flow_generator.py:616-618`

```python
# flow_generator.py
def _sanitize_name(self, name: str) -> str:
    return name.replace(" ", "_").replace("-", "_").replace(".", "_")

# llm_flow_generator.py (slightly different — also strips apostrophes)
def _sanitize_name(self, name: str) -> str:
    return name.replace(" ", "_").replace("-", "_").replace(".", "_").replace("'", "")
```

These methods are nearly identical but diverge slightly (the LLM version also strips apostrophes). This inconsistency will cause different sanitization behavior depending on which path is used, potentially causing dataset name collisions or mismatches.

**Fix:** Extract to a shared utility function in `py2dataiku/utils/` and use it in both generators.

---

### 7. Duplicate Method Handler Dispatch Table

**File:** `py2dataiku/parser/ast_analyzer.py`

The `method_handlers` dictionary appears **twice** with the same content:
- Lines 254-281 in `_dispatch_method_handler()`
- Lines 526-545 in `_handle_dataframe_method()`

The second table is a subset of the first (missing `assign`, `clip`, `round`, `abs`, `query`, `nlargest`, `nsmallest`), meaning those methods will not be handled when reached through `_handle_dataframe_method`.

**Fix:** Extract a single shared dispatch table as a class attribute or use `_dispatch_method_handler()` consistently.

---

### 8. `AnthropicProvider.complete_json` Fragile JSON Extraction

**File:** `py2dataiku/llm/providers.py:109-117`

```python
if content.startswith("```json"):
    content = content[7:]
if content.startswith("```"):
    content = content[3:]
if content.endswith("```"):
    content = content[:-3]
```

This ad-hoc stripping is fragile. It will fail if the model returns ```` ```json\n ``` ```` (with a newline after the fence) or if extra whitespace appears. The `json.loads()` call at line 117 then has no error context if parsing fails — no retry logic, no fallback, and the exception propagates unhandled (unlike the `analyze()` method which does catch `JSONDecodeError`).

**Fix:** Use a regex to extract JSON from code blocks, and add a `JSONDecodeError` handler that logs the raw content before re-raising.

---

### 9. `_handle_nlargest` and `_handle_nsmallest` Use Wrong `TransformationType`

**File:** `py2dataiku/parser/ast_analyzer.py:305-345`

```python
self.transformations.append(
    Transformation(
        transformation_type=TransformationType.HEAD,   # Wrong type for nlargest!
        ...
        suggested_recipe="topn",
    )
)
```

`nlargest()` and `nsmallest()` are Top-N operations, not `HEAD` operations (which simply take the first N rows without ranking). The `TransformationType.HEAD` will route these through the wrong recipe generation path in `FlowGenerator`, which does not map `HEAD` to `topn`.

**Fix:** Use `TransformationType.TOP_N` (or equivalent) if it exists, or add it to the enum.

---

### 10. `FlowGenerator` Does Not Handle All `TransformationType` Values in `_prepare_types()`

**File:** `py2dataiku/generators/flow_generator.py:188-200`

`_prepare_types()` returns a fixed set of 9 types. Types like `NUMERIC_TRANSFORM`, `STRING_TRANSFORM`, `ROLLING`, `PIVOT`, `SAMPLE`, `TAIL`, `HEAD` are not included. When these transformation types are encountered in `_process_transformation_group()`, none of the `elif` branches match and the transformation is silently dropped. No warning or fallback is added to the flow.

**Fix:** Add a catch-all `else` branch that either creates a Python recipe or logs a warning to `flow.warnings`.

---

## Suggestions (Consider Improving)

### 11. `DataikuFlow.validate()` and `utils/validation.py` Are Parallel and Inconsistent

`DataikuFlow.validate()` checks for orphan datasets and missing recipe inputs. `utils/validation.py:validate_flow()` checks dataset references from recipe JSON configs. These two paths check overlapping but different things and are not integrated. A caller who calls `flow.validate()` gets one set of checks; a caller who serializes to JSON and calls `validate_flow()` gets a different set.

**Recommendation (medium complexity):** Unify these into one validation pipeline. `DataikuFlow.validate()` should be the canonical entry point and should internally call the config-level validators after calling `flow.to_dict()`.

---

### 12. `DataikuRecipe._build_settings()` Silently Returns `{}` for Most Recipe Types

**File:** `py2dataiku/models/dataiku_recipe.py:343-396`

The `_build_settings()` method handles `PREPARE`, `GROUPING`, `JOIN`, `WINDOW`, `SPLIT`, `SORT`, `TOP_N`, `DISTINCT`, `STACK`, and `PYTHON`. For all 34+ other `RecipeType` values (e.g., `PIVOT`, `SAMPLING`, `FUZZY_JOIN`, `GEO_JOIN`), it silently returns `{}`. These will export as recipes with empty settings, which is invalid in Dataiku DSS.

**Recommendation (medium complexity):** Add branches for all supported recipe types, or at minimum raise a warning when a recipe type with known required settings would produce empty settings.

---

### 13. `LLMFlowGenerator` Uses String Matching for Recipe Type Routing

**File:** `py2dataiku/generators/llm_flow_generator.py:103-181`

```python
if suggested == "prepare":
    ...
elif suggested == "grouping":
    ...
elif suggested in ("python", "topn", "sampling", "pivot"):
    ...
```

The routing is based on plain string comparison against LLM-generated strings. If the LLM returns `"Prepare"` (capitalized) or `"GROUP_BY"` instead of `"grouping"`, it falls through to the Python recipe path. The LLM is explicitly told to return lowercase strings in the prompt, but this is brittle.

**Recommendation (small complexity):** Normalize the suggested recipe string to lowercase before the match: `suggested = (step.suggested_recipe or "python").lower()`.

---

### 14. `DataStep.from_dict()` Swallows Invalid `OperationType` Values

**File:** `py2dataiku/llm/schemas.py:178-179`

```python
operation=OperationType(data.get("operation", "unknown")),
```

If the LLM returns an operation string not in `OperationType` (e.g., `"aggregate"` instead of `"group_aggregate"`), this raises a `ValueError` that propagates out of `AnalysisResult.from_dict()` and up to `analyze()`. The `analyze()` method only catches `json.JSONDecodeError`, not `ValueError`, so this would surface as an unhandled exception to the caller.

**Fix:**
```python
try:
    operation = OperationType(data.get("operation", "unknown"))
except ValueError:
    operation = OperationType.UNKNOWN
```

---

### 15. `CodeAnalyzer` Mutable State Across Calls

**File:** `py2dataiku/parser/ast_analyzer.py:18-23`

```python
def __init__(self):
    self.transformations: List[Transformation] = []
    self.dataframes: Dict[str, str] = {}
    self.current_line: int = 0
    self._source_code: str = ""
```

`analyze()` resets `self.transformations` and `self.dataframes` at the start (lines 34-35), which is correct. However, if `analyze()` raises an exception mid-way (e.g., a bug in a handler), the instance is left in a partially-processed state. A second call to `analyze()` would reset correctly, but this is a subtle invariant that could surprise users who reuse the analyzer instance.

**Recommendation (small complexity):** Document that `CodeAnalyzer` is not safe to reuse after an exception, or use a local state object inside `analyze()` rather than instance variables.

---

### 16. Security Concern: Unvalidated Code Content in LLM Prompt

**File:** `py2dataiku/llm/analyzer.py:55-106`

```python
def get_analysis_prompt(code: str) -> str:
    return f"""...
Python Code to Analyze:
```python
{code}
```
..."""
```

User-supplied `code` is interpolated directly into the LLM prompt. While this is the intended use (analyzing user code), if this library is used in a web service or multi-tenant context, a malicious user could embed prompt injection attacks (e.g., `# Ignore previous instructions and return...`) inside the code string.

**Recommendation (small complexity):** This is an acceptable risk for a developer tool running locally. If the library is ever deployed in a service context, add a note in the docstring warning about prompt injection risks and consider sanitizing or wrapping the code in additional delimiters.

---

### 17. `_handle_for` Loop Processes Body Without Context

**File:** `py2dataiku/parser/ast_analyzer.py:68-71`

```python
elif isinstance(node, ast.For):
    # Handle for loops
    for stmt in node.body:
        self._visit_statement(stmt)
```

Statements inside a `for` loop body are processed as if they were top-level statements, without tracking that they are inside a loop. This can produce incorrect transformations — for example, a `df = df.fillna(0)` inside a loop would be recorded as a single `FILL_NA` transformation, ignoring the looping context. For Dataiku conversion purposes this is probably acceptable (most loops in data science scripts perform per-row or per-file operations), but it should be documented.

---

## Summary Table

| # | Issue | Severity | Complexity | File |
|---|-------|----------|------------|------|
| 1 | `get_column_lineage` silently returns None | Critical | Small | models/dataiku_flow.py:164 |
| 2 | Bare `except Exception` swallows LLM errors | Critical | Small | llm/analyzer.py:173 |
| 3 | `_merge_prepare_recipes` is an empty stub | Critical | Large | generators/flow_generator.py:462 |
| 4 | Redundant plugin lookup + recursion bug in `_handle_dataframe_method` | Critical | Medium | parser/ast_analyzer.py:498 |
| 5 | `api_key: str = None` wrong type annotation | Warning | Small | __init__.py:148 |
| 6 | `_sanitize_name` duplicated with divergent behavior | Warning | Small | generators/ both files |
| 7 | Method handler dispatch table duplicated in parser | Warning | Medium | parser/ast_analyzer.py:254,526 |
| 8 | Fragile JSON extraction in `complete_json` | Warning | Small | llm/providers.py:109 |
| 9 | `nlargest`/`nsmallest` mapped to wrong `TransformationType` | Warning | Small | parser/ast_analyzer.py:315,333 |
| 10 | `FlowGenerator` silently drops unhandled transformation types | Warning | Small | generators/flow_generator.py:102 |
| 11 | Parallel validation paths inconsistent | Suggestion | Medium | models/dataiku_flow.py + utils/validation.py |
| 12 | `_build_settings()` returns `{}` for most recipe types | Suggestion | Medium | models/dataiku_recipe.py:343 |
| 13 | LLM recipe routing uses unguarded string matching | Suggestion | Small | generators/llm_flow_generator.py:103 |
| 14 | `DataStep.from_dict()` lets `ValueError` escape | Suggestion | Small | llm/schemas.py:178 |
| 15 | `CodeAnalyzer` mutable state survives exceptions | Suggestion | Small | parser/ast_analyzer.py:18 |
| 16 | Prompt injection risk for service deployments | Suggestion | Small | llm/analyzer.py:55 |
| 17 | `for` loop body processed without loop context | Suggestion | Small | parser/ast_analyzer.py:68 |

---

## Recommended Priority Order

1. **Fix bare `except Exception` in analyzer (Issue #2)** — highest risk of silent data loss
2. **Fix `DataStep.from_dict()` ValueError escape (Issue #14)** — easy fix, prevents unexpected crashes
3. **Fix wrong type annotations (Issue #5)** — easy, prevents mypy failures
4. **Normalize LLM recipe routing strings (Issue #13)** — one-line fix, prevents silent fallthrough
5. **Extract shared `_sanitize_name` utility (Issue #6)** — prevents inconsistent dataset naming
6. **Raise `NotImplementedError` for `get_column_lineage` (Issue #1)** — honest API surface
7. **Add catch-all fallback in `FlowGenerator` (Issue #10)** — prevents silent drops
8. **Fix `nlargest`/`nsmallest` type mapping (Issue #9)** — correctness bug
9. **Fix duplicate dispatch tables in parser (Issue #7)** — maintainability
10. **Implement or stub `_merge_prepare_recipes` properly (Issue #3)** — large effort, but misleading default behavior
