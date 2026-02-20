"""MLOps model deployment and versioning models for Dataiku DSS."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class EndpointType(Enum):
    """Types of API endpoints."""

    REST = "rest"
    BATCH = "batch"


class ModelFramework(Enum):
    """Supported ML frameworks."""

    SCIKIT_LEARN = "scikit_learn"
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    TENSORFLOW = "tensorflow"
    PYTORCH = "pytorch"
    CUSTOM = "custom"


class DriftMetricType(Enum):
    """Types of drift detection metrics."""

    PSI = "psi"  # Population Stability Index
    KS = "ks"  # Kolmogorov-Smirnov
    CHI_SQUARED = "chi_squared"
    WASSERSTEIN = "wasserstein"


@dataclass
class APIEndpoint:
    """REST API endpoint configuration for model deployment."""

    name: str
    model_name: str
    endpoint_type: EndpointType = EndpointType.REST
    url_path: Optional[str] = None
    input_schema: Dict[str, str] = field(default_factory=dict)
    output_schema: Dict[str, str] = field(default_factory=dict)
    auth_required: bool = True
    rate_limit: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "name": self.name,
            "modelName": self.model_name,
            "type": self.endpoint_type.value,
            "authRequired": self.auth_required,
        }
        if self.url_path:
            result["urlPath"] = self.url_path
        if self.input_schema:
            result["inputSchema"] = self.input_schema
        if self.output_schema:
            result["outputSchema"] = self.output_schema
        if self.rate_limit is not None:
            result["rateLimit"] = self.rate_limit
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "APIEndpoint":
        return cls(
            name=data["name"],
            model_name=data["modelName"],
            endpoint_type=EndpointType(data.get("type", "rest")),
            url_path=data.get("urlPath"),
            input_schema=data.get("inputSchema", {}),
            output_schema=data.get("outputSchema", {}),
            auth_required=data.get("authRequired", True),
            rate_limit=data.get("rateLimit"),
        )


@dataclass
class ModelVersion:
    """Version tracking for ML models."""

    version_id: str
    model_name: str
    framework: ModelFramework = ModelFramework.SCIKIT_LEARN
    algorithm: Optional[str] = None
    metrics: Dict[str, float] = field(default_factory=dict)
    features: List[str] = field(default_factory=list)
    target: Optional[str] = None
    active: bool = False
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "versionId": self.version_id,
            "modelName": self.model_name,
            "framework": self.framework.value,
            "algorithm": self.algorithm,
            "metrics": self.metrics,
            "features": self.features,
            "target": self.target,
            "active": self.active,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelVersion":
        return cls(
            version_id=data["versionId"],
            model_name=data["modelName"],
            framework=ModelFramework(data.get("framework", "scikit_learn")),
            algorithm=data.get("algorithm"),
            metrics=data.get("metrics", {}),
            features=data.get("features", []),
            target=data.get("target"),
            active=data.get("active", False),
            tags=data.get("tags", []),
        )


@dataclass
class DriftConfig:
    """Configuration for model drift detection."""

    enabled: bool = True
    metric: DriftMetricType = DriftMetricType.PSI
    threshold: float = 0.2
    columns: List[str] = field(default_factory=list)
    check_frequency: str = "daily"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "metric": self.metric.value,
            "threshold": self.threshold,
            "columns": self.columns,
            "checkFrequency": self.check_frequency,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DriftConfig":
        return cls(
            enabled=data.get("enabled", True),
            metric=DriftMetricType(data.get("metric", "psi")),
            threshold=data.get("threshold", 0.2),
            columns=data.get("columns", []),
            check_frequency=data.get("checkFrequency", "daily"),
        )
