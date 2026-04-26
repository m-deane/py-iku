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

from ..deps import Settings, get_flows_repo, get_settings
from ..schemas.flows import SavedFlowResponse
from ..security.share_links import InvalidShareToken
from ..security.share_links import verify as verify_share_token
from ..store import FlowsRepo

logger = logging.getLogger(__name__)

router = APIRouter(tags=["share"])


# ---------------------------------------------------------------------------
# Token bucket
# ---------------------------------------------------------------------------


class _TokenBucket:
    """Per-key token bucket.  Refills *capacity* tokens every *period* seconds."""

    def __init__(self, capacity: int, period: float = 60.0) -> None:
        self._capacity = float(capacity)
        self._period = float(period)
        self._tokens: dict[str, float] = defaultdict(lambda: self._capacity)
        self._last: dict[str, float] = defaultdict(lambda: time.monotonic())
        self._lock = threading.Lock()

    def allow(self, key: str, *, now: float | None = None) -> bool:
        """Consume one token for *key*; return False if the bucket is empty."""
        now = time.monotonic() if now is None else now
        rate = self._capacity / self._period
        with self._lock:
            elapsed = now - self._last[key]
            refill = elapsed * rate
            self._tokens[key] = min(self._capacity, self._tokens[key] + refill)
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
    return SavedFlowResponse(
        id=record.id,
        name=record.name,
        flow=record.flow,  # type: ignore[arg-type]
        created_at=record.created_at,
        updated_at=record.updated_at,
        tags=list(record.tags),
    )
