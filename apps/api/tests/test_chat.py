"""Tests for the /chat endpoint using the MockProvider — no real LLM calls."""

from __future__ import annotations

import json
from typing import Any

import pytest
from py2dataiku.llm.providers import MockProvider

from app.services import chat as chat_service
from app.services.chat import build_prompts, extract_citations
from app.services.llm_audit import estimate_cost_usd

SAMPLE_FLOW: dict[str, Any] = {
    "flow_name": "trade_capture",
    "datasets": [
        {"name": "raw_trades"},
        {"name": "enriched_trades"},
    ],
    "recipes": [
        {
            "name": "prep_raw",
            "type": "PREPARE",
            "inputs": ["raw_trades"],
            "outputs": ["enriched_trades"],
            "steps": [{"processor_type": "FILL_EMPTY_WITH_VALUE"}],
            "confidence": "high",
        },
        {
            "name": "agg_by_book",
            "type": "GROUPING",
            "inputs": ["enriched_trades"],
            "outputs": ["pnl_by_book"],
            "confidence": "medium",
        },
    ],
}


def _patch_provider(monkeypatch, response_text: str) -> MockProvider:
    """Force ``resolve_provider`` to return a stub MockProvider with canned text."""
    mock = MockProvider(responses={"QUESTION": response_text})
    monkeypatch.setattr(chat_service, "resolve_provider", lambda *a, **kw: mock)
    return mock


@pytest.mark.asyncio
async def test_chat_sync_round_trip(client, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Round-trip: question in → answer + valid citations + cost recorded."""
    answer = (
        "The PREPARE recipe [recipe:prep_raw] fills empty values, then "
        "[recipe:agg_by_book] aggregates by book."
    )
    _patch_provider(monkeypatch, answer)

    resp = await client.post(
        "/chat",
        json={
            "flow_json": SAMPLE_FLOW,
            "question": "What does prep_raw do?",
            "provider": "mock",
            "stream": False,
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["answer"] == answer
    cite_ids = [c["recipe_id"] for c in body["citations"]]
    assert cite_ids == ["prep_raw", "agg_by_book"]
    assert body["cost_usd"] == 0.0  # mock provider — no real cost
    assert body["model"] == "mock"


@pytest.mark.asyncio
async def test_chat_filters_invalid_citations(client, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Citations to recipes that don't exist in the flow are dropped."""
    answer = "See [recipe:nonexistent] and [recipe:prep_raw]."
    _patch_provider(monkeypatch, answer)

    resp = await client.post(
        "/chat",
        json={
            "flow_json": SAMPLE_FLOW,
            "question": "QUESTION about the prep step",
            "provider": "mock",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    cite_ids = [c["recipe_id"] for c in body["citations"]]
    assert cite_ids == ["prep_raw"]


@pytest.mark.asyncio
async def test_chat_stream_emits_meta_delta_final(client, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Streaming path emits SSE events in the documented order."""
    answer = "Recipe [recipe:agg_by_book] is a GROUPING recipe."
    _patch_provider(monkeypatch, answer)

    resp = await client.post(
        "/chat",
        json={
            "flow_json": SAMPLE_FLOW,
            "question": "What is agg_by_book?",
            "provider": "mock",
            "stream": True,
        },
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")

    text = resp.text
    # We should see meta first, then at least one delta, then final.
    assert "event: meta" in text
    assert "event: delta" in text
    assert "event: final" in text
    # The final payload contains the answer + citations.
    final_block = text.split("event: final")[-1]
    payload_line = next(l for l in final_block.splitlines() if l.startswith("data: "))
    final = json.loads(payload_line[len("data: "):])
    assert final["answer"] == answer
    assert final["citations"][0]["recipe_id"] == "agg_by_book"


@pytest.mark.asyncio
async def test_chat_logs_to_llm_history(client, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Successful chat calls land in /llm-history."""
    _patch_provider(monkeypatch, "[recipe:prep_raw] fills empties.")
    await client.post(
        "/chat",
        json={
            "flow_json": SAMPLE_FLOW,
            "question": "tell me",
            "provider": "mock",
            "flow_id": "flow-abc",
        },
    )
    hist = await client.get("/llm-history")
    body = hist.json()
    assert body["records"], "expected at least one llm-history record"
    last = body["records"][0]
    assert last["feature"] == "chat"
    assert last["provider"] == "mock"
    assert last["status"] == "success"
    assert last["flow_id"] == "flow-abc"


def test_build_prompts_truncates_long_pandas() -> None:
    """build_prompts must keep the pandas excerpt under a sane bound."""
    long_src = "x = 1\n" * 5000
    from app.schemas.chat import ChatRequest

    req = ChatRequest(
        flow_json=SAMPLE_FLOW,
        question="why?",
        pandas_source=long_src,
    )
    sys, user = build_prompts(req)
    assert "truncated" in sys
    assert len(sys) < 60_000


def test_extract_citations_dedupes() -> None:
    answer = "[recipe:prep_raw] then [recipe:prep_raw] again."
    cites = extract_citations(answer, SAMPLE_FLOW)
    assert [c.recipe_id for c in cites] == ["prep_raw"]


def test_estimate_cost_known_and_unknown_models() -> None:
    """Cost helper has a default fallback so unknown models don't return 0."""
    sonnet = estimate_cost_usd("claude-3-5-sonnet-latest", 1_000_000, 1_000_000)
    # 3.00 + 15.00 = 18.00
    assert pytest.approx(sonnet, rel=1e-3) == 18.00
    unknown = estimate_cost_usd("gpt-future", 1_000_000, 1_000_000)
    assert unknown > 0.0  # default fallback applied


# ---------------------------------------------------------------------------
# Token-level streaming (Sprint 4B → real-stream swap)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chat_stream_emits_real_provider_deltas_in_order(  # type: ignore[no-untyped-def]
    client, monkeypatch
) -> None:
    """MockProvider with `stream_deltas=[3 strings]` produces 3 SSE deltas.

    Verifies the wire shape (event: meta → event: delta+ → event: final)
    is unchanged after switching from stream_chat_chunks (answer-then-slice)
    to provider.stream_complete (token deltas).
    """
    deltas = ["The PREPARE recipe ", "[recipe:prep_raw] fills ", "the empties."]

    class _StreamingMock(MockProvider):
        # Subclass so we can record the system_prompt path through the route.
        pass

    mock = _StreamingMock(stream_deltas=deltas)
    monkeypatch.setattr(chat_service, "resolve_provider", lambda *a, **kw: mock)

    resp = await client.post(
        "/chat",
        json={
            "flow_json": SAMPLE_FLOW,
            "question": "What does prep_raw do?",
            "provider": "mock",
            "stream": True,
        },
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    text = resp.text

    # Order: meta MUST come first, then deltas, then final. Use index of
    # each marker rather than a regex to keep the assertion robust.
    meta_idx = text.find("event: meta")
    final_idx = text.find("event: final")
    assert 0 <= meta_idx < final_idx, "meta must precede final"

    # Extract the data payloads of the delta frames in order.
    delta_frames = []
    for block in text.split("event: delta")[1:]:
        for line in block.splitlines():
            if line.startswith("data: "):
                delta_frames.append(json.loads(line[len("data: "):])["text"])
                break
    assert delta_frames == deltas, (
        f"expected exactly {deltas!r}, got {delta_frames!r}"
    )

    # Final block contains the *concatenated* answer.
    final_block = text.split("event: final")[-1]
    final_payload_line = next(
        l for l in final_block.splitlines() if l.startswith("data: ")
    )
    final = json.loads(final_payload_line[len("data: "):])
    assert final["answer"] == "".join(deltas)


def test_provider_default_stream_complete_falls_back_to_chunker() -> None:
    """The base-class default stream_complete must reproduce the answer."""
    from py2dataiku.llm.providers import MockProvider as _Mock

    mock = _Mock(responses={"hello": "world peace forever"})
    out = list(mock.stream_complete("say hello", chunk_size=5))
    assert "".join(out) == "world peace forever"
    assert all(isinstance(s, str) for s in out)


def test_provider_stream_deltas_yields_in_order() -> None:
    """MockProvider with stream_deltas yields exactly those strings in order."""
    from py2dataiku.llm.providers import MockProvider as _Mock

    mock = _Mock(stream_deltas=["a", "b", "c"])
    assert list(mock.stream_complete("anything")) == ["a", "b", "c"]
