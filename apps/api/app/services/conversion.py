"""Conversion service — thin wrapper over py2dataiku.api.convert / convert_with_llm."""

from __future__ import annotations

import ast
import logging
import os
from typing import Any

from py2dataiku import convert, convert_with_llm
from py2dataiku.exceptions import ConfigurationError, Py2DataikuError

from ..errors import problem_dict
from ..schemas.convert import ConvertMode, ConvertRequest, ConvertResponse
from ..schemas.flow import DataikuFlowModel
from .score import score_flow
from .streaming import ConversionEventEmitter

logger = logging.getLogger(__name__)


def convert_sync(req: ConvertRequest) -> ConvertResponse:
    """Convert Python code to a DataikuFlow and return a ConvertResponse.

    For rule mode: calls py2dataiku.convert().
    For llm mode: resolves provider/model/key from request options then env vars,
    raises ConfigurationError if no key is found, then calls convert_with_llm().

    Py2DataikuError subclasses propagate up to the global error handler in main.py.
    """
    optimize = req.options.optimize if req.options is not None else True

    if req.mode == ConvertMode.RULE:
        flow = convert(req.code, optimize=optimize)
    else:
        # LLM mode — resolve provider, model, api_key
        provider = (
            req.options.provider
            if req.options is not None and req.options.provider is not None
            else "anthropic"
        )
        model = (
            req.options.model
            if req.options is not None and req.options.model is not None
            else None
        )
        temperature = (
            req.options.temperature
            if req.options is not None and req.options.temperature is not None
            else 0.0
        )

        # Key resolution: env vars only — never log the key value
        key_env = "ANTHROPIC_API_KEY" if provider == "anthropic" else "OPENAI_API_KEY"
        api_key = os.environ.get(key_env)
        if not api_key:
            raise ConfigurationError(
                f"LLM mode requires {key_env} environment variable to be set. "
                "Set the key in the API server environment — never send it in the request body."
            )

        flow = convert_with_llm(
            req.code,
            provider=provider,
            api_key=api_key,
            model=model,
            optimize=optimize,
            temperature=temperature,
        )

    flow_dict = flow.to_dict()
    flow_model = DataikuFlowModel.model_validate(flow_dict)
    score = score_flow(flow)

    return ConvertResponse(
        flow=flow_model,
        score=score,
        warnings=list(flow.warnings),
    )


def _resolve_llm_params(req: ConvertRequest) -> tuple[str, str | None, float, str]:
    """Return (provider, model, temperature, api_key); raises ConfigurationError if key missing."""
    provider = (
        req.options.provider
        if req.options is not None and req.options.provider is not None
        else "anthropic"
    )
    model = (
        req.options.model
        if req.options is not None and req.options.model is not None
        else None
    )
    temperature = (
        req.options.temperature
        if req.options is not None and req.options.temperature is not None
        else 0.0
    )
    key_env = "ANTHROPIC_API_KEY" if provider == "anthropic" else "OPENAI_API_KEY"
    api_key = os.environ.get(key_env)
    if not api_key:
        raise ConfigurationError(
            f"LLM mode requires {key_env} environment variable to be set. "
            "Set the key in the API server environment — never send it in the request body."
        )
    return provider, model, temperature, api_key


def _count_ast_nodes(code: str) -> int:
    """Return the number of AST nodes in *code*; 0 on parse error."""
    try:
        tree = ast.parse(code)
        return sum(1 for _ in ast.walk(tree))
    except SyntaxError:
        return 0


def _emit_recipe_events(flow: Any, emitter: ConversionEventEmitter) -> None:
    """Walk a DataikuFlow and emit recipe_created / processor_added synthetic events."""
    for recipe in flow.recipes:
        rtype = recipe.recipe_type
        recipe_type = rtype.value if hasattr(rtype, "value") else str(rtype)
        emitter.recipe_created(recipe_name=recipe.name, recipe_type=recipe_type)
        for idx, step in enumerate(getattr(recipe, "steps", [])):
            proc_type = (
                step.processor_type.value
                if hasattr(step.processor_type, "value")
                else str(step.processor_type)
            )
            emitter.processor_added(
                recipe_name=recipe.name,
                processor_type=proc_type,
                step_index=idx,
            )


def convert_streaming(req: ConvertRequest, emitter: ConversionEventEmitter) -> None:
    """Run a conversion and bridge milestones into *emitter*.

    This function is **synchronous** and intended to run in a worker thread
    via ``asyncio.to_thread``.  It emits synthetic milestones because py-iku
    does not yet expose fine-grained progress hooks at the recipe/processor
    level — only ``convert_with_llm`` offers an ``on_progress`` callback.

    Events emitted (rule mode):
        started → ast_parsed → recipe_created* → processor_added* → optimized → completed

    Events emitted (LLM mode):
        started → provider_call_started → provider_call_completed
        → recipe_created* → processor_added* → optimized → completed

    On any Py2DataikuError: emits ``error`` with RFC 7807 problem dict.
    """
    optimize = req.options.optimize if req.options is not None else True
    code_bytes = len(req.code.encode())

    emitter.started(mode=req.mode.value, code_size_bytes=code_bytes)

    try:
        if req.mode == ConvertMode.RULE:
            node_count = _count_ast_nodes(req.code)
            emitter.ast_parsed(node_count=node_count)

            flow = convert(req.code, optimize=optimize)

            _emit_recipe_events(flow, emitter)
            emitter.optimized(reduction_count=0)

        else:
            # LLM mode
            provider, model, temperature, api_key = _resolve_llm_params(req)

            emitter.provider_call_started(provider=provider, model=model)

            # on_progress callback phases:
            # "start","analyzing","analyzed","generating","optimizing","done"
            _llm_response_holder: dict[str, Any] = {}

            def _on_progress(phase: str, data: Any = None) -> None:  # noqa: ANN401
                pass  # future: emit finer-grained events per phase

            flow = convert_with_llm(
                req.code,
                provider=provider,
                api_key=api_key,
                model=model,
                optimize=optimize,
                temperature=temperature,
                on_progress=_on_progress,
            )

            emitter.provider_call_completed(provider=provider, model=model)

            _emit_recipe_events(flow, emitter)
            emitter.optimized(reduction_count=0)

    except Py2DataikuError as exc:
        logger.warning("Py2DataikuError in streaming conversion: %s", exc)
        emitter.error(problem_dict(exc, instance="/convert/stream"))
        return

    except Exception as exc:
        logger.exception("Unexpected error in streaming conversion: %s", exc)
        from py2dataiku.exceptions import ConversionError
        wrapped = ConversionError(str(exc))
        emitter.error(problem_dict(wrapped, instance="/convert/stream"))
        return

    # Build response models
    try:
        flow_dict = flow.to_dict()
        flow_model = DataikuFlowModel.model_validate(flow_dict)
        score = score_flow(flow)
        emitter.completed(flow=flow_model, score=score, warnings=list(flow.warnings))
    except Exception as exc:
        logger.exception("Error building completion payload: %s", exc)
        from py2dataiku.exceptions import ConversionError
        wrapped = ConversionError(str(exc))
        emitter.error(problem_dict(wrapped, instance="/convert/stream"))
