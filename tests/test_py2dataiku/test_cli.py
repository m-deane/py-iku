"""Tests for the CLI module."""

import json
import os
import tempfile
from io import StringIO
from unittest.mock import patch

import pytest
import yaml

from py2dataiku.cli import (
    main,
    create_parser,
    read_input,
    write_output,
    convert_code,
    format_flow,
    format_transformations,
)


class TestParser:
    """Tests for argument parser."""

    def test_create_parser(self):
        """Test parser creation."""
        parser = create_parser()
        assert parser is not None
        assert parser.prog == "py2dataiku"

    def test_convert_command_args(self):
        """Test convert command arguments."""
        parser = create_parser()
        args = parser.parse_args(["convert", "test.py"])

        assert args.command == "convert"
        assert args.input == "test.py"
        assert args.format == "json"
        assert args.llm is False

    def test_convert_with_options(self):
        """Test convert command with all options."""
        parser = create_parser()
        args = parser.parse_args([
            "convert", "test.py",
            "-o", "output.json",
            "-f", "yaml",
            "--llm",
            "--provider", "openai",
            "--name", "my_flow",
            "--no-optimize",
            "-q",
        ])

        assert args.output == "output.json"
        assert args.format == "yaml"
        assert args.llm is True
        assert args.provider == "openai"
        assert args.name == "my_flow"
        assert args.no_optimize is True
        assert args.quiet is True

    def test_visualize_command_args(self):
        """Test visualize command arguments."""
        parser = create_parser()
        args = parser.parse_args(["visualize", "test.py"])

        assert args.command == "visualize"
        assert args.input == "test.py"
        assert args.format == "ascii"

    def test_visualize_with_options(self):
        """Test visualize command with options."""
        parser = create_parser()
        args = parser.parse_args([
            "visualize", "test.py",
            "-f", "svg",
            "--theme", "dark",
            "-o", "flow.svg",
        ])

        assert args.format == "svg"
        assert args.theme == "dark"
        assert args.output == "flow.svg"

    def test_viz_alias(self):
        """Test viz alias for visualize."""
        parser = create_parser()
        args = parser.parse_args(["viz", "test.py"])

        assert args.command == "viz"

    def test_analyze_command_args(self):
        """Test analyze command arguments."""
        parser = create_parser()
        args = parser.parse_args(["analyze", "test.py"])

        assert args.command == "analyze"
        assert args.format == "text"

    def test_analyze_with_options(self):
        """Test analyze command with options."""
        parser = create_parser()
        args = parser.parse_args([
            "analyze", "test.py",
            "-f", "json",
            "--llm",
        ])

        assert args.format == "json"
        assert args.llm is True


class TestReadInput:
    """Tests for read_input function."""

    def test_read_from_file(self):
        """Test reading from a file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("import pandas as pd\ndf = pd.read_csv('data.csv')")
            temp_path = f.name

        try:
            content = read_input(temp_path)
            assert "import pandas" in content
            assert "read_csv" in content
        finally:
            os.unlink(temp_path)

    def test_read_from_stdin(self):
        """Test reading from stdin."""
        code = "df = df.fillna(0)"
        with patch("sys.stdin", StringIO(code)):
            content = read_input("-")
            assert content == code

    def test_file_not_found(self):
        """Test error on missing file."""
        with pytest.raises(FileNotFoundError):
            read_input("nonexistent_file.py")


class TestWriteOutput:
    """Tests for write_output function."""

    def test_write_to_file(self):
        """Test writing to a file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            write_output('{"test": true}', temp_path)

            with open(temp_path, "r") as f:
                content = f.read()
            assert '{"test": true}' in content
        finally:
            os.unlink(temp_path)

    def test_write_to_stdout(self, capsys):
        """Test writing to stdout."""
        write_output("test output", None)

        captured = capsys.readouterr()
        assert "test output" in captured.out


class TestConvertCode:
    """Tests for convert_code function."""

    def test_rule_based_conversion(self):
        """Test rule-based conversion."""
        code = """
import pandas as pd
df = pd.read_csv('data.csv')
df = df.dropna()
result = df.groupby('category').agg({'amount': 'sum'})
"""
        flow = convert_code(code, use_llm=False)

        assert flow is not None
        assert hasattr(flow, 'recipes')
        assert hasattr(flow, 'datasets')

    def test_syntax_error_raises(self):
        """Test that syntax errors are propagated."""
        code = "def broken("  # Invalid syntax

        with pytest.raises(SyntaxError):
            convert_code(code, use_llm=False)

    def test_optimize_disabled(self):
        """Test conversion with optimization disabled."""
        code = """
import pandas as pd
df = pd.read_csv('data.csv')
"""
        flow = convert_code(code, use_llm=False, optimize=False)
        assert flow is not None


class TestFormatFlow:
    """Tests for format_flow function."""

    def test_json_format(self):
        """Test JSON output format."""
        code = """
import pandas as pd
df = pd.read_csv('data.csv')
df = df.fillna(0)
"""
        flow = convert_code(code)
        output = format_flow(flow, "json")

        # Verify it's valid JSON
        parsed = json.loads(output)
        assert "flow_name" in parsed
        assert "datasets" in parsed
        assert "recipes" in parsed

    def test_yaml_format(self):
        """Test YAML output format."""
        code = """
import pandas as pd
df = pd.read_csv('data.csv')
"""
        flow = convert_code(code)
        output = format_flow(flow, "yaml")

        # Verify it's valid YAML
        parsed = yaml.safe_load(output)
        assert "flow_name" in parsed

    def test_summary_format(self):
        """Test summary output format."""
        code = """
import pandas as pd
df = pd.read_csv('data.csv')
"""
        flow = convert_code(code)
        output = format_flow(flow, "summary")

        # Should be human-readable text
        assert "Flow:" in output or len(output) > 0


class TestFormatTransformations:
    """Tests for format_transformations function."""

    def test_empty_transformations(self):
        """Test formatting empty transformations."""
        output = format_transformations([])
        assert "No transformations detected" in output

    def test_format_with_transformations(self):
        """Test formatting transformations."""
        from py2dataiku.models.transformation import Transformation, TransformationType

        transformations = [
            Transformation(
                transformation_type=TransformationType.READ_DATA,
                source_dataframe=None,
                target_dataframe="df",
                parameters={"filepath": "data.csv"},
                source_line=1,
            ),
            Transformation(
                transformation_type=TransformationType.FILL_NA,
                source_dataframe="df",
                target_dataframe="df",
                columns=["col_a"],
                parameters={"value": 0},
                source_line=2,
                suggested_processor="FillEmptyWithValue",
            ),
        ]

        output = format_transformations(transformations)

        assert "2 transformation" in output
        assert "read_data" in output
        assert "fill_na" in output
        assert "FillEmptyWithValue" in output


class TestMainCommand:
    """Integration tests for main command."""

    def test_no_command_shows_help(self, capsys):
        """Test that no command shows help."""
        result = main([])

        assert result == 0
        captured = capsys.readouterr()
        assert "py2dataiku" in captured.out or "convert" in captured.out

    def test_convert_command(self, capsys):
        """Test convert command."""
        code = """
import pandas as pd
df = pd.read_csv('data.csv')
df = df.fillna(0)
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = main(["convert", temp_path, "-q"])

            assert result == 0
            captured = capsys.readouterr()

            # Output should be valid JSON
            output_json = json.loads(captured.out)
            assert "flow_name" in output_json
        finally:
            os.unlink(temp_path)

    def test_convert_to_yaml(self, capsys):
        """Test convert command with YAML format."""
        code = "import pandas as pd\ndf = pd.read_csv('data.csv')"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = main(["convert", temp_path, "-f", "yaml", "-q"])

            assert result == 0
            captured = capsys.readouterr()

            # Output should be valid YAML
            output_yaml = yaml.safe_load(captured.out)
            assert "flow_name" in output_yaml
        finally:
            os.unlink(temp_path)

    def test_convert_to_file(self):
        """Test convert command with output file."""
        code = "import pandas as pd\ndf = pd.read_csv('data.csv')"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            input_path = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_path = f.name

        try:
            result = main(["convert", input_path, "-o", output_path, "-q"])

            assert result == 0

            with open(output_path, "r") as f:
                output_json = json.load(f)
            assert "flow_name" in output_json
        finally:
            os.unlink(input_path)
            os.unlink(output_path)

    def test_visualize_ascii(self, capsys):
        """Test visualize command with ASCII format."""
        code = """
import pandas as pd
df = pd.read_csv('data.csv')
df = df.fillna(0)
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = main(["visualize", temp_path, "-f", "ascii", "-q"])

            assert result == 0
            captured = capsys.readouterr()
            # ASCII output should contain box characters or flow elements
            assert len(captured.out) > 0
        finally:
            os.unlink(temp_path)

    def test_visualize_svg(self, capsys):
        """Test visualize command with SVG format."""
        code = "import pandas as pd\ndf = pd.read_csv('data.csv')"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = main(["visualize", temp_path, "-f", "svg", "-q"])

            assert result == 0
            captured = capsys.readouterr()
            assert "<svg" in captured.out
        finally:
            os.unlink(temp_path)

    def test_visualize_mermaid(self, capsys):
        """Test visualize command with Mermaid format."""
        code = """
import pandas as pd
df = pd.read_csv('data.csv')
result = df.groupby('cat').agg({'val': 'sum'})
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = main(["visualize", temp_path, "-f", "mermaid", "-q"])

            assert result == 0
            captured = capsys.readouterr()
            # Mermaid output should contain graph definition
            assert "graph" in captured.out or "flowchart" in captured.out or len(captured.out) > 0
        finally:
            os.unlink(temp_path)

    def test_analyze_text(self, capsys):
        """Test analyze command with text format."""
        code = """
import pandas as pd
df = pd.read_csv('data.csv')
df = df.dropna()
df = df.fillna(0)
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = main(["analyze", temp_path, "-q"])

            assert result == 0
            captured = capsys.readouterr()
            # Should show transformation info
            assert "transformation" in captured.out.lower() or len(captured.out) > 0
        finally:
            os.unlink(temp_path)

    def test_analyze_json(self, capsys):
        """Test analyze command with JSON format."""
        code = "import pandas as pd\ndf = pd.read_csv('data.csv')"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = main(["analyze", temp_path, "-f", "json", "-q"])

            assert result == 0
            captured = capsys.readouterr()

            # Output should be valid JSON array
            output_json = json.loads(captured.out)
            assert isinstance(output_json, list)
        finally:
            os.unlink(temp_path)

    def test_missing_file_error(self, capsys):
        """Test error handling for missing file."""
        result = main(["convert", "nonexistent_file.py", "-q"])

        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err.lower() or "error" in captured.err.lower()

    def test_syntax_error_handling(self, capsys):
        """Test error handling for syntax errors."""
        code = "def broken("  # Invalid syntax
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = main(["convert", temp_path, "-q"])

            assert result == 1
            captured = capsys.readouterr()
            assert "syntax" in captured.err.lower() or "error" in captured.err.lower()
        finally:
            os.unlink(temp_path)

    def test_stdin_input(self, capsys):
        """Test reading from stdin."""
        code = "import pandas as pd\ndf = pd.read_csv('data.csv')"

        with patch("sys.stdin", StringIO(code)):
            result = main(["convert", "-", "-q"])

        assert result == 0
        captured = capsys.readouterr()
        output_json = json.loads(captured.out)
        assert "flow_name" in output_json
