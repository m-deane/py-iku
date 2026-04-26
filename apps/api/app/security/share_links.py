"""HMAC-signed share-link tokens.

The token is a base64url-encoded JSON payload of the form::

    {"flow_id": "...", "exp": 1730000000, "scopes": ["read"], "sig": "<hex>"}

where ``sig = HMAC-SHA256(secret, f"{flow_id}.{exp}.{scopes_canonical}")``
and ``scopes_canonical`` is a comma-joined, sorted list of scopes.

``verify`` raises :class:`InvalidShareToken` for any malformed,
tampered, or expired token; otherwise returns a :class:`SharePayload`.
"""

from __future__ import annotations

import base64
import hmac
import json
import time
from dataclasses import dataclass
from hashlib import sha256


class InvalidShareToken(Exception):
    """Raised when a share token cannot be verified."""


@dataclass(frozen=True)
class SharePayload:
    """Decoded share-link payload."""

    flow_id: str
    exp: int
    scopes: tuple[str, ...]


def _canonical_scopes(scopes: list[str] | tuple[str, ...]) -> str:
    return ",".join(sorted(str(s) for s in scopes))


def _sign_message(secret: str, message: str) -> str:
    return hmac.new(secret.encode("utf-8"), message.encode("utf-8"), sha256).hexdigest()


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(token: str) -> bytes:
    pad = "=" * ((4 - len(token) % 4) % 4)
    return base64.urlsafe_b64decode((token + pad).encode("ascii"))


def sign(
    flow_id: str, *, ttl_seconds: int, scopes: list[str], secret: str
) -> str:
    """Create a base64url-encoded signed share token for *flow_id*."""
    if ttl_seconds <= 0:
        raise ValueError("ttl_seconds must be positive")
    if not flow_id:
        raise ValueError("flow_id must be non-empty")
    exp = int(time.time()) + int(ttl_seconds)
    canonical = _canonical_scopes(scopes)
    sig = _sign_message(secret, f"{flow_id}.{exp}.{canonical}")
    payload = {
        "flow_id": flow_id,
        "exp": exp,
        "scopes": list(scopes),
        "sig": sig,
    }
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return _b64url_encode(raw)


def verify(token: str, *, secret: str) -> SharePayload:
    """Verify *token* against *secret*; return the payload or raise."""
    if not token:
        raise InvalidShareToken("empty token")
    try:
        raw = _b64url_decode(token)
    except (ValueError, TypeError) as exc:
        raise InvalidShareToken("token is not valid base64url") from exc

    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidShareToken("token payload is not valid JSON") from exc

    if not isinstance(data, dict):
        raise InvalidShareToken("token payload must be an object")

    try:
        flow_id = str(data["flow_id"])
        exp = int(data["exp"])
        scopes = list(data.get("scopes") or [])
        sig = str(data["sig"])
    except (KeyError, TypeError, ValueError) as exc:
        raise InvalidShareToken("token payload is missing required fields") from exc

    expected = _sign_message(secret, f"{flow_id}.{exp}.{_canonical_scopes(scopes)}")
    if not hmac.compare_digest(expected, sig):
        raise InvalidShareToken("signature mismatch")

    if int(time.time()) >= exp:
        raise InvalidShareToken("token expired")

    return SharePayload(flow_id=flow_id, exp=exp, scopes=tuple(scopes))
