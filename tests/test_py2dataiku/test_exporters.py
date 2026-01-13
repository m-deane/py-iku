"""Tests for the DSS exporter module."""

import json
import os
import shutil
import tempfile
import zipfile

import pytest

from py2dataiku import convert, DataikuFlow
from py2dataiku.exporters import DSSExporter, DSSProjectConfig, export_to_dss
from py2dataiku.models.dataiku_recipe import DataikuRecipe, RecipeType
from py2dataiku.models.dataiku_dataset import DataikuDataset, DatasetType
from py2dataiku.models.prepare_step import PrepareStep, ProcessorType


class TestDSSProjectConfig:
    """Tests for DSSProjectConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = DSSProjectConfig()

        assert config.project_key == "CONVERTED_PROJECT"
        assert config.project_name == "Converted Python Pipeline"
        assert config.owner == "py2dataiku"
        assert "py2dataiku" in config.tags

    def test_custom_config(self):
        """Test custom configuration."""
        config = DSSProjectConfig(
            project_key="MY_PROJECT",
            project_name="My Pipeline",
            owner="user@example.com",
            description="Custom description",
        )

        assert config.project_key == "MY_PROJECT"
        assert config.project_name == "My Pipeline"
        assert config.owner == "user@example.com"
        assert config.description == "Custom description"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = DSSProjectConfig(project_key="TEST_PROJECT")
        d = config.to_dict()

        assert d["projectKey"] == "TEST_PROJECT"
        assert "name" in d
        assert "owner" in d


class TestDSSExporter:
    """Tests for DSSExporter class."""

    def setup_method(self):
        """Create a test flow before each test."""
        self.flow = DataikuFlow(name="test_flow")
        self.flow.add_dataset(DataikuDataset(name="input_data", dataset_type=DatasetType.INPUT))
        self.flow.add_dataset(DataikuDataset(name="output_data", dataset_type=DatasetType.OUTPUT))
        self.flow.add_recipe(DataikuRecipe(
            name="prepare_1",
            recipe_type=RecipeType.PREPARE,
            inputs=["input_data"],
            outputs=["output_data"],
            steps=[PrepareStep(processor_type=ProcessorType.FILL_EMPTY_WITH_VALUE, params={"column": "col", "value": "0"})],
        ))

        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temp directory after each test."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_exporter_init(self):
        """Test exporter initialization."""
        exporter = DSSExporter(self.flow, project_key="MY_PROJECT")

        assert exporter.flow == self.flow
        assert exporter.config.project_key == "MY_PROJECT"

    def test_exporter_with_config(self):
        """Test exporter with custom config."""
        config = DSSProjectConfig(
            project_key="CUSTOM_KEY",
            project_name="Custom Name",
        )
        exporter = DSSExporter(self.flow, config=config)

        assert exporter.config.project_key == "CUSTOM_KEY"
        assert exporter.config.project_name == "Custom Name"

    def test_export_creates_directory_structure(self):
        """Test that export creates proper directory structure."""
        exporter = DSSExporter(self.flow, project_key="TEST_PROJECT")
        output_path = exporter.export(self.temp_dir)

        assert os.path.exists(output_path)
        assert os.path.isdir(os.path.join(output_path, "datasets"))
        assert os.path.isdir(os.path.join(output_path, "recipes"))
        assert os.path.isdir(os.path.join(output_path, "flow"))

    def test_export_creates_project_json(self):
        """Test that export creates project.json."""
        exporter = DSSExporter(self.flow, project_key="TEST_PROJECT")
        output_path = exporter.export(self.temp_dir)

        project_json_path = os.path.join(output_path, "project.json")
        assert os.path.exists(project_json_path)

        with open(project_json_path, "r") as f:
            data = json.load(f)

        assert data["projectKey"] == "TEST_PROJECT"
        assert "versionTag" in data

    def test_export_creates_params_json(self):
        """Test that export creates params.json."""
        exporter = DSSExporter(self.flow, project_key="TEST_PROJECT")
        output_path = exporter.export(self.temp_dir)

        params_path = os.path.join(output_path, "params.json")
        assert os.path.exists(params_path)

        with open(params_path, "r") as f:
            data = json.load(f)

        assert "projectVariables" in data

    def test_export_creates_dataset_configs(self):
        """Test that export creates dataset configuration files."""
        exporter = DSSExporter(self.flow, project_key="TEST_PROJECT")
        output_path = exporter.export(self.temp_dir)

        datasets_dir = os.path.join(output_path, "datasets")

        # Should have configs for each dataset
        assert os.path.exists(os.path.join(datasets_dir, "input_data.json"))
        assert os.path.exists(os.path.join(datasets_dir, "output_data.json"))

    def test_export_creates_recipe_configs(self):
        """Test that export creates recipe configuration files."""
        exporter = DSSExporter(self.flow, project_key="TEST_PROJECT")
        output_path = exporter.export(self.temp_dir)

        recipes_dir = os.path.join(output_path, "recipes")

        # Should have config for each recipe
        assert os.path.exists(os.path.join(recipes_dir, "prepare_1.json"))

    def test_export_recipe_has_correct_type(self):
        """Test that exported recipe has correct DSS type."""
        exporter = DSSExporter(self.flow, project_key="TEST_PROJECT")
        output_path = exporter.export(self.temp_dir)

        recipe_path = os.path.join(output_path, "recipes", "prepare_1.json")
        with open(recipe_path, "r") as f:
            data = json.load(f)

        # Prepare recipe should be "shaker" in DSS
        assert data["type"] == "shaker"
        assert "params" in data

    def test_export_creates_flow_zones(self):
        """Test that export creates flow zone configuration."""
        exporter = DSSExporter(self.flow, project_key="TEST_PROJECT")
        output_path = exporter.export(self.temp_dir)

        zones_path = os.path.join(output_path, "flow", "zones.json")
        assert os.path.exists(zones_path)

        with open(zones_path, "r") as f:
            data = json.load(f)

        assert "zones" in data

    def test_export_creates_readme(self):
        """Test that export creates README.md."""
        exporter = DSSExporter(self.flow, project_key="TEST_PROJECT")
        output_path = exporter.export(self.temp_dir)

        readme_path = os.path.join(output_path, "README.md")
        assert os.path.exists(readme_path)

        with open(readme_path, "r") as f:
            content = f.read()

        assert "TEST_PROJECT" in content
        assert "Import Instructions" in content

    def test_export_creates_zip(self):
        """Test that export can create a zip file."""
        exporter = DSSExporter(self.flow, project_key="ZIP_PROJECT")
        zip_path = exporter.export(self.temp_dir, create_zip=True)

        assert zip_path.endswith(".zip")
        assert os.path.exists(zip_path)

        # Verify zip contents
        with zipfile.ZipFile(zip_path, 'r') as z:
            names = z.namelist()
            assert any("project.json" in n for n in names)
            assert any("recipes" in n for n in names)
            assert any("datasets" in n for n in names)

    def test_get_api_bundle(self):
        """Test getting API-compatible bundle."""
        exporter = DSSExporter(self.flow, project_key="API_PROJECT")
        bundle = exporter.get_api_bundle()

        assert bundle["projectKey"] == "API_PROJECT"
        assert "datasets" in bundle
        assert "recipes" in bundle
        assert len(bundle["datasets"]) == 2
        assert len(bundle["recipes"]) == 1


class TestDSSExporterRecipeTypes:
    """Tests for different recipe type exports."""

    def setup_method(self):
        """Set up temp directory."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_export_join_recipe(self):
        """Test exporting a JOIN recipe."""
        flow = DataikuFlow(name="join_test")
        flow.add_recipe(DataikuRecipe(
            name="join_1",
            recipe_type=RecipeType.JOIN,
            inputs=["left_data", "right_data"],
            outputs=["joined_data"],
        ))

        exporter = DSSExporter(flow, project_key="JOIN_TEST")
        output_path = exporter.export(self.temp_dir)

        recipe_path = os.path.join(output_path, "recipes", "join_1.json")
        with open(recipe_path, "r") as f:
            data = json.load(f)

        assert data["type"] == "join"

    def test_export_grouping_recipe(self):
        """Test exporting a GROUPING recipe."""
        flow = DataikuFlow(name="grouping_test")
        recipe = DataikuRecipe(
            name="grouping_1",
            recipe_type=RecipeType.GROUPING,
            inputs=["input_data"],
            outputs=["grouped_data"],
        )
        recipe.parameters = {"keys": ["category"], "aggregations": {"amount": "sum"}}
        flow.add_recipe(recipe)

        exporter = DSSExporter(flow, project_key="GROUP_TEST")
        output_path = exporter.export(self.temp_dir)

        recipe_path = os.path.join(output_path, "recipes", "grouping_1.json")
        with open(recipe_path, "r") as f:
            data = json.load(f)

        assert data["type"] == "grouping"

    def test_export_sort_recipe(self):
        """Test exporting a SORT recipe."""
        flow = DataikuFlow(name="sort_test")
        recipe = DataikuRecipe(
            name="sort_1",
            recipe_type=RecipeType.SORT,
            inputs=["input_data"],
            outputs=["sorted_data"],
        )
        recipe.parameters = {"columns": ["col_a"], "ascending": True}
        flow.add_recipe(recipe)

        exporter = DSSExporter(flow, project_key="SORT_TEST")
        output_path = exporter.export(self.temp_dir)

        recipe_path = os.path.join(output_path, "recipes", "sort_1.json")
        with open(recipe_path, "r") as f:
            data = json.load(f)

        assert data["type"] == "sort"

    def test_export_python_recipe(self):
        """Test exporting a Python recipe."""
        flow = DataikuFlow(name="python_test")
        recipe = DataikuRecipe(
            name="python_1",
            recipe_type=RecipeType.PYTHON,
            inputs=["input_data"],
            outputs=["output_data"],
        )
        recipe.parameters = {"code": "# Custom code\ndf = df.apply(custom_func)"}
        recipe.notes = ["Complex transformation"]
        flow.add_recipe(recipe)

        exporter = DSSExporter(flow, project_key="PYTHON_TEST")
        output_path = exporter.export(self.temp_dir)

        recipe_path = os.path.join(output_path, "recipes", "python_1.json")
        with open(recipe_path, "r") as f:
            data = json.load(f)

        assert data["type"] == "python"
        assert "params" in data
        assert "code" in data["params"]


class TestExportToDSSFunction:
    """Tests for the convenience export_to_dss function."""

    def setup_method(self):
        """Set up temp directory."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_export_to_dss_basic(self):
        """Test basic export_to_dss call."""
        flow = DataikuFlow(name="test")
        flow.add_dataset(DataikuDataset(name="ds", dataset_type=DatasetType.INPUT))

        output_path = export_to_dss(flow, self.temp_dir, project_key="BASIC_TEST")

        assert os.path.exists(output_path)
        assert os.path.exists(os.path.join(output_path, "project.json"))

    def test_export_to_dss_with_zip(self):
        """Test export_to_dss with zip creation."""
        flow = DataikuFlow(name="test")
        flow.add_dataset(DataikuDataset(name="ds", dataset_type=DatasetType.INPUT))

        zip_path = export_to_dss(flow, self.temp_dir, project_key="ZIP_TEST", create_zip=True)

        assert zip_path.endswith(".zip")
        assert os.path.exists(zip_path)


class TestDSSExporterIntegration:
    """Integration tests for DSS export from converted code."""

    def setup_method(self):
        """Set up temp directory."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_export_converted_pipeline(self):
        """Test exporting a converted pipeline."""
        code = """
import pandas as pd
df = pd.read_csv('data.csv')
df = df.dropna()
df = df.fillna(0)
result = df.groupby('category').agg({'amount': 'sum'})
"""
        flow = convert(code)
        output_path = export_to_dss(flow, self.temp_dir, project_key="PIPELINE_TEST")

        # Verify structure
        assert os.path.exists(os.path.join(output_path, "project.json"))
        assert os.path.isdir(os.path.join(output_path, "datasets"))
        assert os.path.isdir(os.path.join(output_path, "recipes"))

        # Verify datasets were created
        datasets_dir = os.path.join(output_path, "datasets")
        dataset_files = os.listdir(datasets_dir)
        assert len(dataset_files) > 0

        # Verify recipes were created
        recipes_dir = os.path.join(output_path, "recipes")
        recipe_files = os.listdir(recipes_dir)
        assert len(recipe_files) > 0

    def test_export_preserves_flow_structure(self):
        """Test that export preserves flow structure."""
        code = """
import pandas as pd
df1 = pd.read_csv('data1.csv')
df2 = pd.read_csv('data2.csv')
merged = pd.merge(df1, df2, on='key')
"""
        flow = convert(code)
        exporter = DSSExporter(flow, project_key="STRUCTURE_TEST")
        bundle = exporter.get_api_bundle()

        # Should preserve multiple datasets
        assert len(bundle["datasets"]) >= 2
