"""Pydantic schema for `expected/{script_id}.json`.

Each expected file pins the minimum invariants we require of an LLM-converted
flow for a given corpus script. The schema is intentionally loose — we record
*expected* recipe types and counts, not exact dicts, because LLM output will
vary in cosmetic ways (settings ordering, dataset names, etc.).
"""
from __future__ import annotations

from typing import List

try:
    from pydantic import BaseModel, Field, field_validator
except ImportError:  # pragma: no cover - pydantic is a hard dep already
    from pydantic import BaseModel, Field  # type: ignore

    def field_validator(*args, **kwargs):  # type: ignore
        def _decorator(fn):
            return fn

        return _decorator


VALID_CATEGORIES = {
    "single_recipe_type",
    "trading_domain",
    "stress_edge",
}


class ExpectedFlow(BaseModel):
    """Schema for tests/test_llm_corpus/expected/{script_id}.json."""

    id: str = Field(..., description="Script id; matches `<scripts>/<id>.py` filename stem.")
    category: str = Field(..., description="single_recipe_type | trading_domain | stress_edge")
    expected_recipe_types: List[str] = Field(
        default_factory=list,
        description="Lowercase recipe type strings expected in the output flow (multiset).",
    )
    expected_dataset_count: int = Field(..., ge=0)
    expected_outputs: List[str] = Field(
        default_factory=list,
        description="Final output dataset names (sanitized).",
    )
    must_not_contain: List[str] = Field(
        default_factory=list,
        description="Recipe types that should NOT appear (e.g. 'python' as escape hatch).",
    )
    known_issues: List[str] = Field(
        default_factory=list,
        description="Bug tags or analyzer-known-issue tags this script targets.",
    )
    notes: str = ""

    @field_validator("category")
    @classmethod
    def _validate_category(cls, value: str) -> str:
        if value not in VALID_CATEGORIES:
            raise ValueError(
                f"category must be one of {sorted(VALID_CATEGORIES)}, got {value!r}"
            )
        return value
