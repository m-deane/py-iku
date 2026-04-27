"""Tests for the Share fixture-data preview/bundle endpoints."""

from __future__ import annotations

import pytest

from app.services.fixture_synthesizer import (
    COMMODITIES,
    CURRENCIES,
    VENUES,
    build_fixture_payload,
    find_input_datasets,
    synthesize_rows,
)


def _flow_with_inputs() -> dict:
    return {
        "flow_name": "trade-blotter",
        "total_recipes": 1,
        "total_datasets": 2,
        "datasets": [
            {
                "name": "trades_raw",
                "type": "Filesystem",
                "schema": [
                    "trade_id",
                    "trade_date",
                    "commodity",
                    "side",
                    "quantity",
                    "price",
                    "notional",
                    "currency",
                    "counterparty",
                    "venue",
                ],
            },
            {
                "name": "trades_clean",
                "type": "Filesystem",
                "schema": [],
            },
        ],
        "recipes": [
            {
                "name": "prepare_trades",
                "type": "PREPARE",
                "inputs": ["trades_raw"],
                "outputs": ["trades_clean"],
            }
        ],
    }


def test_synthesize_rows_is_deterministic() -> None:
    cols = ["trade_id", "commodity", "notional", "currency"]
    a = synthesize_rows(cols, n_rows=10, dataset_name="trades_raw")
    b = synthesize_rows(cols, n_rows=10, dataset_name="trades_raw")
    assert a == b
    assert all(row["commodity"] in COMMODITIES for row in a)
    assert all(row["currency"] in CURRENCIES for row in a)


def test_find_input_datasets_picks_only_leaves() -> None:
    inputs = find_input_datasets(_flow_with_inputs())
    assert [d["name"] for d in inputs] == ["trades_raw"]


def test_build_fixture_payload_caps_at_100() -> None:
    payload = build_fixture_payload(_flow_with_inputs(), n_rows=500)
    assert "trades_raw" in payload
    assert len(payload["trades_raw"]) <= 100
    sample = payload["trades_raw"][0]
    # Schema-derived columns are present
    for col in ("trade_id", "commodity", "venue", "notional"):
        assert col in sample
    assert sample["venue"] in VENUES


def test_canonical_schemas_round_trip_all_columns() -> None:
    """Every canonical column-name family in the catalogue resolves to a value."""
    cols = [
        "trade_id",
        "trade_date",
        "settle_date",
        "commodity",
        "side",
        "quantity",
        "price",
        "notional",
        "pnl",
        "delta",
        "fx_rate",
        "currency",
        "counterparty",
        "desk",
        "trader",
        "venue",
        "tenor",
        "is_active",
        "timestamp",
    ]
    rows = synthesize_rows(cols, n_rows=3, dataset_name="all_cols")
    assert len(rows) == 3
    for row in rows:
        for col in cols:
            assert col in row
            assert row[col] is not None


@pytest.mark.asyncio
async def test_share_fixtures_preview_endpoint(client) -> None:  # type: ignore[no-untyped-def]
    response = await client.post(
        "/share/fixtures/preview",
        json={"flow": _flow_with_inputs(), "n_rows": 3},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["n_rows"] == 3
    names = {d["name"] for d in body["datasets"]}
    assert "trades_raw" in names
    trades = next(d for d in body["datasets"] if d["name"] == "trades_raw")
    assert len(trades["sample_rows"]) == 3


@pytest.mark.asyncio
async def test_share_fixtures_bundle_endpoint(client) -> None:  # type: ignore[no-untyped-def]
    response = await client.post(
        "/share/fixtures/bundle",
        json={"flow": _flow_with_inputs(), "n_rows": 25},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["n_rows"] == 25
    assert "trades_raw" in body["datasets"]
    assert len(body["datasets"]["trades_raw"]) == 25


@pytest.mark.asyncio
async def test_share_fixtures_bundle_caps_n_rows(client) -> None:  # type: ignore[no-untyped-def]
    response = await client.post(
        "/share/fixtures/bundle",
        json={"flow": _flow_with_inputs(), "n_rows": 500},
    )
    # 500 exceeds the schema's le=100 — Pydantic returns a 422.
    assert response.status_code == 422
