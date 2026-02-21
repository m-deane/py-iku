# Scenarios & Metrics

Automation, monitoring, and data quality models for Dataiku DSS.

---

## DataikuScenario

Automation scenario with triggers, steps, and reporters.

```python
from py2dataiku import DataikuScenario, ScenarioTrigger, ScenarioStep, ScenarioReporter
```

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | *required* | Scenario name |
| `triggers` | `List[ScenarioTrigger]` | `[]` | Event triggers |
| `steps` | `List[ScenarioStep]` | `[]` | Execution steps |
| `reporters` | `List[ScenarioReporter]` | `[]` | Notification reporters |
| `active` | `bool` | `True` | Whether scenario is active |

### Methods

```python
scenario.to_dict()
DataikuScenario.from_dict(data)
```

### Example

```python
scenario = DataikuScenario(
    name="daily_etl",
    triggers=[
        ScenarioTrigger.time_based("daily_6am", "0 6 * * *"),
        ScenarioTrigger.dataset_change("on_raw_update", "raw_data"),
    ],
    steps=[
        ScenarioStep.build("build_pipeline", "output_dataset"),
        ScenarioStep.run_checks("validate_output", "output_dataset"),
    ],
    reporters=[
        ScenarioReporter.email("notify_team", ["team@example.com"]),
        ScenarioReporter.slack("slack_alert", "#data-alerts"),
    ],
)
```

---

## ScenarioTrigger

Event that starts a scenario.

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | *required* | Trigger name |
| `trigger_type` | `TriggerType` | *required* | Trigger type |
| `params` | `Dict[str, Any]` | `{}` | Trigger parameters |
| `active` | `bool` | `True` | Whether trigger is active |

### Factory Methods

```python
# Cron-based schedule
trigger = ScenarioTrigger.time_based("daily_6am", cron="0 6 * * *", timezone="UTC")

# Triggered when dataset changes
trigger = ScenarioTrigger.dataset_change("on_update", dataset="raw_data")
```

### TriggerType

| Value | Description |
|-------|-------------|
| `TIME_BASED` | Cron schedule |
| `DATASET_CHANGE` | Dataset modification |
| `SQL_QUERY` | SQL condition check |
| `PYTHON` | Custom Python condition |

---

## ScenarioStep

An action within a scenario.

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | *required* | Step name |
| `step_type` | `StepType` | *required* | Step type |
| `params` | `Dict[str, Any]` | `{}` | Step parameters |

### Factory Methods

```python
ScenarioStep.build("build_output", dataset="output_dataset")
ScenarioStep.train("retrain_model", model_id="my_model")
ScenarioStep.run_checks("validate", dataset="output_dataset")
ScenarioStep.execute_python("custom", code="print('done')")
ScenarioStep.send_message("notify", channel="slack", message="Build complete")
```

### StepType

| Value | Description |
|-------|-------------|
| `BUILD` | Build a dataset |
| `TRAIN` | Train a model |
| `CHECK` | Run data checks |
| `SQL_EXECUTE` | Execute SQL |
| `PYTHON_EXECUTE` | Execute Python |
| `SEND_MESSAGE` | Send notification |

---

## ScenarioReporter

Notification configuration for scenario outcomes.

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | *required* | Reporter name |
| `reporter_type` | `ReporterType` | *required* | Reporter type |
| `params` | `Dict[str, Any]` | `{}` | Reporter parameters |
| `on_success` | `bool` | `True` | Notify on success |
| `on_failure` | `bool` | `True` | Notify on failure |

### Factory Methods

```python
ScenarioReporter.email("email_team", recipients=["team@example.com"], subject="ETL Report")
ScenarioReporter.slack("slack_alert", channel="#data-alerts")
```

### ReporterType

| Value | Description |
|-------|-------------|
| `EMAIL` | Email notification |
| `SLACK` | Slack message |
| `WEBHOOK` | HTTP webhook |

---

## DataikuMetric

Dataset metric definition.

```python
from py2dataiku import DataikuMetric, MetricType
```

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | *required* | Metric name |
| `metric_type` | `MetricType` | *required* | Metric type |
| `column` | `Optional[str]` | `None` | Target column |
| `params` | `Dict[str, Any]` | `{}` | Additional parameters |

### Factory Methods

```python
DataikuMetric.row_count()
DataikuMetric.column_min("price")
DataikuMetric.column_max("price")
DataikuMetric.column_avg("price")
DataikuMetric.column_missing("email")
DataikuMetric.custom_sql("revenue", query="SELECT SUM(amount) FROM data")
```

### MetricType

| Value | Description |
|-------|-------------|
| `ROW_COUNT` | Total row count |
| `COLUMN_MIN` | Minimum value |
| `COLUMN_MAX` | Maximum value |
| `COLUMN_AVG` | Average value |
| `COLUMN_SUM` | Sum of values |
| `COLUMN_STDDEV` | Standard deviation |
| `COLUMN_DISTINCT` | Distinct count |
| `COLUMN_MISSING` | Missing value count |
| `CUSTOM_SQL` | Custom SQL metric |
| `CUSTOM_PYTHON` | Custom Python metric |

---

## DataikuCheck

Validation check against a metric.

```python
from py2dataiku import DataikuCheck, CheckCondition, CheckSeverity
```

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | *required* | Check name |
| `metric_name` | `str` | *required* | Metric to check against |
| `condition` | `CheckCondition` | *required* | Check condition |
| `value` | `Any` | `None` | Comparison value |
| `min_value` | `Optional[Any]` | `None` | Range minimum |
| `max_value` | `Optional[Any]` | `None` | Range maximum |
| `severity` | `CheckSeverity` | `CheckSeverity.ERROR` | Failure severity |

### Factory Methods

```python
DataikuCheck.not_empty("has_rows", metric_name="row_count")
DataikuCheck.between("price_range", metric_name="price_avg", min_value=10, max_value=1000)
```

### CheckCondition

`EQUALS`, `NOT_EQUALS`, `GREATER_THAN`, `LESS_THAN`, `GREATER_OR_EQUAL`, `LESS_OR_EQUAL`, `BETWEEN`, `NOT_EMPTY`

### CheckSeverity

| Value | Description |
|-------|-------------|
| `WARNING` | Non-blocking warning |
| `ERROR` | Blocking error |

---

## DataQualityRule

Column-level data quality rule.

```python
from py2dataiku import DataQualityRule
```

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | *required* | Rule name |
| `column` | `str` | *required* | Target column |
| `rule_type` | `str` | *required* | Rule type |
| `params` | `Dict[str, Any]` | `{}` | Rule parameters |

### Rule Types

| Type | Description |
|------|-------------|
| `"not_null"` | Column must not contain nulls |
| `"unique"` | Column values must be unique |
| `"in_range"` | Values must be within a range |
| `"regex_match"` | Values must match a pattern |
| `"in_set"` | Values must be in an allowed set |

### Example

```python
rules = [
    DataQualityRule("email_not_null", "email", "not_null"),
    DataQualityRule("age_range", "age", "in_range", {"min": 0, "max": 150}),
    DataQualityRule("status_valid", "status", "in_set", {"values": ["active", "inactive"]}),
    DataQualityRule("email_format", "email", "regex_match", {"pattern": r"^[\w.]+@[\w.]+$"}),
]
```
