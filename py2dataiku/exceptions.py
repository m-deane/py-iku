"""Custom exception hierarchy for py2dataiku."""


class Py2DataikuError(Exception):
    """Base exception for all py2dataiku errors."""


class ConversionError(Py2DataikuError):
    """Error during code-to-flow conversion."""


class ProviderError(Py2DataikuError):
    """Error communicating with an LLM provider."""


class LLMResponseParseError(ProviderError):
    """Error parsing the JSON response from an LLM provider."""


class InvalidPythonCodeError(ConversionError):
    """The provided Python code could not be parsed or analyzed."""


class ValidationError(Py2DataikuError):
    """Error during flow or recipe validation."""


class ExportError(Py2DataikuError):
    """Error during DSS project export."""


class ConfigurationError(Py2DataikuError):
    """Error in py2dataiku configuration."""
