"""WebSocket event envelope and typed payload schemas (M1c)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any

from pydantic import BaseModel, Field

from .convert import ComplexityScore
from .flow import DataikuFlowModel

# ---------------------------------------------------------------------------
# Typed payload models — one per event kind
# ---------------------------------------------------------------------------


class ConversionStartedPayload(BaseModel):
    """Payload for the ``started`` event."""

    mode: str = Field(..., description="Conversion mode: 'rule' or 'llm'")
    code_size_bytes: int = Field(..., description="Size of the submitted code in bytes")
    flow_name: str = Field(default="converted_flow", description="Target flow name")


class AstParsedPayload(BaseModel):
    """Payload for the ``ast_parsed`` event (rule mode)."""

    node_count: int = Field(..., description="Number of AST nodes detected")


class ProviderCallStartedPayload(BaseModel):
    """Payload for the ``provider_call_started`` event (LLM mode)."""

    provider: str = Field(..., description="LLM provider name")
    model: str | None = Field(default=None, description="Model name if known")


class ProviderCallCompletedPayload(BaseModel):
    """Payload for the ``provider_call_completed`` event (LLM mode)."""

    provider: str = Field(..., description="LLM provider name")
    model: str | None = Field(default=None, description="Model name from response")
    input_tokens: int | None = Field(default=None)
    output_tokens: int | None = Field(default=None)


class RecipeCreatedPayload(BaseModel):
    """Payload for the ``recipe_created`` event."""

    recipe_name: str
    recipe_type: str


class ProcessorAddedPayload(BaseModel):
    """Payload for the ``processor_added`` event."""

    recipe_name: str
    processor_type: str
    step_index: int


class OptimizedPayload(BaseModel):
    """Payload for the ``optimized`` event."""

    reduction_count: int = Field(..., description="Number of recipes/steps removed by optimizer")


class CompletedPayload(BaseModel):
    """Payload for the ``completed`` event."""

    flow: DataikuFlowModel
    score: ComplexityScore
    warnings: list[str] = Field(default_factory=list)


class ErrorPayload(BaseModel):
    """Payload for the ``error`` event — RFC 7807 problem+json shape."""

    type: str
    title: str
    status: int
    detail: str
    instance: str = ""


class CancelledPayload(BaseModel):
    """Payload for the ``cancelled`` event."""

    reason: str = "Client requested cancellation"


class PingPayload(BaseModel):
    """Payload for the ``ping`` keepalive event."""

    pass


# ---------------------------------------------------------------------------
# Discriminated union of all payload types
# ---------------------------------------------------------------------------

WSEventPayload = Annotated[
    ConversionStartedPayload
    | AstParsedPayload
    | ProviderCallStartedPayload
    | ProviderCallCompletedPayload
    | RecipeCreatedPayload
    | ProcessorAddedPayload
    | OptimizedPayload
    | CompletedPayload
    | ErrorPayload
    | CancelledPayload
    | PingPayload,
    Field(discriminator=None),
]


# ---------------------------------------------------------------------------
# WSEvent envelope — tightened payload field
# ---------------------------------------------------------------------------


class WSEvent(BaseModel):
    """Envelope for all WebSocket messages sent by the server.

    Attributes:
        event: Event name, e.g. ``"started"``, ``"completed"``, ``"error"``.
        seq:   Monotonically increasing sequence number per connection.
        ts:    UTC timestamp of the event.
        payload: Typed event-specific data.
    """

    event: str = Field(..., description="Event name")
    seq: int = Field(..., ge=0, description="Monotonically increasing sequence number")
    ts: datetime = Field(
        default_factory=lambda: datetime.now(tz=UTC),
        description="UTC timestamp",
    )
    payload: Any = Field(default_factory=dict, description="Event payload")
