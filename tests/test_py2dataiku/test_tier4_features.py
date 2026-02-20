"""Tests for Tier 4 platform features (T4.4-T4.7, T4.9, T4.10)."""

import json
import os
import tempfile

import pytest

from py2dataiku.models.dataiku_scenario import (
    DataikuScenario,
    ScenarioTrigger,
    ScenarioStep,
    ScenarioReporter,
    TriggerType,
    StepType,
    ReporterType,
)
from py2dataiku.models.dataiku_metrics import (
    DataikuMetric,
    DataikuCheck,
    DataQualityRule,
    MetricType,
    CheckCondition,
    CheckSeverity,
)
from py2dataiku.models.dataiku_mlops import (
    APIEndpoint,
    ModelVersion,
    DriftConfig,
    EndpointType,
    ModelFramework,
    DriftMetricType,
)
from py2dataiku.models.dataiku_flow import DataikuFlow, FlowZone
from py2dataiku.config import Py2DataikuConfig, load_config, find_config_file


# ==================== T4.4: DataikuScenario ====================


class TestScenarioTrigger:
    """Tests for ScenarioTrigger."""

    def test_create_time_based(self):
        trigger = ScenarioTrigger.time_based("daily_run", "0 0 * * *")
        assert trigger.name == "daily_run"
        assert trigger.trigger_type == TriggerType.TIME_BASED
        assert trigger.params["cron"] == "0 0 * * *"
        assert trigger.active is True

    def test_create_dataset_change(self):
        trigger = ScenarioTrigger.dataset_change("on_data_update", "input_ds")
        assert trigger.trigger_type == TriggerType.DATASET_CHANGE
        assert trigger.params["dataset"] == "input_ds"

    def test_to_dict(self):
        trigger = ScenarioTrigger(
            name="test", trigger_type=TriggerType.PYTHON, params={"code": "pass"}
        )
        d = trigger.to_dict()
        assert d["name"] == "test"
        assert d["type"] == "python"
        assert d["params"]["code"] == "pass"
        assert d["active"] is True

    def test_round_trip(self):
        trigger = ScenarioTrigger.time_based("nightly", "0 2 * * *", timezone="US/Eastern")
        d = trigger.to_dict()
        restored = ScenarioTrigger.from_dict(d)
        assert restored.name == trigger.name
        assert restored.trigger_type == trigger.trigger_type
        assert restored.params == trigger.params

    def test_trigger_types(self):
        assert TriggerType.TIME_BASED.value == "time_based"
        assert TriggerType.DATASET_CHANGE.value == "dataset_change"
        assert TriggerType.SQL_QUERY.value == "sql_query"
        assert TriggerType.PYTHON.value == "python"


class TestScenarioStep:
    """Tests for ScenarioStep."""

    def test_build_step(self):
        step = ScenarioStep.build("build_output", "output_dataset")
        assert step.step_type == StepType.BUILD
        assert step.params["dataset"] == "output_dataset"

    def test_train_step(self):
        step = ScenarioStep.train("train_model", "model_123")
        assert step.step_type == StepType.TRAIN
        assert step.params["modelId"] == "model_123"

    def test_run_checks_step(self):
        step = ScenarioStep.run_checks("validate", "cleaned_data")
        assert step.step_type == StepType.CHECK

    def test_execute_python_step(self):
        step = ScenarioStep.execute_python("custom", "print('hello')")
        assert step.step_type == StepType.PYTHON_EXECUTE
        assert step.params["code"] == "print('hello')"

    def test_send_message_step(self):
        step = ScenarioStep.send_message("notify", "#data", "Pipeline done")
        assert step.step_type == StepType.SEND_MESSAGE

    def test_round_trip(self):
        step = ScenarioStep.build("build", "ds")
        d = step.to_dict()
        restored = ScenarioStep.from_dict(d)
        assert restored.name == step.name
        assert restored.step_type == step.step_type

    def test_step_types(self):
        assert StepType.BUILD.value == "build_dataset"
        assert StepType.TRAIN.value == "train_model"
        assert StepType.CHECK.value == "run_checks"
        assert StepType.SQL_EXECUTE.value == "execute_sql"
        assert StepType.PYTHON_EXECUTE.value == "execute_python"
        assert StepType.SEND_MESSAGE.value == "send_message"


class TestScenarioReporter:
    """Tests for ScenarioReporter."""

    def test_email_reporter(self):
        reporter = ScenarioReporter.email("notify", ["a@b.com"], subject="Done")
        assert reporter.reporter_type == ReporterType.EMAIL
        assert reporter.params["recipients"] == ["a@b.com"]
        assert reporter.params["subject"] == "Done"

    def test_slack_reporter(self):
        reporter = ScenarioReporter.slack("slack_notify", "#data", "https://hooks.slack.com/x")
        assert reporter.reporter_type == ReporterType.SLACK

    def test_webhook_reporter(self):
        reporter = ScenarioReporter.webhook("webhook", "https://api.example.com/hook")
        assert reporter.reporter_type == ReporterType.WEBHOOK

    def test_on_success_failure_flags(self):
        reporter = ScenarioReporter(
            name="test",
            reporter_type=ReporterType.EMAIL,
            on_success=False,
            on_failure=True,
        )
        d = reporter.to_dict()
        assert d["onSuccess"] is False
        assert d["onFailure"] is True

    def test_round_trip(self):
        reporter = ScenarioReporter.email("r", ["x@y.com"])
        d = reporter.to_dict()
        restored = ScenarioReporter.from_dict(d)
        assert restored.name == reporter.name
        assert restored.reporter_type == reporter.reporter_type


class TestDataikuScenario:
    """Tests for DataikuScenario."""

    def test_create_scenario(self):
        scenario = DataikuScenario(name="daily_pipeline")
        assert scenario.name == "daily_pipeline"
        assert scenario.active is True
        assert len(scenario.triggers) == 0
        assert len(scenario.steps) == 0
        assert len(scenario.reporters) == 0

    def test_add_components(self):
        scenario = DataikuScenario(name="test")
        scenario.add_trigger(ScenarioTrigger.time_based("nightly", "0 0 * * *"))
        scenario.add_step(ScenarioStep.build("build", "output"))
        scenario.add_reporter(ScenarioReporter.email("email", ["admin@test.com"]))
        assert len(scenario.triggers) == 1
        assert len(scenario.steps) == 1
        assert len(scenario.reporters) == 1

    def test_to_dict(self):
        scenario = DataikuScenario(name="test", tags=["production"])
        scenario.add_trigger(ScenarioTrigger.time_based("daily", "0 6 * * *"))
        scenario.add_step(ScenarioStep.build("b", "ds"))
        d = scenario.to_dict()
        assert d["name"] == "test"
        assert d["active"] is True
        assert d["tags"] == ["production"]
        assert len(d["triggers"]) == 1
        assert len(d["steps"]) == 1

    def test_to_json(self):
        scenario = DataikuScenario(name="prod_pipeline")
        j = scenario.to_json()
        assert j["id"] == "prod_pipeline"
        assert j["type"] == "step_based"
        assert "versionTag" in j

    def test_round_trip(self):
        scenario = DataikuScenario(name="full_scenario", tags=["v1"])
        scenario.add_trigger(ScenarioTrigger.time_based("hourly", "0 * * * *"))
        scenario.add_trigger(ScenarioTrigger.dataset_change("on_update", "raw_data"))
        scenario.add_step(ScenarioStep.build("build_clean", "clean_data"))
        scenario.add_step(ScenarioStep.train("train", "model_1"))
        scenario.add_reporter(ScenarioReporter.slack("slack", "#ml", "https://x"))
        d = scenario.to_dict()
        restored = DataikuScenario.from_dict(d)
        assert restored.name == "full_scenario"
        assert len(restored.triggers) == 2
        assert len(restored.steps) == 2
        assert len(restored.reporters) == 1
        assert restored.tags == ["v1"]

    def test_repr(self):
        scenario = DataikuScenario(name="s1")
        scenario.add_trigger(ScenarioTrigger.time_based("t", "* * * * *"))
        r = repr(scenario)
        assert "s1" in r
        assert "triggers=1" in r


# ==================== T4.5: Metrics and Checks ====================


class TestDataikuMetric:
    """Tests for DataikuMetric."""

    def test_row_count(self):
        m = DataikuMetric.row_count()
        assert m.metric_type == MetricType.ROW_COUNT
        assert m.name == "row_count"

    def test_column_min(self):
        m = DataikuMetric.column_min("price")
        assert m.metric_type == MetricType.COLUMN_MIN
        assert m.column == "price"
        assert m.name == "price_min"

    def test_column_max(self):
        m = DataikuMetric.column_max("score", name="max_score")
        assert m.name == "max_score"
        assert m.column == "score"

    def test_column_avg(self):
        m = DataikuMetric.column_avg("amount")
        assert m.metric_type == MetricType.COLUMN_AVG

    def test_column_missing(self):
        m = DataikuMetric.column_missing("email")
        assert m.metric_type == MetricType.COLUMN_MISSING

    def test_custom_sql(self):
        m = DataikuMetric.custom_sql("dup_count", "SELECT COUNT(*) FROM t GROUP BY id HAVING COUNT(*) > 1")
        assert m.metric_type == MetricType.CUSTOM_SQL
        assert "SELECT" in m.params["query"]

    def test_to_dict(self):
        m = DataikuMetric.column_avg("val")
        d = m.to_dict()
        assert d["type"] == "column_avg"
        assert d["column"] == "val"

    def test_round_trip(self):
        m = DataikuMetric.custom_sql("test", "SELECT 1")
        d = m.to_dict()
        restored = DataikuMetric.from_dict(d)
        assert restored.name == m.name
        assert restored.metric_type == m.metric_type
        assert restored.params == m.params

    def test_metric_types_enum(self):
        assert len(MetricType) == 10


class TestDataikuCheck:
    """Tests for DataikuCheck."""

    def test_not_empty(self):
        c = DataikuCheck.not_empty("row_check", "row_count")
        assert c.condition == CheckCondition.NOT_EMPTY
        assert c.severity == CheckSeverity.ERROR

    def test_between(self):
        c = DataikuCheck.between("range_check", "price_avg", 10, 1000, CheckSeverity.WARNING)
        assert c.condition == CheckCondition.BETWEEN
        assert c.min_value == 10
        assert c.max_value == 1000
        assert c.severity == CheckSeverity.WARNING

    def test_to_dict(self):
        c = DataikuCheck(
            name="val_check",
            metric_name="row_count",
            condition=CheckCondition.GREATER_THAN,
            value=0,
        )
        d = c.to_dict()
        assert d["condition"] == "greater_than"
        assert d["value"] == 0

    def test_round_trip(self):
        c = DataikuCheck.between("test", "m", 1, 100)
        d = c.to_dict()
        restored = DataikuCheck.from_dict(d)
        assert restored.name == c.name
        assert restored.condition == c.condition
        assert restored.min_value == c.min_value
        assert restored.max_value == c.max_value


class TestDataQualityRule:
    """Tests for DataQualityRule."""

    def test_not_null(self):
        r = DataQualityRule.not_null("email")
        assert r.rule_type == "not_null"
        assert r.column == "email"

    def test_unique(self):
        r = DataQualityRule.unique("id")
        assert r.rule_type == "unique"

    def test_in_range(self):
        r = DataQualityRule.in_range("age", 0, 150)
        assert r.params["min"] == 0
        assert r.params["max"] == 150

    def test_regex_match(self):
        r = DataQualityRule.regex_match("email", r"^[\w.]+@[\w.]+\.\w+$")
        assert r.rule_type == "regex_match"

    def test_in_set(self):
        r = DataQualityRule.in_set("status", ["active", "inactive", "pending"])
        assert r.params["values"] == ["active", "inactive", "pending"]

    def test_round_trip(self):
        r = DataQualityRule.in_range("score", 0, 100)
        d = r.to_dict()
        restored = DataQualityRule.from_dict(d)
        assert restored.column == r.column
        assert restored.rule_type == r.rule_type
        assert restored.params == r.params


# ==================== T4.6: sklearn ML mappings ====================


class TestSklearnMappings:
    """Tests for sklearn ML model -> recipe mappings in ast_analyzer."""

    def test_random_forest_classifier(self):
        from py2dataiku.parser.ast_analyzer import CodeAnalyzer
        code = """
from sklearn.ensemble import RandomForestClassifier
model = RandomForestClassifier(n_estimators=100)
"""
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        recipes = [t.suggested_recipe for t in transformations if t.suggested_recipe]
        assert "prediction_scoring" in recipes

    def test_kmeans_clustering(self):
        from py2dataiku.parser.ast_analyzer import CodeAnalyzer
        code = """
from sklearn.cluster import KMeans
kmeans = KMeans(n_clusters=5)
"""
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        recipes = [t.suggested_recipe for t in transformations if t.suggested_recipe]
        assert "clustering_scoring" in recipes

    def test_cross_val_score(self):
        from py2dataiku.parser.ast_analyzer import CodeAnalyzer
        code = """
from sklearn.model_selection import cross_val_score
scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')
"""
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        recipes = [t.suggested_recipe for t in transformations if t.suggested_recipe]
        assert "evaluation" in recipes

    def test_grid_search_cv(self):
        from py2dataiku.parser.ast_analyzer import CodeAnalyzer
        code = """
from sklearn.model_selection import GridSearchCV
grid = GridSearchCV(model, param_grid)
"""
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        recipes = [t.suggested_recipe for t in transformations if t.suggested_recipe]
        assert "python" in recipes

    def test_column_transformer(self):
        from py2dataiku.parser.ast_analyzer import CodeAnalyzer
        code = """
from sklearn.compose import ColumnTransformer
ct = ColumnTransformer(transformers=[('num', scaler, num_cols)])
"""
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        recipes = [t.suggested_recipe for t in transformations if t.suggested_recipe]
        assert "prepare" in recipes

    def test_logistic_regression(self):
        from py2dataiku.parser.ast_analyzer import CodeAnalyzer
        code = """
from sklearn.linear_model import LogisticRegression
lr = LogisticRegression()
"""
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        recipes = [t.suggested_recipe for t in transformations if t.suggested_recipe]
        assert "prediction_scoring" in recipes

    def test_dbscan(self):
        from py2dataiku.parser.ast_analyzer import CodeAnalyzer
        code = """
from sklearn.cluster import DBSCAN
db = DBSCAN(eps=0.5)
"""
        analyzer = CodeAnalyzer()
        transformations = analyzer.analyze(code)
        recipes = [t.suggested_recipe for t in transformations if t.suggested_recipe]
        assert "clustering_scoring" in recipes


# ==================== T4.7: Flow Zones ====================


class TestFlowZone:
    """Tests for FlowZone."""

    def test_create_zone(self):
        zone = FlowZone(name="ETL")
        assert zone.name == "ETL"
        assert zone.color == "#4b96e6"
        assert zone.datasets == []
        assert zone.recipes == []

    def test_add_dataset(self):
        zone = FlowZone(name="ML")
        zone.add_dataset("training_data")
        zone.add_dataset("training_data")  # duplicate, should not add
        assert len(zone.datasets) == 1

    def test_add_recipe(self):
        zone = FlowZone(name="Reporting")
        zone.add_recipe("aggregate")
        zone.add_recipe("aggregate")  # duplicate
        assert len(zone.recipes) == 1

    def test_to_dict(self):
        zone = FlowZone(name="ETL", color="#ff0000")
        zone.add_dataset("raw")
        zone.add_recipe("clean")
        d = zone.to_dict()
        assert d["name"] == "ETL"
        assert d["color"] == "#ff0000"
        assert "raw" in d["datasets"]

    def test_round_trip(self):
        zone = FlowZone(name="ML", color="#00ff00")
        zone.add_dataset("features")
        zone.add_recipe("train")
        d = zone.to_dict()
        restored = FlowZone.from_dict(d)
        assert restored.name == zone.name
        assert restored.color == zone.color
        assert restored.datasets == zone.datasets
        assert restored.recipes == zone.recipes


class TestFlowWithZones:
    """Tests for DataikuFlow zone integration."""

    def test_add_zone(self):
        flow = DataikuFlow(name="test_flow")
        zone = FlowZone(name="ETL")
        flow.add_zone(zone)
        assert len(flow.zones) == 1

    def test_get_zone(self):
        flow = DataikuFlow(name="test_flow")
        flow.add_zone(FlowZone(name="ETL"))
        flow.add_zone(FlowZone(name="ML"))
        assert flow.get_zone("ETL") is not None
        assert flow.get_zone("ML") is not None
        assert flow.get_zone("nonexistent") is None

    def test_to_dict_with_zones(self):
        flow = DataikuFlow(name="test_flow")
        flow.add_zone(FlowZone(name="ETL"))
        d = flow.to_dict()
        assert "zones" in d
        assert len(d["zones"]) == 1

    def test_to_dict_without_zones(self):
        flow = DataikuFlow(name="test_flow")
        d = flow.to_dict()
        assert "zones" not in d

    def test_round_trip_with_zones(self):
        flow = DataikuFlow(name="zoned_flow")
        zone = FlowZone(name="Data Prep", color="#abcdef")
        zone.add_dataset("raw_data")
        zone.add_recipe("clean_recipe")
        flow.add_zone(zone)
        d = flow.to_dict()
        restored = DataikuFlow.from_dict(d)
        assert len(restored.zones) == 1
        assert restored.zones[0].name == "Data Prep"
        assert restored.zones[0].color == "#abcdef"


# ==================== T4.9: MLOps Models ====================


class TestAPIEndpoint:
    """Tests for APIEndpoint."""

    def test_create_endpoint(self):
        ep = APIEndpoint(name="predict", model_name="fraud_model")
        assert ep.endpoint_type == EndpointType.REST
        assert ep.auth_required is True

    def test_to_dict(self):
        ep = APIEndpoint(
            name="score",
            model_name="churn_model",
            url_path="/api/v1/score",
            input_schema={"customer_id": "int", "features": "array"},
            rate_limit=100,
        )
        d = ep.to_dict()
        assert d["name"] == "score"
        assert d["urlPath"] == "/api/v1/score"
        assert d["rateLimit"] == 100

    def test_round_trip(self):
        ep = APIEndpoint(
            name="predict",
            model_name="model",
            endpoint_type=EndpointType.BATCH,
        )
        d = ep.to_dict()
        restored = APIEndpoint.from_dict(d)
        assert restored.name == ep.name
        assert restored.endpoint_type == EndpointType.BATCH


class TestModelVersion:
    """Tests for ModelVersion."""

    def test_create_version(self):
        v = ModelVersion(
            version_id="v1.0",
            model_name="fraud_detector",
            framework=ModelFramework.SCIKIT_LEARN,
            algorithm="RandomForest",
            metrics={"accuracy": 0.95, "f1": 0.92},
            features=["amount", "merchant", "time"],
            target="is_fraud",
            active=True,
        )
        assert v.version_id == "v1.0"
        assert v.framework == ModelFramework.SCIKIT_LEARN

    def test_to_dict(self):
        v = ModelVersion(version_id="v2", model_name="m", active=True)
        d = v.to_dict()
        assert d["versionId"] == "v2"
        assert d["active"] is True

    def test_round_trip(self):
        v = ModelVersion(
            version_id="v3",
            model_name="model",
            framework=ModelFramework.XGBOOST,
            metrics={"rmse": 1.5},
        )
        d = v.to_dict()
        restored = ModelVersion.from_dict(d)
        assert restored.version_id == v.version_id
        assert restored.framework == ModelFramework.XGBOOST
        assert restored.metrics == v.metrics

    def test_frameworks(self):
        assert len(ModelFramework) == 6


class TestDriftConfig:
    """Tests for DriftConfig."""

    def test_defaults(self):
        dc = DriftConfig()
        assert dc.enabled is True
        assert dc.metric == DriftMetricType.PSI
        assert dc.threshold == 0.2

    def test_custom(self):
        dc = DriftConfig(
            metric=DriftMetricType.KS,
            threshold=0.1,
            columns=["amount", "age"],
            check_frequency="hourly",
        )
        d = dc.to_dict()
        assert d["metric"] == "ks"
        assert d["threshold"] == 0.1
        assert len(d["columns"]) == 2

    def test_round_trip(self):
        dc = DriftConfig(
            metric=DriftMetricType.WASSERSTEIN,
            threshold=0.3,
            columns=["f1", "f2"],
        )
        d = dc.to_dict()
        restored = DriftConfig.from_dict(d)
        assert restored.metric == dc.metric
        assert restored.threshold == dc.threshold
        assert restored.columns == dc.columns


# ==================== T4.10: Configuration ====================


class TestPy2DataikuConfig:
    """Tests for Py2DataikuConfig."""

    def test_defaults(self):
        config = Py2DataikuConfig()
        assert config.default_provider == "anthropic"
        assert config.project_key == "MY_PROJECT"
        assert config.optimize is True
        assert config.default_format == "svg"

    def test_to_dict(self):
        config = Py2DataikuConfig(project_key="TEST_PROJECT")
        d = config.to_dict()
        assert d["project"]["key"] == "TEST_PROJECT"

    def test_from_dict(self):
        data = {
            "provider": {"default": "openai", "model": "gpt-4"},
            "project": {"key": "MY_KEY"},
            "optimization": {"enabled": False, "level": 0},
            "naming": {"dataset_prefix": "ds_"},
            "output": {"format": "html"},
        }
        config = Py2DataikuConfig.from_dict(data)
        assert config.default_provider == "openai"
        assert config.default_model == "gpt-4"
        assert config.project_key == "MY_KEY"
        assert config.optimize is False
        assert config.optimization_level == 0
        assert config.dataset_prefix == "ds_"
        assert config.default_format == "html"

    def test_round_trip(self):
        config = Py2DataikuConfig(
            default_provider="openai",
            project_key="PROJ",
            optimize=False,
        )
        d = config.to_dict()
        restored = Py2DataikuConfig.from_dict(d)
        assert restored.default_provider == config.default_provider
        assert restored.project_key == config.project_key
        assert restored.optimize == config.optimize


class TestLoadConfig:
    """Tests for config file loading."""

    def test_load_default_when_no_file(self):
        config = load_config(auto_discover=False)
        assert config.default_provider == "anthropic"

    def test_load_yaml_config(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write("""
provider:
  default: openai
  model: gpt-4o
project:
  key: TEST_KEY
  flow_name: my_flow
optimization:
  enabled: true
  level: 2
""")
            f.flush()
            config = load_config(config_path=f.name)
        os.unlink(f.name)
        assert config.default_provider == "openai"
        assert config.default_model == "gpt-4o"
        assert config.project_key == "TEST_KEY"
        assert config.flow_name == "my_flow"
        assert config.optimization_level == 2

    def test_load_nonexistent_file(self):
        config = load_config(config_path="/nonexistent/path/config.yaml")
        assert config.default_provider == "anthropic"  # defaults

    def test_find_config_file_none(self):
        result = find_config_file(start_dir="/nonexistent/dir")
        # May find home dir config or return None
        assert result is None or result.exists()

    def test_env_var_override(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write("provider:\n  default: anthropic\n")
            f.flush()
            old_env = os.environ.get("PY2DATAIKU_PROVIDER")
            os.environ["PY2DATAIKU_PROVIDER"] = "openai"
            try:
                config = load_config(config_path=f.name)
                assert config.default_provider == "openai"
            finally:
                if old_env is None:
                    os.environ.pop("PY2DATAIKU_PROVIDER", None)
                else:
                    os.environ["PY2DATAIKU_PROVIDER"] = old_env
        os.unlink(f.name)


# ==================== Integration: imports from __init__ ====================


class TestTier4Exports:
    """Test that all Tier 4 models are properly exported."""

    def test_scenario_exports(self):
        from py2dataiku import (
            DataikuScenario, ScenarioTrigger, ScenarioStep, ScenarioReporter,
            TriggerType, StepType, ReporterType,
        )
        assert DataikuScenario is not None

    def test_metrics_exports(self):
        from py2dataiku import (
            DataikuMetric, DataikuCheck, DataQualityRule,
            MetricType, CheckCondition, CheckSeverity,
        )
        assert DataikuMetric is not None

    def test_mlops_exports(self):
        from py2dataiku import (
            APIEndpoint, ModelVersion, DriftConfig,
            EndpointType, ModelFramework, DriftMetricType,
        )
        assert APIEndpoint is not None

    def test_flow_zone_export(self):
        from py2dataiku import FlowZone
        assert FlowZone is not None

    def test_config_exports(self):
        from py2dataiku import Py2DataikuConfig, load_config, find_config_file
        assert Py2DataikuConfig is not None
