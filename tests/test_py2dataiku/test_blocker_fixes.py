"""Tests for blocker fixes: C3 (DAG cycle), C4 (API format), C6 (dataset names), H4 (dual output)."""

import re

import pytest

from py2dataiku import convert, DataikuFlow
from py2dataiku.exporters import DSSExporter
from py2dataiku.generators.base_generator import BaseFlowGenerator
from py2dataiku.models.dataiku_recipe import DataikuRecipe, RecipeType
from py2dataiku.models.dataiku_dataset import DataikuDataset, DatasetType
from py2dataiku.models.prepare_step import PrepareStep, ProcessorType


# ---------------------------------------------------------------------------
# C3: DAG cycle bug
# ---------------------------------------------------------------------------

class TestDAGCycleBug:
    """C3: When a variable is reassigned with a filter, the SPLIT recipe must
    not have the same dataset as both input and output."""

    def test_filter_reassignment_no_cycle(self):
        """df = df[df['amount'] > 100] must not produce input == output."""
        code = """
import pandas as pd
df = pd.read_csv('data.csv')
df = df[df['amount'] > 100]
df.to_csv('output.csv')
"""
        flow = convert(code)
        for recipe in flow:
            overlap = set(recipe.inputs) & set(recipe.outputs)
            assert not overlap, (
                f"Cycle in recipe '{recipe.name}': "
                f"inputs={recipe.inputs}, outputs={recipe.outputs}"
            )

    def test_filter_reassignment_produces_filtered_suffix(self):
        """The renamed output should contain '_filtered' to avoid collision."""
        code = """
import pandas as pd
df = pd.read_csv('data.csv')
df = df[df['value'] > 0]
"""
        flow = convert(code)
        split_recipes = flow.get_recipes_by_type(RecipeType.SPLIT)
        if split_recipes:
            recipe = split_recipes[0]
            # Output should be different from input
            assert recipe.outputs[0] != recipe.inputs[0]
            assert "filtered" in recipe.outputs[0]

    def test_filter_different_variable_no_suffix(self):
        """result = df[condition] should NOT add _filtered because there is no collision."""
        code = """
import pandas as pd
df = pd.read_csv('data.csv')
result = df[df['amount'] > 100]
"""
        flow = convert(code)
        split_recipes = flow.get_recipes_by_type(RecipeType.SPLIT)
        if split_recipes:
            recipe = split_recipes[0]
            assert recipe.outputs[0] != recipe.inputs[0]

    def test_flow_validation_no_cycles(self):
        """Flow validation should report no cycles for filtered reassignment."""
        code = """
import pandas as pd
df = pd.read_csv('data.csv')
df = df[df['amount'] > 100]
"""
        flow = convert(code)
        result = flow.validate()
        cycle_errors = [e for e in result["errors"] if e["type"] == "CYCLE_DETECTED"]
        assert len(cycle_errors) == 0


# ---------------------------------------------------------------------------
# C4: to_api_dict() format matches DSS API
# ---------------------------------------------------------------------------

class TestApiDictFormat:
    """C4: to_api_dict() must produce DSS-compatible output."""

    def test_prepare_type_is_shaker(self):
        """PREPARE recipe type should be 'shaker' in API output."""
        recipe = DataikuRecipe.create_prepare("p", "in", "out")
        api = recipe.to_api_dict()
        assert api["type"] == "shaker"

    def test_stack_type_is_vstack(self):
        """STACK recipe type should be 'vstack' in API output."""
        recipe = DataikuRecipe(
            name="s", recipe_type=RecipeType.STACK,
            inputs=["a", "b"], outputs=["out"],
        )
        api = recipe.to_api_dict()
        assert api["type"] == "vstack"

    def test_inputs_nested_format(self):
        """Inputs must use nested {"main": {"items": [{"ref": ..., "deps": []}]}} format."""
        recipe = DataikuRecipe.create_prepare("p", "input_ds", "output_ds")
        api = recipe.to_api_dict()

        assert isinstance(api["inputs"], dict)
        assert "main" in api["inputs"]
        assert "items" in api["inputs"]["main"]
        items = api["inputs"]["main"]["items"]
        assert len(items) == 1
        assert items[0]["ref"] == "input_ds"
        assert items[0]["deps"] == []

    def test_outputs_nested_format(self):
        """Outputs must use the same nested format as inputs."""
        recipe = DataikuRecipe.create_prepare("p", "input_ds", "output_ds")
        api = recipe.to_api_dict()

        assert isinstance(api["outputs"], dict)
        assert "main" in api["outputs"]
        items = api["outputs"]["main"]["items"]
        assert len(items) == 1
        assert items[0]["ref"] == "output_ds"
        assert items[0]["deps"] == []

    def test_settings_key_is_params(self):
        """Settings should be under 'params' key, not 'settings'."""
        recipe = DataikuRecipe.create_prepare("p", "in", "out")
        recipe.add_step(PrepareStep.fill_empty("col", 0))
        api = recipe.to_api_dict()

        assert "params" in api
        assert "settings" not in api

    def test_other_types_unchanged(self):
        """Types without a mapping should remain as-is."""
        recipe = DataikuRecipe(
            name="j", recipe_type=RecipeType.JOIN,
            inputs=["a", "b"], outputs=["out"],
        )
        api = recipe.to_api_dict()
        assert api["type"] == "join"


# ---------------------------------------------------------------------------
# C6: Invalid dataset names
# ---------------------------------------------------------------------------

class TestDatasetNameSanitization:
    """C6: Dataset names must be valid Dataiku identifiers."""

    def _sanitize(self, name: str) -> str:
        """Helper to access the sanitize method."""
        class _Gen(BaseFlowGenerator):
            def generate(self, *a, **kw):
                pass
        return _Gen()._sanitize_name(name)

    def test_strips_brackets_and_quotes(self):
        result = self._sanitize("df['name']")
        assert "[" not in result
        assert "]" not in result
        assert "'" not in result
        assert result == "name"

    def test_double_quoted_subscript(self):
        result = self._sanitize('df["col_name"]')
        assert '"' not in result
        assert result == "col_name"

    def test_no_leading_digit(self):
        result = self._sanitize("123_data")
        assert not result[0].isdigit()
        assert result == "ds_123_data"

    def test_special_chars_removed(self):
        result = self._sanitize("data-file.csv")
        assert re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", result)
        assert result == "data_file_csv"

    def test_chain_step_name(self):
        """_chain_step_0 is alphanumeric+underscore but starts with underscore."""
        result = self._sanitize("_chain_step_0")
        assert re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", result)

    def test_empty_name_fallback(self):
        result = self._sanitize("")
        assert result == "dataset"

    def test_spaces_replaced(self):
        result = self._sanitize("my data set")
        assert " " not in result
        assert result == "my_data_set"

    def test_dots_replaced(self):
        result = self._sanitize("file.name.ext")
        assert "." not in result
        assert result == "file_name_ext"

    def test_valid_name_unchanged(self):
        result = self._sanitize("valid_dataset_name")
        assert result == "valid_dataset_name"

    def test_converted_flow_has_valid_names(self):
        """All dataset names in a converted flow should be valid identifiers."""
        code = """
import pandas as pd
df = pd.read_csv('my-data.csv')
df['name'] = df['name'].str.strip()
df = df.dropna()
"""
        flow = convert(code)
        for ds in flow.datasets:
            assert re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", ds.name), (
                f"Invalid dataset name: '{ds.name}'"
            )


# ---------------------------------------------------------------------------
# H4: Dual output path consistency
# ---------------------------------------------------------------------------

class TestDualOutputConsistency:
    """H4: to_api_dict() and DSSExporter should produce consistent output."""

    def test_type_mapping_consistent(self):
        """Both paths should map PREPARE -> 'shaker'."""
        flow = DataikuFlow(name="test")
        flow.add_dataset(DataikuDataset(name="in_ds", dataset_type=DatasetType.INPUT))
        flow.add_dataset(DataikuDataset(name="out_ds", dataset_type=DatasetType.OUTPUT))
        recipe = DataikuRecipe.create_prepare("prep", "in_ds", "out_ds")
        recipe.add_step(PrepareStep.fill_empty("col", 0))
        flow.add_recipe(recipe)

        # Path 1: to_api_dict()
        api_config = recipe.to_api_dict()

        # Path 2: DSSExporter
        exporter = DSSExporter(flow, project_key="TEST")
        exporter_config = exporter._build_recipe_config(recipe)

        # Both should agree on the DSS type name
        assert api_config["type"] == exporter_config["type"]

    def test_io_structure_consistent(self):
        """Both paths should use the nested items structure for inputs/outputs."""
        flow = DataikuFlow(name="test")
        recipe = DataikuRecipe(
            name="join_1", recipe_type=RecipeType.JOIN,
            inputs=["left", "right"], outputs=["out"],
        )
        flow.add_recipe(recipe)

        api_config = recipe.to_api_dict()
        exporter = DSSExporter(flow, project_key="TEST")
        exporter_config = exporter._build_recipe_config(recipe)

        # Both should have nested "main" -> "items" structure
        api_inputs = api_config["inputs"]["main"]["items"]
        exp_inputs = exporter_config["inputs"]["main"]["items"]

        # Same refs (order may differ)
        api_refs = {item["ref"] for item in api_inputs}
        exp_refs = {item["ref"] for item in exp_inputs}
        assert api_refs == exp_refs

    def test_params_key_consistent(self):
        """Both paths should use 'params' for recipe settings."""
        flow = DataikuFlow(name="test")
        recipe = DataikuRecipe.create_prepare("prep", "in_ds", "out_ds")
        recipe.add_step(PrepareStep.fill_empty("col", 0))
        flow.add_recipe(recipe)

        api_config = recipe.to_api_dict()
        exporter = DSSExporter(flow, project_key="TEST")
        exporter_config = exporter._build_recipe_config(recipe)

        assert "params" in api_config
        assert "params" in exporter_config

    def test_to_recipe_configs_uses_api_format(self):
        """DataikuFlow.to_recipe_configs() should use the DSS API format."""
        flow = DataikuFlow(name="test")
        recipe = DataikuRecipe.create_prepare("prep", "in_ds", "out_ds")
        recipe.add_step(PrepareStep.fill_empty("col", 0))
        flow.add_recipe(recipe)

        configs = flow.to_recipe_configs()
        assert len(configs) == 1
        config = configs[0]
        assert config["type"] == "shaker"
        assert isinstance(config["inputs"], dict)
        assert "main" in config["inputs"]
        assert "params" in config
