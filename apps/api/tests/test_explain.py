"""Tests for /explain-recipe — uses MockProvider, never hits real APIs.

The MockProvider canned-response shape used here is a SINGLE JSON object with
the three popover fields. The shape mirrors Sprint 4B's chat tests
(``responses={"<substring>": "<canned>"}``) — the substring "EXPLAIN" appears
verbatim in the user prompt so MockProvider's match keys land deterministically.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from py2dataiku.llm.providers import MockProvider

from app.routes import explain as explain_route
from app.services import explain as explain_service
from app.services.explain import (
    ExplainCache,
    parse_explain_payload,
    recipe_cache_key,
)

# ---------------------------------------------------------------------------
# Sample fixtures — match the trading-domain register the service expects.
# ---------------------------------------------------------------------------

GROUPING_RECIPE: dict[str, Any] = {
    "name": "agg_pnl_by_book",
    "type": "GROUPING",
    "inputs": ["enriched_trades"],
    "outputs": ["pnl_by_book"],
    "settings": {
        "group_columns": ["book", "trade_date"],
        "aggregations": [{"column": "pnl_usd", "fn": "SUM"}],
    },
    "confidence": "high",
}

PYTHON_RECIPE: dict[str, Any] = {
    "name": "custom_blotter",
    "type": "PYTHON",
    "inputs": ["raw_trades"],
    "outputs": ["normalised_blotter"],
    "settings": {"code": "df['mid'] = (df['bid'] + df['ask']) / 2"},
    "confidence": "low",
}

CANNED_PAYLOAD = {
    "what_this_does": "Aggregates rows in a GROUPING recipe by book and date "
    "to compute total P&L per book.",
    "trading_context": "Used in EOD MtM rollups to collapse the trade blotter "
    "into per-book P&L for desk reporting.",
    "watch_out_for": "If trade_date isn't normalised to settle timezone first, "
    "rows can land in the wrong day's bucket.",
}


def _patch_provider(monkeypatch, payload: dict[str, str]) -> MockProvider:
    """Force ``resolve_provider`` to return a MockProvider with canned JSON."""
    canned_text = json.dumps(payload)
    mock = MockProvider(responses={"EXPLAIN": canned_text, "JSON": canned_text})
    monkeypatch.setattr(explain_service, "resolve_provider", lambda *a, **kw: mock)
    return mock


# ---------------------------------------------------------------------------
# Pure-unit tests — no HTTP, no fixtures.
# ---------------------------------------------------------------------------


def test_recipe_cache_key_is_stable_across_renames() -> None:
    """Renaming, reordering inputs/outputs, or wobbling confidence MUST NOT
    bust the cache. Settings must."""
    a = dict(GROUPING_RECIPE)
    b = dict(GROUPING_RECIPE)
    b["name"] = "different_name"
    b["confidence"] = "medium"
    b["reasoning"] = "irrelevant prose"
    type_a, key_a = recipe_cache_key(a)
    type_b, key_b = recipe_cache_key(b)
    assert type_a == "GROUPING" == type_b
    assert key_a == key_b

    # Mutating a setting must change the key.
    c = dict(GROUPING_RECIPE)
    c["settings"] = {**GROUPING_RECIPE["settings"], "group_columns": ["book"]}
    _, key_c = recipe_cache_key(c)
    assert key_c != key_a


def test_parse_explain_payload_strips_code_fences() -> None:
    fenced = "```json\n" + json.dumps(CANNED_PAYLOAD) + "\n```"
    parsed = parse_explain_payload(fenced)
    assert parsed["what_this_does"] == CANNED_PAYLOAD["what_this_does"]
    assert parsed["trading_context"] == CANNED_PAYLOAD["trading_context"]
    assert parsed["watch_out_for"] == CANNED_PAYLOAD["watch_out_for"]


def test_parse_explain_payload_rejects_missing_fields() -> None:
    with pytest.raises(Exception):
        parse_explain_payload(json.dumps({"what_this_does": "x"}))


def test_explain_cache_round_trips(tmp_path) -> None:  # type: ignore[no-untyped-def]
    cache = ExplainCache(base_dir=tmp_path)
    assert cache.get("missing") is None
    cache.put("k1", "GROUPING", {"what_this_does": "x"})
    got = cache.get("k1")
    assert got == {"what_this_does": "x"}

    # Re-put updates the latest (newest-wins).
    cache.put("k1", "GROUPING", {"what_this_does": "y"})
    assert cache.get("k1") == {"what_this_does": "y"}


# ---------------------------------------------------------------------------
# HTTP integration — same flow + cost-meter + audit-log plumbing as /chat.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_explain_recipe_returns_three_bullets(client, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Round-trip: recipe in → 3-bullet explanation + cache_key + cache_hit=False."""
    _patch_provider(monkeypatch, CANNED_PAYLOAD)

    resp = await client.post(
        "/explain-recipe",
        json={"recipe": GROUPING_RECIPE, "provider": "mock"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["what_this_does"] == CANNED_PAYLOAD["what_this_does"]
    assert body["trading_context"] == CANNED_PAYLOAD["trading_context"]
    assert body["watch_out_for"] == CANNED_PAYLOAD["watch_out_for"]
    assert body["recipe_type"] == "GROUPING"
    assert body["cache_hit"] is False
    assert body["cost_usd"] == 0.0  # mock provider
    assert body["model"] == "mock"
    assert body["cache_key"].startswith("GROUPING:")


@pytest.mark.asyncio
async def test_explain_recipe_cache_hit_skips_llm(client, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Second call with the same recipe shape returns cache_hit=True and the
    LLM is not consulted (MockProvider.calls stays at 1)."""
    mock = _patch_provider(monkeypatch, CANNED_PAYLOAD)

    first = await client.post(
        "/explain-recipe",
        json={"recipe": GROUPING_RECIPE, "provider": "mock"},
    )
    assert first.status_code == 200
    assert first.json()["cache_hit"] is False
    assert len(mock.calls) == 1

    # Same recipe, renamed → cache key unchanged → cache hit, no extra call.
    same_shape = dict(GROUPING_RECIPE)
    same_shape["name"] = "renamed_recipe"
    same_shape["confidence"] = "medium"
    second = await client.post(
        "/explain-recipe",
        json={"recipe": same_shape, "provider": "mock"},
    )
    assert second.status_code == 200
    second_body = second.json()
    assert second_body["cache_hit"] is True
    assert second_body["cache_key"] == first.json()["cache_key"]
    assert len(mock.calls) == 1, "cache hit must not invoke the provider"


@pytest.mark.asyncio
async def test_explain_recipe_cache_miss_on_different_settings(
    client, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    """Mutating settings invalidates the cache entry → second call hits the LLM."""
    mock = _patch_provider(monkeypatch, CANNED_PAYLOAD)

    first = await client.post(
        "/explain-recipe",
        json={"recipe": GROUPING_RECIPE, "provider": "mock"},
    )
    assert first.status_code == 200

    different = dict(GROUPING_RECIPE)
    different["settings"] = {
        **GROUPING_RECIPE["settings"],
        "group_columns": ["book"],
    }
    second = await client.post(
        "/explain-recipe",
        json={"recipe": different, "provider": "mock"},
    )
    assert second.status_code == 200
    second_body = second.json()
    assert second_body["cache_hit"] is False
    assert second_body["cache_key"] != first.json()["cache_key"]
    assert len(mock.calls) == 2


@pytest.mark.asyncio
async def test_explain_recipe_logs_to_llm_history(client, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Successful explain calls land in /llm-history with feature='explain'."""
    _patch_provider(monkeypatch, CANNED_PAYLOAD)
    await client.post(
        "/explain-recipe",
        json={
            "recipe": PYTHON_RECIPE,
            "provider": "mock",
            "flow_id": "flow-explain-1",
        },
    )
    hist = await client.get("/llm-history")
    body = hist.json()
    rows = [r for r in body["records"] if r["feature"] == "explain"]
    assert rows, "expected at least one llm-history row with feature=explain"
    last = rows[0]
    assert last["status"] == "success"
    assert last["flow_id"] == "flow-explain-1"
    assert last["extra"]["recipe_type"] == "PYTHON"
    assert last["extra"]["cache_hit"] is False


@pytest.mark.asyncio
async def test_explain_recipe_cache_hit_logs_zero_cost(
    client, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    """Cache hits are still audited but at zero cost so the cost-meter is honest."""
    _patch_provider(monkeypatch, CANNED_PAYLOAD)
    await client.post(
        "/explain-recipe",
        json={"recipe": GROUPING_RECIPE, "provider": "mock"},
    )
    await client.post(
        "/explain-recipe",
        json={"recipe": GROUPING_RECIPE, "provider": "mock"},
    )
    hist = await client.get("/llm-history")
    rows = [r for r in hist.json()["records"] if r["feature"] == "explain"]
    assert len(rows) == 2
    cache_hit_row = next(r for r in rows if r["extra"]["cache_hit"])
    assert cache_hit_row["cost_usd"] == 0.0
    assert cache_hit_row["provider"] == "cache"


@pytest.mark.asyncio
async def test_explain_recipe_validation_error_on_empty_recipe(client) -> None:  # type: ignore[no-untyped-def]
    resp = await client.post(
        "/explain-recipe",
        json={"provider": "mock"},
    )
    assert resp.status_code == 422


def test_route_module_exposes_reset_singleton() -> None:
    """Sanity: the conftest hook depends on this symbol existing."""
    assert callable(explain_route.reset_explain_cache_singleton)
