"""POST /explain-recipe — AI explain-this-recipe popover endpoint.

Cache-first: an in-memory + on-disk JSONL cache keyed by ``recipe_type`` plus
a normalised settings hash collapses repeated calls. Cost-meter and audit-log
plumbing match the existing /chat surface so the LLM-history page surfaces
explain calls alongside chat + convert.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from functools import lru_cache
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from py2dataiku.exceptions import ConfigurationError, Py2DataikuError

from ..deps import get_cost_meter, get_llm_audit_repo, get_settings
from ..schemas.explain import ExplainRecipeRequest, ExplainRecipeResponse
from ..services import explain as explain_service
from ..services.cost_meter import CostMeter
from ..services.explain import ExplainCache, recipe_cache_key
from ..services.llm_audit import LlmAuditRepo, LlmCallRecord, estimate_cost_usd

logger = logging.getLogger(__name__)

router = APIRouter(tags=["explain"])


# ---------------------------------------------------------------------------
# Cache singleton — bound to Settings.flows_dir like the audit/cost repos.
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def get_explain_cache() -> ExplainCache:
    settings = get_settings()
    return ExplainCache(base_dir=settings.flows_dir)


def reset_explain_cache_singleton() -> None:
    """Clear the cached singleton — used by tests when ``flows_dir`` rebinds."""
    get_explain_cache.cache_clear()


# Pre-call budget projection. Explain prompts are tiny (~2-4k input tokens)
# and the response is ~150 output tokens, so we use a conservative ceiling.
_PROJECTED_INPUT_TOKENS = 3_500
_PROJECTED_OUTPUT_TOKENS = 250


def _project_call_cost(model: Optional[str]) -> float:
    return estimate_cost_usd(
        model or "claude-3-5-sonnet-latest",
        _PROJECTED_INPUT_TOKENS,
        _PROJECTED_OUTPUT_TOKENS,
    )


@router.post(
    "/explain-recipe",
    response_model=ExplainRecipeResponse,
    summary="Explain a single recipe in trading-domain terms.",
    responses={
        402: {"description": "Budget exceeded — call refused"},
        422: {"description": "Validation error"},
        500: {"description": "Provider error"},
    },
)
async def post_explain_recipe(
    request: Request,
    body: ExplainRecipeRequest,
    audit: LlmAuditRepo = Depends(get_llm_audit_repo),
    meter: CostMeter = Depends(get_cost_meter),
    cache: ExplainCache = Depends(get_explain_cache),
) -> ExplainRecipeResponse:
    """Return a 3-bullet explanation of *body.recipe* for the canvas popover."""
    request_id = getattr(request.state, "request_id", None)

    # Cache hit short-circuits the budget check — no LLM call → no spend.
    recipe_type, key = recipe_cache_key(body.recipe)
    if cache.get(key) is not None:
        try:
            result = await run_in_threadpool(
                explain_service.explain_recipe, body, cache
            )
        except Py2DataikuError:
            raise
        # Audit cache hits as zero-cost so the history page can show the call.
        _record_success(audit, body, result, request_id)
        return result

    # Pre-call budget enforcement. Mock provider is always free.
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
        result = await run_in_threadpool(
            explain_service.explain_recipe, body, cache
        )
    except ConfigurationError:
        raise
    except Py2DataikuError:
        raise
    except Exception as exc:  # pragma: no cover — defensive
        logger.exception("explain-recipe: unexpected error")
        _record_failure(audit, body, str(exc), request_id, recipe_type)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    _record_success(audit, body, result, request_id)
    return result


# ---------------------------------------------------------------------------
# Audit helpers
# ---------------------------------------------------------------------------


def _record_success(
    audit: LlmAuditRepo,
    body: ExplainRecipeRequest,
    result: ExplainRecipeResponse,
    request_id: Optional[str],
) -> None:
    audit.append(
        LlmCallRecord(
            ts=datetime.now(tz=UTC).isoformat(),
            mode="llm",
            provider=body.provider if not result.cache_hit else "cache",
            model=result.model or ("mock" if body.provider == "mock" else ""),
            prompt_tokens=int(result.usage.get("input_tokens", 0) or 0),
            completion_tokens=int(result.usage.get("output_tokens", 0) or 0),
            cost_usd=result.cost_usd,
            status="success",
            flow_id=body.flow_id,
            feature="explain",
            request_id=request_id,
            extra={
                "recipe_type": result.recipe_type,
                "cache_hit": result.cache_hit,
                "cache_key": result.cache_key,
            },
        )
    )


def _record_failure(
    audit: LlmAuditRepo,
    body: ExplainRecipeRequest,
    error: str,
    request_id: Optional[str],
    recipe_type: str,
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
            feature="explain",
            request_id=request_id,
            extra={"recipe_type": recipe_type},
        )
    )
