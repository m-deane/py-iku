# MLOps

Machine learning operations models for API endpoints, model versioning, and drift detection.

---

## APIEndpoint

Model serving endpoint configuration.

```python
from py2dataiku import APIEndpoint, EndpointType
```

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | *required* | Endpoint name |
| `model_name` | `str` | *required* | Model to serve |
| `endpoint_type` | `EndpointType` | `EndpointType.REST` | Endpoint type |
| `url_path` | `Optional[str]` | `None` | URL path |
| `input_schema` | `Dict[str, str]` | `{}` | Input field types |
| `output_schema` | `Dict[str, str]` | `{}` | Output field types |
| `auth_required` | `bool` | `True` | Require authentication |
| `rate_limit` | `Optional[int]` | `None` | Requests per minute |

### EndpointType

| Value | Description |
|-------|-------------|
| `REST` | REST API endpoint |
| `BATCH` | Batch prediction endpoint |

### Example

```python
endpoint = APIEndpoint(
    name="predict_churn",
    model_name="churn_model_v2",
    endpoint_type=EndpointType.REST,
    url_path="/api/v1/predict/churn",
    input_schema={
        "customer_id": "string",
        "tenure_months": "int",
        "monthly_charges": "float",
    },
    output_schema={
        "prediction": "string",
        "probability": "float",
    },
    auth_required=True,
    rate_limit=100,
)
```

---

## ModelVersion

Model version metadata and tracking.

```python
from py2dataiku import ModelVersion, ModelFramework
```

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `version_id` | `str` | *required* | Version identifier |
| `model_name` | `str` | *required* | Model name |
| `framework` | `ModelFramework` | `ModelFramework.SCIKIT_LEARN` | ML framework |
| `algorithm` | `Optional[str]` | `None` | Algorithm name |
| `metrics` | `Dict[str, float]` | `{}` | Performance metrics |
| `features` | `List[str]` | `[]` | Feature names |
| `target` | `Optional[str]` | `None` | Target variable |
| `active` | `bool` | `False` | Whether this version is active |
| `tags` | `List[str]` | `[]` | Tags |

### ModelFramework

| Value | Description |
|-------|-------------|
| `SCIKIT_LEARN` | scikit-learn |
| `XGBOOST` | XGBoost |
| `LIGHTGBM` | LightGBM |
| `TENSORFLOW` | TensorFlow |
| `PYTORCH` | PyTorch |
| `CUSTOM` | Custom framework |

### Example

```python
version = ModelVersion(
    version_id="v2.1.0",
    model_name="churn_model",
    framework=ModelFramework.XGBOOST,
    algorithm="XGBClassifier",
    metrics={"accuracy": 0.92, "f1": 0.88, "auc": 0.95},
    features=["tenure", "monthly_charges", "contract_type"],
    target="churn",
    active=True,
    tags=["production", "validated"],
)
```

---

## DriftConfig

Model drift detection configuration.

```python
from py2dataiku import DriftConfig, DriftMetricType
```

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | `bool` | `True` | Enable drift detection |
| `metric` | `DriftMetricType` | `DriftMetricType.PSI` | Drift metric |
| `threshold` | `float` | `0.2` | Alert threshold |
| `columns` | `List[str]` | `[]` | Columns to monitor |
| `check_frequency` | `str` | `"daily"` | Check frequency |

### DriftMetricType

| Value | Description |
|-------|-------------|
| `PSI` | Population Stability Index |
| `KS` | Kolmogorov-Smirnov test |
| `CHI_SQUARED` | Chi-squared test |
| `WASSERSTEIN` | Wasserstein distance |

### Example

```python
drift = DriftConfig(
    enabled=True,
    metric=DriftMetricType.PSI,
    threshold=0.15,
    columns=["tenure", "monthly_charges", "contract_type"],
    check_frequency="daily",
)
```
