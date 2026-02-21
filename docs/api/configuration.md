# Configuration

Configuration system for py-iku with file-based and environment variable support.

---

## Py2DataikuConfig

Configuration dataclass with all library settings.

```python
from py2dataiku import Py2DataikuConfig, load_config, find_config_file
```

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `default_provider` | `str` | `"anthropic"` | Default LLM provider |
| `default_model` | `Optional[str]` | `None` | Default model name |
| `api_key` | `Optional[str]` | `None` | API key |
| `project_key` | `str` | `"MY_PROJECT"` | DSS project key |
| `flow_name` | `str` | `"converted_flow"` | Default flow name |
| `optimize` | `bool` | `True` | Enable flow optimization |
| `optimization_level` | `int` | `1` | 0=none, 1=basic, 2=aggressive |
| `dataset_prefix` | `str` | `""` | Prefix for dataset names |
| `dataset_suffix` | `str` | `""` | Suffix for dataset names |
| `recipe_prefix` | `str` | `""` | Prefix for recipe names |
| `recipe_suffix` | `str` | `""` | Suffix for recipe names |
| `default_format` | `str` | `"svg"` | Default visualization format |
| `default_connection` | `str` | `"Filesystem"` | Default data connection |
| `extra` | `Dict[str, Any]` | `{}` | Additional settings |

### Methods

```python
config.to_dict()                      # -> Dict[str, Any]
Py2DataikuConfig.from_dict(data)      # -> Py2DataikuConfig (classmethod)
```

---

## load_config()

Load configuration from file or defaults.

```python
def load_config(
    config_path: Optional[str] = None,
    auto_discover: bool = True,
) -> Py2DataikuConfig
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `config_path` | `Optional[str]` | `None` | Explicit path to config file |
| `auto_discover` | `bool` | `True` | Search standard locations |

**Returns:** `Py2DataikuConfig`

**Behavior:**
1. If `config_path` is provided, loads from that file
2. If `auto_discover=True`, searches for config files (see `find_config_file()`)
3. Falls back to default values
4. Environment variables override file values

---

## find_config_file()

Search for configuration files in standard locations.

```python
def find_config_file(start_dir: Optional[str] = None) -> Optional[Path]
```

**Search order:**
1. `py2dataiku.toml` (current directory, walking up to root)
2. `.py2dataikurc` (current directory, walking up to root)
3. `.py2dataiku.yaml` / `.py2dataiku.yml` (current directory, walking up to root)
4. `~/.config/py2dataiku/config.toml`
5. `~/.py2dataikurc`

**Returns:** `Optional[Path]` - Path to first config file found, or `None`

---

## Config File Formats

### TOML (`py2dataiku.toml`)

```toml
[py2dataiku]
default_provider = "anthropic"
default_model = "claude-sonnet-4-20250514"
project_key = "SALES_PIPELINE"
optimize = true
optimization_level = 2
default_format = "svg"
default_connection = "postgresql_prod"
dataset_prefix = "ds_"
recipe_prefix = "r_"
```

### YAML (`.py2dataiku.yaml`)

```yaml
py2dataiku:
  default_provider: anthropic
  project_key: SALES_PIPELINE
  optimize: true
  optimization_level: 2
  default_format: svg
```

---

## Environment Variables

Environment variables override file-based configuration:

| Variable | Config Field | Description |
|----------|-------------|-------------|
| `PY2DATAIKU_PROVIDER` | `default_provider` | LLM provider |
| `PY2DATAIKU_MODEL` | `default_model` | Model name |
| `ANTHROPIC_API_KEY` | `api_key` | Anthropic API key |
| `OPENAI_API_KEY` | `api_key` | OpenAI API key |
| `PY2DATAIKU_PROJECT_KEY` | `project_key` | DSS project key |
| `PY2DATAIKU_OPTIMIZE` | `optimize` | Enable optimization |
