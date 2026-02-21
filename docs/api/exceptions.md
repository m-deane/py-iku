# Exceptions

Custom exception hierarchy for structured error handling.

```python
from py2dataiku import (
    Py2DataikuError,
    ConversionError,
    ProviderError,
    LLMResponseParseError,
    InvalidPythonCodeError,
    ValidationError,
    ExportError,
    ConfigurationError,
)
```

---

## Hierarchy

```
Exception
└── Py2DataikuError              # Base exception for all py2dataiku errors
    ├── ConversionError          # Error during code-to-flow conversion
    │   └── InvalidPythonCodeError  # Code could not be parsed or analyzed
    ├── ProviderError            # Error communicating with LLM provider
    │   └── LLMResponseParseError   # LLM response could not be parsed as JSON
    ├── ValidationError          # Error during flow or recipe validation
    ├── ExportError              # Error during DSS project export
    └── ConfigurationError       # Error in py2dataiku configuration
```

---

## Py2DataikuError

Base exception for all py2dataiku errors. Catch this to handle any library error.

```python
try:
    flow = convert(code)
except Py2DataikuError as e:
    print(f"py2dataiku error: {e}")
```

---

## ConversionError

Raised when code-to-flow conversion fails.

```python
try:
    flow = convert(invalid_code)
except ConversionError as e:
    print(f"Conversion failed: {e}")
```

---

## InvalidPythonCodeError

Subclass of `ConversionError`. Raised when the provided Python code cannot be parsed or analyzed (e.g., syntax errors).

```python
try:
    flow = convert("this is not python code !!!")
except InvalidPythonCodeError as e:
    print(f"Invalid Python: {e}")
```

---

## ProviderError

Raised when communication with an LLM provider fails (network errors, authentication failures, rate limits).

```python
try:
    flow = convert_with_llm(code, provider="anthropic")
except ProviderError as e:
    print(f"LLM provider error: {e}")
```

---

## LLMResponseParseError

Subclass of `ProviderError`. Raised when the LLM returns a response that cannot be parsed as valid JSON.

```python
try:
    flow = convert_with_llm(code)
except LLMResponseParseError as e:
    print(f"Could not parse LLM response: {e}")
```

---

## ValidationError

Raised when flow or recipe validation fails (e.g., cycles in DAG, missing datasets).

```python
try:
    result = flow.validate()
except ValidationError as e:
    print(f"Validation failed: {e}")
```

---

## ExportError

Raised when DSS project export fails (e.g., I/O errors, invalid configuration).

```python
try:
    export_to_dss(flow, "output/")
except ExportError as e:
    print(f"Export failed: {e}")
```

---

## ConfigurationError

Raised when configuration is invalid (e.g., malformed config file, missing required settings).

```python
try:
    config = load_config("bad_config.toml")
except ConfigurationError as e:
    print(f"Config error: {e}")
```

---

## Error Handling Patterns

### Catch all library errors

```python
from py2dataiku import Py2DataikuError

try:
    flow = convert_with_llm(code)
    export_to_dss(flow, "output/")
except Py2DataikuError as e:
    logging.error(f"py2dataiku: {e}")
```

### Granular error handling

```python
from py2dataiku import (
    InvalidPythonCodeError,
    LLMResponseParseError,
    ProviderError,
    ConversionError,
)

try:
    flow = convert_with_llm(code)
except InvalidPythonCodeError:
    print("The code has syntax errors")
except LLMResponseParseError:
    print("LLM returned invalid response, try again")
except ProviderError:
    print("LLM provider unavailable, falling back to rule-based")
    flow = convert(code)
except ConversionError:
    print("Conversion failed for another reason")
```

### LLM fallback pattern

```python
from py2dataiku import convert, convert_with_llm, ProviderError

try:
    flow = convert_with_llm(code)
except ProviderError:
    flow = convert(code)  # Fall back to rule-based
```
