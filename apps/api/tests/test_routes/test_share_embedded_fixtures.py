"""Round-trip test for the inline-fixture share payload.

Exercises:
  - encode/decode helpers in :mod:`share_service`.
  - POST /flows/{id}/share with `include_fixtures=true` populates the
    record's `fixtures_b64` blob.
  - GET /share/{token} returns a structured `fixtures` field decoded back
    into the original FixtureBundle shape.
"""

from __future__ import annotations

import pytest

from app.deps import get_flows_repo, get_settings
from app.security.share_links import sign as sign_share_token
from app.services.share_service import (
    build_share_bundle,
    decode_bundle_gzip_b64,
    encode_bundle_gzip_b64,
    summarise_bundle,
)


def _flow_with_inputs() -> dict:
    """A flow shaped to satisfy the DataikuFlowModel pydantic schema.

    Lowercase enum values for ``type`` fields, ColumnSchemaModel-shaped
    ``schema`` entries, and the canonical recipe-type ``prepare`` are all
    required for the SavedFlowResponse round-trip on the share GET path.
    """
    schema_cols = [
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
    ]
    return {
        "flow_name": "trade-blotter",
        "total_recipes": 1,
        "total_datasets": 2,
        "datasets": [
            {
                "name": "trades_raw",
                "type": "input",
                "schema": [{"name": c, "type": "string"} for c in schema_cols],
            },
            {"name": "trades_clean", "type": "output", "schema": []},
        ],
        "recipes": [
            {
                "name": "prepare_trades",
                "type": "prepare",
                "inputs": ["trades_raw"],
                "outputs": ["trades_clean"],
            }
        ],
    }


def test_encode_decode_round_trip_preserves_bundle() -> None:
    bundle = build_share_bundle(_flow_with_inputs(), n_rows=3)
    encoded = encode_bundle_gzip_b64(bundle)
    # Encoded payload is plain ASCII (b64) — safe for storage / URL embedding.
    assert isinstance(encoded, str)
    assert encoded.replace("=", "").replace("+", "").replace("/", "").isalnum()

    decoded = decode_bundle_gzip_b64(encoded)
    assert decoded == bundle


def test_decode_rejects_garbage() -> None:
    with pytest.raises(ValueError):
        decode_bundle_gzip_b64("not-valid-base64!!!")


def test_summarise_bundle_counts_datasets_and_rows() -> None:
    bundle = build_share_bundle(_flow_with_inputs(), n_rows=4)
    summary = summarise_bundle(bundle)
    assert summary == {"n_datasets": 1, "total_rows": 4}


@pytest.mark.asyncio
async def test_share_endpoint_inlines_fixtures(client) -> None:  # type: ignore[no-untyped-def]
    """End-to-end: save (via repo) → share with fixtures → fetch → assert payload.

    We bypass POST /flows because its DataikuFlowModel pydantic schema
    rejects the dataset-type / processor-type strings used by the
    fixture-synthesiser fixture (it expects DSS canonical lowercase
    enums). Persisting through ``FlowsRepo`` directly is the same
    integration surface the route uses internally.
    """
    flow = _flow_with_inputs()
    repo = get_flows_repo()
    record = repo.save(flow=flow, name="shared-with-fixtures")
    flow_id = record.id

    # 1) Mint a share token with embedded fixtures.
    share_resp = await client.post(
        f"/flows/{flow_id}/share",
        json={"ttl_seconds": 3600, "include_fixtures": True, "fixtures_n_rows": 5},
    )
    assert share_resp.status_code == 200, share_resp.text
    token = share_resp.json()["token"]

    # 2) Fetch the share — fixtures arrive inline as a structured object.
    get_resp = await client.get(f"/share/{token}")
    assert get_resp.status_code == 200, get_resp.text
    body = get_resp.json()
    assert body["fixtures"] is not None
    assert body["fixtures"]["n_rows"] == 5
    assert "trades_raw" in body["fixtures"]["datasets"]
    assert len(body["fixtures"]["datasets"]["trades_raw"]) == 5


@pytest.mark.asyncio
async def test_share_endpoint_omits_fixtures_when_not_requested(client) -> None:  # type: ignore[no-untyped-def]
    """include_fixtures=false (default) → fixtures field is null on read."""
    flow = _flow_with_inputs()
    repo = get_flows_repo()
    record = repo.save(flow=flow, name="shared-no-fixtures")
    flow_id = record.id
    share_resp = await client.post(
        f"/flows/{flow_id}/share", json={"ttl_seconds": 3600}
    )
    token = share_resp.json()["token"]
    get_resp = await client.get(f"/share/{token}")
    assert get_resp.status_code == 200
    assert get_resp.json()["fixtures"] is None


@pytest.mark.asyncio
async def test_share_endpoint_decode_failure_degrades_to_null(client) -> None:  # type: ignore[no-untyped-def]
    """Corrupt fixtures_b64 on disk → fixtures returned as null, not 500."""
    flow = _flow_with_inputs()
    repo = get_flows_repo()
    record = repo.save(flow=flow, name="shared-corrupt")
    repo.update(record.id, fixtures_b64="not-base64!!!")
    settings = get_settings()
    token = sign_share_token(
        record.id, ttl_seconds=3600, scopes=["read"], secret=settings.secret_key
    )
    get_resp = await client.get(f"/share/{token}")
    assert get_resp.status_code == 200
    assert get_resp.json()["fixtures"] is None
