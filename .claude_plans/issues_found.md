# py-iku Issues Found During Testing

**Date:** 2026-01-12
**Testing Type:** Comprehensive library testing

---

## Critical Issues

*None found - library is stable and functional*

---

## Major Issues

### Issue #1: Syntax Errors Not Raised

**Severity:** Major
**Component:** `py2dataiku/parser/ast_analyzer.py`

**Description:**
Invalid Python syntax in input code returns an empty flow (0 recipes, 0 datasets) instead of raising a `SyntaxError` exception.

**Steps to Reproduce:**
```python
from py2dataiku import convert

code = "df = invalid_syntax("  # Missing closing paren
flow = convert(code)
print(len(flow.recipes))  # Prints 0 instead of raising error
```

**Expected Behavior:**
Should raise `SyntaxError` with line number and error message.

**Actual Behavior:**
Returns empty `DataikuFlow` with 0 recipes, 0 datasets.

**Impact:**
Users may not realize their input code is invalid, leading to confusion.

**Suggested Fix:**
```python
# In ast_analyzer.py
def analyze(self, code: str):
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise SyntaxError(f"Invalid Python syntax: {e.msg}") from e
```

---

### Issue #2: Chained Method Calls Not Parsed

**Severity:** Major
**Component:** `py2dataiku/parser/ast_analyzer.py`

**Description:**
Chained pandas method calls like `df.dropna().fillna().sort_values()` are not properly parsed and produce 0 recipes.

**Steps to Reproduce:**
```python
from py2dataiku import convert

code = '''
import pandas as pd
df = pd.read_csv('data.csv')
result = df.dropna().fillna(0).sort_values('col').head(10)
result.to_csv('output.csv')
'''

flow = convert(code)
print(len(flow.recipes))  # Prints 0, should be 1+ recipes
```

**Expected Behavior:**
Should generate PREPARE recipe with multiple steps (REMOVE_ROWS_ON_EMPTY, FILL_EMPTY_WITH_VALUE) and SORT/TOP_N recipes.

**Actual Behavior:**
Returns flow with only input dataset detected.

**Impact:**
Common pandas pattern (method chaining) not supported.

---

### Issue #3: Missing Public API Exports

**Severity:** Major
**Component:** `py2dataiku/__init__.py`

**Description:**
Core model classes are not exported from the main module, requiring users to import from submodules.

**Missing Exports:**
- `PrepareStep`
- `RecipeType`
- `ProcessorType`
- `DatasetType`

**Steps to Reproduce:**
```python
from py2dataiku import RecipeType  # ImportError
from py2dataiku.models import RecipeType  # Works but inconsistent
```

**Suggested Fix:**
Add to `py2dataiku/__init__.py`:
```python
from .models import PrepareStep, RecipeType, ProcessorType, DatasetType
```

---

## Minor Issues

### Issue #4: Validation Returns Unexpected Format

**Severity:** Minor
**Component:** `py2dataiku/models/dataiku_flow.py`

**Description:**
`flow.validate()` returns `['valid', 'errors', 'warnings', 'info']` instead of a list of actual validation errors.

**Steps to Reproduce:**
```python
from py2dataiku import convert

flow = convert("import pandas as pd")
errors = flow.validate()
print(errors)  # ['valid', 'errors', 'warnings', 'info']
```

**Expected Behavior:**
Should return list of validation errors/warnings, or empty list if valid.

---

### Issue #5: Zero Coverage on Optimizer Module

**Severity:** Minor
**Component:** `py2dataiku/optimizer/`

**Description:**
`flow_optimizer.py` and `recipe_merger.py` have 0% test coverage.

**Impact:**
Optimization functionality may have untested bugs.

**Suggested Fix:**
Add `tests/test_py2dataiku/test_optimizer.py` with comprehensive tests.

---

### Issue #6: Zero Coverage on Mappings Module

**Severity:** Minor
**Component:** `py2dataiku/mappings/`

**Description:**
`pandas_mappings.py` and `processor_catalog.py` have 0% test coverage.

**Impact:**
Core mapping logic untested.

---

### Issue #7: PrepareStep Parameter Naming

**Severity:** Minor
**Component:** Documentation / `py2dataiku/models/prepare_step.py`

**Description:**
PrepareStep uses `params` parameter but some documentation references `settings`.

**Correct Usage:**
```python
step = PrepareStep(
    processor_type=ProcessorType.COLUMN_RENAMER,
    params={'column': 'old_name', 'new_name': 'new_name'}
)
```

---

### Issue #8: YAML Serialization Performance

**Severity:** Minor
**Component:** `py2dataiku/models/dataiku_flow.py`

**Description:**
YAML serialization is significantly slower than other formats.

**Benchmarks:**
- `to_dict()`: 0.04ms
- `to_json()`: 0.30ms
- `to_yaml()`: 6.66ms (166x slower than dict)

**Impact:**
Minor performance issue for large flows.

---

## Documentation Gaps

### Gap #1: Chained Operations

**Location:** CLAUDE.md, README.md

**Issue:**
No documentation on limitations of chained method call parsing.

### Gap #2: PrepareStep Parameters

**Location:** CLAUDE.md

**Issue:**
Documentation inconsistently references `settings` vs `params`.

### Gap #3: Optimizer Module

**Location:** All docs

**Issue:**
No documentation on optimizer functionality and usage.

---

## Edge Cases to Handle

### Edge Case #1: Very Long Column Names

**Status:** Handled (truncation in visualization)

### Edge Case #2: Special Characters in Names

**Status:** Handled (escaping works)

### Edge Case #3: Empty Flow Visualization

**Status:** Handled (produces minimal valid output)

### Edge Case #4: Single Dataset Flow

**Status:** Handled

### Edge Case #5: 100+ DataFrame Operations

**Status:** Handled (linear performance scaling)

---

## Test Coverage Gaps

| Module | Current | Target |
|--------|---------|--------|
| optimizer/flow_optimizer.py | 0% | 80% |
| optimizer/recipe_merger.py | 0% | 80% |
| mappings/pandas_mappings.py | 0% | 80% |
| mappings/processor_catalog.py | 0% | 80% |
| utils/validation.py | 0% | 80% |
| parser/dataflow_tracker.py | 23% | 70% |
| llm/analyzer.py | 46% | 60% |
| llm/providers.py | 52% | 60% |

---

## Reproducible Test Cases

### Test: Syntax Error Handling
```python
def test_syntax_error_raises():
    from py2dataiku import convert
    import pytest

    with pytest.raises(SyntaxError):
        convert("df = invalid_syntax(")
```

### Test: Chained Methods
```python
def test_chained_methods():
    from py2dataiku import convert

    code = '''
    import pandas as pd
    df = pd.read_csv('data.csv')
    result = df.dropna().fillna(0).sort_values('col')
    result.to_csv('output.csv')
    '''

    flow = convert(code)
    assert len(flow.recipes) >= 1, "Chained methods should produce recipes"
```

### Test: Public Exports
```python
def test_public_exports():
    from py2dataiku import (
        convert,
        DataikuFlow,
        DataikuRecipe,
        PrepareStep,
        RecipeType,
        ProcessorType,
        DatasetType,
    )
    assert RecipeType.PREPARE is not None
```

---

## Priority Summary

| Priority | Count | Examples |
|----------|-------|----------|
| Critical | 0 | - |
| Major | 3 | Syntax errors, chained methods, missing exports |
| Minor | 5 | Validation format, coverage gaps |
| Doc gaps | 3 | Chained ops, params naming, optimizer docs |
