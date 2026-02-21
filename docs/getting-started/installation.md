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
| `cairosvg` | PNG/PDF export from SVG | `pip install cairosvg` |

## Requirements

- Python 3.9+
- pyyaml >= 6.0

## API Keys

For LLM-based conversion, set your API key as an environment variable:

```bash
# Anthropic (Claude)
export ANTHROPIC_API_KEY="your-key-here"

# OpenAI (GPT)
export OPENAI_API_KEY="your-key-here"
```

Or pass it directly:

```python
flow = convert_with_llm(code, provider="anthropic", api_key="your-key")
```

## Verify Installation

```python
import py2dataiku
print(py2dataiku.__version__)
```
