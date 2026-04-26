"""Export service — converts a ``DataikuFlow`` into a binary payload.

Used by ``apps/api/app/routes/export.py``.  Delegates JSON / YAML / ZIP to the
``FlowSink`` implementations in ``apps/api/app/sinks.py``; SVG is handled via
``flow.visualize(format="svg")``; PNG and PDF are rasterised through
``cairosvg`` (the same dependency py-iku already documents for these formats).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from py2dataiku.models.dataiku_flow import DataikuFlow

from ..schemas.export import ExportFormat
from ..sinks import JsonSink, SinkResult, YamlSink, ZipBundleSink

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class ExportNotSupportedError(RuntimeError):
    """Raised when the requested format requires unavailable system deps.

    The route maps this to ``HTTP 501 Not Implemented`` so callers can degrade
    gracefully instead of seeing an opaque 500.
    """

    def __init__(self, message: str, *, hint: str | None = None) -> None:
        super().__init__(message)
        self.hint = hint


# ---------------------------------------------------------------------------
# Result wrapper (the route doesn't need to care about which sink ran)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExportResult:
    """A ready-to-stream export payload."""

    content: bytes
    media_type: str
    filename: str


def _from_sink(result: SinkResult) -> ExportResult:
    return ExportResult(
        content=result.content,
        media_type=result.media_type,
        filename=result.filename,
    )


# ---------------------------------------------------------------------------
# Format-specific helpers
# ---------------------------------------------------------------------------


def _export_svg(flow: DataikuFlow, opts: dict[str, Any] | None) -> ExportResult:
    svg = flow.visualize(format="svg")
    if not isinstance(svg, str):  # defensive: visualize should always return str
        svg = str(svg)
    return ExportResult(
        content=svg.encode("utf-8"),
        media_type="image/svg+xml",
        filename=f"{flow.name}.svg",
    )


def _export_png(flow: DataikuFlow, opts: dict[str, Any] | None) -> ExportResult:
    try:
        import cairosvg  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover — env-specific
        raise ExportNotSupportedError(
            "PNG export requires the 'cairosvg' package",
            hint="pip install cairosvg",
        ) from exc

    scale = float((opts or {}).get("scale", 2.0))
    svg_text = flow.visualize(format="svg")
    png_bytes = cairosvg.svg2png(bytestring=svg_text.encode("utf-8"), scale=scale)
    return ExportResult(
        content=png_bytes,
        media_type="image/png",
        filename=f"{flow.name}.png",
    )


def _export_pdf(flow: DataikuFlow, opts: dict[str, Any] | None) -> ExportResult:
    try:
        import cairosvg  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover — env-specific
        raise ExportNotSupportedError(
            "PDF export requires the 'cairosvg' package",
            hint="pip install cairosvg",
        ) from exc

    svg_text = flow.visualize(format="svg")
    pdf_bytes = cairosvg.svg2pdf(bytestring=svg_text.encode("utf-8"))
    return ExportResult(
        content=pdf_bytes,
        media_type="application/pdf",
        filename=f"{flow.name}.pdf",
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def export_flow(
    flow: DataikuFlow,
    fmt: ExportFormat,
    opts: dict[str, Any] | None = None,
) -> ExportResult:
    """Render ``flow`` in the requested format and return the bytes."""
    if fmt is ExportFormat.JSON:
        return _from_sink(JsonSink().write(flow, opts))
    if fmt is ExportFormat.YAML:
        return _from_sink(YamlSink().write(flow, opts))
    if fmt is ExportFormat.ZIP:
        return _from_sink(ZipBundleSink().write(flow, opts))
    if fmt is ExportFormat.SVG:
        return _export_svg(flow, opts)
    if fmt is ExportFormat.PNG:
        return _export_png(flow, opts)
    if fmt is ExportFormat.PDF:
        return _export_pdf(flow, opts)
    # ExportFormat is a closed enum, but mypy / runtime guard:
    raise ExportNotSupportedError(f"Unknown export format: {fmt!r}")
