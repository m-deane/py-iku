"""Async conversion event emitter — bridges sync py-iku callbacks to WS frames.

Each public method enqueues a ``WSEvent`` with an auto-incremented seq number
and the correct typed payload.  ``stream()`` is an async iterator that yields
events until a terminal event (completed/error/cancelled) is produced.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from itertools import count
from typing import Any

from ..schemas.events import (
    AstParsedPayload,
    CancelledPayload,
    CompletedPayload,
    ConversionStartedPayload,
    ErrorPayload,
    OptimizedPayload,
    PingPayload,
    ProcessorAddedPayload,
    ProviderCallCompletedPayload,
    ProviderCallStartedPayload,
    RecipeCreatedPayload,
    WSEvent,
)

logger = logging.getLogger(__name__)

# Sentinel for queue termination
_SENTINEL: object = object()

_TERMINAL_EVENTS: frozenset[str] = frozenset({"completed", "error", "cancelled"})


class ConversionEventEmitter:
    """Collects progress events from a conversion run and exposes them via an async iterator.

    Usage::

        emitter = ConversionEventEmitter()
        # In a worker task:
        emitter.started(meta)
        emitter.ast_parsed(42)
        emitter.completed(flow, score, warnings)
        # In the WS handler:
        async for event in emitter.stream():
            await ws.send_text(event.model_dump_json())
    """

    def __init__(self) -> None:
        self._queue: asyncio.Queue[WSEvent | object] = asyncio.Queue()
        self._seq = count(0)
        self._done = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _emit(self, event: str, payload: Any) -> None:
        """Enqueue a WSEvent.  No-op if already terminal (avoids double-close)."""
        if self._done and event not in _TERMINAL_EVENTS:
            return
        evt = WSEvent(
            event=event,
            seq=next(self._seq),
            ts=datetime.now(tz=UTC),
            payload=payload.model_dump() if hasattr(payload, "model_dump") else payload,
        )
        self._queue.put_nowait(evt)
        if event in _TERMINAL_EVENTS:
            self._done = True
            self._queue.put_nowait(_SENTINEL)

    # ------------------------------------------------------------------
    # Public event methods
    # ------------------------------------------------------------------

    def started(self, mode: str, code_size_bytes: int, flow_name: str = "converted_flow") -> None:
        """Emit a ``started`` event."""
        self._emit("started", ConversionStartedPayload(
            mode=mode,
            code_size_bytes=code_size_bytes,
            flow_name=flow_name,
        ))

    def ast_parsed(self, node_count: int) -> None:
        """Emit an ``ast_parsed`` event."""
        self._emit("ast_parsed", AstParsedPayload(node_count=node_count))

    def provider_call_started(self, provider: str, model: str | None = None) -> None:
        """Emit a ``provider_call_started`` event (LLM mode)."""
        self._emit(
            "provider_call_started",
            ProviderCallStartedPayload(provider=provider, model=model),
        )

    def provider_call_completed(
        self,
        provider: str,
        model: str | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
    ) -> None:
        """Emit a ``provider_call_completed`` event (LLM mode)."""
        self._emit("provider_call_completed", ProviderCallCompletedPayload(
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        ))

    def recipe_created(self, recipe_name: str, recipe_type: str) -> None:
        """Emit a ``recipe_created`` event."""
        self._emit("recipe_created", RecipeCreatedPayload(
            recipe_name=recipe_name,
            recipe_type=recipe_type,
        ))

    def processor_added(self, recipe_name: str, processor_type: str, step_index: int) -> None:
        """Emit a ``processor_added`` event."""
        self._emit("processor_added", ProcessorAddedPayload(
            recipe_name=recipe_name,
            processor_type=processor_type,
            step_index=step_index,
        ))

    def optimized(self, reduction_count: int) -> None:
        """Emit an ``optimized`` event."""
        self._emit("optimized", OptimizedPayload(reduction_count=reduction_count))

    def completed(self, flow: Any, score: Any, warnings: list[str]) -> None:
        """Emit a terminal ``completed`` event."""
        self._emit("completed", CompletedPayload(
            flow=flow,
            score=score,
            warnings=warnings,
        ))

    def error(self, problem: dict[str, Any]) -> None:
        """Emit a terminal ``error`` event with an RFC 7807 problem dict."""
        self._emit("error", ErrorPayload(**problem))

    def cancelled(self, reason: str = "Client requested cancellation") -> None:
        """Emit a terminal ``cancelled`` event."""
        self._emit("cancelled", CancelledPayload(reason=reason))

    def ping(self) -> None:
        """Emit a keepalive ``ping`` event."""
        self._emit("ping", PingPayload())

    # ------------------------------------------------------------------
    # Async iterator
    # ------------------------------------------------------------------

    async def stream(self) -> AsyncIterator[WSEvent]:
        """Yield WSEvents until a terminal event is emitted.

        The iterator terminates after yielding the terminal event itself
        (completed / error / cancelled).
        """
        while True:
            item = await self._queue.get()
            if item is _SENTINEL:
                break
            if isinstance(item, WSEvent):
                yield item
                if item.event in _TERMINAL_EVENTS:
                    # Drain the sentinel if not yet consumed
                    try:
                        self._queue.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                    break
