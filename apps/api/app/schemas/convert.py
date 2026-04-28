"""Pydantic v2 schemas for the POST /convert endpoint."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .flow import DataikuFlowModel


class ConvertMode(StrEnum):
    """Conversion mode: rule-based AST or LLM-assisted."""

    RULE = "rule"
    LLM = "llm"


class ConvertOptions(BaseModel):
    """Optional per-request conversion options."""

    provider: Literal["anthropic", "openai"] | None = Field(
        default=None, description="LLM provider (llm mode only)"
    )
    model: str | None = Field(
        default=None, description="LLM model name override"
    )
    temperature: float | None = Field(
        default=None, ge=0.0, le=2.0, description="LLM temperature"
    )
    optimize: bool = Field(
        default=True, description="Run flow optimizer after conversion"
    )
    max_code_size_bytes: int = Field(
        default=262144,  # 256 KB
        gt=0,
        description="Maximum allowed code size in bytes",
    )


class ConvertRequest(BaseModel):
    """Request body for POST /convert."""

    code: str = Field(..., description="Python source code to convert")
    mode: ConvertMode = Field(default=ConvertMode.RULE, description="Conversion mode")
    options: ConvertOptions | None = Field(default=None)

    @model_validator(mode="after")
    def check_code_size(self) -> "ConvertRequest":  # noqa: UP037
        """Reject code exceeding max_code_size_bytes."""
        max_bytes = (
            self.options.max_code_size_bytes
            if self.options is not None
            else 262144
        )
        if len(self.code.encode()) > max_bytes:
            raise ValueError(
                f"Code size {len(self.code.encode())} bytes exceeds "
                f"maximum of {max_bytes} bytes"
            )
        if not self.code.strip():
            raise ValueError("code must not be empty")
        return self


class ComplexityScore(BaseModel):
    """Flow complexity metrics derived from FlowGraph analysis."""

    recipe_count: int = Field(..., description="Total number of recipes")
    processor_count: int = Field(..., description="Total prepare steps across all PREPARE recipes")
    dataset_count: int = Field(
        default=0,
        description="Total number of datasets in the flow (input + intermediate + output)",
    )
    max_depth: int = Field(..., description="Longest path from root to leaf (node hops)")
    fan_out_max: int = Field(..., description="Maximum out-degree of any single node")
    complexity: float = Field(..., description="Composite complexity score [0, ∞)")
    cost_estimate: float | None = Field(
        default=None, description="Estimated LLM cost in USD (LLM mode only)"
    )
    usage: dict[str, int | None] | None = Field(
        default=None,
        description=(
            "Token-usage telemetry for the LLM call (LLM mode only). "
            "Keys: input_tokens, output_tokens, cache_read_input_tokens, "
            "cache_creation_input_tokens. Pricing assumes Claude Sonnet 4 "
            "($3/MTok input, $15/MTok output, $0.30/MTok cache read)."
        ),
    )


class ConvertResponse(BaseModel):
    """Response body from POST /convert."""

    flow: DataikuFlowModel
    score: ComplexityScore
    warnings: list[str] = Field(default_factory=list)
