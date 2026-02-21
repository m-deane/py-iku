# Core Functions

Top-level convenience functions for converting Python code to Dataiku DSS flows.

All functions are importable directly from `py2dataiku`:

```python
from py2dataiku import convert, convert_with_llm, convert_file, convert_file_with_llm
```

---

## `convert()`

Convert Python code to a Dataiku flow using rule-based AST analysis.

```python
def convert(code: str, optimize: bool = True) -> DataikuFlow
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `code` | `str` | *required* | Python source code string |
| `optimize` | `bool` | `True` | Whether to optimize the flow (merge recipes, remove orphan datasets) |

**Returns:** [`DataikuFlow`](models.md#dataikuflow) - The converted pipeline

**Example:**

```python
from py2dataiku import convert

flow = convert("""
import pandas as pd
df = pd.read_csv('sales.csv')
df = df.dropna(subset=['amount'])
df['amount'] = df['amount'].round(2)
result = df.groupby('region').agg({'amount': 'sum'})
result.to_csv('summary.csv')
""")

print(flow.get_summary())
# Datasets: 2 (1 input, 1 output)
# Recipes: 2 (1 prepare, 1 grouping)
```

**Notes:**
- This is the legacy method using AST pattern matching
- Fast and deterministic but less accurate for complex code
- For better results with complex pipelines, use [`convert_with_llm()`](#convert_with_llm)

---

## `convert_with_llm()`

Convert Python code to a Dataiku flow using LLM-based semantic analysis.

```python
def convert_with_llm(
    code: str,
    provider: str = "anthropic",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    optimize: bool = True,
    flow_name: str = "converted_flow",
) -> DataikuFlow
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `code` | `str` | *required* | Python source code string |
| `provider` | `str` | `"anthropic"` | LLM provider: `"anthropic"` or `"openai"` |
| `api_key` | `Optional[str]` | `None` | API key (uses `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` env var if not provided) |
| `model` | `Optional[str]` | `None` | Model name (provider default if not specified) |
| `optimize` | `bool` | `True` | Whether to optimize the flow |
| `flow_name` | `str` | `"converted_flow"` | Name for the generated flow |

**Returns:** [`DataikuFlow`](models.md#dataikuflow) - The converted pipeline

**Raises:**
- [`ProviderError`](exceptions.md#providererror) - If LLM communication fails
- [`LLMResponseParseError`](exceptions.md#llmresponseparseerror) - If LLM response cannot be parsed
- [`ConversionError`](exceptions.md#conversionerror) - If flow generation fails

**Example:**

```python
from py2dataiku import convert_with_llm

flow = convert_with_llm("""
import pandas as pd
from sklearn.preprocessing import StandardScaler

df = pd.read_csv('customers.csv')
df = df.merge(pd.read_csv('orders.csv'), on='customer_id')
df['total_spent'] = df.groupby('customer_id')['amount'].transform('sum')
scaler = StandardScaler()
df[['total_spent']] = scaler.fit_transform(df[['total_spent']])
""", provider="anthropic")

print(flow.visualize(format="ascii"))
```

**Notes:**
- This is the recommended method for production use
- Requires an API key (set via parameter or environment variable)
- Default models: `claude-sonnet-4-20250514` (Anthropic), `gpt-4o` (OpenAI)

---

## `convert_file()`

Convert a Python file to a Dataiku flow using rule-based analysis.

```python
def convert_file(path: str, optimize: bool = True) -> DataikuFlow
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `str` | *required* | Path to a Python file |
| `optimize` | `bool` | `True` | Whether to optimize the flow |

**Returns:** [`DataikuFlow`](models.md#dataikuflow) - The converted pipeline (with `source_file` set)

**Example:**

```python
from py2dataiku import convert_file

flow = convert_file("pipelines/etl_pipeline.py")
print(f"Source: {flow.source_file}")
print(flow.get_summary())
```

---

## `convert_file_with_llm()`

Convert a Python file to a Dataiku flow using LLM-based analysis.

```python
def convert_file_with_llm(
    path: str,
    provider: str = "anthropic",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    optimize: bool = True,
    flow_name: Optional[str] = None,
) -> DataikuFlow
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `str` | *required* | Path to a Python file |
| `provider` | `str` | `"anthropic"` | LLM provider name |
| `api_key` | `Optional[str]` | `None` | API key |
| `model` | `Optional[str]` | `None` | Model name |
| `optimize` | `bool` | `True` | Whether to optimize the flow |
| `flow_name` | `Optional[str]` | `None` | Flow name (defaults to filename without extension) |

**Returns:** [`DataikuFlow`](models.md#dataikuflow) - The converted pipeline (with `source_file` set)

**Example:**

```python
from py2dataiku import convert_file_with_llm

flow = convert_file_with_llm(
    "pipelines/etl_pipeline.py",
    provider="anthropic",
    flow_name="etl_flow"
)
flow.to_json()
```
