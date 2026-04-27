"""Tests for /suggest-mapping — uses MockProvider, never hits real APIs.

The MockProvider canned-response shape used here is a SINGLE JSON object with
fields {confidence, suggested_recipe_type, transformed_pandas, reasoning}.
Mirrors Sprint 4B's chat-test pattern: ``responses={"<substring>": "<canned>"}``
where the substring "Suggest a mapping" appears verbatim in the user prompt.
"""

from __future__ import annotations

import json

import pytest
from py2dataiku.llm.providers import MockProvider

from app.services import suggest as suggest_service
from app.services.suggest import (
    parse_suggest_payload,
    visual_recipe_targets,
)

# ---------------------------------------------------------------------------
# Fixtures — a snippet that obviously maps to a GROUPING recipe.
# ---------------------------------------------------------------------------

PYTHON_SOURCE = """\
import pandas as pd
df = pd.read_csv('trades.csv')
result = df.groupby(['book', 'trade_date'])['pnl_usd'].sum().reset_index()
result.to_csv('pnl_by_book.csv', index=False)
"""

CANNED_PAYLOAD: dict[str, object] = {
    "confidence": 0.92,
    "suggested_recipe_type": "GROUPING",
    "transformed_pandas": (
        "import pandas as pd\n"
        "df = pd.read_csv('trades.csv')\n"
        "result = df.groupby(['book', 'trade_date'], as_index=False)"
        "['pnl_usd'].sum()\n"
    ),
    "reasoning": (
        "The snippet aggregates trade rows by book and trade_date — that is "
        "the canonical shape of a GROUPING recipe."
    ),
}


def _patch_provider(monkeypatch, payload: dict) -> MockProvider:  # type: ignore[type-arg]
    canned = json.dumps(payload)
    mock = MockProvider(responses={"Suggest a mapping": canned, "JSON": canned})
    monkeypatch.setattr(
        suggest_service, "resolve_provider", lambda *a, **kw: mock
    )
    return mock


# ---------------------------------------------------------------------------
# Pure-unit tests
# ---------------------------------------------------------------------------


def test_visual_recipe_targets_omits_python_and_code_hatches() -> None:
    targets = set(visual_recipe_targets())
    assert "GROUPING" in targets
    assert "WINDOW" in targets
    assert "PYTHON" not in targets
    assert "SQL_SCRIPT" not in targets
    assert "PYSPARK" not in targets
    # The convenience PREPARE+processor shorthands are present.
    assert "PREPARE+FoldMultipleColumns" in targets
    assert "PREPARE+FilterOnFormula" in targets


def test_parse_suggest_payload_strips_code_fences() -> None:
    fenced = "```json\n" + json.dumps(CANNED_PAYLOAD) + "\n```"
    parsed = parse_suggest_payload(fenced)
    assert parsed["confidence"] == 0.92
    assert parsed["suggested_recipe_type"] == "GROUPING"
    assert "groupby" in parsed["transformed_pandas"]
    assert parsed["reasoning"].startswith("The snippet")


def test_parse_suggest_payload_clamps_confidence() -> None:
    high = parse_suggest_payload(
        json.dumps({**CANNED_PAYLOAD, "confidence": 1.7})
    )
    assert high["confidence"] == 1.0
    low = parse_suggest_payload(
        json.dumps({**CANNED_PAYLOAD, "confidence": -0.3})
    )
    assert low["confidence"] == 0.0


def test_parse_suggest_payload_degrades_unknown_type() -> None:
    """Fabricated recipe types degrade confidence rather than crash."""
    parsed = parse_suggest_payload(
        json.dumps(
            {
                **CANNED_PAYLOAD,
                "confidence": 0.95,
                "suggested_recipe_type": "MADE_UP_TYPE",
            }
        )
    )
    assert parsed["suggested_recipe_type"] == "MADE_UP_TYPE"
    assert parsed["confidence"] <= 0.4


def test_parse_suggest_payload_rejects_missing_fields() -> None:
    with pytest.raises(Exception):
        parse_suggest_payload(json.dumps({"confidence": 0.5}))


# ---------------------------------------------------------------------------
# HTTP integration
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_suggest_mapping_returns_full_shape(client, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Round-trip: source in → confidence + suggested type + rewrite + reasoning."""
    _patch_provider(monkeypatch, CANNED_PAYLOAD)
    resp = await client.post(
        "/suggest-mapping",
        json={"python_source": PYTHON_SOURCE, "provider": "mock"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["suggested_recipe_type"] == "GROUPING"
    assert body["confidence"] == 0.92
    assert "groupby" in body["transformed_pandas"]
    assert body["reasoning"].startswith("The snippet")
    assert body["model"] == "mock"
    assert body["cost_usd"] == 0.0


@pytest.mark.asyncio
async def test_suggest_mapping_logs_to_llm_history(client, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Successful suggest calls land in /llm-history with feature='suggest'."""
    _patch_provider(monkeypatch, CANNED_PAYLOAD)
    await client.post(
        "/suggest-mapping",
        json={
            "python_source": PYTHON_SOURCE,
            "provider": "mock",
            "flow_id": "flow-suggest-1",
        },
    )
    hist = await client.get("/llm-history")
    body = hist.json()
    rows = [r for r in body["records"] if r["feature"] == "suggest"]
    assert rows, "expected at least one llm-history row with feature=suggest"
    last = rows[0]
    assert last["status"] == "success"
    assert last["flow_id"] == "flow-suggest-1"
    assert last["extra"]["suggested_recipe_type"] == "GROUPING"
    assert last["extra"]["confidence"] == 0.92
    assert last["extra"]["source_chars"] == len(PYTHON_SOURCE)


@pytest.mark.asyncio
async def test_suggest_mapping_validation_error_on_empty_source(
    client,
) -> None:  # type: ignore[no-untyped-def]
    resp = await client.post(
        "/suggest-mapping",
        json={"python_source": "", "provider": "mock"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_suggest_mapping_low_confidence_for_unmappable_snippet(
    client, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    """A snippet the LLM can't map cleanly returns confidence < 0.5 — the UI
    treats this as informational (no Apply CTA)."""
    low_payload = {
        "confidence": 0.2,
        "suggested_recipe_type": "PYTHON",
        "transformed_pandas": PYTHON_SOURCE,  # unchanged
        "reasoning": "This snippet uses scikit-learn primitives with no "
        "visual-recipe equivalent in the catalog.",
    }
    _patch_provider(monkeypatch, low_payload)
    resp = await client.post(
        "/suggest-mapping",
        json={
            "python_source": "from sklearn import linear_model\nm = linear_model.Lasso()",
            "provider": "mock",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    # PYTHON is excluded from visual_recipe_targets so this degrades.
    assert body["confidence"] <= 0.4
    assert body["suggested_recipe_type"] == "PYTHON"
