# DSS Integration

Deploy py-iku flows directly to a running Dataiku DSS instance, or generate MCP tool calls for use with AI-powered deployment.

---

## Deployment Approaches

py-iku provides three ways to get flows into Dataiku DSS:

| Approach | Module | Requires DSS | Best For |
|----------|--------|-------------|----------|
| **API Deployment** | `DSSFlowDeployer` | Yes | Automated pipelines, CI/CD |
| **MCP Tool Calls** | `generate_mcp_tool_calls()` | No (generates payloads) | AI-assisted deployment via MCP servers |
| **Bundle Export** | `DSSExporter` | No (creates files) | Manual import via DSS UI |

---

## Prerequisites

**For API deployment:**

- A running Dataiku DSS instance (DSS 14+)
- A personal API key ([DSS documentation](https://doc.dataiku.com/dss/latest/python-api/outside-usage.html))
- The `dataikuapi` package:

```bash
pip install dataiku-api-client
```

**For MCP deployment:**

- An MCP-aware client (e.g., Claude Desktop)
- The [dataiku_factory](https://github.com/hhobin/dataiku_factory) MCP server configured

**For bundle export:**

- See [Exporters](exporters.md)

---

## DSSFlowDeployer

Deploys a `DataikuFlow` to a Dataiku DSS instance via the `dataikuapi` Python client.

```python
from py2dataiku.integrations import DSSFlowDeployer
```

### Constructor

```python
DSSFlowDeployer(
    host: str,
    api_key: str,
    project_key: str,
    dry_run: bool = False,
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `host` | `str` | *required* | DSS instance URL (e.g. `"https://dss.example.com"`) |
| `api_key` | `str` | *required* | Personal API key for authentication |
| `project_key` | `str` | *required* | Target DSS project key |
| `dry_run` | `bool` | `False` | If `True`, validate without creating resources |

### Methods

#### `deploy()`

```python
def deploy(self, flow: DataikuFlow) -> DeploymentResult
```

Deploy an entire flow to DSS. Datasets are created first, then recipes in topological order.

**Returns:** [`DeploymentResult`](#deploymentresult)

**Raises:** [`ExportError`](exceptions.md#exporterror) if `dataikuapi` is not installed (live mode only)

#### `deploy_dataset()`

```python
def deploy_dataset(self, dataset: DataikuDataset) -> Dict[str, Any]
```

Create a single dataset in DSS. Returns a summary dict with `name`, `type`, and `connection_type` keys.

#### `deploy_recipe()`

```python
def deploy_recipe(self, recipe: DataikuRecipe) -> Dict[str, Any]
```

Create a single recipe in DSS. Returns a summary dict with `name`, `type`, `inputs`, and `outputs` keys.

### Dry-Run Mode

Dry-run mode validates the flow and reports what would be created without making any API calls. No `dataikuapi` installation or DSS connection is required.

```python
from py2dataiku import convert
from py2dataiku.integrations import DSSFlowDeployer

flow = convert("""
import pandas as pd
df = pd.read_csv('sales.csv')
df = df.dropna()
result = df.groupby('region').agg({'amount': 'sum'})
""")

deployer = DSSFlowDeployer("", "", "SALES_PROJECT", dry_run=True)
result = deployer.deploy(flow)

print(result)
# DeploymentResult(DRY RUN: 3 datasets, 2 recipes, 0 errors)
print(result.datasets_created)
print(result.recipes_created)
```

### Live Deployment Example

```python
from py2dataiku import convert
from py2dataiku.integrations import DSSFlowDeployer

flow = convert(code)

deployer = DSSFlowDeployer(
    host="https://dss.example.com",
    api_key="your-api-key",
    project_key="MY_PROJECT",
)

result = deployer.deploy(flow)

if result.success:
    print(f"Created {len(result.datasets_created)} datasets")
    print(f"Created {len(result.recipes_created)} recipes")
else:
    for error in result.errors:
        print(f"Error: {error}")
```

---

## DeploymentResult

Dataclass returned by `DSSFlowDeployer.deploy()`.

```python
from py2dataiku.integrations import DeploymentResult
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `datasets_created` | `List[str]` | Names of datasets created |
| `recipes_created` | `List[str]` | Names of recipes created |
| `errors` | `List[str]` | Error messages (empty on success) |
| `warnings` | `List[str]` | Warning messages |
| `dry_run` | `bool` | Whether this was a dry-run deployment |

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `success` | `bool` | `True` if no errors occurred |

### Methods

```python
result.to_dict()    # -> Dict[str, Any]
```

---

## MCP Tool Call Generation

Generate [Model Context Protocol](https://modelcontextprotocol.io/) tool call payloads compatible with the [dataiku_factory](https://github.com/hhobin/dataiku_factory) MCP server.

### generate_mcp_tool_calls()

```python
from py2dataiku.integrations import generate_mcp_tool_calls

tool_calls = generate_mcp_tool_calls(flow, project_key="MY_PROJECT")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `flow` | `DataikuFlow` | *required* | Flow to convert |
| `project_key` | `str` | *required* | Target DSS project key |

**Returns:** `List[Dict[str, Any]]` - Ordered list of tool call dicts, each with `tool_name` and `arguments` keys.

Tool calls are ordered topologically so datasets are created before the recipes that reference them. Each dict has the structure:

```python
{
    "tool_name": "create_dataset",  # or "create_recipe"
    "arguments": { ... }
}
```

### format_mcp_script()

```python
from py2dataiku.integrations import format_mcp_script

script = format_mcp_script(tool_calls)
print(script)
```

Formats tool calls as a human-readable script for copy-pasting into an MCP client or for documentation.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `tool_calls` | `List[Dict]` | Tool calls from `generate_mcp_tool_calls()` |

**Returns:** `str` - Formatted multi-line string

**Example output:**

```text
# MCP Tool Calls for Dataiku DSS
# Total calls: 5

# Step 1: create_dataset
tool: create_dataset
arguments: {
  "project_key": "MY_PROJECT",
  "dataset_name": "sales",
  "connection_type": "filesystem_managed"
}

# Step 2: create_recipe
tool: create_recipe
arguments: {
  "project_key": "MY_PROJECT",
  "recipe_name": "prepare_sales",
  "recipe_type": "shaker",
  "inputs": ["sales"],
  "outputs": ["sales_prepared"]
}
```

### MCP Integration Example

```python
from py2dataiku import convert
from py2dataiku.integrations import generate_mcp_tool_calls, format_mcp_script

flow = convert("""
import pandas as pd
df = pd.read_csv('data.csv')
df = df.dropna()
result = df.groupby('category').agg({'value': 'sum'})
""")

tool_calls = generate_mcp_tool_calls(flow, "ANALYTICS_PROJECT")
print(format_mcp_script(tool_calls))
```

---

## to_dss_builder_args()

All 12 `RecipeSettings` subclasses implement `to_dss_builder_args()`, which returns a dictionary suitable for the DSS recipe builder API.

```python
recipe.settings.to_dss_builder_args()  # -> Dict[str, Any]
```

This method is used internally by `DSSFlowDeployer` when applying recipe-specific configuration. The returned dict can also be used directly with `dataikuapi`:

```python
import dataikuapi

client = dataikuapi.DSSClient("https://dss.example.com", "api-key")
project = client.get_project("MY_PROJECT")

builder = project.new_recipe("grouping", "compute_group_by")
builder.with_input("sales_data")
builder.with_output("sales_grouped")
recipe = builder.create()

# Apply settings from py-iku
settings = recipe.get_settings()
settings.get_json_payload().update(
    recipe.settings.to_dss_builder_args()
)
settings.save()
```

---

## End-to-End Workflow

Convert Python code and deploy the resulting flow to DSS:

```python
from py2dataiku import convert
from py2dataiku.integrations import DSSFlowDeployer

# 1. Convert Python code to a Dataiku flow
code = """
import pandas as pd
df = pd.read_csv('transactions.csv')
df['amount'] = df['amount'].fillna(0)
df['date'] = pd.to_datetime(df['date'])
summary = df.groupby('category').agg({'amount': 'sum'})
summary.to_csv('category_totals.csv')
"""
flow = convert(code)

# 2. Preview what will be created (dry run)
deployer = DSSFlowDeployer("", "", "FINANCE_PROJECT", dry_run=True)
preview = deployer.deploy(flow)
print(preview)

# 3. Deploy to DSS
deployer = DSSFlowDeployer(
    host="https://dss.company.com",
    api_key="your-api-key",
    project_key="FINANCE_PROJECT",
)
result = deployer.deploy(flow)

if result.success:
    print(f"Deployed: {result.datasets_created} + {result.recipes_created}")
```
