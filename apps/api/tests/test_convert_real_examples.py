"""End-to-end regression tests against real textbook scripts (rule mode).

Each script comes from `docs/textbook/_running_example.md` (V1-V5) or one of
`docs/textbook/examples-0[1-4]-*.md` (8 trading examples). The textbook
documents a specific recipe-shape for each script; if the rule-based engine
or the API post-processor regresses, these tests catch it.

These run against the in-process FastAPI app via the standard `client`
fixture, so they require no live network or LLM credentials.
"""

from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# Test scripts — verbatim from docs/textbook/.
# ---------------------------------------------------------------------------

V1_RETAIL = '''import pandas as pd

orders = pd.read_csv("orders.csv")
orders["discount_pct"] = orders["discount_pct"].fillna(0.0)
orders["revenue"] = orders["quantity"] * orders["unit_price"] * (1 - orders["discount_pct"])
orders = orders.rename(columns={"order_date": "ordered_at"})
orders_clean = orders
'''

V2_RETAIL = V1_RETAIL + '''
customers = pd.read_csv("customers.csv")
products = pd.read_csv("products.csv")
orders_enriched = orders_clean.merge(customers, on="customer_id", how="left")
orders_enriched = orders_enriched.merge(products, on="product_id", how="left")
'''

V5_RETAIL = V2_RETAIL + '''
orders_enriched = orders_enriched.sort_values(["customer_id", "ordered_at"])
orders_windowed = orders_enriched.copy()
orders_windowed["rolling_30d_revenue"] = (
    orders_windowed
    .groupby("customer_id")["revenue"]
    .rolling("30D", on="ordered_at")
    .sum()
    .reset_index(level=0, drop=True)
)
lifetime = orders_windowed.groupby("customer_id")["revenue"].sum().rename("lifetime_revenue")
orders_ranked = orders_windowed.merge(lifetime, on="customer_id", how="left")
orders_ranked = orders_ranked.sort_values("lifetime_revenue", ascending=False)
high_value_customers = orders_ranked[orders_ranked["lifetime_revenue"] >= 1000]
remaining_customers = orders_ranked[orders_ranked["lifetime_revenue"] < 1000]
'''

EX01_TRADE_INGESTION = '''import pandas as pd

trades = pd.read_csv("trades.csv")
trades = trades.dropna(subset=["trade_id", "trade_date", "notional"])
trades["trade_date"] = pd.to_datetime(trades["trade_date"]).dt.date
trades["value_date"] = pd.to_datetime(trades["value_date"]).dt.date
trades["commodity_code"] = trades["instrument"].str.extract(r"^([A-Z]+)")
filtered = trades[(trades["notional"] > 0) & (trades["trade_date"] <= "2026-04-26")]
exposure = filtered.pivot(index="book", columns="commodity", values="notional")
exposure.to_csv("trade_blotter.csv")
'''

EX01_TRADE_DEDUP = '''import pandas as pd

endur = pd.read_csv("endur_trades.csv")
allegro = pd.read_csv("allegro_trades.csv")
internal = pd.read_csv("internal_trades.csv")
combined = pd.concat([endur, allegro, internal])
combined = combined.drop_duplicates(subset=["trade_id", "version"])
combined = combined.sort_values("booked_at", ascending=False)
combined.to_json("consolidated_trades.json")
'''

EX02_POSITION_PNL = '''import pandas as pd

trades = pd.read_csv("trades.csv")
recent = trades[trades["trade_date"] >= "2024-01-01"]

curves = pd.read_csv("curves.csv")
priced = recent.merge(curves, on=["commodity", "tenor", "delivery_location"], how="left")
priced["mtm_value"] = (priced["mid_price"] - priced["price"]) * priced["notional"]

exposures = priced.groupby(["book", "commodity", "tenor"]).agg(
    total_notional=("notional", "sum"),
    total_mtm=("mtm_value", "sum"),
    avg_price=("price", "mean"),
    n_trades=("trade_id", "nunique"),
).reset_index()

exposures_sorted = exposures.sort_values(["book", "trade_date"])
rolling_pnl = (
    exposures_sorted.groupby("book")["total_mtm"]
    .rolling("30D", on="trade_date")
    .sum()
    .reset_index()
    .rename(columns={"total_mtm": "rolling_30d_pnl"})
)
top_books = rolling_pnl.nlargest(50, "rolling_30d_pnl")
'''

EX02_PJM_TICKS = '''import pandas as pd

ticks = pd.read_csv("pjm_lmps.csv")
ticks_sorted = ticks.sort_values(["node_id", "timestamp"])
ticks_vwap = (
    ticks_sorted.groupby("node_id")["lmp"]
    .rolling(6, on="timestamp")
    .mean()
    .reset_index()
    .rename(columns={"lmp": "vwap_30min"})
)
ticks_vol = (
    ticks_sorted.groupby("node_id")["lmp"]
    .rolling(12, on="timestamp")
    .std()
    .reset_index()
    .rename(columns={"lmp": "rolling_vol"})
)
'''

EX03_COUNTERPARTY = '''import pandas as pd
trades = pd.read_csv("trades.csv")
counterparties = pd.read_csv("counterparty_master.csv")
features = trades.merge(counterparties, on="counterparty_id", how="left")
features = features.assign(days_since_last_trade=lambda x: x["trade_date"] - "2026-04-26")
features["credit_rating"] = features["credit_rating"].fillna("NR")
features["exposure_bucket"] = pd.qcut(features["current_exposure"], q=5, labels=["Q1", "Q2", "Q3", "Q4", "Q5"])
features = pd.get_dummies(features, columns=["credit_rating"])
features = features.dropna(subset=["days_since_last_trade"])
features.to_parquet("counterparty_features.parquet")
'''

EX03_CURVE_SCD = '''import pandas as pd
ref_date = "2026-04-26"
df = pd.read_csv("curve_history.csv")
cond = (df["effective_date"] <= ref_date) & ((df["end_date"].isna()) | (df["end_date"] > ref_date))
current = df[cond]
history = df[~cond]
current.to_parquet("curves_current.parquet")
history.to_parquet("curves_history.parquet")
'''

EX04_PJM_HUB = '''import pandas as pd

positions = pd.read_csv("lmp_positions.csv")
nodes = pd.read_csv("node_to_zone.csv")

enriched = positions.merge(
    nodes,
    on="node_id",
    how="left",
)

by_zone = enriched.groupby(["zone", "hour_ending"]).agg({
    "volume_mwh": "sum",
    "position_id": "count",
})
'''

EX04_TRADE_EVENTS = '''import pandas as pd

events = pd.read_csv("trade_events.csv")

per_trader = events.groupby("trader_id").agg({
    "trade_id": "nunique",
    "event_id": "count",
})

events["events_in_session"] = events["event_id"].rolling("1H").count()
'''


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _post_rule(client, code: str) -> dict:
    r = await client.post("/convert", json={"code": code, "mode": "rule"})
    assert r.status_code == 200, f"convert failed: HTTP {r.status_code}\n{r.text[:500]}"
    return r.json()


def _recipe_types(resp: dict) -> list[str]:
    return [r["type"] for r in resp["flow"]["recipes"]]


def _dataset_names(resp: dict) -> list[str]:
    return [d["name"] for d in resp["flow"]["datasets"]]


def _datasets_by_role(resp: dict, role: str) -> list[str]:
    return [d["name"] for d in resp["flow"]["datasets"] if d["type"] == role]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


async def test_v1_retail_running_example_pure_prepare(client):
    """V1: a single PREPARE recipe; orders → orders_clean (terminal output)."""
    resp = await _post_rule(client, V1_RETAIL)
    assert _recipe_types(resp) == ["prepare"]
    assert "orders" in _datasets_by_role(resp, "input")
    # The post-sanitizer promotes the terminal intermediate to output.
    assert len(_datasets_by_role(resp, "output")) >= 1
    assert resp["score"]["recipe_count"] == 1
    assert resp["score"]["dataset_count"] >= 2


async def test_v2_retail_join_added(client):
    resp = await _post_rule(client, V2_RETAIL)
    types = _recipe_types(resp)
    assert "prepare" in types
    assert types.count("join") >= 1
    assert {"orders", "customers", "products"} <= set(_datasets_by_role(resp, "input"))


async def test_v5_retail_split_complementary(client):
    """V5: two SPLIT outputs (high_value/remaining); both should be terminal outputs."""
    resp = await _post_rule(client, V5_RETAIL)
    names = _dataset_names(resp)
    outputs = _datasets_by_role(resp, "output")
    assert "high_value_customers" in names
    assert "remaining_customers" in names
    assert "high_value_customers" in outputs
    assert "remaining_customers" in outputs
    # No empty-name placeholder dataset should remain after sanitization.
    assert "" not in names


async def test_ex01_trade_ingestion_validation_recipe_shape(client):
    resp = await _post_rule(client, EX01_TRADE_INGESTION)
    types = _recipe_types(resp)
    # textbook expects 4: prepare, prepare, split, pivot
    assert types == ["prepare", "prepare", "split", "pivot"]
    assert "trades" in _datasets_by_role(resp, "input")
    assert any("pivot" in d.lower() or "blotter" in d.lower() or d == "filtered_pivoted"
               for d in _datasets_by_role(resp, "output"))


async def test_ex01_trade_dedup_to_json_now_terminal_output(client):
    """Wave-2 fix: to_json() / .to_json was previously dropped.

    With the parser-level sink list extended to include to_json, the terminal
    dataset is now correctly classified as an output dataset.
    """
    resp = await _post_rule(client, EX01_TRADE_DEDUP)
    types = _recipe_types(resp)
    assert types == ["stack", "prepare", "sort"]
    assert {"endur", "allegro", "internal"} <= set(_datasets_by_role(resp, "input"))
    # Terminal dataset should be classified as output (via post-sanitizer).
    assert len(_datasets_by_role(resp, "output")) >= 1


async def test_ex02_position_pnl_six_recipes(client):
    resp = await _post_rule(client, EX02_POSITION_PNL)
    types = _recipe_types(resp)
    # textbook: ['split', 'join', 'grouping', 'sort', 'window', 'topn']
    # Post-Bug#1 fix: the analyzer now emits a PREPARE recipe for the
    # mtm_value = (...) * (...) formula that was previously silently
    # dropped. The new shape includes that PREPARE between JOIN and
    # GROUPING. Test asserts the family-level shape (PREPARE optional)
    # so this stays correct whether or not future optimizations merge
    # the PREPARE step into a neighbour.
    assert types[0] == "split"
    assert types[1] == "join"
    # PREPARE may be present (post-Bug#1) or absorbed by the optimizer.
    assert {"grouping", "sort", "window", "topn"}.issubset(set(types))
    # No empty-name dataset placeholder after sanitization.
    assert "" not in _dataset_names(resp)
    # WINDOW input should be re-routed to upstream sort output, not "".
    win = next(r for r in resp["flow"]["recipes"] if r["type"] == "window")
    assert "" not in win["inputs"]


async def test_ex02_pjm_ticks_window_merge(client):
    resp = await _post_rule(client, EX02_PJM_TICKS)
    types = _recipe_types(resp)
    # Optimizer merges the two adjacent WINDOW recipes -> [sort, window]
    assert types == ["sort", "window"]
    # Window should have a real upstream input, not an empty placeholder.
    win = next(r for r in resp["flow"]["recipes"] if r["type"] == "window")
    assert "" not in win["inputs"]
    assert "ticks_sorted" in win["inputs"]


async def test_ex03_counterparty_features(client):
    resp = await _post_rule(client, EX03_COUNTERPARTY)
    types = _recipe_types(resp)
    assert types == ["join", "prepare", "prepare", "prepare"]
    assert {"trades", "counterparties"} <= set(_datasets_by_role(resp, "input"))


async def test_ex03_curve_scd_consolidated_split(client):
    """Complementary df[cond] / df[~cond] must consolidate into ONE split recipe."""
    resp = await _post_rule(client, EX03_CURVE_SCD)
    types = _recipe_types(resp)
    assert types == ["split"]
    splits = [r for r in resp["flow"]["recipes"] if r["type"] == "split"]
    assert len(splits) == 1
    assert set(splits[0]["outputs"]) == {"current", "history"}
    # Both outputs are terminal sinks (to_parquet) -> classified as outputs.
    assert {"current", "history"} <= set(_datasets_by_role(resp, "output"))


async def test_ex04_pjm_hub_join_grouping(client):
    resp = await _post_rule(client, EX04_PJM_HUB)
    types = _recipe_types(resp)
    assert types == ["join", "grouping"]
    assert {"positions", "nodes"} <= set(_datasets_by_role(resp, "input"))


async def test_ex04_trade_events_window_grouping(client):
    """events['events_in_session'] subscript-target name should be normalized."""
    resp = await _post_rule(client, EX04_TRADE_EVENTS)
    types = _recipe_types(resp)
    assert set(types) == {"grouping", "window"}
    # The bracket-notation name from the assignment target gets sanitized.
    names = _dataset_names(resp)
    assert not any("[" in n or "]" in n for n in names)


# ---------------------------------------------------------------------------
# Cross-cutting invariants
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "code",
    [
        V1_RETAIL,
        V2_RETAIL,
        V5_RETAIL,
        EX01_TRADE_INGESTION,
        EX01_TRADE_DEDUP,
        EX02_POSITION_PNL,
        EX02_PJM_TICKS,
        EX03_COUNTERPARTY,
        EX03_CURVE_SCD,
        EX04_PJM_HUB,
        EX04_TRADE_EVENTS,
    ],
    ids=[
        "v1_retail",
        "v2_retail",
        "v5_retail",
        "ex01_trade_ingestion",
        "ex01_trade_dedup",
        "ex02_position_pnl",
        "ex02_pjm_ticks",
        "ex03_counterparty",
        "ex03_curve_scd",
        "ex04_pjm_hub",
        "ex04_trade_events",
    ],
)
async def test_no_empty_dataset_references_after_sanitize(client, code):
    """Wave-2 invariant: no recipe input/output should reference the empty string.

    Pre-fix, chained ``groupby(...).rolling(...).reset_index().rename(...)``
    leaks ``""`` into recipe.inputs and into the datasets list. The
    sanitizer rewrites those references and drops the placeholder dataset.
    """
    resp = await _post_rule(client, code)
    for recipe in resp["flow"]["recipes"]:
        assert "" not in recipe["inputs"], (
            f"{recipe['name']} has empty-string in inputs: {recipe['inputs']}"
        )
        assert "" not in recipe["outputs"], (
            f"{recipe['name']} has empty-string in outputs: {recipe['outputs']}"
        )
    for ds in resp["flow"]["datasets"]:
        assert ds["name"] != "", "empty-name dataset placeholder should be scrubbed"


@pytest.mark.parametrize(
    "code",
    [V1_RETAIL, EX01_TRADE_INGESTION, EX01_TRADE_DEDUP, EX02_POSITION_PNL,
     EX03_COUNTERPARTY, EX03_CURVE_SCD],
)
async def test_pydantic_dataset_references_validate(client, code):
    """Every recipe input/output must point at a known dataset (Pydantic invariant)."""
    resp = await _post_rule(client, code)
    known = {d["name"] for d in resp["flow"]["datasets"]}
    for r in resp["flow"]["recipes"]:
        for ref in list(r["inputs"]) + list(r["outputs"]):
            assert ref in known, f"recipe {r['name']} references unknown {ref!r}"


async def test_score_dataset_count_matches_datasets_array(client):
    resp = await _post_rule(client, V5_RETAIL)
    assert resp["score"]["dataset_count"] == len(resp["flow"]["datasets"])
