"""Suggest-mapping service — asks the LLM to rewrite a Python recipe as a
visual-recipe equivalent.

The list of available py-iku recipe types is sourced from the canonical
``RecipeType`` enum so prompts stay in lock-step with what the rule-based
path can actually emit. The LLM returns a JSON object with confidence,
suggested type, transformed pandas source, and a one-sentence reasoning.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

from py2dataiku.exceptions import ConfigurationError, Py2DataikuError
from py2dataiku.llm.providers import (
    LLMProvider,
    MockProvider,
    get_provider,
)
from py2dataiku.models.dataiku_recipe import RecipeType

from ..schemas.suggest import SuggestMappingRequest, SuggestMappingResponse
from .llm_audit import estimate_cost_usd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Available targets — sourced from the RecipeType enum so we can never drift.
# We exclude the PYTHON escape hatch itself plus the engine-specific code
# recipes (R, SQL_SCRIPT, HIVE, IMPALA, SPARK_*) — those are alternative
# escape hatches, not visual-recipe equivalents.
# ---------------------------------------------------------------------------


_CODE_HATCHES = {
    "PYTHON",
    "R",
    "SHELL",
    "SQL_SCRIPT",
    "HIVE",
    "IMPALA",
    "SPARK_SQL_QUERY",
    "PYSPARK",
    "SPARK_SCALA",
    "SPARKR",
}


def visual_recipe_targets() -> list[str]:
    """Return the canonical names of every non-code recipe type, plus a few
    handy ``PREPARE+<processor>`` shorthand targets that the prompt can pick.
    """
    base = sorted(
        rt.name for rt in RecipeType if rt.name.upper() not in _CODE_HATCHES
    )
    # Add the PREPARE+processor convenience targets the rubric whitelists.
    extras = [
        "PREPARE+FoldMultipleColumns",
        "PREPARE+UnfoldColumn",
        "PREPARE+FilterOnValue",
        "PREPARE+FilterOnNumericRange",
        "PREPARE+FilterOnFormula",
        "PREPARE+CreateColumnWithGREL",
    ]
    return base + extras


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------


SYSTEM_RUBRIC = """You are an assistant embedded in py-iku Studio, a tool that
converts pandas/numpy/sklearn pipelines to Dataiku DSS flows. The rule-based
path could not map the snippet below to a visual recipe and emitted a PYTHON
recipe instead.

Your job: judge whether the snippet *could* be rewritten so it routes to
one of the canonical visual recipe types listed below, and if so produce
the rewrite.

Output rules:
1. Respond with a SINGLE JSON object — no prose before or after, no markdown.
2. Required keys (exact spelling):
   - "confidence":             float in [0.0, 1.0]
   - "suggested_recipe_type":  one of the AVAILABLE RECIPE TYPES verbatim
   - "transformed_pandas":     the rewritten pandas code (one or more lines)
   - "reasoning":              ONE sentence explaining the mapping
3. If no mapping is plausible, return confidence < 0.5 and explain why in
   ``reasoning``. Do NOT return a fabricated rewrite — leave
   ``transformed_pandas`` as the original snippet in that case.
4. Use the textbook DSS terminology: "PREPARE recipe", "GROUPING recipe",
   "WINDOW recipe", "TOP_N recipe", "SPLIT recipe", "processor".
5. The user is a front-office data engineer at an oil/gas/power trading
   desk — favour rewrites that map onto blotter aggregation, tenor curves,
   P&L attribution, MtM rollups, ISO LMP joins, and similar workflows when
   the snippet looks like one of those.
"""


def build_suggest_prompts(req: SuggestMappingRequest) -> tuple[str, str]:
    """Return ``(system_prompt, user_prompt)`` for the LLM call."""
    targets = "\n".join(f"  - {name}" for name in visual_recipe_targets())
    ctx_block = ""
    if req.context:
        ctx_compact = json.dumps(req.context, separators=(",", ":"))[:1500]
        ctx_block = f"\n\n--- SURROUNDING FLOW CONTEXT ---\n{ctx_compact}"

    system = (
        SYSTEM_RUBRIC
        + "\n\n--- AVAILABLE RECIPE TYPES ---\n"
        + targets
        + "\n\n--- ORIGINAL PYTHON RECIPE BODY ---\n"
        + req.python_source[:8000]
        + ctx_block
    )
    user = (
        "Suggest a mapping for the snippet above, returning the JSON object "
        "specified above. No markdown."
    )
    return system.strip(), user.strip()


# ---------------------------------------------------------------------------
# Provider resolution (mirrors chat / explain — env-only key lookup)
# ---------------------------------------------------------------------------


def resolve_provider(
    provider: str,
    model: Optional[str] = None,
) -> LLMProvider:
    if provider == "mock":
        return MockProvider()
    key_env = "ANTHROPIC_API_KEY" if provider == "anthropic" else "OPENAI_API_KEY"
    api_key = os.environ.get(key_env)
    if not api_key:
        raise ConfigurationError(
            f"suggest-mapping requires {key_env} to be set in the API server "
            "environment."
        )
    return get_provider(provider=provider, api_key=api_key, model=model)


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------


_REQUIRED_FIELDS = (
    "confidence",
    "suggested_recipe_type",
    "transformed_pandas",
    "reasoning",
)


def parse_suggest_payload(content: str) -> dict[str, Any]:
    """Pull the suggestion JSON object out of an LLM response.

    Tolerates leading/trailing prose and code fences. Validates that
    ``suggested_recipe_type`` lands in the known target list — drops to
    confidence=0 when it doesn't, since silently surfacing a fabricated
    type would be worse than admitting the model didn't follow instructions.
    """
    raw = content.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise Py2DataikuError(
            "suggest-mapping response did not contain a JSON object."
        )
    try:
        parsed = json.loads(raw[start : end + 1])
    except json.JSONDecodeError as exc:
        raise Py2DataikuError(
            f"suggest-mapping response was not valid JSON: {exc}"
        ) from exc
    for field in _REQUIRED_FIELDS:
        if field not in parsed:
            raise Py2DataikuError(
                f"suggest-mapping response missing required field: {field}"
            )

    confidence = float(parsed["confidence"])
    confidence = max(0.0, min(1.0, confidence))
    recipe_type = str(parsed["suggested_recipe_type"]).strip()
    if recipe_type not in set(visual_recipe_targets()):
        # Don't reject — degrade. The frontend gates the Apply CTA on
        # confidence ≥ 0.7 so a low-confidence "unknown" suggestion is fine
        # to surface as informational.
        confidence = min(confidence, 0.4)

    return {
        "confidence": confidence,
        "suggested_recipe_type": recipe_type,
        "transformed_pandas": str(parsed["transformed_pandas"]).rstrip() + "\n",
        "reasoning": str(parsed["reasoning"]).strip(),
    }


# ---------------------------------------------------------------------------
# Top-level orchestration
# ---------------------------------------------------------------------------


def suggest_mapping(
    req: SuggestMappingRequest,
    provider: Optional[LLMProvider] = None,
) -> SuggestMappingResponse:
    """Run a single suggest-mapping turn."""
    prov = provider or resolve_provider(req.provider, req.model)
    system, user = build_suggest_prompts(req)
    resp = prov.complete(prompt=user, system_prompt=system)
    parsed = parse_suggest_payload(resp.content)

    usage = resp.usage or {}
    p_tok = int(usage.get("input_tokens", 0) or 0)
    c_tok = int(usage.get("output_tokens", 0) or 0)
    model_name = resp.model or prov.model_name
    cost = estimate_cost_usd(model_name, p_tok, c_tok)

    return SuggestMappingResponse(
        confidence=parsed["confidence"],
        suggested_recipe_type=parsed["suggested_recipe_type"],
        transformed_pandas=parsed["transformed_pandas"],
        reasoning=parsed["reasoning"],
        model=model_name,
        usage={"input_tokens": p_tok, "output_tokens": c_tok},
        cost_usd=cost,
    )
