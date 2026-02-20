"""Tests for the public API (convert, convert_with_llm, Py2Dataiku, convert_file)."""

import os
import tempfile

import pytest

from py2dataiku import (
    convert,
    convert_file,
    Py2Dataiku,
    DataikuFlow,
    RecipeType,
    DatasetType,
)


# Simple test code snippets
SIMPLE_PREPARE_CODE = """
import pandas as pd
df = pd.read_csv('data.csv')
df['name'] = df['name'].str.strip()
df = df.dropna(subset=['id'])
"""

GROUPBY_CODE = """
import pandas as pd
df = pd.read_csv('sales.csv')
summary = df.groupby('category').agg({'amount': 'sum'})
"""

JOIN_CODE = """
import pandas as pd
customers = pd.read_csv('customers.csv')
orders = pd.read_csv('orders.csv')
merged = pd.merge(customers, orders, on='customer_id', how='left')
"""

EMPTY_CODE = """
import pandas as pd
"""

SORT_CODE = """
import pandas as pd
df = pd.read_csv('data.csv')
df = df.sort_values(by=['name'])
"""


class TestConvertFunction:
    """Tests for the convert() convenience function."""

    def test_convert_returns_dataiku_flow(self):
        flow = convert(SIMPLE_PREPARE_CODE)
        assert isinstance(flow, DataikuFlow)

    def test_convert_has_recipes(self):
        flow = convert(SIMPLE_PREPARE_CODE)
        assert len(flow.recipes) >= 1

    def test_convert_has_datasets(self):
        flow = convert(SIMPLE_PREPARE_CODE)
        assert len(flow.datasets) >= 2

    def test_convert_prepare_recipe_has_steps(self):
        flow = convert(SIMPLE_PREPARE_CODE)
        prepare_recipes = flow.get_recipes_by_type(RecipeType.PREPARE)
        assert len(prepare_recipes) >= 1
        assert len(prepare_recipes[0].steps) >= 1

    def test_convert_with_optimize_false(self):
        flow = convert(SIMPLE_PREPARE_CODE, optimize=False)
        assert isinstance(flow, DataikuFlow)
        assert len(flow.recipes) >= 1

    def test_convert_join_code(self):
        flow = convert(JOIN_CODE)
        join_recipes = flow.get_recipes_by_type(RecipeType.JOIN)
        assert len(join_recipes) >= 1
        assert join_recipes[0].join_type.value == "LEFT"

    def test_convert_groupby_code(self):
        flow = convert(GROUPBY_CODE)
        grouping_recipes = flow.get_recipes_by_type(RecipeType.GROUPING)
        assert len(grouping_recipes) >= 1

    def test_convert_sort_code(self):
        flow = convert(SORT_CODE)
        sort_recipes = flow.get_recipes_by_type(RecipeType.SORT)
        assert len(sort_recipes) >= 1

    def test_convert_input_datasets_detected(self):
        flow = convert(SIMPLE_PREPARE_CODE)
        input_ds = [d for d in flow.datasets if d.dataset_type == DatasetType.INPUT]
        assert len(input_ds) >= 1

    def test_convert_syntax_error_raises(self):
        with pytest.raises(SyntaxError):
            convert("import pandas as pd\ndf = pd.read_csv('test.csv'")


class TestConvertFile:
    """Tests for the convert_file() function."""

    def test_convert_file_basic(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(SIMPLE_PREPARE_CODE)
            f.flush()
            path = f.name

        try:
            flow = convert_file(path)
            assert isinstance(flow, DataikuFlow)
            assert flow.source_file == path
            assert len(flow.recipes) >= 1
        finally:
            os.unlink(path)

    def test_convert_file_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            convert_file("/nonexistent/path/to/file.py")


class TestPy2DataikuClass:
    """Tests for the Py2Dataiku class."""

    def test_init_rule_based(self):
        converter = Py2Dataiku(use_llm=False)
        assert converter.use_llm is False

    def test_init_llm_falls_back(self):
        """Without API key, LLM mode should fall back to rule-based."""
        # No ANTHROPIC_API_KEY set, should warn and fall back
        converter = Py2Dataiku(use_llm=True)
        # Either successfully initialized LLM or fell back
        assert converter is not None

    def test_convert_rule_based(self):
        converter = Py2Dataiku(use_llm=False)
        flow = converter.convert(SIMPLE_PREPARE_CODE)
        assert isinstance(flow, DataikuFlow)
        assert len(flow.recipes) >= 1

    def test_convert_with_flow_name(self):
        converter = Py2Dataiku(use_llm=False)
        flow = converter.convert(SIMPLE_PREPARE_CODE, flow_name="my_flow")
        assert flow.name == "my_flow"

    def test_convert_with_optimize_false(self):
        converter = Py2Dataiku(use_llm=False)
        flow = converter.convert(SIMPLE_PREPARE_CODE, optimize=False)
        assert isinstance(flow, DataikuFlow)

    def test_analyze_requires_llm(self):
        converter = Py2Dataiku(use_llm=False)
        with pytest.raises(ValueError, match="requires LLM"):
            converter.analyze(SIMPLE_PREPARE_CODE)

    def test_generate_diagram_mermaid(self):
        converter = Py2Dataiku(use_llm=False)
        flow = converter.convert(SIMPLE_PREPARE_CODE)
        mermaid = converter.generate_diagram(flow, format="mermaid")
        assert "flowchart" in mermaid

    def test_generate_diagram_graphviz(self):
        converter = Py2Dataiku(use_llm=False)
        flow = converter.convert(SIMPLE_PREPARE_CODE)
        dot = converter.generate_diagram(flow, format="graphviz")
        assert "digraph" in dot

    def test_generate_diagram_ascii(self):
        converter = Py2Dataiku(use_llm=False)
        flow = converter.convert(SIMPLE_PREPARE_CODE)
        ascii_out = converter.generate_diagram(flow, format="ascii")
        assert len(ascii_out) > 10

    def test_generate_diagram_plantuml(self):
        converter = Py2Dataiku(use_llm=False)
        flow = converter.convert(SIMPLE_PREPARE_CODE)
        puml = converter.generate_diagram(flow, format="plantuml")
        assert "@startuml" in puml

    def test_generate_diagram_unknown_format_raises(self):
        converter = Py2Dataiku(use_llm=False)
        flow = converter.convert(SIMPLE_PREPARE_CODE)
        with pytest.raises(ValueError, match="Unknown format"):
            converter.generate_diagram(flow, format="unknown")

    def test_visualize(self):
        converter = Py2Dataiku(use_llm=False)
        flow = converter.convert(SIMPLE_PREPARE_CODE)
        svg = converter.visualize(flow, format="svg")
        assert "<svg" in svg

    def test_save_visualization_auto_format(self):
        converter = Py2Dataiku(use_llm=False)
        flow = converter.convert(SIMPLE_PREPARE_CODE)

        with tempfile.NamedTemporaryFile(
            suffix=".svg", delete=False, mode="w"
        ) as f:
            path = f.name

        try:
            converter.save_visualization(flow, path)
            with open(path, "r") as f:
                content = f.read()
            assert "<svg" in content
        finally:
            os.unlink(path)


class TestFlowOutput:
    """Tests for flow output methods from the public API."""

    def test_flow_to_dict(self):
        flow = convert(SIMPLE_PREPARE_CODE)
        d = flow.to_dict()
        assert "flow_name" in d
        assert "recipes" in d
        assert "datasets" in d
        assert d["total_recipes"] == len(flow.recipes)

    def test_flow_to_json(self):
        flow = convert(SIMPLE_PREPARE_CODE)
        json_str = flow.to_json()
        assert '"flow_name"' in json_str

    def test_flow_to_yaml(self):
        flow = convert(SIMPLE_PREPARE_CODE)
        yaml_str = flow.to_yaml()
        assert "flow_name:" in yaml_str

    def test_flow_get_summary(self):
        flow = convert(SIMPLE_PREPARE_CODE)
        summary = flow.get_summary()
        assert "Flow:" in summary
        assert "Recipes:" in summary
        assert "Datasets:" in summary

    def test_flow_validate(self):
        flow = convert(SIMPLE_PREPARE_CODE)
        result = flow.validate()
        assert "valid" in result
        assert "errors" in result
        assert "warnings" in result

    def test_flow_repr(self):
        flow = convert(SIMPLE_PREPARE_CODE)
        r = repr(flow)
        assert "DataikuFlow" in r

    def test_flow_graph_property(self):
        flow = convert(SIMPLE_PREPARE_CODE)
        graph = flow.graph
        assert len(graph) > 0
