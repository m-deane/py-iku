"""POST /suggest-mapping — AI suggest-mapping endpoint for PYTHON recipes.

Audited the same way as /chat and /explain-recipe so the LLM-history page
shows convert + chat + explain + suggest in one timeline. Pre-call budget
check matches /chat (gates on per-call and monthly caps).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from py2dataiku.exceptions import ConfigurationError, Py2DataikuError

from ..deps import get_cost_meter, get_llm_audit_repo
from ..schemas.suggest import SuggestMappingRequest, SuggestMappingResponse
from ..services import suggest as suggest_service
from ..services.cost_meter import CostMeter
from ..services.llm_audit import LlmAuditRepo, LlmCallRecord, estimate_cost_usd

logger = logging.getLogger(__name__)

router = APIRouter(tags=["suggest"])


# Pre-call budget projection. Suggest prompts are larger than explain — the
# original Python source can run to a few thousand chars — but the response
# stays small. Use a slightly higher input ceiling than explain.
_PROJECTED_INPUT_TOKENS = 5_000
_PROJECTED_OUTPUT_TOKENS = 600


def _project_call_cost(model: Optional[str]) -> float:
    return estimate_cost_usd(
        model or "claude-3-5-sonnet-latest",
        _PROJECTED_INPUT_TOKENS,
        _PROJECTED_OUTPUT_TOKENS,
    )


@router.post(
    "/suggest-mapping",
    response_model=SuggestMappingResponse,
    summary="Suggest a visual-recipe equivalent for a PYTHON recipe.",
    responses={
        402: {"description": "Budget exceeded — call refused"},
        422: {"description": "Validation error"},
        500: {"description": "Provider error"},
    },
)
async def post_suggest_mapping(
    request: Request,
    body: SuggestMappingRequest,
    audit: LlmAuditRepo = Depends(get_llm_audit_repo),
    meter: CostMeter = Depends(get_cost_meter),
) -> SuggestMappingResponse:
    """Return an LLM-derived suggestion for rewriting a PYTHON recipe."""
    request_id = getattr(request.state, "request_id", None)

    if body.provider != "mock":
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

    try:
        result = await run_in_threadpool(suggest_service.suggest_mapping, body)
    except ConfigurationError:
        raise
    except Py2DataikuError:
        raise
    except Exception as exc:  # pragma: no cover — defensive
        logger.exception("suggest-mapping: unexpected error")
        _record_failure(audit, body, str(exc), request_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    _record_success(audit, body, result, request_id)
    return result


# ---------------------------------------------------------------------------
# Audit helpers
# ---------------------------------------------------------------------------


def _record_success(
    audit: LlmAuditRepo,
    body: SuggestMappingRequest,
    result: SuggestMappingResponse,
    request_id: Optional[str],
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
            feature="suggest",
            request_id=request_id,
            extra={
                "suggested_recipe_type": result.suggested_recipe_type,
                "confidence": result.confidence,
                "source_chars": len(body.python_source),
            },
        )
    )


def _record_failure(
    audit: LlmAuditRepo,
    body: SuggestMappingRequest,
    error: str,
    request_id: Optional[str],
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
            feature="suggest",
            request_id=request_id,
        )
    )
