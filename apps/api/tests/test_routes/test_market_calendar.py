"""Tests for GET /market-calendar — Sprint 4 settle-window guard."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_market_calendar_returns_static_v1_kind(client) -> None:  # type: ignore[no-untyped-def]
    """The endpoint returns a typed ``schedule_kind`` so the frontend can branch."""
    response = await client.get("/market-calendar")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["schedule_kind"] == "static-v1"


@pytest.mark.asyncio
async def test_market_calendar_carries_staleness_note(client) -> None:  # type: ignore[no-untyped-def]
    """The 'static schedule for v1' provenance disclaimer must ship in the payload."""
    response = await client.get("/market-calendar")
    body = response.json()
    note = body["note"]
    assert "static schedule" in note.lower()
    assert "wave 5" in note.lower() or "v1" in note.lower()


@pytest.mark.asyncio
async def test_market_calendar_lists_real_venues(client) -> None:  # type: ignore[no-untyped-def]
    """At least the four headline venues a US/EU desk cares about are present."""
    response = await client.get("/market-calendar")
    body = response.json()
    venues = {s["venue"] for s in body["sessions"]}
    # Real venue tickers, no synthetic placeholders.
    must_have = {"NYMEX", "ICE-EUR", "PJM", "ERCOT"}
    missing = must_have - venues
    assert not missing, f"Missing canonical venues: {missing}"


@pytest.mark.asyncio
async def test_market_calendar_session_fields(client) -> None:  # type: ignore[no-untyped-def]
    """Each session carries the fields the frontend Deploy gate expects."""
    response = await client.get("/market-calendar")
    body = response.json()
    required = {
        "venue",
        "venue_name",
        "product",
        "timezone",
        "close_time",
        "settle_window_minutes",
        "note",
    }
    for s in body["sessions"]:
        missing = required - set(s.keys())
        assert not missing, f"Session {s.get('venue')!r} missing {missing}"
        # Sanity: HH:MM format.
        assert ":" in s["close_time"]
        assert isinstance(s["settle_window_minutes"], int)
        assert s["settle_window_minutes"] >= 0


@pytest.mark.asyncio
async def test_market_calendar_carries_cache_header(client) -> None:  # type: ignore[no-untyped-def]
    """The schedule is static enough to cache for 5 min."""
    response = await client.get("/market-calendar")
    assert response.status_code == 200
    assert response.headers.get("Cache-Control") == "public, max-age=300"


@pytest.mark.asyncio
async def test_market_calendar_timezones_are_iana(client) -> None:  # type: ignore[no-untyped-def]
    """All timezones are real IANA names so the frontend Intl call doesn't blow up."""
    response = await client.get("/market-calendar")
    body = response.json()
    for s in body["sessions"]:
        # IANA names contain a slash; e.g. ``America/New_York``.
        assert "/" in s["timezone"], f"Bad timezone {s['timezone']!r}"
