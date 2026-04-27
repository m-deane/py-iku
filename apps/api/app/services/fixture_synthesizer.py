"""Deterministic synthetic fixture-data generator for trading flows.

Used by the Share-as-link feature when the user opts to embed a small
fixture-data snapshot.  Generation is **deterministic** (seeded on the
column name + dataset name) so the same flow always produces the same
fixture rows on the recipient's side — important for diffing and
deterministic e2e replay.

Domain values are taken from real ICE / CME / EEX / NYISO / PJM / EPEX
products; no fictitious commodities or tenors.
"""

from __future__ import annotations

import hashlib
import random
import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any

# ---------------------------------------------------------------------------
# Domain vocabulary — real-only, sourced from public ICE/CME/EEX product specs
# ---------------------------------------------------------------------------

COMMODITIES: list[str] = [
    "Brent",
    "WTI",
    "TTF",
    "NBP",
    "Henry Hub",
    "JKM",
    "API2 Coal",
    "API4 Coal",
    "EUA",
    "PJM West RT",
    "ERCOT North RT",
    "NYISO Zone J",
    "EPEX DE Base",
    "Nordic System",
]

VENUES: list[str] = ["ICE", "CME", "NYMEX", "EEX", "Nasdaq Commodities", "OTC"]

CURRENCIES: list[str] = ["USD", "EUR", "GBP", "NOK", "CHF"]

COUNTERPARTIES: list[str] = [
    "Vitol",
    "Trafigura",
    "Glencore",
    "Mercuria",
    "BP",
    "Shell",
    "TotalEnergies",
    "Equinor",
    "Gunvor",
    "Castleton",
]

DESKS: list[str] = ["Crude", "Gas EU", "Gas US", "Power EU", "Power US", "Coal", "Carbon"]

TRADERS: list[str] = ["mdeane", "jrouse", "kpatel", "amalik", "lschmidt", "cwong"]

SIDES: list[str] = ["BUY", "SELL"]

PRODUCT_TYPES: list[str] = ["FUTURE", "SWAP", "OPTION", "PHYSICAL", "FORWARD"]


# ---------------------------------------------------------------------------
# Column-name → generator routing
# ---------------------------------------------------------------------------


def _seeded_rng(*parts: str) -> random.Random:
    """Return a Random seeded deterministically on the parts.

    Hashing keeps the seed stable across Python invocations even though
    ``hash()`` salts strings between runs.
    """
    h = hashlib.sha256("|".join(parts).encode("utf-8")).digest()
    seed = int.from_bytes(h[:8], "big")
    return random.Random(seed)


def _gen_for_column(
    column: str, row_idx: int, rng: random.Random
) -> Any:
    """Generate a single value for *column* at *row_idx*.

    Routing matches names case-insensitively against keyword fragments.
    """
    name = column.lower()

    # Ids — UUIDs from a deterministic sub-seed so they're stable per row.
    if "trade_id" in name or name.endswith("_id") and "id" not in name[: -3].rstrip("_"):
        # deterministic UUID derived from rng state + row
        sub_seed = rng.getrandbits(128)
        return str(uuid.UUID(int=sub_seed))
    if name in {"id", "uuid"}:
        sub_seed = rng.getrandbits(128)
        return str(uuid.UUID(int=sub_seed))

    # Dates / timestamps
    if "trade_date" in name or "as_of" in name or name == "date":
        anchor = date(2026, 4, 1)
        delta_days = rng.randint(0, 25)
        return (anchor + timedelta(days=delta_days)).isoformat()
    if "settle_date" in name or "value_date" in name:
        anchor = date(2026, 5, 1)
        delta_days = rng.randint(0, 60)
        return (anchor + timedelta(days=delta_days)).isoformat()
    if "timestamp" in name or "ts" == name or name.endswith("_ts"):
        anchor = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)
        offset = timedelta(seconds=rng.randint(0, 25 * 24 * 3600))
        return (anchor + offset).isoformat()

    # Notional / price / qty (uniform numeric ranges with sensible scales)
    if "notional" in name:
        return round(rng.uniform(1_000.0, 1_000_000.0), 2)
    if "price" in name or "px" == name:
        return round(rng.uniform(20.0, 120.0), 4)
    if "quantity" in name or name in {"qty", "lots", "volume"} or "volume" in name:
        return rng.randint(1, 5_000)
    if "pnl" in name:
        return round(rng.uniform(-50_000.0, 50_000.0), 2)
    if "delta" in name or "vega" in name or "gamma" in name:
        return round(rng.uniform(-1.0, 1.0), 4)
    if "fx_rate" in name or name == "rate":
        return round(rng.uniform(0.8, 1.4), 5)

    # Categorical domain attributes
    if "commodity" in name or "underlying" in name:
        return rng.choice(COMMODITIES)
    if "venue" in name or "exchange" in name:
        return rng.choice(VENUES)
    if "currency" in name or name in {"ccy", "ccy1", "ccy2"}:
        return rng.choice(CURRENCIES)
    if "counterparty" in name or "cpty" in name:
        return rng.choice(COUNTERPARTIES)
    if "desk" in name or "book" in name:
        return rng.choice(DESKS)
    if "trader" in name or "user" in name:
        return rng.choice(TRADERS)
    if name == "side" or "buy_sell" in name:
        return rng.choice(SIDES)
    if "product" in name or name == "type":
        return rng.choice(PRODUCT_TYPES)
    if "tenor" in name:
        return rng.choice(["M+1", "M+2", "Q+1", "Q+2", "Cal-27", "Cal-28"])

    # Booleans
    if name.startswith("is_") or name.startswith("has_") or name in {"active", "live"}:
        return rng.random() > 0.5

    # Fallback — short alphanumeric token (deterministic per row).
    return f"{column}-{row_idx:04d}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def synthesize_rows(
    columns: list[str],
    *,
    n_rows: int = 10,
    dataset_name: str = "dataset",
) -> list[dict[str, Any]]:
    """Generate up to *n_rows* deterministic rows for *columns*.

    The seed is derived from ``dataset_name + columns`` so two runs always
    produce identical fixture data (good for diffing in PRs).
    """
    if n_rows <= 0:
        return []
    if n_rows > 100:
        n_rows = 100  # hard cap per request
    rng = _seeded_rng(dataset_name, *columns)
    rows: list[dict[str, Any]] = []
    for i in range(n_rows):
        row: dict[str, Any] = {}
        for col in columns:
            row[col] = _gen_for_column(col, i, rng)
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Schema discovery — find input datasets in a flow and their columns
# ---------------------------------------------------------------------------


def find_input_datasets(flow: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the list of dataset records that look like flow inputs.

    A dataset is considered an "input" when it appears as the source of any
    recipe but is never produced by a recipe (i.e. it's a leaf at the
    upstream end of the DAG).
    """
    datasets = flow.get("datasets") or []
    recipes = flow.get("recipes") or []
    if not isinstance(datasets, list) or not isinstance(recipes, list):
        return []

    consumed: set[str] = set()
    produced: set[str] = set()
    for r in recipes:
        if not isinstance(r, dict):
            continue
        for inp in r.get("inputs") or []:
            if isinstance(inp, str):
                consumed.add(inp)
        for out in r.get("outputs") or []:
            if isinstance(out, str):
                produced.add(out)

    inputs: list[dict[str, Any]] = []
    for d in datasets:
        if not isinstance(d, dict):
            continue
        name = d.get("name")
        if not isinstance(name, str):
            continue
        if name in consumed and name not in produced:
            inputs.append(d)
    return inputs


def _columns_from_dataset(dataset: dict[str, Any]) -> list[str]:
    schema = dataset.get("schema")
    if not isinstance(schema, list):
        return []
    out: list[str] = []
    for col in schema:
        if isinstance(col, str):
            out.append(col)
        elif isinstance(col, dict) and isinstance(col.get("name"), str):
            out.append(str(col["name"]))
    return out


def build_fixture_payload(
    flow: dict[str, Any], *, n_rows: int = 100
) -> dict[str, list[dict[str, Any]]]:
    """Return a ``{dataset_name: [row, …]}`` map for every input dataset."""
    out: dict[str, list[dict[str, Any]]] = {}
    for ds in find_input_datasets(flow):
        name = str(ds["name"])
        cols = _columns_from_dataset(ds)
        if not cols:
            # Fall back to a small canonical trade-blotter schema
            cols = [
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
        out[name] = synthesize_rows(cols, n_rows=n_rows, dataset_name=name)
    return out
