"""Pydantic schemas for the explain-this-recipe popover.

The popover surfaces three short bullets tailored to a front-office trading
data engineer:

* ``what_this_does`` — 1-sentence plain English (textbook DSS terminology).
* ``trading_context`` — 1-sentence linking to common front-office use cases.
* ``watch_out_for`` — 1-sentence common pitfall.

The endpoint returns the same shape regardless of cache hit/miss so the
frontend treats both paths identically; ``cache_hit`` lets the cost-meter
widget show a "0 cost" hint when the LLM was skipped.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class ExplainRecipeRequest(BaseModel):
    """POST /explain-recipe body.

    The full ``recipe`` dict is supplied by the canvas — we only key the cache
    on a normalised digest of ``recipe_type`` + ``settings`` (see
    ``services.explain.recipe_cache_key``), so the wire shape is intentionally
    permissive.
    """

    recipe: dict[str, Any] = Field(
        ...,
        description="Serialized DataikuRecipe (matches one entry in flow.recipes).",
    )
    context: Optional[dict[str, Any]] = Field(
        default=None,
        description=(
            "Optional surrounding context: upstream/downstream recipe types, "
            "dataset names, a code excerpt. Sent to the LLM but never keyed "
            "into the cache."
        ),
    )
    flow_id: Optional[str] = Field(
        default=None,
        description="Optional saved-flow id for audit/history correlation.",
    )
    provider: Literal["anthropic", "openai", "mock"] = Field(default="anthropic")
    model: Optional[str] = Field(default=None)


class ExplainRecipeResponse(BaseModel):
    """Sync response shape — identical for cache hit and cache miss."""

    what_this_does: str
    trading_context: str
    watch_out_for: str
    recipe_type: str = Field(
        ..., description="The canonical recipe type the explanation is keyed against."
    )
    cache_key: str = Field(
        ..., description="Stable hash of (recipe_type, normalised settings)."
    )
    cache_hit: bool = Field(
        ..., description="True when the response came from the on-disk cache."
    )
    model: str = ""
    usage: dict[str, Any] = Field(default_factory=dict)
    cost_usd: float = 0.0
