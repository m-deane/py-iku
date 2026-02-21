# Exporters

Export Dataiku flows as DSS project bundles.

---

## export_to_dss()

Convenience function to export a flow to DSS project format.

```python
from py2dataiku import export_to_dss

path = export_to_dss(flow, "output/my_project")
path = export_to_dss(flow, "output/my_project", create_zip=True)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `flow` | `DataikuFlow` | *required* | Flow to export |
| `output_dir` | `str` | *required* | Output directory path |
| `project_key` | `Optional[str]` | `None` | DSS project key |
| `config` | `Optional[DSSProjectConfig]` | `None` | Project configuration |
| `create_zip` | `bool` | `False` | Whether to create a ZIP archive |

**Returns:** `str` - Path to exported project (directory or zip file)

---

## DSSExporter

Exports a DataikuFlow as a Dataiku DSS project bundle.

```python
from py2dataiku import DSSExporter, DSSProjectConfig
```

### Constructor

```python
DSSExporter(
    flow: DataikuFlow,
    project_key: str = None,
    config: DSSProjectConfig = None,
)
```

### Methods

#### `export()`

```python
def export(self, output_dir: str, create_zip: bool = False) -> str
```

Exports the flow to DSS project format on disk.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `output_dir` | `str` | *required* | Output directory |
| `create_zip` | `bool` | `False` | Create ZIP archive |

**Returns:** `str` - Path to exported project

**Raises:** [`ExportError`](exceptions.md#exporterror) - If export fails

---

## DSSProjectConfig

Configuration for DSS project export.

```python
from py2dataiku import DSSProjectConfig
```

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `project_key` | `str` | `"CONVERTED_PROJECT"` | DSS project key |
| `project_name` | `str` | `"Converted Python Pipeline"` | Display name |
| `owner` | `str` | `"py2dataiku"` | Project owner |
| `description` | `str` | `"Auto-generated..."` | Project description |
| `tags` | `List[str]` | `["py2dataiku", "auto-generated"]` | Project tags |
| `default_connection` | `str` | `"filesystem_managed"` | Default data connection |
| `default_format` | `str` | `"csv"` | Default file format |
| `include_code_comments` | `bool` | `True` | Include source code comments |

### Methods

```python
config.to_dict()                    # -> Dict[str, Any]
```

### Example

```python
from py2dataiku import DSSExporter, DSSProjectConfig, convert

flow = convert(code)

config = DSSProjectConfig(
    project_key="SALES_PIPELINE",
    project_name="Sales Data Pipeline",
    owner="data-team",
    default_connection="postgresql_prod",
)

exporter = DSSExporter(flow, config=config)
exporter.export("output/sales_pipeline", create_zip=True)
```
