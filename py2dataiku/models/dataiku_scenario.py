"""Scenario model for Dataiku DSS."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class TriggerType(Enum):
    """Types of scenario triggers in Dataiku DSS."""

    TIME_BASED = "time_based"
    DATASET_CHANGE = "dataset_change"
    SQL_QUERY = "sql_query"
    PYTHON = "python"


class StepType(Enum):
    """Types of scenario steps in Dataiku DSS."""

    BUILD = "build_dataset"
    TRAIN = "train_model"
    CHECK = "run_checks"
    SQL_EXECUTE = "execute_sql"
    PYTHON_EXECUTE = "execute_python"
    SEND_MESSAGE = "send_message"


class ReporterType(Enum):
    """Types of scenario reporters in Dataiku DSS."""

    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"


@dataclass
class ScenarioTrigger:
    """A trigger that starts a scenario."""

    name: str
    trigger_type: TriggerType
    params: Dict[str, Any] = field(default_factory=dict)
    active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.trigger_type.value,
            "params": self.params,
            "active": self.active,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScenarioTrigger":
        return cls(
            name=data["name"],
            trigger_type=TriggerType(data["type"]),
            params=data.get("params", {}),
            active=data.get("active", True),
        )

    @classmethod
    def time_based(
        cls, name: str, cron: str, timezone: str = "UTC"
    ) -> "ScenarioTrigger":
        """Create a time-based trigger with a cron expression."""
        return cls(
            name=name,
            trigger_type=TriggerType.TIME_BASED,
            params={"cron": cron, "timezone": timezone},
        )

    @classmethod
    def dataset_change(
        cls, name: str, dataset: str
    ) -> "ScenarioTrigger":
        """Create a trigger that fires when a dataset changes."""
        return cls(
            name=name,
            trigger_type=TriggerType.DATASET_CHANGE,
            params={"dataset": dataset},
        )


@dataclass
class ScenarioStep:
    """A step within a scenario."""

    name: str
    step_type: StepType
    params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.step_type.value,
            "params": self.params,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScenarioStep":
        return cls(
            name=data["name"],
            step_type=StepType(data["type"]),
            params=data.get("params", {}),
        )

    @classmethod
    def build(cls, name: str, dataset: str) -> "ScenarioStep":
        """Create a build dataset step."""
        return cls(
            name=name,
            step_type=StepType.BUILD,
            params={"dataset": dataset},
        )

    @classmethod
    def train(cls, name: str, model_id: str) -> "ScenarioStep":
        """Create a train model step."""
        return cls(
            name=name,
            step_type=StepType.TRAIN,
            params={"modelId": model_id},
        )

    @classmethod
    def run_checks(cls, name: str, dataset: str) -> "ScenarioStep":
        """Create a run checks step."""
        return cls(
            name=name,
            step_type=StepType.CHECK,
            params={"dataset": dataset},
        )

    @classmethod
    def execute_python(cls, name: str, code: str) -> "ScenarioStep":
        """Create an execute Python step."""
        return cls(
            name=name,
            step_type=StepType.PYTHON_EXECUTE,
            params={"code": code},
        )

    @classmethod
    def send_message(
        cls, name: str, channel: str, message: str
    ) -> "ScenarioStep":
        """Create a send message step."""
        return cls(
            name=name,
            step_type=StepType.SEND_MESSAGE,
            params={"channel": channel, "message": message},
        )


@dataclass
class ScenarioReporter:
    """A reporter that sends notifications about scenario execution."""

    name: str
    reporter_type: ReporterType
    params: Dict[str, Any] = field(default_factory=dict)
    on_success: bool = True
    on_failure: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.reporter_type.value,
            "params": self.params,
            "onSuccess": self.on_success,
            "onFailure": self.on_failure,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScenarioReporter":
        return cls(
            name=data["name"],
            reporter_type=ReporterType(data["type"]),
            params=data.get("params", {}),
            on_success=data.get("onSuccess", True),
            on_failure=data.get("onFailure", True),
        )

    @classmethod
    def email(
        cls,
        name: str,
        recipients: List[str],
        subject: str = "Scenario Report",
    ) -> "ScenarioReporter":
        """Create an email reporter."""
        return cls(
            name=name,
            reporter_type=ReporterType.EMAIL,
            params={"recipients": recipients, "subject": subject},
        )

    @classmethod
    def slack(
        cls, name: str, channel: str, webhook_url: str
    ) -> "ScenarioReporter":
        """Create a Slack reporter."""
        return cls(
            name=name,
            reporter_type=ReporterType.SLACK,
            params={"channel": channel, "webhookUrl": webhook_url},
        )

    @classmethod
    def webhook(cls, name: str, url: str) -> "ScenarioReporter":
        """Create a webhook reporter."""
        return cls(
            name=name,
            reporter_type=ReporterType.WEBHOOK,
            params={"url": url},
        )


@dataclass
class DataikuScenario:
    """
    Represents a Dataiku DSS scenario.

    Scenarios automate flow execution with triggers, steps, and reporters.
    """

    name: str
    triggers: List[ScenarioTrigger] = field(default_factory=list)
    steps: List[ScenarioStep] = field(default_factory=list)
    reporters: List[ScenarioReporter] = field(default_factory=list)
    active: bool = True
    tags: List[str] = field(default_factory=list)

    def add_trigger(self, trigger: ScenarioTrigger) -> None:
        """Add a trigger to the scenario."""
        self.triggers.append(trigger)

    def add_step(self, step: ScenarioStep) -> None:
        """Add a step to the scenario."""
        self.steps.append(step)

    def add_reporter(self, reporter: ScenarioReporter) -> None:
        """Add a reporter to the scenario."""
        self.reporters.append(reporter)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "active": self.active,
            "tags": self.tags,
            "triggers": [t.to_dict() for t in self.triggers],
            "steps": [s.to_dict() for s in self.steps],
            "reporters": [r.to_dict() for r in self.reporters],
        }

    def to_json(self) -> Dict[str, Any]:
        """Convert to Dataiku API-compatible JSON."""
        return {
            "id": self.name,
            "name": self.name,
            "type": "step_based",
            "active": self.active,
            "params": {
                "triggers": [t.to_dict() for t in self.triggers],
                "steps": [s.to_dict() for s in self.steps],
                "reporters": [r.to_dict() for r in self.reporters],
            },
            "versionTag": {"versionNumber": 1},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DataikuScenario":
        """Reconstruct a DataikuScenario from a dictionary."""
        return cls(
            name=data["name"],
            active=data.get("active", True),
            tags=data.get("tags", []),
            triggers=[
                ScenarioTrigger.from_dict(t)
                for t in data.get("triggers", [])
            ],
            steps=[
                ScenarioStep.from_dict(s)
                for s in data.get("steps", [])
            ],
            reporters=[
                ScenarioReporter.from_dict(r)
                for r in data.get("reporters", [])
            ],
        )

    def __repr__(self) -> str:
        return (
            f"DataikuScenario(name='{self.name}', "
            f"triggers={len(self.triggers)}, "
            f"steps={len(self.steps)}, "
            f"reporters={len(self.reporters)})"
        )
