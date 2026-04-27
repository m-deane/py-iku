"""Pydantic schemas for the chat-with-flow endpoint."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatCitation(BaseModel):
    """A single citation pinning the answer to a recipe in the flow."""

    recipe_id: str = Field(..., description="Recipe name in the flow.recipes array")
    source_lines: Optional[list[int]] = Field(
        default=None,
        description="Optional 1-based line numbers in the original Python source.",
    )


class ChatRequest(BaseModel):
    """POST /chat body."""

    flow_json: dict[str, Any] = Field(
        ...,
        description="Serialized DataikuFlow (the same shape ConvertResponse.flow returns).",
    )
    question: str = Field(..., min_length=1, max_length=4_000)
    history: list[ChatMessage] = Field(default_factory=list)
    pandas_source: Optional[str] = Field(
        default=None,
        description="Original pandas source code for context (truncated server-side).",
    )
    flow_id: Optional[str] = Field(
        default=None,
        description="Optional saved-flow id (used for audit/history correlation).",
    )
    provider: Literal["anthropic", "openai", "mock"] = Field(default="anthropic")
    model: Optional[str] = Field(default=None)
    stream: bool = Field(
        default=False,
        description="If True, the endpoint returns text/event-stream with SSE deltas.",
    )


class ChatResponse(BaseModel):
    """Sync response shape (also the terminal payload of an SSE stream)."""

    answer: str
    citations: list[ChatCitation] = Field(default_factory=list)
    model: str
    usage: dict[str, Any] = Field(default_factory=dict)
    cost_usd: float = 0.0
