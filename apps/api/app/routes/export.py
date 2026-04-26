"""POST /export/{format} — render a DataikuFlow as a binary download."""

from __future__ import annotations

import logging
from urllib.parse import quote

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from py2dataiku.exceptions import Py2DataikuError
from py2dataiku.models.dataiku_flow import DataikuFlow

from ..schemas.export import ExportFormat, ExportRequest
from ..services.export_service import (
    ExportNotSupportedError,
    export_flow,
)

router = APIRouter(prefix="/export", tags=["export"])

logger = logging.getLogger(__name__)


def _content_disposition(filename: str) -> str:
    """RFC 6266-ish header value (handles non-ASCII filenames safely)."""
    safe = quote(filename, safe="._-")
    return f'attachment; filename="{filename}"; filename*=UTF-8\'\'{safe}'


@router.post(
    "/{format}",
    summary="Export a DataikuFlow as a binary payload",
    response_class=Response,
    responses={
        200: {
            "description": "Binary export payload (zip / json / yaml / svg / png / pdf)",
            "content": {
                "application/zip": {},
                "application/json": {},
                "application/x-yaml": {},
                "image/svg+xml": {},
                "image/png": {},
                "application/pdf": {},
            },
        },
        422: {"description": "Invalid format or malformed flow body"},
        501: {"description": "Format not supported in this environment"},
    },
)
def post_export(format: ExportFormat, body: ExportRequest) -> Response:
    """Render the flow as ``format`` and stream it back as an attachment."""
    try:
        flow = DataikuFlow.from_dict(body.flow)
    except (Py2DataikuError, ValueError, KeyError, TypeError) as exc:
        # 422 — body parsed as JSON but doesn't conform to a DataikuFlow shape.
        raise HTTPException(
            status_code=422,
            detail=f"Malformed flow body: {exc}",
        ) from exc

    try:
        result = export_flow(flow, format, body.opts)
    except ExportNotSupportedError as exc:
        logger.warning("Export format unsupported: %s", exc)
        detail = str(exc)
        if exc.hint:
            detail = f"{detail} (hint: {exc.hint})"
        raise HTTPException(status_code=501, detail=detail) from exc

    headers = {"Content-Disposition": _content_disposition(result.filename)}
    return Response(
        content=result.content,
        media_type=result.media_type,
        headers=headers,
    )
