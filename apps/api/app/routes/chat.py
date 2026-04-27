"""POST /chat — chat-with-flow endpoint.

Two response shapes are supported:

* JSON when the request body has ``stream: false`` (default).
* ``text/event-stream`` SSE when ``stream: true``. SSE events:
    - ``meta``   — `{model, provider}` emitted first.
    - ``delta``  — `{text}` repeated for each chunk.
    - ``final``  — full ``ChatResponse`` payload (citations + usage + cost).
    - ``error``  — `{title, detail}` if an exception is raised mid-stream.

Every successful answer is recorded by ``LlmAuditRepo`` and counts toward
the ``CostMeter`` budget. Pre-call budget enforcement runs before we hit the
LLM — over-budget calls return HTTP 402 with the projected cost in the body
so the frontend can pop a confirmation modal.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from py2dataiku.exceptions import ConfigurationError, Py2DataikuError

from ..deps import get_cost_meter, get_llm_audit_repo
from ..schemas.chat import ChatRequest, ChatResponse
from ..services import chat as chat_service
from ..services.chat import (
    answer_chat,
    build_prompts,
    stream_chat_chunks,
    stream_chat_provider,
)
from ..services.cost_meter import CostMeter
from ..services.llm_audit import LlmAuditRepo, LlmCallRecord, estimate_cost_usd

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


# Rough projection used for the *pre-call* budget check. We don't know the
# response size yet so we estimate output tokens from a fixed small ceiling
# (chat answers in this surface are tightly capped). The real cost is logged
# afterwards — this projection only gates obvious budget-busters before we
# spend any real tokens.
_PROJECTED_INPUT_TOKENS = 6_000
_PROJECTED_OUTPUT_TOKENS = 800


def _project_call_cost(model: str | None) -> float:
    return estimate_cost_usd(
        model or "claude-3-5-sonnet-latest",
        _PROJECTED_INPUT_TOKENS,
        _PROJECTED_OUTPUT_TOKENS,
    )


@router.post(
    "/chat",
    summary="Ask a question about the active flow.",
    responses={
        402: {"description": "Budget exceeded — call refused"},
        422: {"description": "Validation error"},
        500: {"description": "Provider error"},
    },
)
async def post_chat(
    request: Request,
    body: ChatRequest,
    audit: LlmAuditRepo = Depends(get_llm_audit_repo),
    meter: CostMeter = Depends(get_cost_meter),
    force: bool = False,
):
    """Answer a chat-with-flow question; supports SSE streaming.

    When the caller passes ``?force=true``, the pre-call budget cap is bypassed
    so the request proceeds even when the projected cost would breach the
    monthly cap or per-call cap. The actual cost is still logged afterwards
    via :func:`_record_success`, so the budget reflects the true spend.
    """
    request_id = getattr(request.state, "request_id", None)

    # Pre-call budget enforcement. Mock provider has zero cost so it sails through.
    # When the caller has acknowledged the budget warning via ?force=true, we
    # skip the pre-call gate but still record actual cost on the success path.
    if body.provider != "mock" and not force:
        projected = _project_call_cost(body.model)
        allowed, reason = meter.check_call_allowed(projected)
        if not allowed:
            raise HTTPException(
                status_code=402,
                detail={
                    "title": "Budget exceeded",
                    "reason": reason,
                    "projected_cost_usd": projected,
                    "budget": meter.summary().to_dict(),
                },
            )

    if body.stream:
        return StreamingResponse(
            _sse_stream(body, audit, meter, request_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "X-Accel-Buffering": "no",
            },
        )

    # Sync path
    try:
        result = await run_in_threadpool(answer_chat, body)
    except ConfigurationError as exc:
        # Re-raise so the global Py2DataikuError handler maps it to problem+json.
        raise exc
    except Py2DataikuError:
        raise
    except Exception as exc:  # pragma: no cover — defensive
        logger.exception("chat: unexpected error")
        _record_failure(audit, body, str(exc), request_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    _record_success(audit, body, result, request_id)
    return result


# ---------------------------------------------------------------------------
# SSE generator
# ---------------------------------------------------------------------------


def _sse_event(event: str, data: dict) -> bytes:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n".encode("utf-8")


async def _sse_stream(
    body: ChatRequest,
    audit: LlmAuditRepo,
    meter: CostMeter,
    request_id: str | None,
) -> AsyncGenerator[bytes, None]:
    # 1) Meta — emit immediately so the client paints the assistant bubble.
    yield _sse_event(
        "meta",
        {"provider": body.provider, "model": body.model or "(default)"},
    )

    # 2) Open a token-level stream against the provider. The provider's
    # ``stream_complete()`` returns real token deltas on Anthropic/OpenAI
    # and a chunked-fallback iterator on the base / mock implementations.
    try:
        provider, deltas = await run_in_threadpool(stream_chat_provider, body)
    except Py2DataikuError as exc:
        yield _sse_event("error", {"title": "Provider error", "detail": str(exc)})
        return
    except Exception as exc:  # pragma: no cover
        logger.exception("chat stream: provider open failed")
        yield _sse_event("error", {"title": "Provider error", "detail": str(exc)})
        return

    # 3) Pump deltas. We accumulate the full answer locally so we can build
    # the final ChatResponse with citations + cost. Each provider yield maps
    # 1:1 to one ``event: delta`` SSE frame.
    answer_parts: list[str] = []
    try:
        # Iterate the (sync) provider stream off the event loop so the
        # network read doesn't block other requests. We pull chunks one at
        # a time via run_in_threadpool — the marginal cost is negligible
        # next to the LLM round-trip.
        sentinel = object()

        def _next_chunk() -> object:
            try:
                return next(deltas)
            except StopIteration:
                return sentinel

        while True:
            chunk = await run_in_threadpool(_next_chunk)
            if chunk is sentinel:
                break
            text = chunk if isinstance(chunk, str) else str(chunk)
            answer_parts.append(text)
            yield _sse_event("delta", {"text": text})
    except Py2DataikuError as exc:
        yield _sse_event("error", {"title": "Provider error", "detail": str(exc)})
        return
    except Exception as exc:  # pragma: no cover
        logger.exception("chat stream: provider yield failed")
        yield _sse_event("error", {"title": "Provider error", "detail": str(exc)})
        return

    answer = "".join(answer_parts)

    # 4) Final payload — citations + usage + cost.
    from ..services.chat import extract_citations

    citations = extract_citations(answer, body.flow_json)
    # Real-streaming providers don't surface per-call usage on the stream
    # iterator itself. Estimate input/output tokens from prompt+answer
    # character counts (rough 4-chars-per-token heuristic) so the cost meter
    # still records a non-zero value for the streamed call. This is a
    # documented approximation — the global LLM-history page should label
    # streamed rows accordingly when we surface that.
    from ..services.chat import build_prompts as _bp

    sys_p, user_p = _bp(body)
    p_tok = max(1, (len(sys_p) + len(user_p)) // 4)
    c_tok = max(1, len(answer) // 4)
    cost = estimate_cost_usd(provider.model_name, p_tok, c_tok)
    final = ChatResponse(
        answer=answer,
        citations=citations,
        model=provider.model_name,
        usage={"input_tokens": p_tok, "output_tokens": c_tok},
        cost_usd=cost,
    )
    yield _sse_event("final", final.model_dump())

    _record_success(audit, body, final, request_id)


# ---------------------------------------------------------------------------
# Audit helpers
# ---------------------------------------------------------------------------


def _record_success(
    audit: LlmAuditRepo,
    body: ChatRequest,
    result: ChatResponse,
    request_id: str | None,
) -> None:
    audit.append(
        LlmCallRecord(
            ts=datetime.now(tz=UTC).isoformat(),
            mode="llm",
            provider=body.provider,
            model=result.model,
            prompt_tokens=int(result.usage.get("input_tokens", 0) or 0),
            completion_tokens=int(result.usage.get("output_tokens", 0) or 0),
            cost_usd=result.cost_usd,
            status="success",
            flow_id=body.flow_id,
            feature="chat",
            request_id=request_id,
            extra={
                "question_chars": len(body.question),
                "history_len": len(body.history),
            },
        )
    )


def _record_failure(
    audit: LlmAuditRepo,
    body: ChatRequest,
    error: str,
    request_id: str | None,
) -> None:
    audit.append(
        LlmCallRecord(
            ts=datetime.now(tz=UTC).isoformat(),
            mode="llm",
            provider=body.provider,
            model=body.model or "",
            prompt_tokens=0,
            completion_tokens=0,
            cost_usd=0.0,
            status="failure",
            flow_id=body.flow_id,
            error=error,
            feature="chat",
            request_id=request_id,
        )
    )
