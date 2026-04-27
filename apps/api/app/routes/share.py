"""GET /share/{token} — public read-only flow viewer with rate limiting.

The rate limiter is a tiny in-memory token bucket keyed by client IP.
We hand-rolled it (rather than pulling in ``slowapi``) because:

* the API has no other rate-limited endpoints,
* the cap is small (10 req/minute) and an in-memory bucket suffices for
  the single-process deployment we target in M7,
* avoiding a Redis or extra-dep introduction matches the stated
  M7 constraint.
"""

from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from ..deps import Settings, get_flows_repo, get_settings
from ..schemas.flows import SavedFlowResponse
from ..security.share_links import InvalidShareToken
from ..security.share_links import verify as verify_share_token
from ..services.share_service import build_share_bundle, fixture_preview
from ..store import FlowsRepo

logger = logging.getLogger(__name__)

router = APIRouter(tags=["share"])


# ---------------------------------------------------------------------------
# Token bucket
# ---------------------------------------------------------------------------


class _TokenBucket:
    """Per-key token bucket.  Refills *capacity* tokens every *period* seconds.

    Buckets for keys that have been idle for more than ``_TTL`` seconds are
    evicted periodically to prevent unbounded memory growth in long-lived
    processes serving many unique client IPs.
    """

    # Evict buckets idle for more than 10 minutes.
    _TTL: float = 600.0

    def __init__(self, capacity: int, period: float = 60.0) -> None:
        self._capacity = float(capacity)
        self._period = float(period)
        self._tokens: dict[str, float] = defaultdict(lambda: self._capacity)
        self._last: dict[str, float] = {}
        self._lock = threading.Lock()
        # Use -inf so that the first request for any key triggers eviction check.
        self._last_eviction: float = float("-inf")

    def _evict_stale(self, now: float) -> None:
        """Evict idle buckets (caller must hold ``self._lock``)."""
        stale = [k for k, t in self._last.items() if now - t > self._TTL]
        for k in stale:
            self._tokens.pop(k, None)
            self._last.pop(k, None)
        self._last_eviction = now

    def allow(self, key: str, *, now: float | None = None) -> bool:
        """Consume one token for *key*; return False if the bucket is empty."""
        now = time.monotonic() if now is None else now
        rate = self._capacity / self._period
        with self._lock:
            # Periodic eviction: run at most once per TTL period.
            if now - self._last_eviction >= self._TTL:
                self._evict_stale(now)
            # New keys start with a full bucket; existing keys refill proportionally.
            last = self._last.get(key, now)
            elapsed = now - last
            current_tokens = self._tokens.get(key, self._capacity)
            refill = elapsed * rate
            self._tokens[key] = min(self._capacity, current_tokens + refill)
            self._last[key] = now
            if self._tokens[key] >= 1.0:
                self._tokens[key] -= 1.0
                return True
            return False

    def reset(self) -> None:
        with self._lock:
            self._tokens.clear()
            self._last.clear()


# Module-level singleton, sized from settings on first request.
_bucket: _TokenBucket | None = None
_bucket_lock = threading.Lock()


def _get_bucket(capacity: int) -> _TokenBucket:
    global _bucket
    with _bucket_lock:
        if _bucket is None or _bucket._capacity != float(capacity):
            _bucket = _TokenBucket(capacity=capacity, period=60.0)
        return _bucket


def reset_share_rate_limiter() -> None:
    """Clear the per-IP rate-limit state (used by the test suite)."""
    global _bucket
    with _bucket_lock:
        _bucket = None


def _client_ip(request: Request) -> str:
    """Return the best-effort client IP for rate-limit keying.

    When running behind a trusted reverse proxy, prefer the leftmost address in
    ``X-Forwarded-For`` (the original client IP).  Fall back to the direct
    peer address when the header is absent.

    Note: In production, restrict forwarded-IP trust to known proxy CIDR
    ranges to prevent spoofing.  This implementation accepts the header at
    face value, which is appropriate for single-trusted-proxy deployments.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For: client, proxy1, proxy2 — take the leftmost entry.
        first = forwarded_for.split(",")[0].strip()
        if first:
            return first
    return request.client.host if request.client else "unknown"


def _enforce_rate_limit(request: Request, settings: Settings) -> None:
    bucket = _get_bucket(settings.share_rate_limit_per_minute)
    if not bucket.allow(_client_ip(request)):
        raise HTTPException(
            status_code=429,
            detail=(
                f"Rate limit exceeded "
                f"({settings.share_rate_limit_per_minute} requests/minute)"
            ),
            headers={"Retry-After": "60"},
        )


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------


@router.get(
    "/share/{token}",
    response_model=SavedFlowResponse,
    summary="Public read-only view of a shared flow",
    responses={
        401: {"description": "Token signature is invalid"},
        404: {"description": "Token references an unknown flow"},
        410: {"description": "Token expired"},
        429: {"description": "Rate limit exceeded"},
    },
)
def get_share(
    token: str,
    request: Request,
    settings: Settings = Depends(get_settings),
    flows: FlowsRepo = Depends(get_flows_repo),
) -> SavedFlowResponse:
    _enforce_rate_limit(request, settings)
    try:
        payload = verify_share_token(token, secret=settings.secret_key)
    except InvalidShareToken as exc:
        msg = str(exc)
        if "expired" in msg:
            raise HTTPException(status_code=410, detail=msg) from exc
        raise HTTPException(status_code=401, detail=msg) from exc

    record = flows.get(payload.flow_id)
    if record is None:
        raise HTTPException(
            status_code=404, detail=f"flow '{payload.flow_id}' not found"
        )

    # If the share was minted with embedded fixtures, decode the gzip+base64
    # payload off-disk into a structured FixtureBundle so the recipient's
    # SharePage can offer "Run with embedded fixtures" without a second
    # round-trip. Decode failures degrade gracefully — the recipient still
    # gets the flow, just without fixtures attached.
    fixtures_payload: dict | None = None
    if record.fixtures_b64:
        try:
            from ..services.share_service import decode_bundle_gzip_b64

            fixtures_payload = dict(decode_bundle_gzip_b64(record.fixtures_b64))
        except ValueError:
            fixtures_payload = None

    return SavedFlowResponse(
        id=record.id,
        name=record.name,
        flow=record.flow,  # type: ignore[arg-type]
        created_at=record.created_at,
        updated_at=record.updated_at,
        tags=list(record.tags),
        fixtures=fixtures_payload,
    )


# ---------------------------------------------------------------------------
# Fixture-data preview + bundle endpoints
# ---------------------------------------------------------------------------


class FixturePreviewRequest(BaseModel):
    """Body for ``POST /share/fixtures/preview`` — accepts a flow inline."""

    flow: dict[str, object]
    n_rows: int = Field(default=5, ge=0, le=25)


@router.post(
    "/share/fixtures/preview",
    summary="Preview fixture rows for a flow's input datasets",
)
def post_fixture_preview(body: FixturePreviewRequest) -> dict[str, object]:
    """Return a preview pane payload — each input dataset + a small row sample.

    Used by the Share modal's "Include fixture data" checkbox to populate
    the preview pane on the right.  Backend-only generation keeps the
    synthesizer code off the wire and ensures determinism.
    """
    return fixture_preview(body.flow, n_rows=body.n_rows)


class FixtureBundleRequest(BaseModel):
    """Body for ``POST /share/fixtures/bundle`` — full bundle for a flow."""

    flow: dict[str, object]
    n_rows: int = Field(default=100, ge=0, le=100)


@router.post(
    "/share/fixtures/bundle",
    summary="Generate a full fixture-data bundle for a flow (up to 100 rows/input)",
)
def post_fixture_bundle(body: FixtureBundleRequest) -> dict[str, object]:
    """Return the full ``{n_rows, datasets: {name: [rows]}}`` bundle.

    The bundle is suitable for embedding in a self-contained share payload
    or attaching as part of a downloadable archive.  The recipient can
    replay the flow against the embedded rows without sourcing the data
    themselves.
    """
    bundle = build_share_bundle(body.flow, n_rows=body.n_rows)
    return dict(bundle)
