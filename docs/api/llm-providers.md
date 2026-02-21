# LLM Providers

LLM integration for semantic code analysis. Supports Anthropic (Claude) and OpenAI (GPT).

---

## get_provider()

Factory function to create an LLM provider.

```python
from py2dataiku import get_provider

provider = get_provider("anthropic")
provider = get_provider("openai", api_key="sk-...")
provider = get_provider("mock")  # For testing
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `provider` | `str` | *required* | `"anthropic"`, `"openai"`, or `"mock"` |
| `api_key` | `Optional[str]` | `None` | API key (env var fallback) |
| `model` | `Optional[str]` | `None` | Model name override |

**Returns:** `LLMProvider` instance

---

## LLMProvider (ABC)

Abstract base class for LLM providers.

```python
from py2dataiku import LLMProvider
```

### Abstract Methods

```python
def complete(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse
def complete_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]
```

### Abstract Properties

```python
@property
def model_name(self) -> str
```

---

## AnthropicProvider

```python
from py2dataiku import AnthropicProvider
```

### Constructor

```python
AnthropicProvider(
    api_key: Optional[str] = None,       # Falls back to ANTHROPIC_API_KEY env var
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 4096,
    timeout: Optional[float] = None,
    max_retries: int = 2,
)
```

**Requires:** `pip install anthropic` (or `pip install py-iku[llm]`)

---

## OpenAIProvider

```python
from py2dataiku import OpenAIProvider
```

### Constructor

```python
OpenAIProvider(
    api_key: Optional[str] = None,       # Falls back to OPENAI_API_KEY env var
    model: str = "gpt-4o",
    max_tokens: int = 4096,
    timeout: Optional[float] = None,
    max_retries: int = 2,
)
```

**Requires:** `pip install openai` (or `pip install py-iku[llm]`)

---

## MockProvider

For testing without API calls.

```python
from py2dataiku import MockProvider

provider = MockProvider()
```

---

## LLMCodeAnalyzer

Analyzes Python code using LLM to extract data manipulation steps.

```python
from py2dataiku import LLMCodeAnalyzer
```

### Constructor

```python
LLMCodeAnalyzer(
    provider: Optional[LLMProvider] = None,
    provider_name: str = "anthropic",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
)
```

Can either pass a pre-created `LLMProvider` instance or specify `provider_name`/`api_key`/`model` to create one.

### Methods

#### `analyze()`

```python
def analyze(self, code: str) -> AnalysisResult
```

Analyzes Python code and extracts data manipulation steps.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `code` | `str` | Python source code to analyze |

**Returns:** `AnalysisResult`

**Raises:**
- `LLMResponseParseError` - If LLM response cannot be parsed as JSON
- `ProviderError` - If communication with LLM provider fails

---

## AnalysisResult

Result of LLM code analysis.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `code_summary` | `str` | High-level description of what the code does |
| `total_operations` | `int` | Number of data operations detected |
| `complexity_score` | `int` | Code complexity score (1-10) |
| `datasets` | `List[Dict[str, Any]]` | Detected datasets |
| `steps` | `List[DataStep]` | Ordered list of data manipulation steps |
| `recommendations` | `List[str]` | Conversion recommendations |
| `warnings` | `List[str]` | Conversion warnings |

---

## DataStep

A single data manipulation step extracted from code.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `step_number` | `int` | Sequential step number |
| `operation` | `OperationType` | Type of operation |
| `description` | `str` | Human-readable description |
| `input_datasets` | `List[str]` | Input dataset names |
| `output_dataset` | `Optional[str]` | Output dataset name |
| `columns` | `List[str]` | Affected columns |
| `filter_conditions` | `List[FilterCondition]` | Filter conditions |
| `aggregations` | `List[Aggregation]` | Aggregation configs |
| `group_by_columns` | `List[str]` | Group-by columns |
| `join_conditions` | `List[JoinCondition]` | Join conditions |
| `join_type` | `Optional[str]` | Join type |
| `column_transforms` | `List[ColumnTransform]` | Column transforms |
| `rename_mapping` | `Dict[str, str]` | Column renames |
| `sort_columns` | `List[Dict[str, str]]` | Sort specifications |
| `fill_value` | `Optional[Any]` | Fill value for missing |
| `source_lines` | `List[int]` | Source code line numbers |
| `source_code` | `Optional[str]` | Source code snippet |
| `suggested_recipe` | `Optional[str]` | Suggested Dataiku recipe type |
| `suggested_processors` | `List[str]` | Suggested processors |
| `requires_python_recipe` | `bool` | Whether a Python recipe is needed |
| `reasoning` | `Optional[str]` | LLM reasoning for mapping |

---

## OperationType

Types of data operations the LLM can detect.

```python
from py2dataiku import OperationType
```

**Data I/O:** `READ_DATA`, `WRITE_DATA`

**Column operations:** `FILTER`, `SELECT_COLUMNS`, `DROP_COLUMNS`, `RENAME_COLUMNS`, `ADD_COLUMN`, `TRANSFORM_COLUMN`

**Missing data:** `FILL_MISSING`, `DROP_MISSING`

**Deduplication:** `DROP_DUPLICATES`

**Aggregation:** `GROUP_AGGREGATE`, `WINDOW_FUNCTION`

**Combining:** `JOIN`, `UNION`

**Reshaping:** `PIVOT`, `UNPIVOT`

**Ordering:** `SORT`, `TOP_N`, `SAMPLE`

**Type conversion:** `CAST_TYPE`, `PARSE_DATE`

**Transformations:** `SPLIT_COLUMN`, `ENCODE_CATEGORICAL`, `NORMALIZE_SCALE`

**Geographic:** `GEO_OPERATION`

**Other:** `CUSTOM_FUNCTION`, `UNKNOWN`
