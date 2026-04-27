"""Pydantic schemas for the AI suggest-mapping endpoint.

When the rule-based path emits a ``RecipeType.PYTHON`` recipe (the escape
hatch for unmappable code), the canvas surfaces a yellow banner offering a
visual-recipe equivalent. The endpoint asks the LLM to rewrite the original
pandas snippet into one that would route to a known py-iku recipe type.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class SuggestMappingRequest(BaseModel):
    """POST /suggest-mapping body."""

    python_source: str = Field(
        ...,
        min_length=1,
        max_length=20_000,
        description="The original pandas/numpy/sklearn source that fell through "
        "to the PYTHON escape hatch.",
    )
    context: Optional[dict[str, Any]] = Field(
        default=None,
        description="Optional surrounding flow context (upstream recipes, dataset "
        "names) — supplied to the LLM but not stored.",
    )
    flow_id: Optional[str] = Field(
        default=None,
        description="Optional saved-flow id for audit/history correlation.",
    )
    provider: Literal["anthropic", "openai", "mock"] = Field(default="anthropic")
    model: Optional[str] = Field(default=None)


class SuggestMappingResponse(BaseModel):
    """LLM-derived suggestion. Confidence drives the UI's "Apply" CTA gating."""

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="0.0–1.0 confidence the suggestion is sound. ≥0.7 unlocks "
        "the Apply CTA on the frontend.",
    )
    suggested_recipe_type: str = Field(
        ...,
        description="Canonical recipe spec, e.g. 'GROUPING' / 'WINDOW' / "
        "'PREPARE+FoldMultipleColumns'.",
    )
    transformed_pandas: str = Field(
        ...,
        description="Rewrite of the original pandas code that would route to "
        "the suggested recipe type.",
    )
    reasoning: str = Field(
        ...,
        description="One-sentence explanation of why this mapping fits.",
    )
    model: str = ""
    usage: dict[str, Any] = Field(default_factory=dict)
    cost_usd: float = 0.0
