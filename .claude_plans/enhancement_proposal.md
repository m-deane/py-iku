# py-iku Enhancement Proposal

**Date:** 2026-01-12
**Based on:** Comprehensive Library Testing

---

## Priority Matrix

| Enhancement | Impact | Effort | Priority |
|-------------|--------|--------|----------|
| Fix missing public exports | High | Low | P0 |
| Fix syntax error handling | High | Low | P0 |
| Add optimizer tests | Medium | Low | P0 |
| Chained method parsing | High | Medium | P1 |
| scikit-learn support | High | High | P1 |
| Plugin architecture | High | High | P1 |
| More pandas operations | High | Medium | P1 |
| Interactive visualization | Medium | High | P2 |
| Direct DSS export | High | Medium | P2 |
| CLI improvements | Medium | Low | P2 |
| IDE integration | Medium | High | P3 |

---

## P0: Critical Fixes (Immediate)

### 1. Add Missing Public Exports

**Problem:** `PrepareStep`, `RecipeType`, `ProcessorType`, `DatasetType` not exported from main module.

**Solution:**

```python
# py2dataiku/__init__.py - Add to exports

from .models import (
    PrepareStep,
    RecipeType,
    ProcessorType,
    DatasetType,
)

__all__ = [
    # ... existing exports
    'PrepareStep',
    'RecipeType',
    'ProcessorType',
    'DatasetType',
]
```

**Effort:** 15 minutes

### 2. Fix Syntax Error Handling

**Problem:** Invalid Python syntax returns empty flow instead of raising exception.

**Solution:**

```python
# py2dataiku/parser/ast_analyzer.py

def analyze(self, code: str) -> AnalysisResult:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise SyntaxError(f"Invalid Python syntax at line {e.lineno}: {e.msg}") from e
    # ... rest of analysis
```

**Effort:** 30 minutes

### 3. Add Optimizer Module Tests

**Problem:** `optimizer/flow_optimizer.py` and `optimizer/recipe_merger.py` have 0% coverage.

**Solution:** Create `tests/test_py2dataiku/test_optimizer.py`:

```python
import pytest
from py2dataiku.optimizer import FlowOptimizer, RecipeMerger
from py2dataiku.models import DataikuFlow, DataikuRecipe, RecipeType

class TestFlowOptimizer:
    def test_optimize_empty_flow(self):
        flow = DataikuFlow(name="test")
        optimizer = FlowOptimizer()
        optimized = optimizer.optimize(flow)
        assert optimized is not None

    def test_optimize_single_recipe(self):
        # ... test implementation

class TestRecipeMerger:
    def test_merge_compatible_recipes(self):
        # ... test implementation
```

**Effort:** 2-3 hours

---

## P1: High-Priority Features

### 4. Chained Method Parsing

**Problem:** `df.dropna().fillna().sort_values()` chains produce 0 recipes.

**Current behavior:** Only standalone operations are detected.

**Solution approach:**

1. Modify AST analyzer to track method call chains
2. Build operation sequence from chained calls
3. Generate appropriate recipes for the sequence

```python
# Pseudocode for enhanced parsing
def analyze_chain(self, node: ast.Call) -> List[Operation]:
    operations = []
    current = node

    while isinstance(current, ast.Call):
        if isinstance(current.func, ast.Attribute):
            op = self.parse_method_call(current)
            operations.insert(0, op)  # Prepend to maintain order
            current = current.func.value
        else:
            break

    return operations
```

**Effort:** 1-2 days

### 5. scikit-learn Support

**Problem:** No support for ML preprocessing operations.

**Proposed mappings:**

| scikit-learn | Dataiku Processor |
|--------------|-------------------|
| StandardScaler | STANDARD_SCALER |
| MinMaxScaler | MIN_MAX_SCALER |
| LabelEncoder | LABEL_ENCODER |
| OneHotEncoder | ONE_HOT_ENCODER |
| train_test_split | SPLIT recipe |
| Pipeline | Recipe chain |

**Implementation:**

1. Add scikit-learn patterns to `parser/pattern_matcher.py`
2. Add sklearn → Dataiku mappings to `mappings/`
3. Create examples in `examples/sklearn_examples.py`
4. Add tests

**Effort:** 3-5 days

### 6. Plugin Architecture

**Problem:** No way to add custom recipe/processor types without modifying core code.

**Proposed design:**

```python
# Usage
from py2dataiku import register_recipe_type, register_processor

@register_recipe_type("CUSTOM_TRANSFORM")
class CustomTransformRecipe:
    def from_pandas(self, call: ast.Call) -> DataikuRecipe:
        # Custom parsing logic
        pass

@register_processor("CUSTOM_PROCESSOR")
class CustomProcessor:
    def from_pandas(self, call: ast.Call) -> PrepareStep:
        pass

# In py2dataiku/__init__.py
_recipe_registry = {}
_processor_registry = {}

def register_recipe_type(name: str):
    def decorator(cls):
        _recipe_registry[name] = cls
        return cls
    return decorator
```

**Effort:** 1-2 weeks

### 7. Additional pandas Operations

**Currently missing:**
- `df.apply()` with lambda functions
- `df.pipe()` for chained operations
- `df.transform()` for grouped transformations
- `df.explode()` for list columns
- `df.melt()` and `df.wide_to_long()`
- `df.query()` for filtering

**Implementation:**

```python
# mappings/pandas_mappings.py additions

PANDAS_TO_DATAIKU = {
    # Existing...

    # New mappings
    'apply': {
        'recipe': RecipeType.PREPARE,
        'processor': ProcessorType.PYTHON_UDF,
    },
    'explode': {
        'recipe': RecipeType.PREPARE,
        'processor': ProcessorType.ARRAY_UNFOLD,
    },
    'melt': {
        'recipe': RecipeType.PIVOT,  # Unpivot operation
        'settings': {'mode': 'UNPIVOT'}
    },
    'query': {
        'recipe': RecipeType.PREPARE,
        'processor': ProcessorType.FILTER_ON_FORMULA,
    },
}
```

**Effort:** 2-3 days

---

## P2: Medium-Priority Features

### 8. Interactive Visualization

**Concept:** Web-based flow editor with drag-and-drop.

**Technologies:**
- React/Vue frontend
- D3.js or Cytoscape.js for graph rendering
- WebSocket for real-time updates

**Features:**
- Drag-and-drop recipe/dataset placement
- Click to inspect recipe details
- Live code-to-flow preview
- Export to SVG/PNG

**Effort:** 2-4 weeks

### 9. Direct DSS Export

**Problem:** No direct export to Dataiku DSS project format.

**Proposed format:**

```
project_export/
├── project.json           # Project metadata
├── recipes/
│   ├── prepare_1.json    # Recipe configurations
│   └── join_2.json
├── datasets/
│   ├── input_data.json   # Dataset definitions
│   └── output_data.json
└── flow.json             # Flow connections
```

**Implementation:**

```python
class DSSExporter:
    def export(self, flow: DataikuFlow, output_dir: str):
        # Create project structure
        # Export each recipe in DSS format
        # Export dataset definitions
        # Create flow.json with connections
```

**Effort:** 1 week

### 10. CLI Improvements

**Current:** Library-only, no CLI.

**Proposed CLI:**

```bash
# Convert file
py2dataiku convert input.py -o flow.json

# Convert with visualization
py2dataiku convert input.py --viz svg -o flow.svg

# Watch mode
py2dataiku watch input.py --format ascii

# Validate flow
py2dataiku validate flow.json
```

**Implementation:**

```python
# py2dataiku/cli.py
import click

@click.group()
def cli():
    pass

@cli.command()
@click.argument('input_file')
@click.option('-o', '--output', default='-')
@click.option('--format', default='json')
def convert(input_file, output, format):
    # Implementation
```

**Effort:** 2-3 days

---

## P3: Future Enhancements

### 11. IDE Integration

**VS Code Extension:**
- Syntax highlighting for py-iku configs
- Real-time flow preview panel
- Code lens showing recipe types
- Auto-complete for Dataiku types

**Jupyter Integration:**
- Magic command: `%%py2dataiku`
- Inline flow visualization
- Interactive recipe inspection

**Effort:** 2-4 weeks per IDE

### 12. NumPy Operation Support

**Mappings:**

| NumPy | Dataiku |
|-------|---------|
| `np.where()` | FORMULA processor |
| `np.clip()` | CLIP_COLUMN processor |
| `np.log()` | LOG_TRANSFORMER processor |
| `np.abs()` | ABS_COLUMN processor |

**Effort:** 1 week

### 13. Documentation Generation

**Auto-generate:**
- Flow documentation (Markdown/HTML)
- Column lineage reports
- Data quality expectations
- Recipe dependency graphs

**Effort:** 1 week

---

## Implementation Roadmap

### Phase 1: Stabilization (Week 1)
- [ ] P0.1: Add missing exports
- [ ] P0.2: Fix syntax error handling
- [ ] P0.3: Add optimizer tests
- [ ] Increase coverage to 75%

### Phase 2: Core Enhancements (Weeks 2-3)
- [ ] P1.4: Chained method parsing
- [ ] P1.7: Additional pandas operations
- [ ] P2.10: CLI implementation

### Phase 3: Advanced Features (Weeks 4-6)
- [ ] P1.5: scikit-learn support
- [ ] P2.9: Direct DSS export
- [ ] P1.6: Plugin architecture (design)

### Phase 4: Ecosystem (Weeks 7+)
- [ ] P2.8: Interactive visualization
- [ ] P3.11: VS Code extension
- [ ] P3.12: NumPy support

---

## Technical Debt to Address

1. **Inconsistent parameter naming** - `params` vs `settings`
2. **Validation return format** - Should return list of ValidationError objects
3. **LLM fallback logging** - Should use proper logging instead of print
4. **Type hints** - Some modules missing comprehensive type hints
5. **Docstrings** - Some public methods lack docstrings

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Test coverage | 66% | 85% |
| Recipe types | 37 | 45+ |
| Processor types | 112 | 130+ |
| pandas operations | ~30 | 60+ |
| Documentation pages | 4 | 10+ |

---

## Resource Requirements

| Phase | Estimated Effort | Skills Needed |
|-------|-----------------|---------------|
| Phase 1 | 1 week | Python, pytest |
| Phase 2 | 2 weeks | Python, AST, pandas |
| Phase 3 | 3 weeks | Python, Dataiku DSS |
| Phase 4 | 4+ weeks | React, TypeScript, VS Code API |

---

## Appendix: Feature Request Template

```markdown
## Feature: [Name]

### Problem
[What problem does this solve?]

### Proposed Solution
[How should it work?]

### Example Usage
```python
# Code example
```

### Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

### Priority
[P0/P1/P2/P3]
```
