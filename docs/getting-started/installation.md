# Installation

## Basic Install

```bash
pip install py-iku
```

This installs the core library with rule-based conversion support.

## With LLM Support

For LLM-based conversion (recommended for complex pipelines):

```bash
pip install py-iku[llm]
```

This adds `anthropic` and `openai` as dependencies.

## Development Install

For contributing or running tests:

```bash
git clone https://github.com/m-deane/py-iku.git
cd py-iku
pip install -e ".[dev]"
```

## Optional Dependencies

| Package | Purpose | Install |
|---------|---------|---------|
| `anthropic` | Claude LLM analysis | `pip install py-iku[llm]` |
| `openai` | GPT LLM analysis | `pip install py-iku[llm]` |
| `matplotlib` | High-quality PNG export via `flow.visualize(format="png")` and `flow.save("flow.png")` | `pip install matplotlib` |
| `cairosvg` | SVG-to-PNG/PDF export via `flow.to_png()` / `flow.to_pdf()` | `pip install cairosvg` |

## Requirements

- Python 3.9+
- pyyaml >= 6.0

## API Keys

For LLM-based conversion, py-iku reads provider keys from the environment.
The recommended pattern for local development is a gitignored `.env.local`
file at the repo root (this is what `scripts/llm_smoke_test.py` uses):

```text
# .env.local  (gitignored — never commit this file)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

Load it before calling `convert_with_llm`:

```python
from pathlib import Path
import os

for line in Path(".env.local").read_text().splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    os.environ.setdefault(k.strip(), v.strip())
```

`scripts/llm_smoke_test.py` shows a worked end-to-end example of this
pattern, including handling for both Anthropic and OpenAI.

If a key is missing when an LLM call is made, py-iku raises
`ConfigurationError` (a subclass of `ValueError`):

```python
from py2dataiku import convert_with_llm
from py2dataiku.exceptions import ConfigurationError

try:
    flow = convert_with_llm(code, provider="anthropic")
except ConfigurationError as e:
    print("Set ANTHROPIC_API_KEY in .env.local:", e)
```

You can also pass a key directly (useful in tests / notebooks):

```python
flow = convert_with_llm(code, provider="anthropic", api_key="sk-ant-...")
```

## Verify Installation

```python
import py2dataiku
print(py2dataiku.__version__)
```
