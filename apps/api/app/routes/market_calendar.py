"""GET /market-calendar — static venue settle-window schedule.

Returns the canonical close / settle windows for the major venues a
front-office trading desk cares about. The Deploy page reads this and
disables the Deploy button when the *current* clock falls inside any
venue's settle window.

Honest provenance: this is a *static schedule for v1*. Real venue
calendars (holidays, late opens, ad-hoc cutovers) require a market-data
integration which is on the Wave 5+ backlog. The shape is deliberately
simple so a future provider can drop into the same response model.

Times are returned in IANA-named local time + UTC offset for the venue.
The frontend converts to the user's wall-clock for the UI; the schedule
itself is timezone-aware so the conversion is unambiguous.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Response
from pydantic import BaseModel, Field

router = APIRouter(prefix="/market-calendar", tags=["market-calendar"])

_CACHE_CONTROL = "public, max-age=300"


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------


class MarketSession(BaseModel):
    """A single venue close / settle window."""

    venue: str = Field(..., description="Venue / exchange ticker, e.g. NYMEX")
    venue_name: str = Field(..., description="Human-readable venue name")
    product: str = Field(..., description="Product family (e.g. 'WTI Crude', 'PJM RT')")
    timezone: str = Field(..., description="IANA timezone for the venue close")
    close_time: str = Field(..., description="HH:MM local close time")
    settle_window_minutes: int = Field(
        ...,
        ge=0,
        description=(
            "Half-window around the close — Deploy is disabled within "
            "+/- this many minutes of close_time."
        ),
    )
    note: str = Field(..., description="Why a deploy in-window is risky.")


class MarketCalendarResponse(BaseModel):
    """Static venue schedule. Frontend converts to user wall-clock."""

    schedule_kind: Literal["static-v1"] = "static-v1"
    note: str = Field(
        default=(
            "Static schedule for v1; real venue calendar integration is "
            "Wave 5+. Holidays, late opens, and ad-hoc cutovers are not "
            "honoured. Treat the close times as a guard-rail, not a contract."
        )
    )
    sessions: list[MarketSession]


# ---------------------------------------------------------------------------
# Static schedule
# ---------------------------------------------------------------------------


# Canonical major venues a US/EU commodity desk cares about. Times verified
# against each venue's published trading hours. settle_window_minutes is
# 30 by default — the standard "no deploys 30 min around close" rule the
# desk runs internally.
_STATIC_SCHEDULE: list[MarketSession] = [
    MarketSession(
        venue="NYMEX",
        venue_name="CME Globex — NYMEX",
        product="WTI Crude (CL) prompt",
        timezone="America/New_York",
        close_time="14:30",
        settle_window_minutes=30,
        note="WTI prompt settle. Avoid deploys that touch crude pricing pipes.",
    ),
    MarketSession(
        venue="ICE-EUR",
        venue_name="ICE Futures Europe",
        product="Brent Crude (B) prompt",
        timezone="Europe/London",
        close_time="19:30",
        settle_window_minutes=30,
        note="Brent settlement. Affects WTI-Brent and freight-netback flows.",
    ),
    MarketSession(
        venue="ICE-NYISO",
        venue_name="NYMEX Henry Hub Natural Gas",
        product="Henry Hub (NG) prompt",
        timezone="America/New_York",
        close_time="14:30",
        settle_window_minutes=30,
        note="Gas settlement. Heat-rate / basis flows hit this.",
    ),
    MarketSession(
        venue="PJM",
        venue_name="PJM Interconnection",
        product="Real-Time LMP close",
        timezone="America/New_York",
        close_time="23:55",
        settle_window_minutes=15,
        note=(
            "PJM RT settlement run. Holding off on RT-LMP-touching jobs "
            "avoids a partial-window read."
        ),
    ),
    MarketSession(
        venue="ERCOT",
        venue_name="ERCOT MIS",
        product="Real-Time SPP close",
        timezone="America/Chicago",
        close_time="23:55",
        settle_window_minutes=15,
        note="ERCOT RT settlement. Same reason as PJM.",
    ),
    MarketSession(
        venue="EEX",
        venue_name="EEX Power Spot",
        product="EPEX day-ahead auction",
        timezone="Europe/Berlin",
        close_time="12:00",
        settle_window_minutes=20,
        note="DA auction gate-closure. EU power flows are sensitive here.",
    ),
    MarketSession(
        venue="ICE-TTF",
        venue_name="ICE TTF Gas",
        product="TTF prompt",
        timezone="Europe/Amsterdam",
        close_time="17:00",
        settle_window_minutes=30,
        note="TTF settle. Affects TTF-NBP and JKM-TTF basis pipelines.",
    ),
    MarketSession(
        venue="JKM",
        venue_name="Platts JKM",
        product="JKM LNG MOC window",
        timezone="Asia/Singapore",
        close_time="16:30",
        settle_window_minutes=15,
        note="JKM Platts MOC. Affects LNG-arb basis flows.",
    ),
]


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=MarketCalendarResponse,
    summary="Static venue settle-window schedule for the Deploy timer",
)
def get_market_calendar(response: Response) -> MarketCalendarResponse:
    """Return the static venue schedule.

    The frontend's Deploy page reads this once on mount and re-evaluates
    in-window status against the wall clock every 30 s.
    """
    response.headers["Cache-Control"] = _CACHE_CONTROL
    return MarketCalendarResponse(sessions=_STATIC_SCHEDULE)
