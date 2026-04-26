"""Unit tests for ConversionEventEmitter in isolation."""

from __future__ import annotations

import asyncio

import pytest

from app.services.streaming import ConversionEventEmitter


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


async def _collect(emitter: ConversionEventEmitter, limit: int = 50) -> list[dict]:
    """Collect all events from the emitter stream into a list of dicts."""
    events = []
    async for evt in emitter.stream():
        events.append({"event": evt.event, "seq": evt.seq, "payload": evt.payload})
        if len(events) >= limit:
            break
    return events


# ---------------------------------------------------------------------------
# seq autoincrement
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_seq_starts_at_zero() -> None:
    emitter = ConversionEventEmitter()
    emitter.started(mode="rule", code_size_bytes=100)
    emitter.completed(
        flow=_minimal_flow(),
        score=_minimal_score(),
        warnings=[],
    )
    events = await _collect(emitter)
    seqs = [e["seq"] for e in events]
    assert seqs[0] == 0


@pytest.mark.asyncio
async def test_seq_monotonically_increasing() -> None:
    emitter = ConversionEventEmitter()
    emitter.started(mode="rule", code_size_bytes=100)
    emitter.ast_parsed(node_count=10)
    emitter.recipe_created(recipe_name="r1", recipe_type="PREPARE")
    emitter.optimized(reduction_count=1)
    emitter.completed(
        flow=_minimal_flow(),
        score=_minimal_score(),
        warnings=[],
    )
    events = await _collect(emitter)
    seqs = [e["seq"] for e in events]
    assert seqs == sorted(seqs), "seq not monotonically increasing"
    assert len(set(seqs)) == len(seqs), "seq not unique"


# ---------------------------------------------------------------------------
# Terminal events stop the iterator
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_completed_terminates_stream() -> None:
    emitter = ConversionEventEmitter()
    emitter.started(mode="rule", code_size_bytes=50)
    emitter.completed(
        flow=_minimal_flow(),
        score=_minimal_score(),
        warnings=["w1"],
    )
    events = await _collect(emitter)
    event_names = [e["event"] for e in events]
    assert "completed" in event_names
    assert event_names[-1] == "completed"


@pytest.mark.asyncio
async def test_error_terminates_stream() -> None:
    emitter = ConversionEventEmitter()
    emitter.started(mode="rule", code_size_bytes=50)
    emitter.error({
        "type": "https://py-iku.dev/errors/ConversionError",
        "title": "Conversion Error",
        "status": 422,
        "detail": "something went wrong",
        "instance": "/convert/stream",
    })
    events = await _collect(emitter)
    event_names = [e["event"] for e in events]
    assert "error" in event_names
    assert event_names[-1] == "error"


@pytest.mark.asyncio
async def test_cancelled_terminates_stream() -> None:
    emitter = ConversionEventEmitter()
    emitter.started(mode="rule", code_size_bytes=50)
    emitter.cancelled()
    events = await _collect(emitter)
    event_names = [e["event"] for e in events]
    assert "cancelled" in event_names
    assert event_names[-1] == "cancelled"


# ---------------------------------------------------------------------------
# No events after terminal
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_events_after_terminal_ignored() -> None:
    """Events enqueued after a terminal event are not yielded."""
    emitter = ConversionEventEmitter()
    emitter.started(mode="rule", code_size_bytes=50)
    emitter.completed(
        flow=_minimal_flow(),
        score=_minimal_score(),
        warnings=[],
    )
    # These should be no-ops
    emitter.ast_parsed(node_count=99)
    emitter.recipe_created(recipe_name="phantom", recipe_type="JOIN")

    events = await _collect(emitter)
    event_names = [e["event"] for e in events]
    assert "ast_parsed" not in event_names
    assert "recipe_created" not in event_names


# ---------------------------------------------------------------------------
# Ping events
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ping_does_not_terminate_stream() -> None:
    emitter = ConversionEventEmitter()
    emitter.started(mode="rule", code_size_bytes=50)
    emitter.ping()
    emitter.ping()
    emitter.completed(
        flow=_minimal_flow(),
        score=_minimal_score(),
        warnings=[],
    )
    events = await _collect(emitter)
    event_names = [e["event"] for e in events]
    assert event_names.count("ping") == 2
    assert event_names[-1] == "completed"


# ---------------------------------------------------------------------------
# Cancellation drains cleanly
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cancellation_payload() -> None:
    emitter = ConversionEventEmitter()
    emitter.cancelled(reason="test cancel")
    events = await _collect(emitter)
    assert events[0]["event"] == "cancelled"
    assert events[0]["payload"]["reason"] == "test cancel"


# ---------------------------------------------------------------------------
# Concurrent producers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_two_emitters_independent_seq() -> None:
    """Two emitters have independent seq counters."""
    e1 = ConversionEventEmitter()
    e2 = ConversionEventEmitter()

    e1.started(mode="rule", code_size_bytes=10)
    e1.completed(flow=_minimal_flow(), score=_minimal_score(), warnings=[])

    e2.started(mode="rule", code_size_bytes=20)
    e2.completed(flow=_minimal_flow(), score=_minimal_score(), warnings=[])

    events1 = await _collect(e1)
    events2 = await _collect(e2)

    # Both start at 0
    assert events1[0]["seq"] == 0
    assert events2[0]["seq"] == 0


# ---------------------------------------------------------------------------
# Payload content sanity
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_started_payload_content() -> None:
    emitter = ConversionEventEmitter()
    emitter.started(mode="llm", code_size_bytes=512, flow_name="my_flow")
    emitter.cancelled()
    events = await _collect(emitter)
    started = next(e for e in events if e["event"] == "started")
    assert started["payload"]["mode"] == "llm"
    assert started["payload"]["code_size_bytes"] == 512
    assert started["payload"]["flow_name"] == "my_flow"


@pytest.mark.asyncio
async def test_ast_parsed_payload_content() -> None:
    emitter = ConversionEventEmitter()
    emitter.ast_parsed(node_count=42)
    emitter.cancelled()
    events = await _collect(emitter)
    ap = next(e for e in events if e["event"] == "ast_parsed")
    assert ap["payload"]["node_count"] == 42


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _minimal_flow() -> object:
    """Return a minimal DataikuFlowModel-compatible dict."""
    from app.schemas.flow import DataikuFlowModel

    return DataikuFlowModel.model_validate({
        "flow_name": "test_flow",
        "total_recipes": 0,
        "total_datasets": 0,
        "datasets": [],
        "recipes": [],
    })


def _minimal_score() -> object:
    from app.schemas.convert import ComplexityScore

    return ComplexityScore(
        recipe_count=0,
        processor_count=0,
        max_depth=0,
        fan_out_max=0,
        complexity=0.0,
    )
