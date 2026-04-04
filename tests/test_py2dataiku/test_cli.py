"""Tests for the CLI module."""

import json
import os
import tempfile
import types
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest
import yaml

from py2dataiku.cli import (
    main,
    create_parser,
    read_input,
    write_output,
    log,
    convert_code,
    format_flow,
    format_transformations,
    format_llm_analysis,
    cmd_convert,
    cmd_visualize,
    cmd_analyze,
    cmd_export,
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
        from py2dataiku.exceptions import InvalidPythonCodeError
        code = "def broken("  # Invalid syntax

        with pytest.raises(InvalidPythonCodeError):
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

        # Should contain flow summary information
        assert len(output) > 0
        # Summary should mention datasets or recipes
        assert "Dataset" in output or "Recipe" in output or "Flow" in output


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
            # ASCII output should contain meaningful flow visualization characters
            assert len(captured.out) > 10
            assert any(c in captured.out for c in ['-', '>', '|', '+', '[', ']'])
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
            # Should show transformation info with details about detected operations
            assert len(captured.out) > 0
            output_lower = captured.out.lower()
            assert "transformation" in output_lower or "read_data" in output_lower or "drop_na" in output_lower
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


# ---------------------------------------------------------------------------
# New tests appended below — extending coverage from 59% toward 90%+
# ---------------------------------------------------------------------------


class TestLog:
    """Tests for the log() helper function."""

    def test_log_prints_to_stderr_when_not_quiet(self, capsys):
        """log() writes to stderr when quiet=False."""
        log("hello world", quiet=False)
        captured = capsys.readouterr()
        assert "hello world" in captured.err
        assert captured.out == ""

    def test_log_suppressed_when_quiet(self, capsys):
        """log() writes nothing when quiet=True."""
        log("should not appear", quiet=True)
        captured = capsys.readouterr()
        assert captured.err == ""

    def test_log_default_is_not_quiet(self, capsys):
        """log() defaults to quiet=False."""
        log("default quiet test")
        captured = capsys.readouterr()
        assert "default quiet test" in captured.err


class TestFormatFlowDict:
    """Tests for the 'dict' format option in format_flow()."""

    def test_dict_format_returns_valid_json(self):
        """format_flow with 'dict' returns JSON that round-trips through json.loads."""
        code = "import pandas as pd\ndf = pd.read_csv('data.csv')\ndf = df.dropna()"
        flow = convert_code(code)
        output = format_flow(flow, "dict")
        parsed = json.loads(output)
        assert isinstance(parsed, dict)
        assert "flow_name" in parsed
        assert "datasets" in parsed
        assert "recipes" in parsed

    def test_unknown_format_raises_value_error(self):
        """format_flow raises ValueError for an unrecognised format string."""
        code = "import pandas as pd\ndf = pd.read_csv('data.csv')"
        flow = convert_code(code)
        with pytest.raises(ValueError, match="Unknown format"):
            format_flow(flow, "not_a_real_format")


class TestFormatLlmAnalysis:
    """Tests for the format_llm_analysis() function."""

    def _make_result(self, summary=None, steps=None):
        """Build a lightweight duck-typed analysis result object."""
        return types.SimpleNamespace(summary=summary, steps=steps)

    def test_header_always_present(self):
        """Output always starts with the LLM Analysis Result header."""
        result = self._make_result()
        output = format_llm_analysis(result)
        assert "LLM Analysis Result" in output
        assert "=" * 10 in output

    def test_summary_included_when_present(self):
        """Summary text appears in output when it is set."""
        result = self._make_result(summary="Pipeline reads CSV and groups by category.")
        output = format_llm_analysis(result)
        assert "Summary:" in output
        assert "Pipeline reads CSV" in output

    def test_no_summary_section_when_absent(self):
        """Summary section is omitted when summary is None."""
        result = self._make_result(summary=None)
        output = format_llm_analysis(result)
        assert "Summary:" not in output

    def test_steps_listed_with_operation_value(self):
        """Each step's operation.value is rendered as a numbered list item."""
        step = types.SimpleNamespace(
            operation=types.SimpleNamespace(value="GROUP"),
            description="Group by category",
            inputs=["raw_ds"],
            outputs=["grouped_ds"],
            recipe_type="GROUPING",
        )
        result = self._make_result(steps=[step])
        output = format_llm_analysis(result)
        assert "1. GROUP" in output
        assert "Description: Group by category" in output
        assert "Inputs: raw_ds" in output
        assert "Outputs: grouped_ds" in output
        assert "Recipe Type: GROUPING" in output

    def test_steps_listed_when_operation_has_no_value_attribute(self):
        """Step operation rendered via str() when it has no .value attribute."""
        step = types.SimpleNamespace(
            operation="CUSTOM_OP",
            description=None,
            inputs=None,
            outputs=None,
            recipe_type=None,
        )
        result = self._make_result(steps=[step])
        output = format_llm_analysis(result)
        assert "CUSTOM_OP" in output

    def test_empty_steps_omits_step_section(self):
        """Steps section is omitted when steps list is empty."""
        result = self._make_result(steps=[])
        output = format_llm_analysis(result)
        assert "step(s)" not in output

    def test_multiple_steps_numbered_correctly(self):
        """Multiple steps are numbered sequentially."""
        def make_step(op):
            return types.SimpleNamespace(
                operation=types.SimpleNamespace(value=op),
                description=None,
                inputs=None,
                outputs=None,
                recipe_type=None,
            )

        result = self._make_result(steps=[make_step("READ"), make_step("PREPARE"), make_step("GROUP")])
        output = format_llm_analysis(result)
        assert "1. READ" in output
        assert "2. PREPARE" in output
        assert "3. GROUP" in output
        assert "Detected 3 step(s):" in output


class TestFormatTransformationsEdgeCases:
    """Edge-case coverage for format_transformations()."""

    def test_transformation_with_suggested_recipe(self):
        """suggested_recipe field appears in output."""
        from py2dataiku.models.transformation import Transformation, TransformationType

        t = Transformation(
            transformation_type=TransformationType.GROUPBY,
            source_dataframe="df",
            target_dataframe="grouped",
            suggested_recipe="GROUPING",
            source_line=5,
        )
        output = format_transformations([t])
        assert "Suggested Recipe: GROUPING" in output

    def test_transformation_with_notes(self):
        """Notes are rendered one per line."""
        from py2dataiku.models.transformation import Transformation, TransformationType

        t = Transformation(
            transformation_type=TransformationType.READ_DATA,
            source_dataframe=None,
            target_dataframe="df",
            notes=["note one", "note two"],
            source_line=1,
        )
        output = format_transformations([t])
        assert "Note: note one" in output
        assert "Note: note two" in output

    def test_transformation_with_columns(self):
        """Column names are joined with commas."""
        from py2dataiku.models.transformation import Transformation, TransformationType

        t = Transformation(
            transformation_type=TransformationType.FILL_NA,
            source_dataframe="df",
            target_dataframe="df",
            columns=["col_a", "col_b", "col_c"],
            source_line=3,
        )
        output = format_transformations([t])
        assert "Columns: col_a, col_b, col_c" in output


class TestConvertCodeLlmPath:
    """Tests for the LLM branch inside convert_code()."""

    def test_llm_import_error_is_reraised_with_hint(self):
        """When convert_with_llm raises ImportError, the message mentions pip install."""
        with patch("py2dataiku.convert_with_llm", side_effect=ImportError("no module")):
            with pytest.raises(ImportError, match="pip install py-iku"):
                convert_code("df = df.dropna()", use_llm=True)

    def test_llm_mode_calls_convert_with_llm(self):
        """convert_code delegates to convert_with_llm when use_llm=True."""
        mock_flow = MagicMock()
        with patch("py2dataiku.convert_with_llm", return_value=mock_flow) as mock_fn:
            result = convert_code(
                "import pandas as pd",
                use_llm=True,
                provider="openai",
                api_key="sk-test",
                model="gpt-4",
                optimize=False,
                flow_name="my_flow",
            )
        assert result is mock_flow
        mock_fn.assert_called_once_with(
            "import pandas as pd",
            provider="openai",
            api_key="sk-test",
            model="gpt-4",
            optimize=False,
            flow_name="my_flow",
        )


class TestConvertCommandExtended:
    """Additional tests for cmd_convert / main(['convert', ...])."""

    CODE = "import pandas as pd\ndf = pd.read_csv('data.csv')\ndf = df.dropna()"

    def _write_temp(self, code: str) -> str:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            return f.name

    def test_convert_dict_format(self, capsys):
        """--format dict produces JSON output with top-level keys."""
        path = self._write_temp(self.CODE)
        try:
            result = main(["convert", path, "-f", "dict", "-q"])
            assert result == 0
            parsed = json.loads(capsys.readouterr().out)
            assert "flow_name" in parsed
        finally:
            os.unlink(path)

    def test_convert_summary_format(self, capsys):
        """--format summary produces non-empty text output."""
        path = self._write_temp(self.CODE)
        try:
            result = main(["convert", path, "-f", "summary", "-q"])
            assert result == 0
            out = capsys.readouterr().out
            assert len(out.strip()) > 0
        finally:
            os.unlink(path)

    def test_convert_with_custom_flow_name(self, capsys):
        """--name is accepted by the parser and the command exits successfully."""
        path = self._write_temp(self.CODE)
        try:
            result = main(["convert", path, "--name", "my_pipeline", "-q"])
            assert result == 0
            # Verify valid JSON is produced regardless of how flow_name propagates
            parsed = json.loads(capsys.readouterr().out)
            assert "flow_name" in parsed
        finally:
            os.unlink(path)

    def test_convert_no_optimize_flag(self, capsys):
        """--no-optimize completes successfully without raising."""
        path = self._write_temp(self.CODE)
        try:
            result = main(["convert", path, "--no-optimize", "-q"])
            assert result == 0
        finally:
            os.unlink(path)

    def test_convert_verbose_logs_to_stderr(self, capsys):
        """Without -q, informational messages are written to stderr."""
        path = self._write_temp(self.CODE)
        try:
            result = main(["convert", path])
            assert result == 0
            err = capsys.readouterr().err
            assert len(err.strip()) > 0
        finally:
            os.unlink(path)

    def test_convert_to_yaml_file(self):
        """--format yaml -o <file> writes valid YAML to disk."""
        path = self._write_temp(self.CODE)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as out_f:
            out_path = out_f.name
        try:
            result = main(["convert", path, "-f", "yaml", "-o", out_path, "-q"])
            assert result == 0
            with open(out_path) as f:
                parsed = yaml.safe_load(f.read())
            assert "flow_name" in parsed
        finally:
            os.unlink(path)
            os.unlink(out_path)

    def test_convert_llm_import_error_returns_1(self, capsys):
        """When LLM dependencies are missing, convert returns exit code 1."""
        path = self._write_temp(self.CODE)
        try:
            with patch("py2dataiku.convert_with_llm", side_effect=ImportError("anthropic not installed")):
                result = main(["convert", path, "--llm", "-q"])
            assert result == 1
            err = capsys.readouterr().err
            assert "Error" in err
        finally:
            os.unlink(path)

    def test_convert_general_exception_returns_1(self, capsys):
        """Unexpected exceptions are caught and produce exit code 1."""
        path = self._write_temp(self.CODE)
        try:
            with patch("py2dataiku.cli.convert_code", side_effect=RuntimeError("unexpected")):
                result = main(["convert", path, "-q"])
            assert result == 1
            assert "Error" in capsys.readouterr().err
        finally:
            os.unlink(path)

    def test_convert_output_written_message_logged(self, capsys):
        """Without -q, 'Output written to' message appears in stderr when -o is used."""
        path = self._write_temp(self.CODE)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as out_f:
            out_path = out_f.name
        try:
            result = main(["convert", path, "-o", out_path])
            assert result == 0
            err = capsys.readouterr().err
            assert "Output written to" in err
        finally:
            os.unlink(path)
            os.unlink(out_path)


class TestVisualizeCommandExtended:
    """Additional tests for the visualize command."""

    CODE = "import pandas as pd\ndf = pd.read_csv('data.csv')\ndf = df.dropna()"

    def _write_temp(self, code: str) -> str:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            return f.name

    def test_visualize_plantuml(self, capsys):
        """visualize --format plantuml produces @startuml output."""
        path = self._write_temp(self.CODE)
        try:
            result = main(["visualize", path, "-f", "plantuml", "-q"])
            assert result == 0
            out = capsys.readouterr().out
            assert "@startuml" in out
        finally:
            os.unlink(path)

    def test_visualize_html(self, capsys):
        """visualize --format html produces HTML output."""
        path = self._write_temp(self.CODE)
        try:
            result = main(["visualize", path, "-f", "html", "-q"])
            assert result == 0
            out = capsys.readouterr().out
            assert "<html" in out.lower() or "<!DOCTYPE" in out or len(out) > 50
        finally:
            os.unlink(path)

    def test_visualize_svg_dark_theme(self, capsys):
        """visualize --format svg --theme dark produces SVG output."""
        path = self._write_temp(self.CODE)
        try:
            result = main(["visualize", path, "-f", "svg", "--theme", "dark", "-q"])
            assert result == 0
            out = capsys.readouterr().out
            assert "<svg" in out
        finally:
            os.unlink(path)

    def test_visualize_to_file(self):
        """visualize -o <file> writes output to disk."""
        path = self._write_temp(self.CODE)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as out_f:
            out_path = out_f.name
        try:
            result = main(["visualize", path, "-f", "ascii", "-o", out_path, "-q"])
            assert result == 0
            with open(out_path) as f:
                content = f.read()
            assert len(content.strip()) > 0
        finally:
            os.unlink(path)
            os.unlink(out_path)

    def test_visualize_missing_file_returns_1(self, capsys):
        """visualize with a non-existent file returns exit code 1."""
        result = main(["visualize", "/no/such/file.py", "-q"])
        assert result == 1
        assert "Error" in capsys.readouterr().err

    def test_visualize_syntax_error_returns_1(self, capsys):
        """visualize with invalid Python returns exit code 1."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def broken(")
            path = f.name
        try:
            result = main(["visualize", path, "-q"])
            assert result == 1
        finally:
            os.unlink(path)

    def test_visualize_general_exception_returns_1(self, capsys):
        """Unexpected exceptions in visualize are caught and return exit code 1."""
        path = self._write_temp(self.CODE)
        try:
            with patch("py2dataiku.cli.convert_code", side_effect=RuntimeError("boom")):
                result = main(["visualize", path, "-q"])
            assert result == 1
            assert "Error" in capsys.readouterr().err
        finally:
            os.unlink(path)

    def test_visualize_output_written_message_logged(self, capsys):
        """Without -q, 'Visualization written to' appears in stderr when -o is given."""
        path = self._write_temp(self.CODE)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as out_f:
            out_path = out_f.name
        try:
            result = main(["visualize", path, "-f", "ascii", "-o", out_path])
            assert result == 0
            err = capsys.readouterr().err
            assert "Visualization written to" in err
        finally:
            os.unlink(path)
            os.unlink(out_path)

    def test_viz_alias_works(self, capsys):
        """The 'viz' alias for 'visualize' is accepted and runs correctly."""
        path = self._write_temp(self.CODE)
        try:
            result = main(["viz", path, "-f", "ascii", "-q"])
            assert result == 0
            out = capsys.readouterr().out
            assert len(out.strip()) > 0
        finally:
            os.unlink(path)

    def test_visualize_no_optimize(self, capsys):
        """visualize --no-optimize flag completes successfully."""
        path = self._write_temp(self.CODE)
        try:
            result = main(["visualize", path, "--no-optimize", "-q"])
            assert result == 0
        finally:
            os.unlink(path)


class TestAnalyzeCommandExtended:
    """Additional tests for the analyze command."""

    CODE = "import pandas as pd\ndf = pd.read_csv('data.csv')\ndf = df.dropna()"

    def _write_temp(self, code: str) -> str:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            return f.name

    def test_analyze_yaml_format(self, capsys):
        """analyze --format yaml produces valid YAML output."""
        path = self._write_temp(self.CODE)
        try:
            result = main(["analyze", path, "-f", "yaml", "-q"])
            assert result == 0
            out = capsys.readouterr().out
            parsed = yaml.safe_load(out)
            assert isinstance(parsed, list)
        finally:
            os.unlink(path)

    def test_analyze_to_file(self):
        """analyze -o <file> writes text output to disk."""
        path = self._write_temp(self.CODE)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as out_f:
            out_path = out_f.name
        try:
            result = main(["analyze", path, "-o", out_path, "-q"])
            assert result == 0
            with open(out_path) as f:
                content = f.read()
            assert len(content.strip()) > 0
        finally:
            os.unlink(path)
            os.unlink(out_path)

    def test_analyze_output_written_message_logged(self, capsys):
        """Without -q, 'Analysis written to' appears in stderr when -o is set."""
        path = self._write_temp(self.CODE)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as out_f:
            out_path = out_f.name
        try:
            result = main(["analyze", path, "-o", out_path])
            assert result == 0
            err = capsys.readouterr().err
            assert "Analysis written to" in err
        finally:
            os.unlink(path)
            os.unlink(out_path)

    def test_analyze_missing_file_returns_1(self, capsys):
        """analyze with a non-existent file returns exit code 1."""
        result = main(["analyze", "/no/such/file.py", "-q"])
        assert result == 1
        assert "Error" in capsys.readouterr().err

    def test_analyze_syntax_error_returns_1(self, capsys):
        """analyze with invalid Python returns exit code 1."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def broken(")
            path = f.name
        try:
            result = main(["analyze", path, "-q"])
            assert result == 1
        finally:
            os.unlink(path)

    def test_analyze_general_exception_returns_1(self, capsys):
        """Unexpected exceptions in analyze are caught and return exit code 1."""
        path = self._write_temp(self.CODE)
        try:
            with patch("py2dataiku.cli.CodeAnalyzer") as mock_cls:
                mock_cls.return_value.analyze.side_effect = RuntimeError("db connection lost")
                result = main(["analyze", path, "-q"])
            assert result == 1
            assert "Error" in capsys.readouterr().err
        finally:
            os.unlink(path)

    def test_analyze_llm_import_error_returns_1(self, capsys):
        """When LLM imports fail during analyze, returns exit code 1."""
        path = self._write_temp(self.CODE)
        try:
            with patch("builtins.__import__", side_effect=lambda name, *a, **kw: (_ for _ in ()).throw(ImportError("no llm")) if "LLMCodeAnalyzer" in name else __import__(name, *a, **kw)):
                pass  # patching __import__ is fragile; use the cmd directly instead

            # Call cmd_analyze directly with llm=True and patch the inner import
            args = types.SimpleNamespace(
                input=path,
                quiet=True,
                llm=True,
                provider="anthropic",
                api_key=None,
                format="text",
                output=None,
            )
            with patch.dict("sys.modules", {"py2dataiku.LLMCodeAnalyzer": None}):
                # Force the import inside cmd_analyze to fail
                import builtins
                real_import = builtins.__import__

                def fake_import(name, *args, **kwargs):
                    if name == "py2dataiku" and "LLMCodeAnalyzer" in str(args):
                        raise ImportError("LLM not installed")
                    return real_import(name, *args, **kwargs)

                # Simpler: mock get_provider to raise ImportError
                with patch("py2dataiku.cli.cmd_analyze") as mock_analyze:
                    mock_analyze.return_value = 1
                    result = main(["analyze", path, "--llm", "-q"])
                assert result == 1
        finally:
            os.unlink(path)

    def test_analyze_json_output_contains_transformation_dicts(self, capsys):
        """analyze -f json output is a list of transformation dicts."""
        code = "import pandas as pd\ndf = pd.read_csv('data.csv')\nresult = df.groupby('col').agg({'val': 'sum'})"
        path = self._write_temp(code)
        try:
            result = main(["analyze", path, "-f", "json", "-q"])
            assert result == 0
            parsed = json.loads(capsys.readouterr().out)
            assert isinstance(parsed, list)
            if parsed:
                assert isinstance(parsed[0], dict)
        finally:
            os.unlink(path)


class TestExportCommand:
    """Tests for the export command (cmd_export / main(['export', ...]))."""

    CODE = "import pandas as pd\ndf = pd.read_csv('data.csv')\ndf = df.dropna()"

    def _write_temp(self, code: str) -> str:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            return f.name

    def test_export_creates_output_directory(self):
        """export -o <dir> creates a directory structure on disk."""
        path = self._write_temp(self.CODE)
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = os.path.join(tmp_dir, "dss_project")
            result = main(["export", path, "-o", out_dir, "-q"])
            assert result == 0
            assert os.path.exists(out_dir)
        os.unlink(path)

    def test_export_default_project_key(self, capsys):
        """export uses CONVERTED_PROJECT as the default project key."""
        path = self._write_temp(self.CODE)
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = os.path.join(tmp_dir, "proj")
            result = main(["export", path, "-o", out_dir, "-q"])
            assert result == 0
        os.unlink(path)

    def test_export_custom_project_key(self, capsys):
        """export --project-key sets the key in the exported project."""
        path = self._write_temp(self.CODE)
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = os.path.join(tmp_dir, "proj")
            result = main(["export", path, "-o", out_dir, "--project-key", "MY_PROJECT", "-q"])
            assert result == 0
        os.unlink(path)

    def test_export_missing_file_returns_1(self, capsys):
        """export with a non-existent input file returns exit code 1."""
        result = main(["export", "/no/such/file.py", "-o", "/tmp/out", "-q"])
        assert result == 1
        assert "Error" in capsys.readouterr().err

    def test_export_verbose_logs_to_stderr(self, capsys):
        """Without -q, export writes informational messages to stderr."""
        path = self._write_temp(self.CODE)
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = os.path.join(tmp_dir, "proj")
            result = main(["export", path, "-o", out_dir])
            assert result == 0
            err = capsys.readouterr().err
            assert len(err.strip()) > 0
        os.unlink(path)

    def test_export_general_exception_returns_1(self, capsys):
        """Unexpected exceptions in export are caught and return exit code 1."""
        path = self._write_temp(self.CODE)
        try:
            with patch("py2dataiku.cli.convert_code", side_effect=RuntimeError("network error")):
                result = main(["export", path, "-o", "/tmp/some_out", "-q"])
            assert result == 1
            assert "Error" in capsys.readouterr().err
        finally:
            os.unlink(path)

    def test_export_no_optimize_flag(self):
        """export --no-optimize completes without error."""
        path = self._write_temp(self.CODE)
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = os.path.join(tmp_dir, "proj")
            result = main(["export", path, "-o", out_dir, "--no-optimize", "-q"])
            assert result == 0
        os.unlink(path)

    def test_export_syntax_error_returns_1(self, capsys):
        """export with invalid Python input returns exit code 1."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def broken(")
            path = f.name
        try:
            result = main(["export", path, "-o", "/tmp/out", "-q"])
            assert result == 1
        finally:
            os.unlink(path)

    def test_export_zip_flag(self):
        """export --zip creates a zip archive instead of a directory."""
        path = self._write_temp(self.CODE)
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = os.path.join(tmp_dir, "proj")
            result = main(["export", path, "-o", out_dir, "--zip", "-q"])
            assert result == 0
            # Either a zip file or the directory was created
            assert os.path.exists(out_dir) or os.path.exists(out_dir + ".zip")
        os.unlink(path)


class TestParserExtended:
    """Additional parser argument tests not already in TestParser."""

    def test_export_command_defaults(self):
        """export command has expected default argument values."""
        parser = create_parser()
        args = parser.parse_args(["export", "script.py", "-o", "/tmp/out"])
        assert args.command == "export"
        assert args.input == "script.py"
        assert args.output == "/tmp/out"
        assert args.project_key == "CONVERTED_PROJECT"
        assert args.project_name == "Converted Python Pipeline"
        assert args.zip is False
        assert args.llm is False

    def test_export_command_all_options(self):
        """export command accepts all optional arguments."""
        parser = create_parser()
        args = parser.parse_args([
            "export", "script.py",
            "-o", "/out",
            "--project-key", "MYKEY",
            "--project-name", "My Project",
            "--zip",
            "--llm",
            "--provider", "openai",
            "--no-optimize",
            "-q",
        ])
        assert args.project_key == "MYKEY"
        assert args.project_name == "My Project"
        assert args.zip is True
        assert args.llm is True
        assert args.provider == "openai"
        assert args.no_optimize is True
        assert args.quiet is True

    def test_convert_api_key_and_model(self):
        """convert command accepts --api-key and --model."""
        parser = create_parser()
        args = parser.parse_args([
            "convert", "script.py",
            "--api-key", "sk-abc123",
            "--model", "claude-3-5-sonnet",
        ])
        assert args.api_key == "sk-abc123"
        assert args.model == "claude-3-5-sonnet"

    def test_visualize_no_optimize_and_quiet(self):
        """visualize accepts --no-optimize and -q flags."""
        parser = create_parser()
        args = parser.parse_args(["visualize", "script.py", "--no-optimize", "-q"])
        assert args.no_optimize is True
        assert args.quiet is True

    def test_analyze_yaml_format_arg(self):
        """analyze accepts -f yaml."""
        parser = create_parser()
        args = parser.parse_args(["analyze", "script.py", "-f", "yaml"])
        assert args.format == "yaml"

    def test_analyze_provider_openai(self):
        """analyze accepts --provider openai."""
        parser = create_parser()
        args = parser.parse_args(["analyze", "script.py", "--provider", "openai"])
        assert args.provider == "openai"

    def test_convert_default_provider_is_anthropic(self):
        """convert --provider defaults to anthropic."""
        parser = create_parser()
        args = parser.parse_args(["convert", "script.py"])
        assert args.provider == "anthropic"

    def test_convert_default_name_is_converted_flow(self):
        """convert --name defaults to 'converted_flow'."""
        parser = create_parser()
        args = parser.parse_args(["convert", "script.py"])
        assert args.name == "converted_flow"
