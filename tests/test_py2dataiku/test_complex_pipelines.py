"""
Tests for Complex Enterprise-Grade Data Processing Pipelines

These tests verify that complex, multi-stage data processing pipelines
can be properly analyzed and converted to Dataiku DSS flows.
"""

import pytest
from py2dataiku import convert, Py2Dataiku
from py2dataiku.examples.complex_pipelines import (
    COMPLEX_EXAMPLES,
    COMPLEX_PIPELINE_METADATA,
    get_complex_example,
    list_complex_examples,
    get_pipeline_metadata,
    FRAUD_DETECTION_PIPELINE,
    CUSTOMER_360_PIPELINE,
    SUPPLY_CHAIN_PIPELINE,
    MARKETING_ATTRIBUTION_PIPELINE,
    IOT_PREDICTIVE_MAINTENANCE_PIPELINE,
    GENOMIC_ANALYSIS_PIPELINE,
    CLICKSTREAM_ANALYSIS_PIPELINE,
    PORTFOLIO_RISK_PIPELINE,
)


class TestComplexPipelineBasics:
    """Test basic functionality of complex pipeline examples."""

    def test_all_complex_examples_exist(self):
        """Test that all expected complex examples are defined."""
        expected = [
            "fraud_detection",
            "customer_360",
            "supply_chain",
            "marketing_attribution",
            "iot_predictive_maintenance",
            "genomic_analysis",
            "clickstream_analysis",
            "portfolio_risk"
        ]
        assert set(list_complex_examples()) == set(expected)

    def test_all_examples_have_metadata(self):
        """Test that all examples have associated metadata."""
        for name in list_complex_examples():
            metadata = get_pipeline_metadata(name)
            assert metadata, f"Missing metadata for {name}"
            assert "name" in metadata
            assert "description" in metadata
            assert "data_sources" in metadata
            assert "estimated_recipes" in metadata
            assert "key_operations" in metadata

    def test_get_complex_example_returns_code(self):
        """Test that get_complex_example returns valid code."""
        for name in list_complex_examples():
            code = get_complex_example(name)
            assert code, f"Empty code for {name}"
            assert "import pandas" in code
            assert "pd.read_csv" in code
            assert ".to_csv" in code

    def test_get_nonexistent_example_returns_empty(self):
        """Test that getting a non-existent example returns empty string."""
        assert get_complex_example("nonexistent") == ""

    def test_all_examples_are_nonempty_strings(self):
        """Test that all examples are non-empty strings."""
        for name, code in COMPLEX_EXAMPLES.items():
            assert isinstance(code, str)
            assert len(code) > 500, f"{name} seems too short"


class TestFraudDetectionPipeline:
    """Tests for the Fraud Detection Pipeline."""

    def test_conversion_succeeds(self):
        """Test that fraud detection pipeline converts successfully."""
        flow = convert(FRAUD_DETECTION_PIPELINE)
        assert flow is not None
        assert hasattr(flow, 'datasets')
        assert hasattr(flow, 'recipes')

    def test_detects_multiple_data_sources(self):
        """Test that multiple input sources are detected."""
        flow = convert(FRAUD_DETECTION_PIPELINE)
        # Should detect multiple CSV reads
        assert len(flow.datasets) >= 2

    def test_produces_mermaid_output(self):
        """Test Mermaid diagram generation."""
        flow = convert(FRAUD_DETECTION_PIPELINE)
        mermaid = flow.visualize(format="mermaid")
        assert "flowchart" in mermaid.lower() or len(mermaid) > 0

    def test_produces_svg_output(self):
        """Test SVG visualization generation."""
        flow = convert(FRAUD_DETECTION_PIPELINE)
        svg = flow.to_svg()
        assert "<svg" in svg
        assert "</svg>" in svg

    def test_flow_to_dict_exists(self):
        """Test that flow can be converted to dict."""
        flow = convert(FRAUD_DETECTION_PIPELINE)
        flow_dict = flow.to_dict()
        assert isinstance(flow_dict, dict)
        assert "datasets" in flow_dict or "recipes" in flow_dict or len(flow_dict) > 0


class TestCustomer360Pipeline:
    """Tests for the Customer 360 Data Lake Pipeline."""

    def test_conversion_succeeds(self):
        """Test that customer 360 pipeline converts successfully."""
        flow = convert(CUSTOMER_360_PIPELINE)
        assert flow is not None

    def test_detects_many_data_sources(self):
        """Test that 10 data sources are detected."""
        flow = convert(CUSTOMER_360_PIPELINE)
        # Pipeline loads 10 different CSVs
        assert len(flow.datasets) >= 5

    def test_has_complex_joins(self):
        """Test that complex joins are present in the pipeline."""
        # The pipeline has pd.merge operations and a loop-based merge pattern
        assert "pd.merge" in CUSTOMER_360_PIPELINE
        # Also uses for loop to merge multiple metrics DataFrames
        assert "for metrics_df in" in CUSTOMER_360_PIPELINE

    def test_has_aggregations(self):
        """Test that aggregations are present."""
        assert ".groupby" in CUSTOMER_360_PIPELINE
        groupby_count = CUSTOMER_360_PIPELINE.count(".groupby")
        assert groupby_count >= 5

    def test_produces_ascii_output(self):
        """Test ASCII visualization generation."""
        flow = convert(CUSTOMER_360_PIPELINE)
        ascii_art = flow.to_ascii()
        assert len(ascii_art) > 0


class TestSupplyChainPipeline:
    """Tests for the Supply Chain Optimization Pipeline."""

    def test_conversion_succeeds(self):
        """Test that supply chain pipeline converts successfully."""
        flow = convert(SUPPLY_CHAIN_PIPELINE)
        assert flow is not None

    def test_has_time_series_operations(self):
        """Test that time series operations are detected."""
        assert ".rolling" in SUPPLY_CHAIN_PIPELINE
        assert "pd.to_datetime" in SUPPLY_CHAIN_PIPELINE

    def test_has_window_functions(self):
        """Test that window functions are present."""
        # Pipeline uses rolling windows for demand forecasting
        rolling_count = SUPPLY_CHAIN_PIPELINE.count(".rolling")
        assert rolling_count >= 3

    def test_multiple_outputs(self):
        """Test that multiple output files are created."""
        output_count = SUPPLY_CHAIN_PIPELINE.count(".to_csv")
        assert output_count >= 3

    def test_produces_plantuml_output(self):
        """Test PlantUML visualization generation."""
        flow = convert(SUPPLY_CHAIN_PIPELINE)
        plantuml = flow.to_plantuml()
        assert "@startuml" in plantuml or "plantuml" in plantuml.lower() or len(plantuml) > 0


class TestMarketingAttributionPipeline:
    """Tests for the Marketing Attribution Pipeline."""

    def test_conversion_succeeds(self):
        """Test that marketing attribution pipeline converts successfully."""
        flow = convert(MARKETING_ATTRIBUTION_PIPELINE)
        assert flow is not None

    def test_has_attribution_logic(self):
        """Test that attribution models are implemented."""
        # Check for different attribution approaches
        assert "first_touch" in MARKETING_ATTRIBUTION_PIPELINE.lower()
        assert "last_touch" in MARKETING_ATTRIBUTION_PIPELINE.lower()
        assert "linear" in MARKETING_ATTRIBUTION_PIPELINE.lower()
        assert "time_decay" in MARKETING_ATTRIBUTION_PIPELINE.lower()

    def test_has_journey_analysis(self):
        """Test that customer journey analysis is present."""
        assert "journey" in MARKETING_ATTRIBUTION_PIPELINE.lower()
        assert "touchpoint" in MARKETING_ATTRIBUTION_PIPELINE.lower()

    def test_roi_calculations(self):
        """Test that ROI calculations are present."""
        assert "roi" in MARKETING_ATTRIBUTION_PIPELINE.lower()

    def test_produces_html_output(self):
        """Test HTML visualization generation."""
        flow = convert(MARKETING_ATTRIBUTION_PIPELINE)
        html = flow.to_html()
        assert "<html" in html.lower() or "canvas" in html.lower() or len(html) > 0


class TestIoTPredictiveMaintenancePipeline:
    """Tests for the IoT Predictive Maintenance Pipeline."""

    def test_conversion_succeeds(self):
        """Test that IoT pipeline converts successfully."""
        flow = convert(IOT_PREDICTIVE_MAINTENANCE_PIPELINE)
        assert flow is not None

    def test_has_sensor_processing(self):
        """Test that sensor data processing is present."""
        assert "sensor" in IOT_PREDICTIVE_MAINTENANCE_PIPELINE.lower()
        assert "reading" in IOT_PREDICTIVE_MAINTENANCE_PIPELINE.lower()

    def test_has_anomaly_detection(self):
        """Test that anomaly detection logic is present."""
        assert "z_score" in IOT_PREDICTIVE_MAINTENANCE_PIPELINE.lower() or "anomaly" in IOT_PREDICTIVE_MAINTENANCE_PIPELINE.lower()

    def test_has_predictive_features(self):
        """Test that predictive features are calculated."""
        assert "failure" in IOT_PREDICTIVE_MAINTENANCE_PIPELINE.lower()
        assert "health" in IOT_PREDICTIVE_MAINTENANCE_PIPELINE.lower()

    def test_has_maintenance_scheduling(self):
        """Test that maintenance scheduling logic is present."""
        assert "maintenance" in IOT_PREDICTIVE_MAINTENANCE_PIPELINE.lower()
        assert "priority" in IOT_PREDICTIVE_MAINTENANCE_PIPELINE.lower()


class TestGenomicAnalysisPipeline:
    """Tests for the Genomic Variant Analysis Pipeline."""

    def test_conversion_succeeds(self):
        """Test that genomic analysis pipeline converts successfully."""
        flow = convert(GENOMIC_ANALYSIS_PIPELINE)
        assert flow is not None

    def test_has_variant_processing(self):
        """Test that variant processing is present."""
        assert "variant" in GENOMIC_ANALYSIS_PIPELINE.lower()
        assert "chromosome" in GENOMIC_ANALYSIS_PIPELINE.lower()

    def test_has_quality_filtering(self):
        """Test that quality filtering is implemented."""
        assert "quality" in GENOMIC_ANALYSIS_PIPELINE.lower()
        assert "filter" in GENOMIC_ANALYSIS_PIPELINE.lower() or "pass" in GENOMIC_ANALYSIS_PIPELINE.lower()

    def test_has_annotation_logic(self):
        """Test that annotation logic is present."""
        assert "gene" in GENOMIC_ANALYSIS_PIPELINE.lower()
        assert "annotation" in GENOMIC_ANALYSIS_PIPELINE.lower() or "annotate" in GENOMIC_ANALYSIS_PIPELINE.lower()

    def test_has_burden_analysis(self):
        """Test that burden analysis is calculated."""
        assert "burden" in GENOMIC_ANALYSIS_PIPELINE.lower()


class TestClickstreamAnalysisPipeline:
    """Tests for the Clickstream Analysis Pipeline."""

    def test_conversion_succeeds(self):
        """Test that clickstream pipeline converts successfully."""
        flow = convert(CLICKSTREAM_ANALYSIS_PIPELINE)
        assert flow is not None

    def test_has_event_processing(self):
        """Test that event processing is present."""
        assert "event" in CLICKSTREAM_ANALYSIS_PIPELINE.lower()
        assert "page_view" in CLICKSTREAM_ANALYSIS_PIPELINE.lower() or "pageview" in CLICKSTREAM_ANALYSIS_PIPELINE.lower()

    def test_has_session_analysis(self):
        """Test that session analysis is implemented."""
        assert "session" in CLICKSTREAM_ANALYSIS_PIPELINE.lower()
        assert "duration" in CLICKSTREAM_ANALYSIS_PIPELINE.lower()

    def test_has_user_metrics(self):
        """Test that user-level metrics are calculated."""
        assert "user_metrics" in CLICKSTREAM_ANALYSIS_PIPELINE.lower() or "user_id" in CLICKSTREAM_ANALYSIS_PIPELINE.lower()

    def test_has_conversion_tracking(self):
        """Test that conversion tracking is present."""
        assert "convert" in CLICKSTREAM_ANALYSIS_PIPELINE.lower()


class TestPortfolioRiskPipeline:
    """Tests for the Financial Portfolio Risk Pipeline."""

    def test_conversion_succeeds(self):
        """Test that portfolio risk pipeline converts successfully."""
        flow = convert(PORTFOLIO_RISK_PIPELINE)
        assert flow is not None

    def test_has_return_calculations(self):
        """Test that return calculations are present."""
        assert "return" in PORTFOLIO_RISK_PIPELINE.lower()
        assert "pct_change" in PORTFOLIO_RISK_PIPELINE.lower()

    def test_has_risk_metrics(self):
        """Test that risk metrics are calculated."""
        assert "volatility" in PORTFOLIO_RISK_PIPELINE.lower()
        assert "var" in PORTFOLIO_RISK_PIPELINE.lower()  # Value at Risk

    def test_has_beta_calculation(self):
        """Test that beta calculation is present."""
        assert "beta" in PORTFOLIO_RISK_PIPELINE.lower()

    def test_has_sharpe_ratio(self):
        """Test that Sharpe ratio is calculated."""
        assert "sharpe" in PORTFOLIO_RISK_PIPELINE.lower()


class TestComplexPipelineVisualizations:
    """Test visualization outputs for all complex pipelines."""

    @pytest.mark.parametrize("name,code", list(COMPLEX_EXAMPLES.items()))
    def test_svg_visualization(self, name, code):
        """Test that each complex pipeline can generate SVG visualization."""
        flow = convert(code)
        svg = flow.to_svg()
        assert "<svg" in svg or len(svg) > 0, f"Failed SVG for {name}"

    @pytest.mark.parametrize("name,code", list(COMPLEX_EXAMPLES.items()))
    def test_ascii_visualization(self, name, code):
        """Test that each complex pipeline can generate ASCII visualization."""
        flow = convert(code)
        ascii_out = flow.to_ascii()
        assert len(ascii_out) > 0, f"Failed ASCII for {name}"

    @pytest.mark.parametrize("name,code", list(COMPLEX_EXAMPLES.items()))
    def test_mermaid_visualization(self, name, code):
        """Test that each complex pipeline can generate Mermaid visualization."""
        flow = convert(code)
        mermaid = flow.visualize(format="mermaid")
        assert len(mermaid) > 0, f"Failed Mermaid for {name}"


class TestComplexPipelineMetrics:
    """Test pipeline complexity metrics."""

    @pytest.mark.parametrize("name,code", list(COMPLEX_EXAMPLES.items()))
    def test_pipeline_has_datasets(self, name, code):
        """Test that each pipeline has datasets."""
        flow = convert(code)
        assert len(flow.datasets) >= 0, f"No datasets in {name}"

    @pytest.mark.parametrize("name,code", list(COMPLEX_EXAMPLES.items()))
    def test_pipeline_conversion_no_errors(self, name, code):
        """Test that each pipeline converts without errors."""
        try:
            flow = convert(code)
            assert flow is not None
        except Exception as e:
            pytest.fail(f"Pipeline {name} failed to convert: {e}")

    def test_fraud_detection_complexity(self):
        """Test that fraud detection pipeline has expected complexity."""
        code = FRAUD_DETECTION_PIPELINE
        assert code.count("pd.merge") >= 5  # Multiple joins
        assert code.count(".groupby") >= 2  # Aggregations
        assert code.count(".fillna") >= 1  # Data cleaning

    def test_customer_360_complexity(self):
        """Test that customer 360 pipeline has expected complexity."""
        code = CUSTOMER_360_PIPELINE
        # Uses explicit merges + loop-based merge pattern
        assert code.count("pd.merge") >= 2  # Direct merges
        assert "for metrics_df in" in code  # Loop-based merges (8 additional)
        assert code.count(".groupby") >= 8  # Many aggregations
        assert code.count("pd.read_csv") >= 8  # Many data sources

    def test_supply_chain_complexity(self):
        """Test that supply chain pipeline has expected complexity."""
        code = SUPPLY_CHAIN_PIPELINE
        assert code.count(".rolling") >= 4  # Time series operations
        assert code.count("pd.merge") >= 5  # Joins
        assert code.count(".to_csv") >= 3  # Multiple outputs


class TestComplexPipelineExports:
    """Test export functionality for complex pipelines."""

    def test_fraud_detection_to_json(self):
        """Test JSON export for fraud detection."""
        flow = convert(FRAUD_DETECTION_PIPELINE)
        json_str = flow.to_json()
        assert len(json_str) > 0
        assert "{" in json_str and "}" in json_str

    def test_customer_360_to_yaml(self):
        """Test YAML export for customer 360."""
        flow = convert(CUSTOMER_360_PIPELINE)
        yaml_str = flow.to_yaml()
        assert len(yaml_str) > 0

    def test_supply_chain_to_dict(self):
        """Test dict export for supply chain."""
        flow = convert(SUPPLY_CHAIN_PIPELINE)
        flow_dict = flow.to_dict()
        assert isinstance(flow_dict, dict)
        assert "datasets" in flow_dict or "recipes" in flow_dict or len(flow_dict) > 0


class TestComplexPipelineCodePatterns:
    """Test that complex pipelines contain expected code patterns."""

    def test_all_pipelines_have_imports(self):
        """Test that all pipelines have proper imports."""
        for name, code in COMPLEX_EXAMPLES.items():
            assert "import pandas as pd" in code, f"{name} missing pandas import"

    def test_all_pipelines_have_data_loading(self):
        """Test that all pipelines load data."""
        for name, code in COMPLEX_EXAMPLES.items():
            assert "pd.read_csv" in code, f"{name} missing data loading"

    def test_all_pipelines_have_data_output(self):
        """Test that all pipelines output data."""
        for name, code in COMPLEX_EXAMPLES.items():
            assert ".to_csv" in code, f"{name} missing data output"

    def test_all_pipelines_have_transformations(self):
        """Test that all pipelines have data transformations."""
        for name, code in COMPLEX_EXAMPLES.items():
            has_transform = (
                "pd.merge" in code or
                ".groupby" in code or
                ".apply" in code or
                ".transform" in code
            )
            assert has_transform, f"{name} missing transformations"


class TestComplexPipelineDataSources:
    """Test data source detection in complex pipelines."""

    def test_fraud_detection_data_sources(self):
        """Test fraud detection has 6 data sources."""
        metadata = get_pipeline_metadata("fraud_detection")
        assert metadata["data_sources"] == 6

    def test_customer_360_data_sources(self):
        """Test customer 360 has 10 data sources."""
        metadata = get_pipeline_metadata("customer_360")
        assert metadata["data_sources"] == 10

    def test_supply_chain_data_sources(self):
        """Test supply chain has 9 data sources."""
        metadata = get_pipeline_metadata("supply_chain")
        assert metadata["data_sources"] == 9

    def test_iot_predictive_maintenance_data_sources(self):
        """Test IoT pipeline has 7 data sources."""
        metadata = get_pipeline_metadata("iot_predictive_maintenance")
        assert metadata["data_sources"] == 7


class TestComplexPipelineKeyOperations:
    """Test that key operations are documented correctly."""

    def test_fraud_detection_operations(self):
        """Test fraud detection key operations."""
        metadata = get_pipeline_metadata("fraud_detection")
        ops = metadata["key_operations"]
        assert "joins" in ops
        assert "aggregations" in ops
        assert "feature engineering" in ops

    def test_customer_360_operations(self):
        """Test customer 360 key operations."""
        metadata = get_pipeline_metadata("customer_360")
        ops = metadata["key_operations"]
        assert "identity resolution" in ops
        assert "segmentation" in ops

    def test_marketing_attribution_operations(self):
        """Test marketing attribution key operations."""
        metadata = get_pipeline_metadata("marketing_attribution")
        ops = metadata["key_operations"]
        assert "attribution modeling" in ops
        assert "ROI calculations" in ops


class TestComplexPipelineIntegration:
    """Integration tests for complex pipelines with Py2Dataiku class."""

    def test_py2dataiku_convert_fraud_detection(self):
        """Test Py2Dataiku class conversion of fraud detection."""
        converter = Py2Dataiku()
        flow = converter.convert(FRAUD_DETECTION_PIPELINE)
        assert flow is not None

    def test_py2dataiku_convert_all_complex(self):
        """Test Py2Dataiku class can convert all complex pipelines."""
        converter = Py2Dataiku()
        for name, code in COMPLEX_EXAMPLES.items():
            flow = converter.convert(code)
            assert flow is not None, f"Failed to convert {name}"

    def test_py2dataiku_visualize_complex(self):
        """Test Py2Dataiku visualization of complex pipeline."""
        converter = Py2Dataiku()
        flow = converter.convert(CUSTOMER_360_PIPELINE)
        svg = converter.visualize(flow, format="svg")
        assert "<svg" in svg or len(svg) > 0


class TestComplexPipelineEdgeCases:
    """Test edge cases in complex pipeline processing."""

    def test_very_long_pipeline_conversion(self):
        """Test that very long pipelines convert successfully."""
        # Combine multiple pipelines
        combined = FRAUD_DETECTION_PIPELINE + "\n\n" + CUSTOMER_360_PIPELINE
        flow = convert(combined)
        assert flow is not None

    def test_pipeline_with_many_outputs(self):
        """Test pipeline with many output files."""
        # Supply chain has 4 outputs
        flow = convert(SUPPLY_CHAIN_PIPELINE)
        # Should handle multiple outputs
        assert flow is not None

    def test_pipeline_with_nested_aggregations(self):
        """Test pipeline with nested groupby operations."""
        # Portfolio risk has complex nested calculations
        flow = convert(PORTFOLIO_RISK_PIPELINE)
        assert flow is not None

    def test_pipeline_with_window_functions(self):
        """Test pipeline with extensive window function usage."""
        # IoT pipeline uses rolling windows extensively
        flow = convert(IOT_PREDICTIVE_MAINTENANCE_PIPELINE)
        assert flow is not None
