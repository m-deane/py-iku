"""POST /convert (sync) and WS /convert/stream (streaming)."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
from pydantic import ValidationError

from ..deps import get_audit_repo, get_cost_meter, get_llm_audit_repo
from ..schemas.convert import ConvertMode, ConvertRequest, ConvertResponse
from ..services.conversion import convert_streaming, convert_sync
from ..services.cost_meter import CostMeter
from ..services.llm_audit import LlmAuditRepo, LlmCallRecord, estimate_cost_usd
from ..services.streaming import ConversionEventEmitter
from ..store import AuditEvent, AuditRepo

router = APIRouter(tags=["convert"])

logger = logging.getLogger(__name__)

_SYNC_TIMEOUT_SECONDS = 30.0
_HEARTBEAT_SECONDS = 15.0
_WS_SUBPROTOCOL = "py-iku-studio.v1"


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
    audit: AuditRepo = Depends(get_audit_repo),
    llm_audit: LlmAuditRepo = Depends(get_llm_audit_repo),
    meter: CostMeter = Depends(get_cost_meter),
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
        raise HTTPException(
            status_code=504,
            detail=f"Conversion did not complete within {_SYNC_TIMEOUT_SECONDS}s",
        ) from exc

    # Audit hook — log every successful conversion.
    actor = request.headers.get("X-Actor") or (
        request.client.host if request.client else "anonymous"
    )
    audit.append(
        AuditEvent(
            actor=actor,
            action="convert.completed",
            resource_type="conversion",
            resource_id=getattr(request.state, "request_id", "-"),
            details={
                "mode": body.mode.value,
                "code_size_bytes": len(body.code.encode()),
                "recipe_count": result.score.recipe_count,
                "warnings": len(result.warnings),
            },
        )
    )

    # Record LLM-mode conversions in the prompt-history log so the /llm-history
    # surface shows convert-time spend alongside chat-time spend. Rule mode is
    # also logged (with zero cost) so users can audit the full session.
    provider = (
        body.options.provider if (body.options and body.options.provider) else "rule"
    )
    model = body.options.model if (body.options and body.options.model) else (
        "rule-engine" if body.mode == ConvertMode.RULE else "(default)"
    )
    # Without provider-side token counts on the convert path we record zeros;
    # the chat surface and any future native-streaming path populate real
    # numbers when available.
    llm_audit.append(
        LlmCallRecord(
            ts=datetime.now(tz=UTC).isoformat(),
            mode=body.mode.value,
            provider=provider,
            model=model,
            prompt_tokens=0,
            completion_tokens=0,
            cost_usd=estimate_cost_usd(model, 0, 0) if body.mode == ConvertMode.LLM else 0.0,
            status="success",
            feature="convert",
            request_id=getattr(request.state, "request_id", None),
            extra={"recipe_count": result.score.recipe_count},
        )
    )
    return result


@router.websocket("/convert/stream")
async def ws_convert_stream(websocket: WebSocket) -> None:
    """WebSocket endpoint for streaming conversion progress events.

    Protocol:
        1. Client connects (optionally with ``Sec-WebSocket-Protocol: py-iku-studio.v1``).
        2. Client sends first text frame containing a JSON-encoded ``ConvertRequest``.
        3. Server streams ``WSEvent`` JSON frames until ``completed``/``error``/``cancelled``.
        4. Client may send ``{"action":"cancel"}`` at any time to cancel the conversion.
        5. Server closes with code 1000 on normal completion.
        6. Keepalive ``ping`` events are sent every 15 seconds during idle periods.

    Limits:
        - Max one concurrent conversion per connection.
        - Code payload subject to ``ConvertOptions.max_code_size_bytes`` (default 256 KB).
    """
    # Negotiate subprotocol
    requested = websocket.headers.get("sec-websocket-protocol", "")
    if _WS_SUBPROTOCOL in [p.strip() for p in requested.split(",")]:
        await websocket.accept(subprotocol=_WS_SUBPROTOCOL)
    else:
        if requested:
            logger.warning(
                "WS client requested unknown subprotocol %r; accepting without subprotocol",
                requested,
            )
        await websocket.accept()

    # Receive and validate first frame
    try:
        raw = await websocket.receive_text()
    except WebSocketDisconnect:
        return

    try:
        req = ConvertRequest.model_validate_json(raw)
    except (ValidationError, ValueError) as exc:
        import json
        problem = {
            "type": "https://py-iku.dev/errors/ValidationError",
            "title": "Validation Error",
            "status": 422,
            "detail": str(exc),
            "instance": "/convert/stream",
        }
        await websocket.send_text(json.dumps(problem))
        await websocket.close(code=1003)
        return

    # --- Run conversion in a worker thread, forward events to client ---
    emitter = ConversionEventEmitter()

    conversion_task: asyncio.Task[None] = asyncio.create_task(
        asyncio.to_thread(convert_streaming, req, emitter)
    )

    async def _forward_events() -> None:
        """Pull events from the emitter and send them to the client."""
        async for event in emitter.stream():
            try:
                await websocket.send_text(event.model_dump_json())
            except (WebSocketDisconnect, RuntimeError):
                conversion_task.cancel()
                return

    async def _listen_for_cancel() -> None:
        """Wait for a cancel message from the client."""
        while True:
            try:
                msg = await websocket.receive_text()
            except (WebSocketDisconnect, RuntimeError):
                conversion_task.cancel()
                return
            try:
                import json
                data = json.loads(msg)
                if isinstance(data, dict) and data.get("action") == "cancel":
                    conversion_task.cancel()
                    emitter.cancelled()
                    return
            except (ValueError, KeyError):
                pass  # Ignore non-cancel messages

    async def _heartbeat() -> None:
        """Send periodic ping events to keep the connection alive."""
        while not conversion_task.done():
            await asyncio.sleep(_HEARTBEAT_SECONDS)
            if not conversion_task.done():
                emitter.ping()

    forward_task = asyncio.create_task(_forward_events())
    listen_task = asyncio.create_task(_listen_for_cancel())
    heartbeat_task = asyncio.create_task(_heartbeat())

    try:
        # Wait for the forward task (which ends when emitter reaches terminal event)
        await forward_task
    except asyncio.CancelledError:
        pass
    finally:
        conversion_task.cancel()
        listen_task.cancel()
        heartbeat_task.cancel()
        # Suppress cancellation exceptions from cleanup
        for t in (conversion_task, listen_task, heartbeat_task):
            try:
                await t
            except (asyncio.CancelledError, Exception):
                pass

    try:
        await websocket.close(code=1000)
    except (WebSocketDisconnect, RuntimeError):
        pass
