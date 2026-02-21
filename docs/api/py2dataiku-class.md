# Py2Dataiku Class

Main converter class with hybrid LLM + rule-based approach.

```python
from py2dataiku import Py2Dataiku
```

---

## Constructor

```python
class Py2Dataiku:
    def __init__(
        self,
        provider: str = "anthropic",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        use_llm: bool = True,
    )
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `provider` | `str` | `"anthropic"` | LLM provider: `"anthropic"` or `"openai"` |
| `api_key` | `Optional[str]` | `None` | API key (uses environment variable if not provided) |
| `model` | `Optional[str]` | `None` | Model name override |
| `use_llm` | `bool` | `True` | Whether to use LLM (`True`) or rule-based (`False`) |

**Notes:**
- If `use_llm=True` but LLM initialization fails, automatically falls back to rule-based with a warning
- Rule-based mode does not require any API key

**Example:**

```python
# LLM mode (recommended)
converter = Py2Dataiku(provider="anthropic")

# Rule-based mode (offline)
converter = Py2Dataiku(use_llm=False)

# OpenAI with specific model
converter = Py2Dataiku(provider="openai", model="gpt-4o")
```

---

## Methods

### `convert()`

Convert Python code to a Dataiku flow.

```python
def convert(
    self,
    code: str,
    flow_name: str = "converted_flow",
    optimize: bool = True,
) -> DataikuFlow
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `code` | `str` | *required* | Python source code |
| `flow_name` | `str` | `"converted_flow"` | Name for the generated flow |
| `optimize` | `bool` | `True` | Whether to optimize the flow |

**Returns:** [`DataikuFlow`](models.md#dataikuflow)

---

### `analyze()`

Analyze code without generating flow (LLM mode only).

```python
def analyze(self, code: str) -> AnalysisResult
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `code` | `str` | *required* | Python source code |

**Returns:** [`AnalysisResult`](llm-providers.md#analysisresult)

**Raises:** `ValueError` if not in LLM mode

---

### `generate_diagram()`

Generate a diagram for a flow (legacy method).

```python
def generate_diagram(self, flow: DataikuFlow, format: str = "mermaid") -> str
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `flow` | `DataikuFlow` | *required* | Flow to visualize |
| `format` | `str` | `"mermaid"` | `"mermaid"`, `"graphviz"`, `"ascii"`, `"plantuml"` |

**Returns:** `str` - Diagram in the specified format

---

### `visualize()`

Generate Dataiku-style visualization of a flow.

```python
def visualize(self, flow: DataikuFlow, format: str = "svg", **kwargs) -> str
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `flow` | `DataikuFlow` | *required* | Flow to visualize |
| `format` | `str` | `"svg"` | `"svg"`, `"html"`, `"ascii"`, `"plantuml"`, `"mermaid"` |

**Returns:** `str` - Visualization in the specified format

---

### `save_visualization()`

Save flow visualization to a file.

```python
def save_visualization(
    self,
    flow: DataikuFlow,
    output_path: str,
    format: str = None,
) -> None
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `flow` | `DataikuFlow` | *required* | Flow to visualize |
| `output_path` | `str` | *required* | Path to save the file |
| `format` | `str` | `None` | Format (auto-detected from extension if `None`) |

**Auto-detected extensions:** `.svg`, `.html`/`.htm`, `.txt` (ASCII), `.puml` (PlantUML), `.png`, `.pdf`

**Notes:**
- PNG and PDF export require `cairosvg` to be installed
