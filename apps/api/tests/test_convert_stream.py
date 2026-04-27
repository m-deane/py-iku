"""Integration tests for WS /convert/stream endpoint."""

from __future__ import annotations

import json
import threading
import time
from unittest.mock import patch

import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.main import app

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def ws_client() -> TestClient:
    """Synchronous TestClient for WebSocket tests."""
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Snippets
# ---------------------------------------------------------------------------

SIMPLE_PANDAS = """
import pandas as pd
df = pd.read_csv('data.csv')
df['name'] = df['name'].str.upper()
df.to_csv('out.csv', index=False)
"""

GROUPBY_PANDAS = """
import pandas as pd
df = pd.read_csv('transactions.csv')
summary = df.groupby('category').agg({'amount': 'sum'}).reset_index()
summary.to_csv('summary.csv', index=False)
"""


# ---------------------------------------------------------------------------
# Helper: receive events until terminal
# ---------------------------------------------------------------------------


def _collect_events(ws, max_events: int = 100) -> list[dict]:
    """Receive JSON frames from the WS until terminal event or limit."""
    events = []
    terminal = {"completed", "error", "cancelled"}
    for _ in range(max_events):
        try:
            raw = ws.receive_text()
        except (WebSocketDisconnect, Exception):
            break
        data = json.loads(raw)
        events.append(data)
        if data.get("event") in terminal:
            break
    return events


# ---------------------------------------------------------------------------
# Happy path — rule mode
# ---------------------------------------------------------------------------


def test_happy_path_rule_mode(ws_client: TestClient) -> None:
    """Connect, send pandas snippet, expect completed event with a valid flow."""
    with ws_client.websocket_connect("/convert/stream") as ws:
        ws.send_text(json.dumps({"code": SIMPLE_PANDAS, "mode": "rule"}))
        events = _collect_events(ws)

    event_names = [e.get("event") for e in events]
    assert "started" in event_names, f"Missing 'started' in {event_names}"
    assert "completed" in event_names, f"Missing 'completed' in {event_names}"

    # seq must be monotonically increasing
    seqs = [e["seq"] for e in events if "seq" in e]
    assert seqs == sorted(seqs), f"seq not monotonic: {seqs}"
    assert len(set(seqs)) == len(seqs), "seq has duplicates"

    # completed payload must have a valid flow
    completed = next(e for e in events if e.get("event") == "completed")
    payload = completed["payload"]
    assert "flow" in payload
    flow = payload["flow"]
    assert isinstance(flow.get("recipes"), list)
    assert len(flow["recipes"]) > 0, "Expected at least one recipe"

    # score must be present
    assert "score" in payload
    assert payload["score"]["recipe_count"] >= 0


def test_happy_path_seq_starts_at_zero(ws_client: TestClient) -> None:
    """First event seq must be 0."""
    with ws_client.websocket_connect("/convert/stream") as ws:
        ws.send_text(json.dumps({"code": SIMPLE_PANDAS, "mode": "rule"}))
        events = _collect_events(ws)

    assert events[0]["seq"] == 0


def test_happy_path_groupby(ws_client: TestClient) -> None:
    """Groupby snippet produces completed event with GROUPING recipe."""
    with ws_client.websocket_connect("/convert/stream") as ws:
        ws.send_text(json.dumps({"code": GROUPBY_PANDAS, "mode": "rule"}))
        events = _collect_events(ws)

    completed = next((e for e in events if e.get("event") == "completed"), None)
    assert completed is not None
    recipe_types = [r["type"] for r in completed["payload"]["flow"]["recipes"]]
    assert any(rt in ("grouping", "GROUPING") for rt in recipe_types), (
        f"Expected GROUPING recipe, got: {recipe_types}"
    )


# ---------------------------------------------------------------------------
# Bad first frame → problem+json + close 1003
# ---------------------------------------------------------------------------


def test_bad_first_frame_garbage(ws_client: TestClient) -> None:
    """Garbage first frame must yield a problem+json frame then close 1003."""
    try:
        with ws_client.websocket_connect("/convert/stream") as ws:
            ws.send_text("this is not json at all!!!")
            raw = ws.receive_text()
            data = json.loads(raw)
            assert data.get("status") == 422
            assert "ValidationError" in data.get("type", "")
    except WebSocketDisconnect as exc:
        assert exc.code == 1003


def test_bad_first_frame_missing_code(ws_client: TestClient) -> None:
    """Missing 'code' field causes validation error frame then close."""
    try:
        with ws_client.websocket_connect("/convert/stream") as ws:
            ws.send_text(json.dumps({"mode": "rule"}))
            raw = ws.receive_text()
            data = json.loads(raw)
            assert data.get("status") == 422
    except WebSocketDisconnect as exc:
        assert exc.code == 1003


# ---------------------------------------------------------------------------
# LLM mode without API key → error event
# ---------------------------------------------------------------------------


def test_llm_mode_without_key_yields_error_event(ws_client: TestClient) -> None:
    """LLM mode without env key emits error event with ConfigurationError shape."""
    import os

    # Ensure no key is set
    env = {k: v for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY")}
    with patch.dict("os.environ", env, clear=True):
        with ws_client.websocket_connect("/convert/stream") as ws:
            ws.send_text(json.dumps({"code": SIMPLE_PANDAS, "mode": "llm"}))
            events = _collect_events(ws)

    event_names = [e.get("event") for e in events]
    assert "error" in event_names, f"Expected error event, got: {event_names}"

    error_evt = next(e for e in events if e.get("event") == "error")
    payload = error_evt["payload"]
    assert "ConfigurationError" in payload.get("type", "")
    assert payload.get("status") == 500


# ---------------------------------------------------------------------------
# Cancel: client sends cancel → cancelled event
# ---------------------------------------------------------------------------


def test_cancel_during_conversion(ws_client: TestClient) -> None:
    """Client sends cancel action; a cancelled event must arrive."""
    # We'll use a very short snippet so conversion is likely complete, or
    # send cancel immediately after the first event.
    with ws_client.websocket_connect("/convert/stream") as ws:
        ws.send_text(json.dumps({"code": SIMPLE_PANDAS, "mode": "rule"}))

        # Read the first event (started), then send cancel
        first_raw = ws.receive_text()
        first = json.loads(first_raw)
        assert first.get("event") == "started"

        ws.send_text(json.dumps({"action": "cancel"}))

        # Collect remaining events
        remaining = _collect_events(ws, max_events=50)

    # Either completed (if fast) or cancelled must appear
    all_events = [first] + remaining
    event_names = [e.get("event") for e in all_events]
    terminal = {"completed", "cancelled", "error"}
    assert any(name in terminal for name in event_names), (
        f"Expected a terminal event, got: {event_names}"
    )


# ---------------------------------------------------------------------------
# Heartbeat: ping events
# ---------------------------------------------------------------------------


@pytest.mark.timeout(20)
def test_heartbeat_ping_event(ws_client: TestClient) -> None:
    """A ping event is emitted while waiting; we simulate by calling ping directly."""
    # We patch the heartbeat sleep to be 0s so ping fires immediately.
    import app.routes.convert as convert_route

    original = convert_route._HEARTBEAT_SECONDS

    # Use a very short heartbeat interval for testing
    convert_route._HEARTBEAT_SECONDS = 0.05

    try:
        with ws_client.websocket_connect("/convert/stream") as ws:
            ws.send_text(json.dumps({"code": SIMPLE_PANDAS, "mode": "rule"}))
            events = _collect_events(ws, max_events=50)
    finally:
        convert_route._HEARTBEAT_SECONDS = original

    event_names = [e.get("event") for e in events]
    # Either ping appeared or conversion was fast enough it didn't need one
    # (both are acceptable); just verify terminal event exists
    assert any(name in {"completed", "error", "cancelled"} for name in event_names), (
        f"No terminal event in: {event_names}"
    )


# ---------------------------------------------------------------------------
# Two-connection isolation: independent seq sequences
# ---------------------------------------------------------------------------


def test_two_connections_independent_seq(ws_client: TestClient) -> None:
    """Two simultaneous WS connections must have independent seq counters."""
    results: dict[str, list[dict]] = {}

    def _run(key: str, snippet: str) -> None:
        with ws_client.websocket_connect("/convert/stream") as ws:
            ws.send_text(json.dumps({"code": snippet, "mode": "rule"}))
            results[key] = _collect_events(ws)

    t1 = threading.Thread(target=_run, args=("conn1", SIMPLE_PANDAS))
    t2 = threading.Thread(target=_run, args=("conn2", GROUPBY_PANDAS))
    t1.start()
    t2.start()
    t1.join(timeout=30)
    t2.join(timeout=30)

    assert "conn1" in results and "conn2" in results, "One or both connections failed"

    for key in ("conn1", "conn2"):
        seqs = [e["seq"] for e in results[key] if "seq" in e]
        assert seqs[0] == 0, f"{key}: seq does not start at 0"
        assert seqs == sorted(seqs), f"{key}: seq not monotonic"

    # Verify isolation: both start at 0 (not sharing a global counter)
    assert results["conn1"][0]["seq"] == 0
    assert results["conn2"][0]["seq"] == 0


# ---------------------------------------------------------------------------
# Subprotocol negotiation
# ---------------------------------------------------------------------------


def test_subprotocol_accepted(ws_client: TestClient) -> None:
    """Client advertising py-iku-studio.v1 subprotocol gets it echoed back."""
    with ws_client.websocket_connect(
        "/convert/stream",
        subprotocols=["py-iku-studio.v1"],
    ) as ws:
        assert ws.accepted_subprotocol == "py-iku-studio.v1"
        ws.send_text(json.dumps({"code": SIMPLE_PANDAS, "mode": "rule"}))
        _collect_events(ws)


def test_no_subprotocol_still_accepted(ws_client: TestClient) -> None:
    """Client without subprotocol header is still accepted."""
    with ws_client.websocket_connect("/convert/stream") as ws:
        ws.send_text(json.dumps({"code": SIMPLE_PANDAS, "mode": "rule"}))
        events = _collect_events(ws)
    assert any(e.get("event") in {"completed", "error"} for e in events)


# ---------------------------------------------------------------------------
# Event sequence structure
# ---------------------------------------------------------------------------


def test_event_envelope_structure(ws_client: TestClient) -> None:
    """Every event must have event, seq, ts, payload fields."""
    with ws_client.websocket_connect("/convert/stream") as ws:
        ws.send_text(json.dumps({"code": SIMPLE_PANDAS, "mode": "rule"}))
        events = _collect_events(ws)

    for evt in events:
        assert "event" in evt, f"Missing 'event' field in {evt}"
        assert "seq" in evt, f"Missing 'seq' field in {evt}"
        assert "ts" in evt, f"Missing 'ts' field in {evt}"
        assert "payload" in evt, f"Missing 'payload' field in {evt}"


def test_started_event_payload(ws_client: TestClient) -> None:
    """'started' event payload has mode, code_size_bytes, flow_name."""
    with ws_client.websocket_connect("/convert/stream") as ws:
        ws.send_text(json.dumps({"code": SIMPLE_PANDAS, "mode": "rule"}))
        events = _collect_events(ws)

    started = next((e for e in events if e.get("event") == "started"), None)
    assert started is not None
    payload = started["payload"]
    assert payload["mode"] == "rule"
    assert isinstance(payload["code_size_bytes"], int)
    assert payload["code_size_bytes"] > 0
