"""RFC 7807 problem+json helpers — shared by HTTP handler and WS error path."""

from __future__ import annotations

from typing import Any

from py2dataiku.exceptions import (
    ConfigurationError,
    ConversionError,
    ExportError,
    InvalidPythonCodeError,
    LLMResponseParseError,
    ProviderError,
    Py2DataikuError,
    ValidationError,
)

# ---------------------------------------------------------------------------
# Status-code mapping for the Py2DataikuError hierarchy
# ---------------------------------------------------------------------------

_EXCEPTION_STATUS: list[tuple[type[Py2DataikuError], int]] = [
    # Most-specific first
    (InvalidPythonCodeError, 400),
    (LLMResponseParseError, 502),
    (ConversionError, 422),
    (ValidationError, 422),
    (ProviderError, 502),
    (ExportError, 500),
    (ConfigurationError, 500),
    (Py2DataikuError, 500),
]

_EXCEPTION_TITLE: dict[type[Py2DataikuError], str] = {
    InvalidPythonCodeError: "Invalid Python Code",
    LLMResponseParseError: "LLM Response Parse Error",
    ConversionError: "Conversion Error",
    ValidationError: "Validation Error",
    ProviderError: "LLM Provider Error",
    ExportError: "Export Error",
    ConfigurationError: "Configuration Error",
    Py2DataikuError: "Internal Server Error",
}


def status_for(exc: Py2DataikuError) -> int:
    """Return the HTTP status code for a Py2DataikuError subclass."""
    for exc_type, status in _EXCEPTION_STATUS:
        if isinstance(exc, exc_type):
            return status
    return 500


def title_for(exc: Py2DataikuError) -> str:
    """Return a human-readable title for a Py2DataikuError subclass."""
    for exc_type, title in _EXCEPTION_TITLE.items():
        if isinstance(exc, exc_type):
            return title
    return "Internal Server Error"


def problem_dict(
    exc: Py2DataikuError, instance: str = "", request_id: str | None = None
) -> dict[str, Any]:
    """Build an RFC 7807 problem+json dict from a Py2DataikuError.

    Args:
        exc: The exception to convert.
        instance: The request URI (or WS path) for the ``instance`` field.
        request_id: Optional request-id to include.

    Returns:
        A dict suitable for JSON serialisation.
    """
    body: dict[str, Any] = {
        "type": f"https://py-iku.dev/errors/{type(exc).__name__}",
        "title": title_for(exc),
        "status": status_for(exc),
        "detail": str(exc),
        "instance": instance,
    }
    if request_id:
        body["request_id"] = request_id
    return body
