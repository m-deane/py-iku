"""Export service — converts a ``DataikuFlow`` into a binary payload.

Used by ``apps/api/app/routes/export.py``.  Delegates JSON / YAML / ZIP to the
``FlowSink`` implementations in ``apps/api/app/sinks.py``; SVG is handled via
``flow.visualize(format="svg")``; PNG is rendered through py-iku's matplotlib
visualizer (``flow.visualize(format="png")``); PDF wraps the SVG in a minimal
HTML shell and uses WeasyPrint to produce the final PDF.

Both PNG (matplotlib) and PDF (WeasyPrint) are listed in ``apps/api/pyproject.toml``
dependencies — the previous cairosvg path was removed because cairosvg is not in
the supported dependency set.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from py2dataiku.models.dataiku_flow import DataikuFlow

from ..schemas.export import ExportFormat
from ..sinks import JsonSink, SinkResult, YamlSink, ZipBundleSink

logger = logging.getLogger(__name__)

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
    """Render the flow as a PNG via py-iku's matplotlib visualizer.

    The matplotlib visualizer accepts ``dpi`` to control output resolution.
    Callers can pass ``{"scale": 2.0}`` (back-compat with the old cairosvg
    contract) or ``{"dpi": 150}`` directly; we map ``scale`` to ``dpi``
    so existing frontends keep working.
    """
    options = opts or {}
    if "dpi" in options:
        dpi = int(options["dpi"])
    else:
        # Back-compat: scale=2.0 → dpi=200, scale=1.0 → dpi=100
        scale = float(options.get("scale", 1.5))
        dpi = max(72, int(scale * 100))

    try:
        png_bytes = flow.visualize(format="png", dpi=dpi)
    except ImportError as exc:
        # matplotlib missing — surface a clean 501 instead of a 500.
        raise ExportNotSupportedError(
            "PNG export requires the 'matplotlib' package",
            hint="pip install matplotlib",
        ) from exc
    except Exception as exc:  # pragma: no cover — defensive
        logger.exception("PNG render failed: %s", exc)
        raise

    if not isinstance(png_bytes, bytes):  # defensive
        raise RuntimeError("matplotlib visualizer did not return bytes")

    return ExportResult(
        content=png_bytes,
        media_type="image/png",
        filename=f"{flow.name}.png",
    )


# Minimal HTML shell wrapping the SVG so WeasyPrint can size the page to the
# diagram. Setting a page-margin of zero keeps the diagram edge-to-edge; we
# expose a generous default page size so wide flows do not get clipped.
_PDF_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<style>
  @page {{ size: {page_size}; margin: {margin}; }}
  html, body {{ margin: 0; padding: 0; }}
  body {{ font-family: sans-serif; }}
  svg {{ display: block; max-width: 100%; height: auto; }}
</style>
</head>
<body>{svg}</body>
</html>"""


def _export_pdf(flow: DataikuFlow, opts: dict[str, Any] | None) -> ExportResult:
    """Render the flow as a PDF by wrapping its SVG in HTML and using WeasyPrint.

    ``opts`` may include:
      - ``page_size`` (CSS @page value, default ``"A4 landscape"``)
      - ``margin`` (CSS @page margin, default ``"0.5in"``)
    """
    try:
        import weasyprint  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover — env-specific
        raise ExportNotSupportedError(
            "PDF export requires the 'weasyprint' package",
            hint="pip install weasyprint",
        ) from exc

    options = opts or {}
    page_size = str(options.get("page_size", "A4 landscape"))
    margin = str(options.get("margin", "0.5in"))

    svg_text = flow.visualize(format="svg")
    if not isinstance(svg_text, str):  # defensive
        svg_text = str(svg_text)

    html = _PDF_HTML_TEMPLATE.format(
        page_size=page_size,
        margin=margin,
        svg=svg_text,
    )

    try:
        pdf_bytes = weasyprint.HTML(string=html).write_pdf()
    except Exception as exc:  # pragma: no cover — env/font-specific
        logger.exception("WeasyPrint PDF render failed: %s", exc)
        raise ExportNotSupportedError(
            "PDF render failed inside WeasyPrint",
            hint="check server logs; commonly caused by missing system fonts",
        ) from exc

    if not pdf_bytes:
        raise RuntimeError("WeasyPrint produced empty PDF bytes")

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
