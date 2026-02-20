"""Tests for the custom exception hierarchy."""

import pytest

from py2dataiku.exceptions import (
    Py2DataikuError,
    ConversionError,
    ProviderError,
    LLMResponseParseError,
    InvalidPythonCodeError,
    ValidationError,
    ExportError,
    ConfigurationError,
)


class TestExceptionHierarchy:
    """Test that exception inheritance is correct."""

    def test_all_inherit_from_base(self):
        """All custom exceptions should inherit from Py2DataikuError."""
        for exc_cls in [
            ConversionError,
            ProviderError,
            LLMResponseParseError,
            InvalidPythonCodeError,
            ValidationError,
            ExportError,
            ConfigurationError,
        ]:
            assert issubclass(exc_cls, Py2DataikuError)

    def test_base_inherits_from_exception(self):
        assert issubclass(Py2DataikuError, Exception)

    def test_llm_response_parse_error_is_provider_error(self):
        assert issubclass(LLMResponseParseError, ProviderError)

    def test_invalid_python_code_error_is_conversion_error(self):
        assert issubclass(InvalidPythonCodeError, ConversionError)

    def test_can_raise_and_catch_base(self):
        with pytest.raises(Py2DataikuError):
            raise ConversionError("test")

    def test_can_raise_and_catch_provider(self):
        with pytest.raises(ProviderError):
            raise LLMResponseParseError("bad json")

    def test_exception_message_preserved(self):
        msg = "something went wrong"
        exc = Py2DataikuError(msg)
        assert str(exc) == msg

    def test_conversion_error_message(self):
        msg = "could not convert code"
        exc = ConversionError(msg)
        assert str(exc) == msg


class TestExceptionExports:
    """Test that exceptions are exported from the package."""

    def test_import_from_package(self):
        import py2dataiku
        assert hasattr(py2dataiku, "Py2DataikuError")
        assert hasattr(py2dataiku, "ConversionError")
        assert hasattr(py2dataiku, "ProviderError")
        assert hasattr(py2dataiku, "LLMResponseParseError")
        assert hasattr(py2dataiku, "InvalidPythonCodeError")
        assert hasattr(py2dataiku, "ValidationError")
        assert hasattr(py2dataiku, "ExportError")
        assert hasattr(py2dataiku, "ConfigurationError")

    def test_in_all(self):
        import py2dataiku
        for name in [
            "Py2DataikuError",
            "ConversionError",
            "ProviderError",
            "LLMResponseParseError",
            "InvalidPythonCodeError",
            "ValidationError",
            "ExportError",
            "ConfigurationError",
        ]:
            assert name in py2dataiku.__all__


class TestLLMAnalyzerExceptions:
    """Test that the LLM analyzer raises proper exceptions."""

    def test_json_parse_error_raises_llm_response_parse_error(self):
        """LLMCodeAnalyzer should raise LLMResponseParseError on bad JSON."""
        from unittest.mock import MagicMock
        from py2dataiku.llm.analyzer import LLMCodeAnalyzer
        import json

        mock_provider = MagicMock()
        mock_provider.complete_json.side_effect = json.JSONDecodeError("bad", "", 0)
        mock_provider.model_name = "test"

        analyzer = LLMCodeAnalyzer(provider=mock_provider)

        with pytest.raises(LLMResponseParseError):
            analyzer.analyze("x = 1")

    def test_api_errors_propagate(self):
        """API errors should not be swallowed."""
        from unittest.mock import MagicMock
        from py2dataiku.llm.analyzer import LLMCodeAnalyzer

        mock_provider = MagicMock()
        mock_provider.complete_json.side_effect = ConnectionError("network down")
        mock_provider.model_name = "test"

        analyzer = LLMCodeAnalyzer(provider=mock_provider)

        with pytest.raises(ConnectionError):
            analyzer.analyze("x = 1")

    def test_analyze_with_context_json_error(self):
        """analyze_with_context should also raise LLMResponseParseError."""
        from unittest.mock import MagicMock
        from py2dataiku.llm.analyzer import LLMCodeAnalyzer
        import json

        mock_provider = MagicMock()
        mock_provider.complete_json.side_effect = json.JSONDecodeError("bad", "", 0)
        mock_provider.model_name = "test"

        analyzer = LLMCodeAnalyzer(provider=mock_provider)

        with pytest.raises(LLMResponseParseError):
            analyzer.analyze_with_context("x = 1")


class TestDataStepFromDict:
    """Test DataStep.from_dict handles invalid operation types."""

    def test_invalid_operation_defaults_to_unknown(self):
        from py2dataiku.llm.schemas import DataStep, OperationType

        step = DataStep.from_dict({
            "step_number": 1,
            "operation": "not_a_real_operation",
            "description": "test",
        })
        assert step.operation == OperationType.UNKNOWN

    def test_missing_operation_defaults_to_unknown(self):
        from py2dataiku.llm.schemas import DataStep, OperationType

        step = DataStep.from_dict({
            "step_number": 1,
            "description": "test",
        })
        assert step.operation == OperationType.UNKNOWN

    def test_valid_operation_preserved(self):
        from py2dataiku.llm.schemas import DataStep, OperationType

        step = DataStep.from_dict({
            "step_number": 1,
            "operation": "filter",
            "description": "test",
        })
        assert step.operation == OperationType.FILTER
