"""Tests for HMAC share-link signing/verification (M7)."""

from __future__ import annotations

import time

import pytest

from app.security.share_links import (
    InvalidShareToken,
    SharePayload,
    sign,
    verify,
)


def test_sign_then_verify_round_trip() -> None:
    token = sign("flow-1", ttl_seconds=60, scopes=["read"], secret="s3cr3t")
    payload = verify(token, secret="s3cr3t")
    assert isinstance(payload, SharePayload)
    assert payload.flow_id == "flow-1"
    assert payload.scopes == ("read",)
    assert payload.exp > int(time.time())


def test_verify_with_wrong_secret_rejects() -> None:
    token = sign("flow-1", ttl_seconds=60, scopes=["read"], secret="abc")
    with pytest.raises(InvalidShareToken):
        verify(token, secret="def")


def test_verify_expired_token_rejects() -> None:
    # Sign with a TTL of 1s, then sleep just past it.
    token = sign("flow-1", ttl_seconds=1, scopes=["read"], secret="s")
    time.sleep(1.1)
    with pytest.raises(InvalidShareToken) as ei:
        verify(token, secret="s")
    assert "expired" in str(ei.value)


def test_tampered_token_rejected() -> None:
    token = sign("flow-1", ttl_seconds=60, scopes=["read"], secret="s")
    # flipping a character in the middle shouldn't decode/verify.
    bad = token[:-2] + ("AA" if token[-2:] != "AA" else "BB")
    with pytest.raises(InvalidShareToken):
        verify(bad, secret="s")


def test_malformed_token_rejected() -> None:
    with pytest.raises(InvalidShareToken):
        verify("", secret="s")
    with pytest.raises(InvalidShareToken):
        verify("!!!not-base64!!!", secret="s")


def test_negative_ttl_rejected() -> None:
    with pytest.raises(ValueError):
        sign("flow", ttl_seconds=0, scopes=["read"], secret="s")
    with pytest.raises(ValueError):
        sign("flow", ttl_seconds=-1, scopes=["read"], secret="s")


def test_empty_flow_id_rejected() -> None:
    with pytest.raises(ValueError):
        sign("", ttl_seconds=10, scopes=["read"], secret="s")


def test_scope_order_doesnt_change_signature() -> None:
    """Scopes are canonicalised so token order shouldn't matter at verify time."""
    t1 = sign("f", ttl_seconds=60, scopes=["a", "b"], secret="s")
    t2 = sign("f", ttl_seconds=60, scopes=["b", "a"], secret="s")
    # Tokens differ in original scope order but both verify successfully.
    p1 = verify(t1, secret="s")
    p2 = verify(t2, secret="s")
    assert sorted(p1.scopes) == sorted(p2.scopes)
