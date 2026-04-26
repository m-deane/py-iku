"""Conversion service — thin wrapper over py2dataiku.api.convert / convert_with_llm."""

from __future__ import annotations

import os

from py2dataiku import convert, convert_with_llm
from py2dataiku.exceptions import ConfigurationError

from ..schemas.convert import ConvertMode, ConvertRequest, ConvertResponse
from ..schemas.flow import DataikuFlowModel
from .score import score_flow


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
