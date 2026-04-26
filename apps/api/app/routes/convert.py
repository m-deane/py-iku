"""POST /convert — synchronous Python-to-Dataiku-flow conversion."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Request, Response
from fastapi.concurrency import run_in_threadpool

from ..schemas.convert import ConvertRequest, ConvertResponse
from ..services.conversion import convert_sync

router = APIRouter(tags=["convert"])

_SYNC_TIMEOUT_SECONDS = 30.0


@router.post(
    "/convert",
    response_model=ConvertResponse,
    summary="Convert Python code to a Dataiku flow (synchronous)",
    responses={
        400: {"description": "Invalid Python syntax"},
        413: {"description": "Code exceeds max_code_size_bytes"},
        422: {"description": "Validation error or conversion failure"},
        500: {"description": "Internal error or configuration problem"},
        502: {"description": "LLM provider error"},
    },
)
async def post_convert(
    request: Request,
    body: ConvertRequest,
    response: Response,
) -> ConvertResponse:
    """Convert Python code to a DataikuFlow.

    - **mode=rule** (default): AST-based, offline, fast.
    - **mode=llm**: LLM-assisted, requires `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`
      set in the server environment. Max 30-second wall-clock timeout.

    Errors in the py2dataiku hierarchy are mapped to RFC 7807 problem+json.
    """
    try:
        result = await asyncio.wait_for(
            run_in_threadpool(convert_sync, body),
            timeout=_SYNC_TIMEOUT_SECONDS,
        )
    except TimeoutError as exc:
        raise TimeoutError(
            f"Conversion did not complete within {_SYNC_TIMEOUT_SECONDS}s"
        ) from exc

    return result
